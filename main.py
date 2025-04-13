import os
import csv
import numpy as np
import sys

from modules.HTML_Analyzer_tiff_locsl import HTML_Analyzer
from modules.Web_Crawling_tiff_local import setup_driver
from helium import set_driver

from phishintention import PhishIntentionWrapper
import time
# Constants
DATASET_PATH = '/home/tiffanybao/PhishIntention/datasets/Learned_Logo_Phishing'
OUTPUT_DIR = '/home/tiffanybao/PhishIntention/results/4.11/Multimodal'
CRAWL_OUTPUT_DIR = '/home/tiffanybao/PhishIntention/results/crawled_sites'



# Call this at the end of process_site() after both branches complete


def fuse_features(image_vector, text_vector):
    """
    Fuse image and text feature vectors
    Args:
        image_vector: numpy array (15 features)
        text_vector: numpy array (12 features - vector1 + vector2)
    Returns:
        Concatenated normalized feature vector
    """
    has_logo = image_vector[0] > 0
    image_weight = 0.7 if has_logo else 0.3
    text_weight = 0.3 if has_logo else 0.7
    
    # Normalize vectors
    norm_image = image_vector / (np.linalg.norm(image_vector) + 1e-8)
    norm_text = text_vector / (np.linalg.norm(text_vector) + 1e-8)
    
    return np.concatenate([image_weight * norm_image, text_weight * norm_text])




def make_decision(fused_vector, image_phish_score, text_phish_score):
    """
    Final phishing decision with these rules:
    1. If image_phish_score >= 0.9 → Phishing (1).
    2. If image_phish_score == 0.5 → Defer to text_phish_score (if >= 0.4 → Phishing).
    3. If text features show strong phishing signals → Phishing (1).
    4. If image_phish_score > 0.5 + moderate text signals → Phishing (1).
    Otherwise → Benign (0).
    """
    # Rule 1: High-confidence image phishing
    if image_phish_score >= 0.9:
        return 1

    # Rule 2: Neutral image score (0.5) → Lower threshold for text_phish_score
    if image_phish_score == 0.5:
        return 1 if text_phish_score >= 0.5 else 0  

    # Rule 3: Strong text-based phishing signals (from fused_vector)
    # Assuming the image vector has 15 elements, and the text features are the rest
    # (without the score, as we're handling that separately)
    image_length = 15
    text_features = fused_vector[image_length:]  
    
    # Check if either Vector1 or Vector2 has strong phishing indicators
    # Vector1 is the first 6 elements, Vector2 is the next 6 elements
    vector1 = text_features[:6]
    vector2 = text_features[6:12]
    
    # Check for suspicious form actions or obfuscated scripts in either vector
    if (vector1[1] > 0 and vector1[3] > 0) or (vector2[1] > 0 and vector2[3] > 0):
        return 1

    # Rule 4: Moderate image score + domain mismatch indicators
    if image_phish_score > 0.5 and (vector1[5] > 0.3 or vector2[5] > 0.3):
        return 1
        
    # Rule 5: High text score (add a threshold appropriate for your normalized scores)
    if text_phish_score >= 0.7:
        return 1

    # Default: Benign
    return 0



