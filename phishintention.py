# import time
# from datetime import datetime
# import argparse
# import os
# import torch
# import cv2
# from configs import load_config
# from modules.awl_detector import pred_rcnn, vis, find_element_type
# from modules.logo_matching import check_domain_brand_inconsistency
# from modules.crp_classifier import credential_classifier_mixed, html_heuristic
# from modules.crp_locator import crp_locator
# from utils.web_utils import driver_loader
# from tqdm import tqdm
# import re
# from memory_profiler import profile
# from modules.dynamic_brand_detection import DynamicBrandDetector

# # check
# os.environ['KMP_DUPLICATE_LIB_OK']='True'

# # Set your OpenAI API key here
# your_openai_api_key = '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'

# # Create a custom print function that logs to file
# log_file_path = '/home/tiffanybao/PhishIntention/results/prompts_printed.txt'
# os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# def log_print(*args, **kwargs):
#     # Get the original print output as a string
#     import sys
#     from io import StringIO
    
#     # First, print to console as normal
#     print(*args, **kwargs)
    
#     # Now, capture what would have been printed to a string
#     temp_out = StringIO()
#     print(*args, file=temp_out, **kwargs)
#     output = temp_out.getvalue()
    
#     # Append to the log file
#     with open(log_file_path, 'a') as f:
#         f.write(output)


# class PhishIntentionWrapper:
#     _caller_prefix = "PhishIntentionWrapper"
#     _DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'

#     def __init__(self):
#         self._load_config()
#         self.dynamic_detector = DynamicBrandDetector(api_key=your_openai_api_key)

#     def _load_config(self):
#         self.AWL_MODEL, self.CRP_CLASSIFIER, self.CRP_LOCATOR_MODEL, self.SIAMESE_MODEL, self.OCR_MODEL, \
#             self.SIAMESE_THRE, self.LOGO_FEATS, self.LOGO_FILES, self.DOMAIN_MAP_PATH = load_config()
#         # ...=load_config(reload_targetlist=True)
#         log_print(f'Length of reference list = {len(self.LOGO_FEATS)}')

#     '''PhishIntention'''
#     @profile
#     def test_orig_phishintention(self, url, screenshot_path):

#         waive_crp_classifier = False
#         phish_category = 0  # 0 for benign, 1 for phish, default is benign
#         pred_target = None
#         matched_domain = None
#         siamese_conf = None
#         awl_detect_time = 0
#         logo_match_time = 0
#         crp_class_time = 0
#         crp_locator_time = 0
#         log_print("Entering PhishIntention")
#         log_print(f"Analyzing URL: {url}")

#         while True:

#             ####################### Step1: Layout detector ##############################################
#             start_time = time.time()
#             pred_boxes, pred_classes, _ = pred_rcnn(im=screenshot_path, predictor=self.AWL_MODEL)
#             awl_detect_time += time.time() - start_time

#             if pred_boxes is not None:
#                 pred_boxes = pred_boxes.numpy()
#                 pred_classes = pred_classes.numpy()
#             plotvis = vis(screenshot_path, pred_boxes, pred_classes)

#             # If no element is reported
#             if pred_boxes is None or len(pred_boxes) == 0:
#                 log_print('No element is detected, reported as benign')
#                 return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
#                             str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
#                             pred_boxes, pred_classes

#             logo_pred_boxes, _ = find_element_type(pred_boxes, pred_classes, bbox_type='logo')
#             if logo_pred_boxes is None or len(logo_pred_boxes) == 0:
#                 log_print('No logo is detected, reported as benign')
#                 return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
#                             str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
#                             pred_boxes, pred_classes

#             log_print('Entering siamese')
#             log_print(f'Number of logo boxes: {len(logo_pred_boxes)}')

#             ######################## Step2: Siamese (Logo matcher) ########################################
#             start_time = time.time()
#             pred_target, matched_domain, matched_coord, siamese_conf = check_domain_brand_inconsistency(logo_boxes=logo_pred_boxes,
#                                                                                       domain_map_path=self.DOMAIN_MAP_PATH,
#                                                                                       model = self.SIAMESE_MODEL,
#                                                                                       ocr_model = self.OCR_MODEL,
#                                                                                       logo_feat_list = self.LOGO_FEATS,
#                                                                                       file_name_list = self.LOGO_FILES,
#                                                                                       url=url,
#                                                                                       shot_path=screenshot_path,
#                                                                                       ts=self.SIAMESE_THRE)
#             logo_match_time += time.time() - start_time
#             log_print(f'Siamese result: pred_target={pred_target}, siamese_conf={siamese_conf}')

