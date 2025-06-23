import os
import csv
import numpy as np
import sys
import argparse

from modules.HTML_Analyzer_tiff_locsl import HTML_Analyzer
from modules.Web_Crawling_tiff_local import setup_driver
from helium import set_driver

from phishintention import PhishIntentionWrapper
import time


DATASET_PATH = './datasets/deployment'
OUTPUT_DIR = './results/deployment'
CRAWL_OUTPUT_DIR = './results/crawled_sites'

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


def fuse_voice_features(voice_vector):
    """
    Weighted fusion of voice features.
    voice_vector: [voiceAI_score, voiceAI_weight, ask_money, ask_pw, ask_info, other_sus]
    Returns: fused score (float) in range 0-1
    """
    # Assign weights for each component
    weights = np.array([
                        6.0,  # asking_for_money
                        5.0,  # asking_for_password
                        3.0,  # asking_for_personal_info
                        9.0   # other_suspicious_content
    ])
    # Take slice to only the last 4 features for fusion (not including AI weight)
    main_scores = np.array(voice_vector[2:])

    # Normalize (optional)
    main_scores_norm = main_scores / (np.linalg.norm(main_scores) + 1e-8)

    # Weighted sum, add AI score separately
    fused = voice_vector[0] * voice_vector[1] + np.dot(main_scores_norm, weights)
    
    # For display purposes, calculate boosted AI score
    ai_score = voice_vector[0]
    if 0.08 <= ai_score <= 0.4:
        ai_score_boosted = ai_score + 0.2
    else:
        ai_score_boosted = ai_score
    
    return fused, ai_score_boosted


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


def make_voice_decision(fused_voice_score, voiceAI_score, content_scores):
    """
    Decides if the voice is phishing, using score/weights and thresholds.
    Returns 1 (phishing) or 0 (benign)
    """
    # If AI-generated score is very high and content is suspicious
    if voiceAI_score > 0.8 and fused_voice_score > 0.7:
        return 1
    # If content-based suspicious scores are high
    if content_scores.get("asking_for_password", 0) >= 5 or content_scores.get("asking_for_money", 0) >= 7:
        return 1
    # If overall score is above a moderate threshold (30% as specified by user)
    if fused_voice_score > 0.3:
        return 1
    return 0


def process_voice_file(wav_path, output_file=None):
    """Process a single voice file for phishing detection"""
    try:
        site_folder = os.path.basename(wav_path)
        print(f"Processing voice file: {site_folder}")
        
        image_analyzer = PhishIntentionWrapper()
        voice_result = image_analyzer.analyze_voice(
            wav_path,
            model_path="models/librifake_pretrained_lambda0.5_epoch_25.pth",
            config_path="Synthetic_Voice_Detection_Vocoder_Artifacts/model_config_RawNet.yaml"
        )
        
        voice_vector = np.array([
            voice_result["voiceAI_score"],        # float, AI gen score
            voice_result["voiceAI_weight"],       # float, AI gen weight (dynamic, 8/3)
            voice_result["voice_content_scores"].get("asking_for_money", 0),
            voice_result["voice_content_scores"].get("asking_for_password", 0),
            voice_result["voice_content_scores"].get("asking_for_personal_info", 0),
            voice_result["voice_content_scores"].get("other_suspicious_content", 0)
        ])
        
        # FUSION & DECISION
        fused_voice_score, ai_score_boosted = fuse_voice_features(voice_vector)
        voice_branch_decision = make_voice_decision(
            fused_voice_score,
            voice_vector[0],
            voice_result["voice_content_scores"]
        )

        print(f"[VOICE-ONLY] Voice vector: {voice_vector}, Voice fused score: {fused_voice_score}")

        # Save results (the rest are zeros)
        result = {
            'site_folder': site_folder,
            'url': '',  # No URL for voice-only
            'decision': 'phishing' if voice_branch_decision == 1 else 'benign',
            'image_phish_score': 0.0,
            'image_decision': 0,
            'text_phish_score': 0.0,
            'text_decision': 0,
            'image_vector': np.zeros(15),
            'text_vector': np.zeros(13),
            'voice_phish_score': round(fused_voice_score, 2),
            'voice_decision': voice_branch_decision,
            'voice_vector': voice_vector,
            'fused_vector': np.zeros(28),  # or just zeros if unused
            'voice_detail': voice_result,
            'multimodal_final': 'phishing' if voice_branch_decision == 1 else 'benign',
            'ai_score_boosted': ai_score_boosted
        }
        save_single_result(result, output_file)
        return result
        
    except Exception as e:
        print(f"Fatal error processing voice file {wav_path}: {str(e)}")
        # Create a minimal result with error information
        result = {
            'site_folder': os.path.basename(wav_path),
            'url': "Error processing voice file",
            'decision': 'error',
            'image_phish_score': 0.0,
            'image_decision': 0,
            'text_phish_score': 0.0,
            'text_decision': 0,
            'image_vector': np.zeros(15),
            'text_vector': np.zeros(13),
            'voice_phish_score': 0.0,
            'voice_decision': 0,
            'voice_vector': np.zeros(6),
            'fused_vector': np.zeros(28),
            'ai_score_boosted': 0.0
        }
        
        # Try to save this result so we still have an entry in the CSV
        try:
            save_single_result(result, output_file)
            print(f"Saved error result for voice file {os.path.basename(wav_path)}")
        except Exception as save_error:
            print(f"Could not save error result for voice file {os.path.basename(wav_path)}: {str(save_error)}")
        
        return result


