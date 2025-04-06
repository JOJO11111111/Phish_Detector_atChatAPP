import os
import csv
import numpy as np
from modules.HTML_Analyzer import HTML_Analyzer
from phishintention import PhishIntentionWrapper

# Constants
DATASET_PATH = '/home/tiffanybao/PhishIntention/datasets/test_sites'
OUTPUT_DIR = '/home/tiffanybao/PhishIntention/results/multimodal_results'



# fusion and decision layer need to be updated more, but currently could  be run

# Fusion layer, need to be updated due to the uncertainty of txt branch's phish score and return vector, see decision layer for more details
def fuse_features(image_vector, text_vector):
    """
    Fuse image and text feature vectors with conditional weighting
    """
    has_logo = image_vector[0] > 0
    image_weight = 0.7 if has_logo else 0.3
    text_weight = 0.3 if has_logo else 0.7
    
    norm_image = image_vector / (np.linalg.norm(image_vector) + 1e-8)
    norm_text = text_vector / (np.linalg.norm(text_vector) + 1e-8)
    
    return np.concatenate([image_weight * norm_image, text_weight * norm_text])

# Decision layer, need to add the txt phish score, (without simply asking gpt to give the score)
def make_decision(fused_vector, image_phish_score):
    """
    Make final phishing/benign decision
    """
    if image_phish_score >= 0.9:
        return 1
    
    text_features = fused_vector[-6:]
    if text_features[1] > 0 and text_features[3] > 0:
        return 1
    if image_phish_score > 0.5 and text_features[5] > 0.3:
        return 1
    
    return 0




def process_site(site_folder):
    """Process a single site with enhanced error handling"""
    try:
        site_path = os.path.join(DATASET_PATH, site_folder)
        
        # Validate files exist
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

            # Convert features to vector with defaults
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
        except Exception as img_e:
            print(f"Image analysis failed for {site_folder}: {str(img_e)}")
            image_vector = np.zeros(15)  # Default vector if image analysis fails
            image_features_dict = {'phish_score': 0.0}

        # 2. Text Analysis
        try:
            with open(required_files['html'], 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            vector1, vector2 = text_analyzer.analyze_html_pipeline(
                html_content, 
                base_url=url
            )
            
            text_vector = np.concatenate([vector1, vector2]) if vector2 is not None else vector1
        except Exception as text_e:
            print(f"Text analysis failed for {site_folder}: {str(text_e)}")
            text_vector = np.zeros(6)  # Default text vector

        # 3. Feature Fusion
        fused_vector = fuse_features(image_vector, text_vector)

        # 4. Decision
        decision = make_decision(fused_vector, image_features_dict.get('phish_score', 0.0))

        # Prepare result
        result = {
            'site_folder': site_folder,
            'url': url,
            'decision': 'phishing' if decision == 1 else 'benign',
            'image_vector': image_vector,
            'text_vector': text_vector,
            'fused_vector': fused_vector,
            'image_phish_score': image_features_dict.get('phish_score', 0.0),
            'text_phish_score': text_vector[-1] if len(text_vector) >= 6 else 0.0
        }

        # 5. Save results
        save_single_result(result)
        return result

    except Exception as e:
        print(f"Fatal error processing {site_folder}: {str(e)}")
        return None
    

    

def save_single_result(result):
    """Save a single site's results to CSV"""
    output_csv = os.path.join(OUTPUT_DIR, 'multimodal_results.csv')
    
    # Create directory if needed
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Check if we need to write headers
    write_header = not os.path.exists(output_csv) or os.stat(output_csv).st_size == 0
    
    try:
        with open(output_csv, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    'Site Folder', 'URL', 'Decision',
                    'Image Phish Score', 'Text Phish Score',
                    'Image Features', 'Text Features', 'Fused Features'
                ])
            
            writer.writerow([
                result['site_folder'],
                result['url'],
                result['decision'],
                f"{result['image_phish_score']:.4f}",
                f"{result['text_phish_score']:.4f}",
                '|'.join([f"{x:.6f}" for x in result['image_vector']]),
                '|'.join([f"{x:.6f}" for x in result['text_vector']]),
                '|'.join([f"{x:.6f}" for x in result['fused_vector']])
            ])
            
    except Exception as e:
        print(f"Failed to save results for {result['site_folder']}: {str(e)}")


def save_single_result(result):
    """Save a single site's results to CSV"""
    output_csv = os.path.join(OUTPUT_DIR, 'multimodal_results.csv')
    
    # Create directory if needed
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    # Check if we need to write headers
    write_header = not os.path.exists(output_csv) or os.stat(output_csv).st_size == 0
    
    try:
        with open(output_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    'Site Folder', 'URL', 'Decision',
                    'Image Phish Score', 'Text Phish Score',
                    'Image Features', 'Text Features', 'Fused Features'
                ])
            
            writer.writerow([
                result['site_folder'],
                result['url'],
                result['decision'],
                result['image_phish_score'],
                result['text_phish_score'],
                '|'.join([f"{x:.6f}" for x in result['image_vector']]),
                '|'.join([f"{x:.6f}" for x in result['text_vector']]),
                '|'.join([f"{x:.6f}" for x in result['fused_vector']])
            ])
            
    except Exception as e:
        print(f"Failed to save results for {result['site_folder']}: {str(e)}")



def process_dataset():
    """Process all sites in the dataset folder"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    results = []
    for site_folder in os.listdir(DATASET_PATH):
        site_path = os.path.join(DATASET_PATH, site_folder)
        if os.path.isdir(site_path):
            try:
                result = process_site(site_folder)
                if result:
                    results.append(result)
                    print(f"Processed {site_folder}: {result['decision']}")
            except Exception as e:
                print(f"Error processing {site_folder}: {str(e)}")
    
    # Save results
    output_csv = os.path.join(OUTPUT_DIR, 'multimodal_results.csv')
    with open(output_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Site Folder', 'URL', 'Decision', 
            'Image Phish Score', 'Text Phish Score',
            'Image Features', 'Text Features', 'Fused Features'
        ])
        for result in results:
            writer.writerow([
                result['site_folder'],
                result['url'],
                result['decision'],
                result['image_phish_score'],
                result['text_phish_score'],
                '|'.join(map(str, result['image_vector'])),
                '|'.join(map(str, result['text_vector'])),
                '|'.join(map(str, result['fused_vector']))
            ])
    
    print(f"Results saved to {output_csv}")
    return results

if __name__ == '__main__':
    process_dataset()