#             if pred_target is None:
#                 log_print('Did not match to any brand, trying dynamic detection')
#                 original_pred_target = pred_target # Store the original pred_target for logging purposes

#                 ########### Added dynamic detection ############
#                 dynamic_brand = self.dynamic_detector.analyze_logo(screenshot_path)
#                 if dynamic_brand:
#                     log_print(f'Dynamically detected brand using GPT: {dynamic_brand}')
#                     log_print(f'Before GPT: pred_target={original_pred_target}, siamese_conf={siamese_conf}')
#                     log_print(f'Before GPT: now stating to match the domains: ... ')
#                     ########## start matching domain ##########
#                     # pred_target = dynamic_brand
#                     import pickle
#                     from tldextract import tldextract

#                     # Load the domain mapping dictionary that maps brands to their legitimate domains
#                     with open(self.DOMAIN_MAP_PATH, 'rb') as handle:
#                         domain_map = pickle.load(handle)
                    
#                     # Normalize the brand name to handle case and spacing variations (paypal)
#                     normalized_brand = dynamic_brand.lower().replace(' ', '')  # "paypal"
#                     expected_domains = []
                    
#                     # Search through the domain map to find the normalized brand
#                     for brand_key in domain_map.keys():
#                         # Check if our normalized brand matches any key in the domain map
#                         if normalized_brand in brand_key.lower() or brand_key.lower() in normalized_brand:
#                             # If found, use the domains associated with that brand
#                             expected_domains = domain_map[brand_key]  # ['paypal.com', 'paypal.me', etc.]
#                             pred_target = brand_key  # Use official brand name from map
#                             break


#                         # If brand wasn't in domain map, use fallback
#                     if not expected_domains:
#                         pred_target = dynamic_brand  # "PayPal"
#                         expected_domains = [f"{normalized_brand}.com"]  # ['paypal.com']
                    
#                     # Extract just the domain from the current URL (paypal)
#                     current_domain = tldextract.extract(url).domain  # "paypal" from "www.paypal.com/hk/home"
                    
#                     # Check if current domain is in the expected domains list
#                     if current_domain in expected_domains:
#                         # We're on a legitimate PayPal domain, mark as benign by setting pred_target to None
#                         pred_target = None  # This makes the code branch to the benign path later
#                         matched_domain = None
#                         log_print("Domain matches brand, legitimate site")
#                     else:
#                         # Domain inconsistency - potential phishing
#                         matched_domain = expected_domains  # Keep the expected domains for reporting
#                         log_print("Domain inconsistency detected, potential phishing")

#                         # Set confidence and coordinates for further processing/visualization
#                     siamese_conf = 0.85  # Default high confidence for GPT-detected brands
#                     if matched_coord is None and len(logo_pred_boxes) > 0:
#                         matched_coord = logo_pred_boxes[0]  # Use first logo box for visualization
                    
#                     log_print(f'After GPT: pred_target={pred_target}, Gpt overwrites its siamese_conf as ={siamese_conf}')




#                 else: #Gpt also says this logo is None 
#                     log_print('even with help of gpt, still did not match to any brand, report as benign')
#                     return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
#                                 str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
#                                 pred_boxes, pred_classes





#             ######################## Step3: CRP classifier (if a target is reported) #################################
#             log_print('A target is reported, enter CRP classifier')
#             if waive_crp_classifier:  # only run dynamic analysis ONCE
#                 break

#             html_path = screenshot_path.replace("shot.png", "html.txt")
#             start_time = time.time()
#             cre_pred = html_heuristic(html_path)
#             if cre_pred == 1:  # if HTML heuristic report as nonCRP
#                 # CRP classifier
#                 cre_pred = credential_classifier_mixed(img=screenshot_path,
#                                                          coords=pred_boxes,
#                                                          types=pred_classes,
#                                                          model=self.CRP_CLASSIFIER)
#             crp_class_time += time.time() - start_time
#             log_print(f'CRP classification result: {cre_pred} (0 = CRP, 1 = non-CRP)')