def process_site(site_folder, dataset_path, output_file=None):
    """Process a single site"""
    try:
        site_path = os.path.join(dataset_path, site_folder)
        if not os.path.isdir(site_path):
            print(f"Site folder {site_folder} does not exist at {site_path}")
            return None
            
        # Check if this is a voice-only folder (contains .wav file)
        wav_path = None
        for file in os.listdir(site_path):
            if file.lower().endswith('.wav'):
                wav_path = os.path.join(site_path, file)
                break
        
        if wav_path:
            # Process as voice-only
            return process_voice_file(wav_path, output_file)
            
        # Get URL from info.txt
        info_file = os.path.join(site_path, "info.txt")
        if not os.path.exists(info_file):
            print(f"No info.txt found in {site_folder}")
            return None
            
        with open(info_file, "r") as f:
            url = f.read().strip()
            print(f"Processing site: {site_folder} with URL: {url}")
            
        # Validate files
        required_files = {
            'screenshot': os.path.join(site_path, 'shot.png'),
            'html': os.path.join(site_path, 'html.txt')
        }
        
        for name, path in required_files.items():
            if not os.path.exists(path):
                print(f"Missing {name} file in {site_folder}")
                return None
        
        # Initialize analyzers
        image_analyzer = PhishIntentionWrapper()
        text_analyzer = HTML_Analyzer()
        
        # 1. Image Analysis
        try:
            print(f"Starting image analysis for {site_folder}")
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
                
            print(f"Image analysis completed for {site_folder}: phish_score={image_phish_score}, decision={image_decision}")
            
        except Exception as img_e:
            print(f"Image analysis failed for {site_folder}: {str(img_e)}")
            image_vector = np.zeros(15)
            image_phish_score = 0.0
            image_decision = 0
            image_features_dict = {'phish_score': 0.0}
    
        # 2. Text Analysis
        try:
            print(f"Starting text analysis for {site_folder}")
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
                using_dead_url=False
            )
            
            # Debug print raw vectors
            print(f"Raw text vector: {text_vector}")
            print(f"Text branch decision: {text_branch_decision}")
            if text_branch_decision == 'Phishing':
                txt_branch_decision = 1
            else:
                txt_branch_decision = 0
                
            # Calculate text phishing score (max of both vectors' scores)
            text_phish_score = text_vector[12] if len(text_vector) > 12 else 0.0
            print(f"Text Phish Score: {text_phish_score}")
            
        except Exception as text_e:
            print(f"Text analysis failed for {site_folder}: {str(text_e)}")
            text_vector = np.zeros(13)
            text_phish_score = 0.0
            txt_branch_decision = 0  # Default to 0 (benign) on error

        # 3. Feature Fusion
        fused_vector = fuse_features(image_vector, text_vector)

        # 4. Decision
        decision = make_decision(fused_vector, image_phish_score, text_phish_score)
        decision_text = 'phishing' if decision == 1 else 'benign'
        print(f"Final decision for {site_folder}: {decision_text} (decision={decision})")

        # Create result dictionary
        result = {
            'site_folder': site_folder,
            'url': url,
            'decision': decision_text,
            'image_phish_score': round(image_phish_score, 2),
            'image_decision': image_decision,
            'text_phish_score': round(text_phish_score, 2),
            'text_decision': txt_branch_decision,
            'image_vector': image_vector,
            'text_vector': text_vector,
            'fused_vector': fused_vector,
            'voice_phish_score': 0.0,
            'voice_decision': 0,
            'voice_vector': np.zeros(6),
            'ai_score_boosted': 0.0
        }

        print(f"Saving results for {site_folder} to {output_file}")
        save_single_result(result, output_file)
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
            'fused_vector': np.zeros(28),  # Adjust this size if needed
            'voice_phish_score': 0.0,
            'voice_decision': 0,
            'voice_vector': np.zeros(6),
            'ai_score_boosted': 0.0
        }
        
        # Try to save this result so we still have an entry in the CSV
        try:
            save_single_result(result, output_file)
            print(f"Saved error result for {site_folder}")
        except Exception as save_error:
            print(f"Could not save error result for {site_folder}: {str(save_error)}")
        
        return result

