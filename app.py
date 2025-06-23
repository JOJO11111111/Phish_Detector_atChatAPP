from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import os
import tempfile
import subprocess
import json
import csv
import logging
from datetime import datetime
from phishintention import PhishIntentionWrapper
import cv2
import numpy as np
import time
import helium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urlparse
import shutil

# Import the setup_driver function from your module
from modules.Web_Crawling_tiff_local import setup_driver

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the PhishIntention wrapper
phish_detector = PhishIntentionWrapper()

# Define paths
DEPLOYMENT_DATASET_PATH = './datasets/deployment'
OUTPUT_DIR = './results/deployment'

# Create directories if they don't exist
os.makedirs(DEPLOYMENT_DATASET_PATH, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def save_website_data(url, site_folder):
    """Save website HTML and screenshot to the specified folder"""
    try:
        # Save URL to info.txt
        info_file = os.path.join(site_folder, "info.txt")
        with open(info_file, "w") as f:
            f.write(url)
        logger.info(f"Saved URL to {info_file}")
        
        # Set up Chrome driver using the imported function
        logger.info("Setting up Chrome driver...")
        try:
            driver = setup_driver()
            logger.info("Chrome driver setup successful")
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {str(e)}")
            return False
        
        try:
            # Load the page
            logger.info(f"Loading URL: {url}")
            driver.get(url)
            logger.info("Page loaded successfully")
            
            # Wait for page to load
            logger.info("Waiting for page to stabilize...")
            time.sleep(5)  # Increased wait time
            
            # Save HTML
            logger.info("Saving HTML content...")
            html_file = os.path.join(site_folder, "html.txt")
            with open(html_file, "w", encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"Saved HTML to {html_file}")
            
            # Take screenshot
            logger.info("Taking screenshot...")
            screenshot_file = os.path.join(site_folder, "shot.png")
            driver.save_screenshot(screenshot_file)
            logger.info(f"Saved screenshot to {screenshot_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during page processing: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
        finally:
            logger.info("Closing Chrome driver...")
            try:
                driver.quit()
                logger.info("Chrome driver closed successfully")
            except Exception as e:
                logger.error(f"Error closing Chrome driver: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error in save_website_data: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def save_voice_file(voice_filename, site_folder):
    """Save voice file to the dataset folder"""
    try:
        # Source path from the Golang backend
        source_path = f"./Realtime-chat-app-golang/web/static/file/{voice_filename}"
        
        if not os.path.exists(source_path):
            logger.error(f"Voice file not found at {source_path}")
            return False
        
        # Destination path in the dataset folder
        dest_path = os.path.join(site_folder, f"{voice_filename}")
        
        # Copy the file
        shutil.copy2(source_path, dest_path)
        logger.info(f"Copied voice file from {source_path} to {dest_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error copying voice file: {str(e)}")
        return False

@app.route('/scan_voice', methods=['POST'])
def scan_voice():
    """Scan a voice file for phishing"""
    try:
        data = request.get_json()
        voice_filename = data.get('voice_filename')
        
        if not voice_filename:
            return jsonify({'error': 'Voice filename is required'}), 400
        
        logger.info(f"Received voice scan request for file: {voice_filename}")
        
        # Create a unique folder for this voice scan
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        voice_folder = f"voice_{timestamp}"
        
        # Create the voice folder
        voice_folder_path = os.path.join(DEPLOYMENT_DATASET_PATH, voice_folder)
        os.makedirs(voice_folder_path, exist_ok=True)
        
        # Save the voice file to the dataset folder
        logger.info(f"Copying voice file {voice_filename} to dataset folder")
        copy_success = save_voice_file(voice_filename, voice_folder_path)
        
        if not copy_success:
            logger.error(f"Failed to copy voice file {voice_filename}")
            return jsonify({'error': 'Failed to access voice file'}), 500
        
        logger.info(f"Voice file copied successfully for {voice_filename}")
        
        # Create a unique output file for this scan
        output_file = os.path.join(OUTPUT_DIR, f'voice_result_{timestamp}.csv')
        
        # Run the voice analysis
        logger.info(f"Running voice analysis for {voice_folder}")
        try:
            # Import the process_voice_file function from main.py
            from main import process_voice_file
            
            # Get the full path to the voice file
            voice_file_path = os.path.join(voice_folder_path, voice_filename)
            
            # Process the voice file
            result = process_voice_file(voice_file_path, output_file)
            
            if result is None:
                logger.error(f"Failed to process voice file {voice_filename}")
                return jsonify({'error': 'Failed to process voice file'}), 500
                
            logger.info(f"Voice analysis completed for {voice_filename}")
            
            # Read the results
            with open(output_file, 'r') as f:
                content = f.read()
                logger.info(f"CSV content: {content}")
                
                # Create a new StringIO object with the content
                import io
                csv_file = io.StringIO(content)
                reader = csv.DictReader(csv_file)
                
                # Get the first row
                row = next(reader, None)
                if row:
                    logger.info(f"Parsed row: {row}")
                    
                    # Map the CSV columns to the expected format
                    decision = row.get("Multimodal_Decision", "").lower()
                    
                    # Check if there was an error in processing
                    if decision == "error":
                        logger.error("Error in processing detected in CSV")
                        return jsonify({'error': 'Error in processing the voice file'}), 500
                    
                    is_phishing = decision == "phishing"
                    confidence = float(row.get("Voice Phish Score", 0.0))
                    
                    # Get GPT response from the result object
                    voice_detail = result.get('voice_detail', {})
                    gpt_response = voice_detail.get('gpt_response', '')
                    transcript = voice_detail.get('transcript', '')
                    ai_score_boosted = result.get('ai_score_boosted', 0.0)
                    
                    # Create a details object with all the information
                    details = {
                        "voice_filename": voice_filename,
                        "voice_phish_score": float(row.get("Voice Phish Score", 0.0)),
                        "voice_decision": int(row.get("Voice_Decision", 0)),
                        "voice_vector": row.get("Voice Features", ""),
                        "image_phish_score": float(row.get("Image Phish Score", 0.0)),
                        "image_decision": int(row.get("Image_Decision", 0)),
                        "text_phish_score": float(row.get("Text Phish Score", 0.0)),
                        "text_decision": int(row.get("Text_Decision", 0)),
                        "image_vector": row.get("Image Features", ""),
                        "text_vector": row.get("Text Features", ""),
                        "fused_vector": row.get("Fused Features", ""),
                        "gpt_response": gpt_response,
                        "transcript": transcript,
                        "ai_score_boosted": ai_score_boosted
                    }
                    
                    logger.info(f"Returning voice results: is_phishing={is_phishing}, confidence={confidence}")
                    
                    return jsonify({
                        'is_phishing': is_phishing,
                        'confidence': confidence,
                        'details': details
                    })
                else:
                    logger.error("No data found in CSV file")
                    return jsonify({'error': 'No results found'}), 500
                    
        except Exception as e:
            logger.error(f"Error in voice analysis: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Error in voice analysis: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in scan_voice: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/scan', methods=['POST'])
def scan_website():
    """Scan a website for phishing"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        logger.info(f"Received scan request for URL: {url}")
        
        # Create a unique folder for this scan
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(url).netloc.replace('.', '_')
        site_folder = f"{domain}_{timestamp}"
        
        # Create the website folder
        website_folder = os.path.join(DEPLOYMENT_DATASET_PATH, site_folder)
        os.makedirs(website_folder, exist_ok=True)
        
        # Save the URL to info.txt
        with open(os.path.join(website_folder, 'info.txt'), 'w') as f:
            f.write(url)
        
        # Crawl the website and save HTML and screenshot
        logger.info(f"Starting website crawling for {url}")
        crawl_success = save_website_data(url, website_folder)
        
        if not crawl_success:
            logger.error(f"Failed to crawl website {url}")
            return jsonify({'error': 'Failed to crawl website'}), 500
        
        logger.info(f"Website crawling completed for {url}")
        
        # Create a unique output file for this scan
        output_file = os.path.join(OUTPUT_DIR, f'result_{timestamp}.csv')
        
        # Run the analysis script
        logger.info(f"Running analysis for {site_folder}")
        try:
            # Import the process_site function from main.py
            from main import process_site
            
            # Process the site
            result = process_site(site_folder, DEPLOYMENT_DATASET_PATH, output_file)
            
            if result is None:
                logger.error(f"Failed to process site {site_folder}")
                return jsonify({'error': 'Failed to process website'}), 500
                
            logger.info(f"Analysis completed for {site_folder}")
            
            # Read the results
            with open(output_file, 'r') as f:
                content = f.read()
                logger.info(f"CSV content: {content}")
                
                # Create a new StringIO object with the content
                import io
                csv_file = io.StringIO(content)
                reader = csv.DictReader(csv_file)
                
                # Get the first row
                row = next(reader, None)
                if row:
                    logger.info(f"Parsed row: {row}")
                    
                    # Map the CSV columns to the expected format
                    # The CSV has columns: Site Folder, URL, Multimodal_Decision, Image Phish Score, Image_Decision, Text Phish Score, Text_Decision, Image Features, Text Features, Fused Features
                    decision = row.get("Multimodal_Decision", "").lower()
                    
                    # Check if there was an error in processing
                    if decision == "error":
                        logger.error("Error in processing detected in CSV")
                        return jsonify({'error': 'Error in processing the website'}), 500
                    
                    is_phishing = decision == "phishing"
                    confidence = float(row.get("Image Phish Score", 0.0))
                    
                    # Create a details object with all the information
                    details = {
                        "url": row.get("URL", url),
                        "image_phish_score": float(row.get("Image Phish Score", 0.0)),
                        "image_decision": int(row.get("Image_Decision", 0)),
                        "text_phish_score": float(row.get("Text Phish Score", 0.0)),
                        "text_decision": int(row.get("Text_Decision", 0)),
                        "image_vector": row.get("Image Features", ""),
                        "text_vector": row.get("Text Features", ""),
                        "fused_vector": row.get("Fused Features", "")
                    }
                    
                    logger.info(f"Returning results: is_phishing={is_phishing}, confidence={confidence}")
                    
                    return jsonify({
                        'is_phishing': is_phishing,
                        'confidence': confidence,
                        'details': details
                    })
                else:
                    logger.error("No data found in CSV file")
                    return jsonify({'error': 'No results found'}), 500
                    
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Error in analysis: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in scan_website: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/')
def home():
    return jsonify({
        'status': 'running',
        'message': 'PhishIntention API is running',
        'endpoints': {
            'detect': '/detect (POST) - Detect phishing in a webpage',
            'analyze': '/analyze (POST) - Analyze a URL for phishing'
        }
    })

@app.route('/analyze', methods=['POST'])
def analyze_url():
    try:
        data = request.json
        if not data:
            logger.error("No JSON data provided")
            return jsonify({'error': 'No JSON data provided'}), 400
            
        url = data.get('url')
        if not url:
            logger.error("Missing URL")
            return jsonify({'error': 'Missing URL'}), 400
        
        logger.info(f"Analyzing URL: {url}")
        
        # Create a unique folder for this analysis
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        site_folder = os.path.join(DEPLOYMENT_DATASET_PATH, f"site_{timestamp}")
        os.makedirs(site_folder, exist_ok=True)
        
        # Save URL to info.txt
        info_file = os.path.join(site_folder, "info.txt")
        with open(info_file, "w") as f:
            f.write(url)
        logger.info(f"Saved URL to {info_file}")
        
        # Run main.py to analyze the URL
        output_file = os.path.join(OUTPUT_DIR, f"result_{timestamp}.csv")
        
        # Get the absolute path to main.py
        main_script = os.path.abspath("main.py")
        logger.info(f"Running main.py from {main_script}")
        
        # Run main.py with the correct paths
        try:
            result = subprocess.run(["python", main_script, 
                                   "--folder", site_folder, 
                                   "--output_txt", output_file], 
                                  check=True, 
                                  capture_output=True, 
                                  text=True)
            logger.info(f"main.py output: {result.stdout}")
            if result.stderr:
                logger.warning(f"main.py stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running main.py: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            return jsonify({'error': f'Error running analysis: {str(e)}'}), 500
        
        # Read the results from the CSV file
        result = {"is_phishing": False, "confidence": 0.0, "details": {}}
        
        if os.path.exists(output_file):
            logger.info(f"Reading results from {output_file}")
            try:
                with open(output_file, 'r') as f:
                    content = f.read()
                    logger.info(f"CSV content: {content}")
                    
                    # Create a new StringIO object with the content
                    import io
                    csv_file = io.StringIO(content)
                    reader = csv.DictReader(csv_file)
                    
                    # Get the first row
                    row = next(reader, None)
                    if row:
                        logger.info(f"Parsed row: {row}")
                        
                        # Map the CSV columns to the expected format
                        decision = row.get("Multimodal_Decision", "").lower()
                        
                        # Check if there was an error in processing
                        if decision == "error":
                            logger.error("Error in processing detected in CSV")
                            return jsonify({'error': 'Error in processing the website'}), 500
                        
                        result["is_phishing"] = decision == "phishing"
                        result["confidence"] = float(row.get("Image Phish Score", 0.0))
                        
                        # Create a details object with all the information
                        result["details"] = {
                            "url": row.get("URL", url),
                            "image_phish_score": float(row.get("Image Phish Score", 0.0)),
                            "image_decision": int(row.get("Image_Decision", 0)),
                            "text_phish_score": float(row.get("Text Phish Score", 0.0)),
                            "text_decision": int(row.get("Text_Decision", 0)),
                            "image_vector": row.get("Image Features", ""),
                            "text_vector": row.get("Text Features", ""),
                            "fused_vector": row.get("Fused Features", "")
                        }
                        
                        logger.info(f"Results: {result}")
                    else:
                        logger.error("No rows found in the CSV file")
                        return jsonify({'error': 'No results found in the output file'}), 500
            except Exception as e:
                logger.error(f"Error reading results file: {e}")
                return jsonify({'error': f'Error reading results: {str(e)}'}), 500
        else:
            logger.error(f"Results file not found: {output_file}")
            return jsonify({'error': 'Results file not found'}), 500
        
        return jsonify(result)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/detect', methods=['POST'])
def detect_phishing():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        url = data.get('url')
        screenshot_base64 = data.get('screenshot')
        
        if not url or not screenshot_base64:
            return jsonify({'error': 'Missing url or screenshot'}), 400
            
        # Decode base64 screenshot
        try:
            screenshot_data = base64.b64decode(screenshot_base64.split(',')[1])
        except Exception as e:
            return jsonify({'error': f'Invalid screenshot data: {str(e)}'}), 400
            
        # Save screenshot to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(screenshot_data)
            screenshot_path = temp_file.name
            
        try:
            # Run detection
            result = phish_detector.test_orig_phishintention(
                url=url,
                screenshot_path=screenshot_path,
                save_vectors=False
            )
            
            # Clean up temporary file
            os.unlink(screenshot_path)
            
            return jsonify({
                'is_phishing': result['is_phishing'],
                'target_brand': result['target_brand'],
                'confidence': result['confidence']
            })
        except Exception as e:
            # Clean up temporary file in case of error
            if os.path.exists(screenshot_path):
                os.unlink(screenshot_path)
            raise e
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not Found', 'message': 'The requested URL was not found on the server'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    # Enable debug mode for more detailed error messages
    app.run(host='0.0.0.0', port=5000, debug=True) 