#             ######################## Step4: Dynamic analysis #################################
#             if cre_pred == 1:
#                 log_print('It is a Non-CRP page, enter dynamic analysis')
#                 # # load driver ONCE!
#                 driver = driver_loader()
#                 log_print('Finish loading webdriver')
#                 # load chromedriver
#                 url, screenshot_path, successful, process_time = crp_locator(url=url,
#                                                                              screenshot_path=screenshot_path,
#                                                                              cls_model=self.CRP_CLASSIFIER,
#                                                                              ele_model=self.AWL_MODEL,
#                                                                              login_model=self.CRP_LOCATOR_MODEL,
#                                                                              driver=driver)
#                 crp_locator_time += process_time
#                 driver.quit()

#                 waive_crp_classifier = True  # only run dynamic analysis ONCE

#                 # If dynamic analysis did not reach a CRP
#                 if not successful:
#                     log_print('Dynamic analysis cannot find any link redirected to a CRP page, report as benign')
#                     return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
#                             str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
#                             pred_boxes, pred_classes

#                 else:  # dynamic analysis successfully found a CRP
#                     log_print('Dynamic analysis found a CRP, go back to layout detector')

#             else:  # already a CRP page
#                 log_print('Already a CRP, continue')
#                 break

#         ######################## Step5: Return #################################
#         if pred_target is not None:
#             log_print('Phishing is found!')
#             phish_category = 1
#             # Visualize, add annotations
#             log_print(f'Adding annotation to visualization: Target: {pred_target} with confidence {siamese_conf}')
#             if matched_coord is not None:
#                 cv2.putText(plotvis, "Target: {} with confidence {:.4f}".format(pred_target, siamese_conf),
#                             (int(matched_coord[0] + 20), int(matched_coord[1] + 20)),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

#         # Final logging before return
#         log_print(f'Final results: phish_category={phish_category}, pred_target={pred_target}, matched_domain={matched_domain}, siamese_conf={siamese_conf}')
        
#         return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
#                     str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
#                     pred_boxes, pred_classes

# if __name__ == '__main__':

#     '''run'''
#     today = datetime.now().strftime('%Y%m%d')

#     parser = argparse.ArgumentParser()
#     parser.add_argument("--folder", required=True, type=str)
#     parser.add_argument("--output_txt", default=f'{today}_results.txt', help="Output txt path")
#     args = parser.parse_args()

#     request_dir = args.folder
#     phishintention_cls = PhishIntentionWrapper()
#     result_txt = args.output_txt

#     os.makedirs(request_dir, exist_ok=True)
    
#     # Clear log file at the start of a new run
#     with open(log_file_path, 'w') as f:
#         f.write(f"=== New Run Started at {datetime.now()} ===\n")

#     for folder in tqdm(os.listdir(request_dir)):
#         html_path = os.path.join(request_dir, folder, "html.txt")
#         screenshot_path = os.path.join(request_dir, folder, "shot.png")
#         info_path = os.path.join(request_dir, folder, 'info.txt')

#         if not os.path.exists(screenshot_path):
#             continue

#         if os.path.exists(info_path):
#             url = open(info_path).read()
#         else:
#             url = "https://" + folder

#         if os.path.exists(result_txt) and url in open(result_txt, encoding='ISO-8859-1').read():
#             continue

#         _forbidden_suffixes = r"\.(mp3|wav|wma|ogg|mkv|zip|tar|xz|rar|z|deb|bin|iso|csv|tsv|dat|txt|css|log|sql|xml|sql|mdb|apk|bat|bin|exe|jar|wsf|fnt|fon|otf|ttf|ai|bmp|gif|ico|jp(e)?g|png|ps|psd|svg|tif|tiff|cer|rss|key|odp|pps|ppt|pptx|c|class|cpp|cs|h|java|sh|swift|vb|odf|xlr|xls|xlsx|bak|cab|cfg|cpl|cur|dll|dmp|drv|icns|ini|lnk|msi|sys|tmp|3g2|3gp|avi|flv|h264|m4v|mov|mp4|mp(e)?g|rm|swf|vob|wmv|doc(x)?|odt|rtf|tex|txt|wks|wps|wpd)$"
#         if re.search(_forbidden_suffixes, url, re.IGNORECASE):
#             continue