# def process_site(site_folder):
    """Process a single site"""
    try:
        site_path = os.path.join(DATASET_PATH, site_folder)
        
        # Validate files
        required_files = {
            'info': os.path.join(site_path, 'info.txt'),
            'screenshot': os.path.join(site_path, 'shot.png'),
            'html': os.path.join(site_path, 'html.txt')
        }
        
        for name, path in required_files.items():
            if not os.path.exists(path):
                print(f"Missing {name} file in {site_folder}")
                return None

        # Read URL
        with open(required_files['info'], 'r') as f:
            url = f.read().strip()
        
        # Initialize analyzers
        image_analyzer = PhishIntentionWrapper()
        text_analyzer = HTML_Analyzer()

        # 1. Image Analysis
        try:
            image_result = image_analyzer.test_orig_phishintention(
                url, 
                required_files['screenshot']
            )
            
            # Unpack results
            (phish_category, pred_target, matched_domain, plotvis, siamese_conf,
             runtime_breakdown, pred_boxes, pred_classes, used_gpt, is_crp,
             has_login_elements, has_password_field, logo_pred_boxes,
             image_features_dict) = image_result

            # Convert features to vector
            image_vector = np.array([
                image_features_dict.get('has_logo', 0),
                image_features_dict.get('brand_matched', 0),
                image_features_dict.get('brand_confidence', 0.0),
                image_features_dict.get('domain_brand_mismatch', 0),
                image_features_dict.get('has_login_elements', 0),
                image_features_dict.get('has_password_field', 0),
                image_features_dict.get('page_has_security_indicators', 0),
                image_features_dict.get('image_quality_score', 0.5),
                image_features_dict.get('logo_size_proportion', 0.0),
                image_features_dict.get('logo_position_typical', 0),
                image_features_dict.get('used_gpt_detection', 0),
                image_features_dict.get('gpt_confidence', 0.0),
                image_features_dict.get('is_crp', 0),
                image_features_dict.get('domain_match_score', 0.0),
                image_features_dict.get('phish_score', 0.0)
            ])
            image_phish_score = image_features_dict.get('phish_score', 0.0)
            if phish_category == 1:
                image_decision = 1
            else:
                image_decision = 0
        except Exception as img_e:
            print(f"Image analysis failed for {site_folder}: {str(img_e)}")
            image_vector = np.zeros(15)
            image_features_dict = {'phish_score': 0.0}
    
 

        # 2. Text Analysis - Modified to properly capture dynamic analysis
        try:
            with open(required_files['html'], 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            print(f"\n[Analyzing text for {site_folder}]")
            
            # Get both vectors from HTML analyzer with screenshot path
            
            driver = setup_driver()
            set_driver(driver)

            text_vector, text_branch_decision = text_analyzer.analyze_html_pipeline(
                required_files['html'],  # Pass path to html file
                base_url=url,
                screenshot_path=required_files['screenshot'],
                using_dead_url=True
            )
            
            # Debug print raw vectors
            print(f"Raw text vector: {text_vector}")
            print(f"Text branch decision: {text_branch_decision}")
            if text_branch_decision == 'Phishing':
                txt_branch_decision = 1
            else:
                txt_branch_decision = 0
    
        except Exception as text_e:
            print(f"Text analysis failed for {site_folder}: {str(text_e)}")
            text_vector = np.zeros(13)
            text_phish_score = 0.0
            txt_branch_decision = 0  # Default to 0 (benign) on error    
            # Calculate text phishing score (max of both vectors' scores)
            text_phish_score = text_vector[12]
            print(f"Text Phish Score: {text_phish_score}")
            
            
        except Exception as text_e:
            print(f"Text analysis failed for {site_folder}: {str(text_e)}")
            text_vector = np.zeros(13)
            text_phish_score = 0.0


        # 3. Feature Fusion
        fused_vector = fuse_features(image_vector, text_vector)

        # 4. Decision
        decision = make_decision(fused_vector,image_phish_score, text_phish_score)

        # Prepare result
        result = {
            'site_folder': site_folder,
            'url': url,
            'decision': 'phishing' if decision == 1 else 'benign',
            'image_phish_score': round(image_phish_score, 2),
            'image_decision': image_decision,
            'text_phish_score': round(text_phish_score, 2),
            'text_decision': txt_branch_decision,
            'image_vector': image_vector,
            'text_vector': text_vector,
            'fused_vector': fused_vector
        }

        save_single_result(result)
        return result

    except Exception as e:
        print(f"Fatal error processing {site_folder}: {str(e)}")
        return None



def process_site(site_folder):
    """Process a single site"""
    try:
        # Initialize default values for all critical variables
        image_vector = np.zeros(15)
        image_phish_score = 0.0
        image_decision = 0
        text_vector = np.zeros(13)
        text_phish_score = 0.0
        txt_branch_decision = 0
        
        site_path = os.path.join(DATASET_PATH, site_folder)
        
        # Validate files
        required_files = {
            'info': os.path.join(site_path, 'info.txt'),
            'screenshot': os.path.join(site_path, 'shot.png'),
            'html': os.path.join(site_path, 'html.txt')
        }
        
        for name, path in required_files.items():
            if not os.path.exists(path):
                print(f"Missing {name} file in {site_folder}")
                return None

        # Read URL
        with open(required_files['info'], 'r') as f:
            url = f.read().strip()
        
        # Initialize analyzers
        image_analyzer = PhishIntentionWrapper()
        text_analyzer = HTML_Analyzer()

        # 1. Image Analysis
        try:
            image_result = image_analyzer.test_orig_phishintention(
                url, 
                required_files['screenshot']
            )
            
            # Unpack results
            (phish_category, pred_target, matched_domain, plotvis, siamese_conf,
             runtime_breakdown, pred_boxes, pred_classes, used_gpt, is_crp,
             has_login_elements, has_password_field, logo_pred_boxes,
             image_features_dict) = image_result

            # Convert features to vector
            image_vector = np.array([
                image_features_dict.get('has_logo', 0),
                image_features_dict.get('brand_matched', 0),
                image_features_dict.get('brand_confidence', 0.0),
                image_features_dict.get('domain_brand_mismatch', 0),
                image_features_dict.get('has_login_elements', 0),
                image_features_dict.get('has_password_field', 0),
                image_features_dict.get('page_has_security_indicators', 0),
                image_features_dict.get('image_quality_score', 0.5),
                image_features_dict.get('logo_size_proportion', 0.0),
                image_features_dict.get('logo_position_typical', 0),
                image_features_dict.get('used_gpt_detection', 0),
                image_features_dict.get('gpt_confidence', 0.0),
                image_features_dict.get('is_crp', 0),
                image_features_dict.get('domain_match_score', 0.0),
                image_features_dict.get('phish_score', 0.0)
            ])
            image_phish_score = image_features_dict.get('phish_score', 0.0)
            if phish_category == 1:
                image_decision = 1
            else:
                image_decision = 0
        except Exception as img_e:
            print(f"Image analysis failed for {site_folder}: {str(img_e)}")
            # Default values are already set at the beginning

        # 2. Text Analysis - Modified to properly capture dynamic analysis
        try:
            with open(required_files['html'], 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            print(f"\n[Analyzing text for {site_folder}]")
            
            # Get both vectors from HTML analyzer with screenshot path
            driver = setup_driver()
            set_driver(driver)

            text_vector, text_branch_decision = text_analyzer.analyze_html_pipeline(
                required_files['html'],  # Pass path to html file
                base_url=url,
                screenshot_path=required_files['screenshot'],
                using_dead_url=True
            )
            
            # Debug print raw vectors
            print(f"Raw text vector: {text_vector}")
            print(f"Text branch decision: {text_branch_decision}")
            if text_branch_decision == 'Phishing':
                txt_branch_decision = 1
            else:
                txt_branch_decision = 0
        except Exception as text_e:
            print(f"Text analysis failed for {site_folder}: {str(text_e)}")
            # Default values are already set at the beginning
        
        # Get phishing score from text vector (outside try/except to ensure it's always set)
        text_phish_score = text_vector[12]
        print(f"Text Phish Score: {text_phish_score}")

        # 3. Feature Fusion
        fused_vector = fuse_features(image_vector, text_vector)

        # 4. Decision
        decision = make_decision(fused_vector, image_phish_score, text_phish_score)

        # Prepare result
        result = {
            'site_folder': site_folder,
            'url': url,
            'decision': 'phishing' if decision == 1 else 'benign',
            'image_phish_score': round(image_phish_score, 2),
            'image_decision': image_decision,
            'text_phish_score': round(text_phish_score, 2),
            'text_decision': txt_branch_decision,
            'image_vector': image_vector,
            'text_vector': text_vector,
            'fused_vector': fused_vector
        }

        save_single_result(result)
        return result

    except Exception as e:
        print(f"Fatal error processing {site_folder}: {str(e)}")
        # Create a minimal result with error information
        result = {
            'site_folder': site_folder,
            'url': "Error processing",
            'decision': 'error',
            'image_phish_score': 0.0,
            'image_decision': 0,
            'text_phish_score': 0.0,
            'text_decision': 0,
            'image_vector': np.zeros(15),
            'text_vector': np.zeros(13),
            'fused_vector': np.zeros(28)  # Adjust this size if needed
        }
        
        # Try to save this result so we still have an entry in the CSV
        try:
            save_single_result(result)
        except:
            print(f"Could not save error result for {site_folder}")
        
        return result

def save_single_result(result):
    """Save results with simplified decimal precision"""
    output_csv = os.path.join(OUTPUT_DIR, 'Learned_Logo_Phishing_predict.csv')
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    write_header = not os.path.exists(output_csv) or os.stat(output_csv).st_size == 0
    
    try:
        with open(output_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    'Site Folder', 'URL', 'Multimodal_Decision',
                    'Image Phish Score','Image_Decision', 'Text Phish Score','Text_Decision',
                    'Image Features', 'Text Features', 'Fused Features'
                ])
            
            # Format with 2 decimal places
            writer.writerow([
                result['site_folder'],
                result['url'],
                result['decision'],
                f"{result['image_phish_score']:.2f}",
                result['image_decision'],
                f"{result['text_phish_score']:.2f}",
                result['text_decision'],
                '|'.join([f"{x:.2f}" for x in result['image_vector']]),
                '|'.join([f"{x:.2f}" for x in result['text_vector']]),
                '|'.join([f"{x:.4f}" for x in result['fused_vector']])  # Keep more precision for fused features
            ])
            
    except Exception as e:
        print(f"Failed to save results for {result['site_folder']}: {str(e)}")

def process_dataset():
    """Process all sites in dataset"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    results = []
    
    for site_folder in os.listdir(DATASET_PATH):
        site_path = os.path.join(DATASET_PATH, site_folder)
        if os.path.isdir(site_path):
            result = process_site(site_folder)
            if result:
                results.append(result)
                print(f"Processed {site_folder}: {result['decision']}")
    
    print(f"Completed processing {len(results)} sites")
    return results

if __name__ == '__main__':
    process_dataset()