def save_single_result(result, output_file=None):
    """Save results with simplified decimal precision"""
    if output_file is None:
        output_file = os.path.join(OUTPUT_DIR, 'Learned_Logo_Phishing_predict.csv')
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    write_header = not os.path.exists(output_file) or os.stat(output_file).st_size == 0
    
    try:
        with open(output_file, 'a', newline='') as f:
            writer = csv.writer(f)
            
            if write_header:
                writer.writerow([
                    'Site Folder', 'URL', 'Multimodal_Decision',
                    'Image Phish Score','Image_Decision', 'Text Phish Score','Text_Decision',
                    'Voice Phish Score', 'Voice_Decision',
                    'Image Features', 'Text Features', 'Voice Features', 'Fused Features', 'AI Score Boosted'
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
                f"{result.get('voice_phish_score', 0.0):.2f}",
                result.get('voice_decision', 0),
                '|'.join([f"{x:.2f}" for x in result['image_vector']]),
                '|'.join([f"{x:.2f}" for x in result['text_vector']]),
                '|'.join([f"{x:.2f}" for x in result.get('voice_vector', np.zeros(6))]),
                '|'.join([f"{x:.4f}" for x in result['fused_vector']]),  # Keep more precision for fused features
                f"{result.get('ai_score_boosted', 0.0):.3f}"
            ])
            
    except Exception as e:
        print(f"Failed to save results for {result['site_folder']}: {str(e)}")

def process_dataset(dataset_path=None, output_file=None):
    """Process all sites in dataset"""
    # Use provided paths or defaults
    dataset_path = dataset_path or DATASET_PATH
    output_dir = os.path.dirname(output_file) if output_file else OUTPUT_DIR
    
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    print(f"Processing dataset from: {dataset_path}")
    
    for entry in os.listdir(dataset_path):
        entry_path = os.path.join(dataset_path, entry)
        
        # If it's a directory, treat as site folder (html/img analysis)
        if os.path.isdir(entry_path):
            result = process_site(entry, dataset_path, output_file)
            if result:
                results.append(result)
                print(f"Processed {entry}: {result['decision']}")
        # If it's a .wav file, treat as voice-only analysis
        elif entry.lower().endswith('.wav'):
            result = process_voice_file(entry_path, output_file)
            if result:
                results.append(result)
                print(f"Processed voice file {entry}: {result['decision']}")
        else:
            continue
    
    print(f"Completed processing {len(results)} entries")
    return results

if __name__ == '__main__':
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Process websites for phishing detection')
    parser.add_argument('--folder', type=str, help='Path to the folder containing website data')
    parser.add_argument('--output_txt', type=str, help='Path to save the output CSV file')
    parser.add_argument('--dataset', type=str, help='Path to the dataset directory')
    parser.add_argument('--output', type=str, help='Path to the output directory')
    
    args = parser.parse_args()
    
    # Use command line arguments if provided, otherwise use defaults
    dataset_path = args.dataset or DATASET_PATH
    output_file = args.output_txt or os.path.join(OUTPUT_DIR, 'Learned_Logo_Phishing_predict.csv')
    
    # Process the dataset
    process_dataset(dataset_path, output_file)