#         # Log site being processed
#         with open(log_file_path, 'a') as f:
#             f.write(f"\n\n===== Processing folder: {folder}, URL: {url} =====\n")

#         phish_category, pred_target, matched_domain, \
#                 plotvis, siamese_conf, runtime_breakdown, \
#                 pred_boxes, pred_classes = phishintention_cls.test_orig_phishintention(url, screenshot_path)

#         try:
#             with open(result_txt, "a+", encoding='ISO-8859-1') as f:
#                 f.write(folder + "\t")
#                 f.write(url + "\t")
#                 f.write(str(phish_category) + "\t")
#                 f.write(str(pred_target) + "\t")  # write top1 prediction only
#                 f.write(str(matched_domain) + "\t")
#                 f.write(str(siamese_conf) + "\t")
#                 f.write(runtime_breakdown + "\n")
#         except UnicodeError:
#             with open(result_txt, "a+", encoding='utf-8') as f:
#                 f.write(folder + "\t")
#                 f.write(url + "\t")
#                 f.write(str(phish_category) + "\t")
#                 f.write(str(pred_target) + "\t")  # write top1 prediction only
#                 f.write(str(matched_domain) + "\t")
#                 f.write(str(siamese_conf) + "\t") 
#                 f.write(runtime_breakdown + "\n")

#         if phish_category:
#             os.makedirs(os.path.join(request_dir, folder), exist_ok=True)
#             cv2.imwrite(os.path.join(request_dir, folder, "predict.png"), plotvis)



