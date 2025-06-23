# modified phishintention model
import time
from datetime import datetime
import argparse
import os
import torch
import cv2
from configs import load_config
from modules.awl_detector import pred_rcnn, vis, find_element_type
from modules.logo_matching import new_check_domain_brand_inconsistency
from modules.crp_classifier import credential_classifier_mixed, html_heuristic
from modules.crp_locator import crp_locator
from utils.web_utils import driver_loader
from tqdm import tqdm
import re
from memory_profiler import profile
from modules.dynamic_brand_detection import DynamicBrandDetector

# Voice detection imports
from Synthetic_Voice_Detection_Vocoder_Artifacts.eval import detect_ai_voice
from modules.voice_content_analysis import analyze_voice_content

# check
os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Set your OpenAI API key here
your_openai_api_key = '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'

# Create a custom print function that logs to file
log_file_path = '/home/tiffanybao/PhishIntention/results/prompts_printed.txt'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

def log_print(*args, **kwargs):
    # Get the original print output as a string
    import sys
    from io import StringIO
    
    # First, print to console as normal
    print(*args, **kwargs)
    
    # Now, capture what would have been printed to a string
    temp_out = StringIO()
    print(*args, file=temp_out, **kwargs)
    output = temp_out.getvalue()
    
    # Append to the log file
    with open(log_file_path, 'a') as f:
        f.write(output)


