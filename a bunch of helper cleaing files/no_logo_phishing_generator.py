import os
import csv
import cv2
import numpy as np
from datetime import datetime

def create_blank_images(base_path, report_file):
    """
    Replace all shot.png files in the given directory with blank white images,
    preserving the original filename.
    
    Args:
        base_path: Path to the no-logo phishing dataset
        report_file: Path to the CSV report file
    """
    # Create a blank white image (800x600 pixels)
    # blank_image = np.ones((800, 600, 3), dtype=np.uint8) * 255
    blank_image = np.ones((600, 800, 3), dtype=np.uint8) * 255

    
    # Get all subfolders
    subfolders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    
    # Create report file
    with open(report_file, 'w', newline='', encoding='utf-8') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Folder Name', 'URL', 'Screenshot Replaced', 'Timestamp'])
        
        print(f"Starting to process {len(subfolders)} folders in {base_path}...")
        
        success_count = 0
        failure_count = 0
        
        for folder in subfolders:
            folder_path = os.path.join(base_path, folder)
            screenshot_path = os.path.join(folder_path, 'shot.png')
            info_path = os.path.join(folder_path, 'info.txt')
            
            # Extract URL from info.txt if it exists
            url = "Unknown"
            if os.path.exists(info_path):
                try:
                    with open(info_path, 'r', encoding='utf-8', errors='ignore') as f:
                        url = f.read().strip()
                except Exception as e:
                    print(f"  Error reading {info_path}: {e}")
            
            print(f"Processing folder: {folder}")
            print(f"  URL: {url}")
            
            # Replace screenshot with blank image
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if os.path.exists(screenshot_path):
                try:
                    # Save blank image with the same name
                    cv2.imwrite(screenshot_path, blank_image)
                    print(f"  Successfully replaced screenshot with blank image")
                    csv_writer.writerow([folder, url, "Yes", timestamp])
                    success_count += 1
                except Exception as e:
                    print(f"  Error replacing screenshot: {e}")
                    csv_writer.writerow([folder, url, f"No - Error: {e}", timestamp])
                    failure_count += 1
            else:
                print(f"  No screenshot found at {screenshot_path}")
                
                # Create the blank image if screenshot doesn't exist
                try:
                    cv2.imwrite(screenshot_path, blank_image)
                    print(f"  Created new blank screenshot")
                    csv_writer.writerow([folder, url, "Yes - Created new", timestamp])
                    success_count += 1
                except Exception as e:
                    print(f"  Error creating screenshot: {e}")
                    csv_writer.writerow([folder, url, f"No - Error: {e}", timestamp])
                    failure_count += 1
    
    print(f"\nProcessing complete!")
    print(f"Total folders processed: {len(subfolders)}")
    print(f"Successful replacements: {success_count}")
    print(f"Failed replacements: {failure_count}")
    print(f"Report saved to: {report_file}")

if __name__ == "__main__":
    # Set paths
    no_logo_phishing_path = "datasets/benign_without_logo"
    report_path = "benign_no_logo_generator_report.csv"
    
    # Create blank images and generate report
    create_blank_images(no_logo_phishing_path, report_path)