import time
from datetime import datetime
import argparse
import os
import torch
import cv2
from configs import load_config
from modules.awl_detector import pred_rcnn, vis, find_element_type
from modules.logo_matching import check_domain_brand_inconsistency
from modules.crp_classifier import credential_classifier_mixed, html_heuristic
from modules.crp_locator import crp_locator
from utils.web_utils import driver_loader
from tqdm import tqdm
import re
from memory_profiler import profile
from modules.dynamic_brand_detection import DynamicBrandDetector

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

    '''PhishIntention'''
    @profile
    def test_orig_phishintention(self, url, screenshot_path):

        waive_crp_classifier = False
        phish_category = 0  # 0 for benign, 1 for phish, default is benign
        pred_target = None
        matched_domain = None
        siamese_conf = None
        awl_detect_time = 0
        logo_match_time = 0
        crp_class_time = 0
        crp_locator_time = 0
        log_print("Entering PhishIntention")
        log_print(f"Analyzing URL: {url}")

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
                return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                            str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                            pred_boxes, pred_classes

            logo_pred_boxes, _ = find_element_type(pred_boxes, pred_classes, bbox_type='logo')
            if logo_pred_boxes is None or len(logo_pred_boxes) == 0:
                log_print('No logo is detected, reported as benign')
                return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                            str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                            pred_boxes, pred_classes

            log_print('Entering siamese')
            log_print(f'Number of logo boxes: {len(logo_pred_boxes)}')

            ######################## Step2: Siamese (Logo matcher) ########################################
            start_time = time.time()
            pred_target, matched_domain, matched_coord, siamese_conf = check_domain_brand_inconsistency(logo_boxes=logo_pred_boxes,
                                                                                      domain_map_path=self.DOMAIN_MAP_PATH,
                                                                                      model = self.SIAMESE_MODEL,
                                                                                      ocr_model = self.OCR_MODEL,
                                                                                      logo_feat_list = self.LOGO_FEATS,
                                                                                      file_name_list = self.LOGO_FILES,
                                                                                      url=url,
                                                                                      shot_path=screenshot_path,
                                                                                      ts=self.SIAMESE_THRE)
            logo_match_time += time.time() - start_time
            log_print(f'Siamese result: pred_target={pred_target}, siamese_conf={siamese_conf}')

            if pred_target is None:
                log_print('Did not match to any brand, trying dynamic detection')
                original_pred_target = pred_target # Store the original pred_target for logging purposes

                ########### Added dynamic detection ############
                dynamic_brand = self.dynamic_detector.analyze_logo(screenshot_path)
                if dynamic_brand:
                    log_print(f'Dynamically detected brand using GPT: {dynamic_brand}')
                    log_print(f'Before GPT: pred_target={original_pred_target}, siamese_conf={siamese_conf}')
                    log_print(f'Before GPT: now starting to match the domains...')
                    
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
                               
                        # Still record the brand detection for reporting purposes but mark as benign
                        siamese_conf = 0.85  # Default high confidence for GPT-detected brands
                        pred_target = dynamic_brand
                        matched_domain = expected_domains

                        # Set matched_coord for visualization
                        if matched_coord is None and len(logo_pred_boxes) > 0:
                            matched_coord = logo_pred_boxes[0]
                            
                        # Return early as benign but with brand identification
                        return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                                str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                                pred_boxes, pred_classes
                    

                    else:
                        # Domain inconsistency - potential phishing
                        matched_domain = expected_domains  # Keep the expected domains for reporting
                        log_print(f"Domain inconsistency detected: {dynamic_brand} brand on {current_domain}, potential phishing")
                        
                        # Set confidence and coordinates for further processing/visualization
                        siamese_conf = 0.85  # Default high confidence for GPT-detected brands
                        if matched_coord is None and len(logo_pred_boxes) > 0:
                            matched_coord = logo_pred_boxes[0]  # Use first logo box for visualization

                    log_print(f'After GPT: pred_target={pred_target}, matched_domain={matched_domain}, siamese_conf={siamese_conf}')

                            
                else: # GPT also says this logo is None 
                    log_print('Even with help of GPT, still did not match to any brand, report as benign')
                    return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                                str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                                pred_boxes, pred_classes




            ######################## Step3: CRP classifier (if a target is reported) #################################
            log_print('A target is reported, enter CRP classifier')
            if waive_crp_classifier:  # only run dynamic analysis ONCE
                break

            html_path = screenshot_path.replace("shot.png", "html.txt")
            start_time = time.time()
            cre_pred = html_heuristic(html_path)
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
                log_print('It is a Non-CRP page, enter dynamic analysis')
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
                    return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                            str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                            pred_boxes, pred_classes

                else:  # dynamic analysis successfully found a CRP
                    log_print('Dynamic analysis found a CRP, go back to layout detector')

            else:  # already a CRP page
                log_print('Already a CRP, continue')
                break

        ######################## Step5: Return #################################
        if pred_target is not None:
            log_print('Phishing is found!')
            phish_category = 1
            # Visualize, add annotations
            log_print(f'Adding annotation to visualization: Target: {pred_target} with confidence {siamese_conf}')
            if matched_coord is not None:
                cv2.putText(plotvis, "Target: {} with confidence {:.4f}".format(pred_target, siamese_conf),
                            (int(matched_coord[0] + 20), int(matched_coord[1] + 20)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

        # Final logging before return
        log_print(f'Final results: phish_category={phish_category}, pred_target={pred_target}, matched_domain={matched_domain}, siamese_conf={siamese_conf}')
        
        return phish_category, pred_target, matched_domain, plotvis, siamese_conf, \
                    str(awl_detect_time) + '|' + str(logo_match_time) + '|' + str(crp_class_time) + '|' + str(crp_locator_time), \
                    pred_boxes, pred_classes

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

        phish_category, pred_target, matched_domain, \
                plotvis, siamese_conf, runtime_breakdown, \
                pred_boxes, pred_classes = phishintention_cls.test_orig_phishintention(url, screenshot_path)

        try:
            with open(result_txt, "a+", encoding='ISO-8859-1') as f:
                f.write(folder + "\t")
                f.write(url + "\t")
                f.write(str(phish_category) + "\t")
                f.write(str(pred_target) + "\t")  # write top1 prediction only
                f.write(str(matched_domain) + "\t")
                f.write(str(siamese_conf) + "\t")
                f.write(runtime_breakdown + "\n")
        except UnicodeError:
            with open(result_txt, "a+", encoding='utf-8') as f:
                f.write(folder + "\t")
                f.write(url + "\t")
                f.write(str(phish_category) + "\t")
                f.write(str(pred_target) + "\t")  # write top1 prediction only
                f.write(str(matched_domain) + "\t")
                f.write(str(siamese_conf) + "\t") 
                f.write(runtime_breakdown + "\n")

        # Generate predict.png for phishing sites AND for legitimate sites where a brand was detected
        if phish_category == 1 or pred_target is not None:
            os.makedirs(os.path.join(request_dir, folder), exist_ok=True)
            cv2.imwrite(os.path.join(request_dir, folder, "predict.png"), plotvis)