class PhishIntentionWrapper:
    _caller_prefix = "PhishIntentionWrapper"
    _DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

    def __init__(self):
        self._load_config()
        self.dynamic_detector = DynamicBrandDetector(api_key=your_openai_api_key)

    def _load_config(self):
        self.AWL_MODEL, self.CRP_CLASSIFIER, self.CRP_LOCATOR_MODEL, self.SIAMESE_MODEL, self.OCR_MODEL, \
            self.SIAMESE_THRE, self.LOGO_FEATS, self.LOGO_FILES, self.DOMAIN_MAP_PATH = load_config()
        # ...=load_config(reload_targetlist=True)
        log_print(f'Length of reference list = {len(self.LOGO_FEATS)}')

    def analyze_voice(
        self,
        wav_path,
        model_path="models/librifake_pretrained_lambda0.5_epoch_25.pth",
        config_path="Synthetic_Voice_Detection_Vocoder_Artifacts/model_config_RawNet.yaml",
        openai_api_key=your_openai_api_key
    ):
        """
        Analyze a wav file for AI-generation and phishing content.
        Returns a dict with:
            - voiceAI_score: float [0, 1]
            - voiceAI_weight: int (3 or 8)
            - voice_content_scores: dict (keys: asking_for_money, asking_for_password, etc.)
            - transcript: str
            - gpt_response: str
            - final_voice_score: float
        """
        # ---- AI-generated detection ----
        model_full_path = os.path.join(os.path.dirname(__file__), model_path)
        config_full_path = os.path.join(os.path.dirname(__file__), config_path)

        ai_result = detect_ai_voice(
            wav_path,
            model_full_path,
            config_path=config_full_path,
            device=self._DEVICE
        )
        ai_fake_score = ai_result.get('ai_fake_score', 0.0)
        ai_weight = 8 if ai_fake_score > 0.8 else 3

        # ---- Content phishing detection ----
        content_result = analyze_voice_content(
            wav_path,
            openai_api_key=openai_api_key or your_openai_api_key
        )
        transcript = content_result.get('transcript', '')
        voice_content_scores = content_result.get('voice_content_scores', {
            "asking_for_money": 0,
            "asking_for_password": 0,
            "asking_for_personal_info": 0,
            "other_suspicious_content": 0
        })
        gpt_response = content_result.get('gpt_response', '')

        # ---- Calculate final score (leave fusion for main.py, just return everything) ----
        return {
            "voiceAI_score": ai_fake_score,
            "voiceAI_weight": ai_weight,
            "voice_content_scores": voice_content_scores,
            "transcript": transcript,
            "gpt_response": gpt_response,
            "final_voice_score": None  # leave this for fusion in main.py!
        }

    '''PhishIntention'''
    # @profile

    def test_orig_phishintention(self, url, screenshot_path, save_vectors=True, vector_file=None):
        if save_vectors and vector_file is None:
            vector_file = os.path.join('/home/tiffanybao/PhishIntention/results', 'image_num_vector.csv')
    
        waive_crp_classifier = False
        phish_category = 0  # 0 for benign, 1 for phish, default is benign
        pred_target = None
        matched_domain = None
        siamese_conf = None
        awl_detect_time = 0
        logo_match_time = 0
        crp_class_time = 0
        crp_locator_time = 0
        used_gpt = 0  # Initialize GPT usage tracking
        is_mismatch = False
        is_crp = False
        has_login_elements = False
        has_password_field = False
        logo_pred_boxes = None
        cre_pred = 1  # Default to non-CRP
        log_print("Entering PhishIntention")
        log_print(f"Analyzing URL: {url}")

        # Define a helper function to save feature vector before each return
        def save_feature_vector():
            if not save_vectors:
                return
                
            # Define feature names for the CSV header
            feature_names = [
                "folder", "url", "has_logo", "brand_matched", "brand_confidence", "domain_brand_mismatch",
                "has_login_elements", "has_password_field", "page_has_security_indicators",
                "image_quality_score", "logo_size_proportion", "logo_position_typical", 
                "used_gpt_detection", "gpt_confidence", "is_crp", "domain_match_score", 
                "phish_score"
            ]
            
            # Create a dictionary of features
            image_features = {
                # Logo and branding features
                "has_logo": (logo_pred_boxes is not None) and   len(logo_pred_boxes) > 0,
                "brand_matched": pred_target is not None,
                "brand_confidence": float(siamese_conf) if siamese_conf is not None else 0.0,
                "domain_brand_mismatch": False,
                
                # Page layout features
                "has_login_elements": has_login_elements,
                "has_password_field": has_password_field,
                "page_has_security_indicators": "https" in url.lower(),
                
                # Visual quality metrics
                "image_quality_score": 0.5,
                
                # Size and position metrics
                "logo_size_proportion": 0.0,
                "logo_position_typical": False,
                
                # Meta-features
                "used_gpt_detection": used_gpt,
                "gpt_confidence": 0.85 if used_gpt == 1 and pred_target is not None else 0.0,
                
                # Additional features from PhishIntention
                "is_crp": is_crp,
                "domain_match_score": 0.0,
                "phish_score": float(phish_category)
            }
            
            # Check domain-brand mismatch if we have brand and domain info
            if matched_domain is not None and pred_target is not None:
                from tldextract import tldextract
                current_domain = tldextract.extract(url).domain
                
                # Check if current domain is in the matched domains
                domain_match = False
                for domain in matched_domain:
                    expected_domain = tldextract.extract(domain).domain
                    if current_domain.lower() == expected_domain.lower():
                        domain_match = True
                        break
                        
                image_features["domain_brand_mismatch"] = not domain_match
                image_features["domain_match_score"] = 1.0 if domain_match else 0.0
            
            # Update visual quality score
            if used_gpt == 1 and pred_target is not None:
                image_features["image_quality_score"] = 0.7
            elif pred_target is not None:
                image_features["image_quality_score"] = 0.8
            
            # Calculate logo size and position if we have logo boxes
            if logo_pred_boxes is not None and len(logo_pred_boxes) > 0:
                import cv2
                img = cv2.imread(screenshot_path)
                if img is not None:
                    img_height, img_width = img.shape[:2]
                    page_area = img_height * img_width
                    
                    logo_box = logo_pred_boxes[0]
                    logo_width = logo_box[2] - logo_box[0]
                    logo_height = logo_box[3] - logo_box[1]
                    logo_area = logo_width * logo_height
                    
                    image_features["logo_size_proportion"] = logo_area / page_area
                    
                    logo_center_x = (logo_box[0] + logo_box[2]) / 2
                    logo_center_y = (logo_box[1] + logo_box[3]) / 2
                    
                    is_top_area = logo_center_y < img_height * 0.3
                    is_left_area = logo_center_x < img_width * 0.3
                    is_center_horizontal = img_width * 0.3 < logo_center_x < img_width * 0.7
                    
                    image_features["logo_position_typical"] = is_top_area and (is_left_area or is_center_horizontal)
            
            # Refine phishing score
            if pred_target is not None:
                if image_features["domain_brand_mismatch"] and image_features["is_crp"]:
                    image_features["phish_score"] = max(image_features["phish_score"], 0.9)
                elif image_features["domain_brand_mismatch"]:
                    image_features["phish_score"] = max(image_features["phish_score"], 0.6)
            
            # Convert features to numeric values for the CSV
            numeric_features = {}
            for key, value in image_features.items():
                if isinstance(value, bool):
                    numeric_features[key] = 1.0 if value else 0.0
                elif isinstance(value, (int, float)):
                    numeric_features[key] = float(value)
                elif value is None:
                    numeric_features[key] = 0.0
            
            # Extract folder name from screenshot path
            folder = os.path.basename(os.path.dirname(screenshot_path))
            
            # Create the CSV row
            csv_row = [
                folder,
                url,
                numeric_features.get("has_logo", 0.0),
                numeric_features.get("brand_matched", 0.0),
                numeric_features.get("brand_confidence", 0.0),
                numeric_features.get("domain_brand_mismatch", 0.0),
                numeric_features.get("has_login_elements", 0.0),
                numeric_features.get("has_password_field", 0.0),
                numeric_features.get("page_has_security_indicators", 0.0),
                numeric_features.get("image_quality_score", 0.5),
                numeric_features.get("logo_size_proportion", 0.0),
                numeric_features.get("logo_position_typical", 0.0),
                numeric_features.get("used_gpt_detection", 0.0),
                numeric_features.get("gpt_confidence", 0.0),
                numeric_features.get("is_crp", 0.0),
                numeric_features.get("domain_match_score", 0.0),
                numeric_features.get("phish_score", 0.0)
                
            ]
            
            # Write to CSV file
            import csv
            file_exists = os.path.isfile(vector_file)
            
            with open(vector_file, mode='a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(feature_names)
                writer.writerow(csv_row)
            
            return numeric_features


        while True:

            ####################### Step1: Layout detector ##############################################
            start_time = time.time()
            pred_boxes, pred_classes, _ = pred_rcnn(im=screenshot_path, predictor=self.AWL_MODEL)
            awl_detect_time += time.time() - start_time

            if pred_boxes is not None:
                pred_boxes = pred_boxes.numpy()
                pred_classes = pred_classes.numpy()
            plotvis = vis(screenshot_path, pred_boxes, pred_classes)

            # If no element is reported
            if pred_boxes is None or len(pred_boxes) == 0:
                log_print('No element is detected, reported as benign')
                image_feature = save_feature_vector()  # Add vector generation before return
                return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                            str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                            pred_boxes, pred_classes, used_gpt, is_crp, has_login_elements, has_password_field, logo_pred_boxes,image_feature

            logo_pred_boxes, _ = find_element_type(pred_boxes, pred_classes, bbox_type='logo')
            if logo_pred_boxes is None or len(logo_pred_boxes) == 0:
                log_print('No logo is detected, reported as benign')
                image_feature = save_feature_vector()  # Add vector generation before return
                return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                            str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                            pred_boxes, pred_classes, used_gpt, is_crp, has_login_elements, has_password_field, logo_pred_boxes,image_feature

            log_print('Entering siamese')
            log_print(f'Number of logo boxes: {len(logo_pred_boxes)}')

            ######################## Step2: Siamese (Logo matcher) ########################################
            start_time = time.time()
            pred_target, matched_domain, matched_coord, siamese_conf, is_mismatch = new_check_domain_brand_inconsistency(logo_boxes=logo_pred_boxes,
                                                                                domain_map_path=self.DOMAIN_MAP_PATH,
                                                                                model=self.SIAMESE_MODEL,
                                                                                ocr_model=self.OCR_MODEL,
                                                                                logo_feat_list=self.LOGO_FEATS,
                                                                                file_name_list=self.LOGO_FILES,
                                                                                url=url,
                                                                                shot_path=screenshot_path,
                                                                                ts=self.SIAMESE_THRE)
            
            logo_match_time += time.time() - start_time
            log_print(f'Siamese result: pred_target={pred_target}, siamese_conf={siamese_conf}')

            if pred_target is None:
                log_print('Did not match to any brand, trying dynamic gpt detection')
                original_pred_target = pred_target # Store the original pred_target for logging purposes

                ########### Added dynamic detection ############
                dynamic_brand = self.dynamic_detector.analyze_logo(screenshot_path)
                
                # if dynamic_brand is not None :
                if dynamic_brand is not None and dynamic_brand.lower() != "none":

                    # Mark as using GPT only if it successfully identified a brand
                    used_gpt = 1
                    log_print(f'Dynamically detected brand using GPT: {dynamic_brand}')
                    log_print(f'Before GPT: pred_target={original_pred_target}, siamese_conf={siamese_conf}')
                    log_print(f'Before GPT: now starting to match the domains...')
                    
                    # Always use the same confidence value for GPT detections
                    siamese_conf = 0.85  # Consistent confidence for GPT



                    ########## Start matching domain ##########
                    import pickle
                    from tldextract import tldextract

                    # Load the domain mapping dictionary that maps brands to their legitimate domains
                    with open(self.DOMAIN_MAP_PATH, 'rb') as handle:
                        domain_map = pickle.load(handle)
                    
                    # Normalize the brand name to handle case and spacing variations (paypal)
                    normalized_brand = dynamic_brand.lower().replace(' ', '')  # "paypal"
                    expected_domains = []
                    
                    # Search through the domain map to find the normalized brand
                    for brand_key in domain_map.keys():
                        # Check if our normalized brand matches any key in the domain map
                        if normalized_brand in brand_key.lower() or brand_key.lower() in normalized_brand:
                            # If found, use the domains associated with that brand
                            expected_domains = domain_map[brand_key]  # ['paypal.com', 'paypal.me', etc.]
                            pred_target = brand_key  # Use official brand name from map
                            break

                    # If brand wasn't in domain map, use fallback
                    if not expected_domains:
                        pred_target = dynamic_brand  # "PayPal"
                        expected_domains = [f"{normalized_brand}.com"]  # ['paypal.com']
                    
                    # Extract just the domain from the current URL (paypal)
                    current_domain = tldextract.extract(url).domain  # "paypal" from "www.paypal.com/hk/home"
                    
                    # Check if current domain matches any expected domain
                    domain_match = False
                    for domain in expected_domains:
                        expected_domain = tldextract.extract(domain).domain  # Extract just the domain part
                        if current_domain.lower() == expected_domain.lower():  # Case-insensitive comparison
                            domain_match = True
                            break
                    
                    if domain_match:
                        # We're on a legitimate domain for this brand
                        log_print(f"Domain matches brand {dynamic_brand}, legitimate site")
                        is_mismatch = False # Domain matches, not phishing
                        # Still record the brand detection for reporting purposes but mark as benign
                        # siamese_conf = 0.85  # Default high confidence for GPT-detected brands
                        pred_target = dynamic_brand
                        matched_domain = expected_domains

                        # Set matched_coord for visualization
                        if matched_coord is None and len(logo_pred_boxes) > 0:
                            matched_coord = logo_pred_boxes[0]
                            
                        # Return early as benign but with brand identification
                        image_feature = save_feature_vector()  # Add vector generation before return
                        return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                                str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                                pred_boxes, pred_classes, used_gpt, is_crp, has_login_elements, has_password_field, logo_pred_boxes,image_feature
                    
                    else:
                        # Domain inconsistency - potential phishing
                        matched_domain = expected_domains  # Keep the expected domains for reporting
                        log_print(f"Domain inconsistency detected: {dynamic_brand} brand on {current_domain}, potential phishing")
                        is_mismatch = True # Domain mismatch detected
                
                        if matched_coord is None and len(logo_pred_boxes) > 0:
                            matched_coord = logo_pred_boxes[0]  # Use first logo box for visualization

                    log_print(f'After GPT: pred_target={pred_target}, matched_domain={matched_domain}, siamese_conf={siamese_conf}')
                        
                
                
                else: # GPT also says this logo is None 
                    log_print('Even with help of GPT, still did not match to any brand, report as benign')
                    used_gpt = 1
                    image_feature = save_feature_vector()  # Add vector generation before return
                    return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                                str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                                pred_boxes, pred_classes, used_gpt, is_crp, has_login_elements, has_password_field, logo_pred_boxes,image_feature

            ######################## Step3: CRP classifier (if a target is reported) #################################
            log_print('A target is reported, enter CRP classifier')
            if waive_crp_classifier:  # only run dynamic analysis ONCE
                break

            html_path = screenshot_path.replace("shot.png", "html.txt")
            start_time = time.time()
            cre_pred = html_heuristic(html_path)
            log_print(f'HTML heuristic result: {cre_pred} (0 = CRP, 1 = non-CRP)')
            if cre_pred == 1:  # if HTML heuristic report as nonCRP
                # CRP classifier
                cre_pred = credential_classifier_mixed(img=screenshot_path,
                                                        coords=pred_boxes,
                                                        types=pred_classes,
                                                        model=self.CRP_CLASSIFIER)
            crp_class_time += time.time() - start_time
            log_print(f'CRP classification result: {cre_pred} (0 = CRP, 1 = non-CRP)')

            ######################## Step4: Dynamic analysis #################################
            if cre_pred == 1:
                log_print('After credential_classifier_mixed detailed checking, This firstpage is a Non-CRP page, enter dynamic analysis')
                # # load driver ONCE!
                driver = driver_loader()
                log_print('Finish loading webdriver')
                # load chromedriver
                url, screenshot_path, successful, process_time = crp_locator(url=url,
                                                                            screenshot_path=screenshot_path,
                                                                            cls_model=self.CRP_CLASSIFIER,
                                                                            ele_model=self.AWL_MODEL,
                                                                            login_model=self.CRP_LOCATOR_MODEL,
                                                                            driver=driver)
                crp_locator_time += process_time
                driver.quit()

                waive_crp_classifier = True  # only run dynamic analysis ONCE

                # If dynamic analysis did not reach a CRP
                if not successful:
                    log_print('Dynamic analysis cannot find any link redirected to a CRP page, report as benign')
                    image_feature = save_feature_vector()  # Add vector generation before return
                    return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                            str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                            pred_boxes, pred_classes, used_gpt, is_crp, has_login_elements, has_password_field, logo_pred_boxes,image_feature

                else:  # dynamic analysis successfully found a CRP
                    # log_print('Dynamic analysis found a CRP, go back to layout detector')
                    log_print('Dynamic analysis confirmed CRP, finalizing classification')

                    cre_pred = 0  # Force CRP classification
                    is_crp = True
                    break  

            else:  # already a CRP page
                log_print('Already a CRP, continue')
                break

        ######################## Step5: Return #################################        
        if pred_target is not None:
            if is_mismatch:  # Any domain mismatch
                if cre_pred == 0:  # With CRP
                    phish_category = 1  # Definite phishing
                else:  # Mismatch without CRP
                    phish_category = 0.5  # Suspicious but not confirmed
            elif cre_pred == 0:  # Matching domain + CRP
                phish_category = 0  # Legitimate
            else:  # Matching domain + no CRP
                phish_category = 0  # Legitimate

            log_print(f'Adding annotation to visualization: Target: {pred_target} with confidence {siamese_conf}')
            if matched_coord is not None:
                cv2.putText(plotvis, "Target: {} with confidence {:.4f}".format(pred_target, siamese_conf),
                            (int(matched_coord[0] + 20), int(matched_coord[1] + 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
                
        # Final logging before return
        log_print(f'Final results: phish_category={phish_category}, pred_target={pred_target}, matched_domain={matched_domain}, siamese_conf={siamese_conf}, used_gpt={used_gpt}')


        # Ensure we return more information as required for the feature extraction purpose
        is_crp = (cre_pred == 0) if 'cre_pred' in locals() else False
        has_login_elements = False
        has_password_field = False

        # Check for login elements and password fields if we have the data
        if pred_boxes is not None and len(pred_boxes) > 0:
            # Find input boxes
            input_pred_boxes, _ = find_element_type(pred_boxes, pred_classes, bbox_type='input')
            button_pred_boxes, _ = find_element_type(pred_boxes, pred_classes, bbox_type='button')
            
            has_login_elements = (
                (input_pred_boxes is not None and len(input_pred_boxes) > 0) or
                (button_pred_boxes is not None and len(button_pred_boxes) > 0)
            )
            
            # Check HTML for password field
            html_path = screenshot_path.replace("shot.png", "html.txt")
            if os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                    html_content = f.read()
                    has_password_field = 'type="password"' in html_content

        # Generate and save feature vector before the final return
        image_feature = save_feature_vector()

        return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                pred_boxes, pred_classes, used_gpt, is_crp, has_login_elements, has_password_field, logo_pred_boxes,image_feature




if __name__ == '__main__':

    '''run'''
    today = datetime.now().strftime('%Y%m%d')

    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, type=str)
    parser.add_argument("--output_txt", default=f'{today}_results.txt', help="Output txt path")
    args = parser.parse_args()

    request_dir = args.folder
    phishintention_cls = PhishIntentionWrapper()
    result_txt = args.output_txt

    os.makedirs(request_dir, exist_ok=True)
    
    # Clear log file at the start of a new run
    with open(log_file_path, 'w') as f:
        f.write(f"=== New Run Started at {datetime.now()} ===\n")

    for folder in tqdm(os.listdir(request_dir)):
        html_path = os.path.join(request_dir, folder, "html.txt")
        screenshot_path = os.path.join(request_dir, folder, "shot.png")
        info_path = os.path.join(request_dir, folder, 'info.txt')

        if not os.path.exists(screenshot_path):
            continue

        if os.path.exists(info_path):
            url = open(info_path).read()
        else:
            url = "https://" + folder

        if os.path.exists(result_txt) and url in open(result_txt, encoding='ISO-8859-1').read():
            continue

        _forbidden_suffixes = r"\.(mp3|wav|wma|ogg|mkv|zip|tar|xz|rar|z|deb|bin|iso|csv|tsv|dat|txt|css|log|sql|xml|sql|mdb|apk|bat|bin|exe|jar|wsf|fnt|fon|otf|ttf|ai|bmp|gif|ico|jp(e)?g|png|ps|psd|svg|tif|tiff|cer|rss|key|odp|pps|ppt|pptx|c|class|cpp|cs|h|java|sh|swift|vb|odf|xlr|xls|xlsx|bak|cab|cfg|cpl|cur|dll|dmp|drv|icns|ini|lnk|msi|sys|tmp|3g2|3gp|avi|flv|h264|m4v|mov|mp4|mp(e)?g|rm|swf|vob|wmv|doc(x)?|odt|rtf|tex|txt|wks|wps|wpd)$"
        if re.search(_forbidden_suffixes, url, re.IGNORECASE):
            continue

        # Log site being processed
        with open(log_file_path, 'a') as f:
            f.write(f"\n\n===== Processing folder: {folder}, URL: {url} =====\n")

        # Extract just the filename from the result_txt path without the extension
        result_txt_basename = os.path.basename(result_txt)
        result_txt_name = os.path.splitext(result_txt_basename)[0]  # This gives you "testNum1" from "testNum1.txt"
        # Create the directory for storing vector files
        vector_dir = os.path.join('/home/tiffanybao/PhishIntention/results', 'image_vec')
        os.makedirs(vector_dir, exist_ok=True)
        # Set the vector filename to match the result_txt name but with .csv extension
        vector_file = os.path.join(vector_dir, f"{result_txt_name}.csv")


        phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                runtime_breakdown, pred_boxes, pred_classes, used_gpt, is_crp, \
                has_login_elements, has_password_field, logo_pred_boxes,img_vec = phishintention_cls.test_orig_phishintention(
                    url, screenshot_path, save_vectors=True, vector_file=vector_file)
        try:
            with open(result_txt, "a+", encoding='ISO-8859-1') as f:
                f.write(folder + "\t")
                f.write(url + "\t")
                f.write(str(phish_category) + "\t") 
                f.write(str(pred_target) + "\t")  # write top1 prediction only
                f.write(str(matched_domain) + "\t")
                f.write(str(siamese_conf) + "\t")
                # f.write(runtime_breakdown + "\t")
                f.write(str(used_gpt) + "\n")  # Add GPT usage flag
        except UnicodeError:
            with open(result_txt, "a+", encoding='utf-8') as f:
                f.write(folder + "\t")
                f.write(url + "\t")
                f.write(str(phish_category) + "\t")
                f.write(str(pred_target) + "\t")  # write top1 prediction only
                f.write(str(matched_domain) + "\t")
                f.write(str(siamese_conf) + "\t") 
                # f.write(runtime_breakdown + "\t")
                f.write(str(used_gpt) + "\n")  # Add GPT usage flag

        # Generate predict.png for phishing sites AND for legitimate sites where a brand was detected
        if phish_category == 1 :
            os.makedirs(os.path.join(request_dir, folder), exist_ok=True)
            cv2.imwrite(os.path.join(request_dir, folder, "predict.png"), plotvis)
        elif  pred_target is not None:
            os.makedirs(os.path.join(request_dir, folder), exist_ok=True)
            cv2.imwrite(os.path.join(request_dir, folder, "Logo_matched_but_benign.png"), plotvis)

