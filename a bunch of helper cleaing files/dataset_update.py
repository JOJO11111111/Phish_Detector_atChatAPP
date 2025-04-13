import os
import json
import csv
import re
from urllib.parse import urlparse
import shutil

def extract_url_from_info(info_path):
    
    """Extract the URL from the info.txt file using multiple methods."""
    try:
        
        with open(info_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
        
        # Method 1: Direct URL - if the entire content is a URL
        if content.startswith('http'):
            return content
            
        # Method 2: Find any URL in the content
        url_pattern = re.compile(r'(https?://[^\s\'"<>]+)')
        matches = url_pattern.findall(content)
        if matches:
            return matches[0]  # Return the first URL found
            
        # Method 3: Try to parse as JSON
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                # Look for common URL field names
                for key in ['url', 'URL', 'link', 'href', 'uri']:
                    if key in data:
                        return data[key]
        except:
            pass
            
        # Method 4: Check for Python dictionary string format
        for field in ['url', 'URL', 'link', 'href']:
            pattern = f"{field}'?:? ?['\"]([^'\"]+)['\"]"
            match = re.search(pattern, content)
            
            if match:
                return match.group(1)
                
        print(f"  Content preview (unable to extract URL): {content[:100]}...")
        
    except Exception as e:
        print(f"  Error reading {info_path}: {e}")
    
    return None

def get_domain(url):
    """Extract domain from URL."""
    try:
        if url:
            return urlparse(url).netloc
    except:
        pass
    return None

def update_folders(base_path, record_file):
    label = 0
    """Update folder names and info.txt files and record changes to CSV."""
    # Get all subfolders
    subfolders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    
    # Create/open CSV file for recording changes
    with open(record_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        # Write header with new label column
        csv_writer.writerow(['Original Folder Name', 'New Folder Name', 'URL', 'label'])
        
        for folder in subfolders:
            folder_path = os.path.join(base_path, folder)
            info_path = os.path.join(folder_path, 'info.txt')
            
            print(f"Processing folder: {folder}")
            
            # Check if info.txt exists
            if os.path.exists(info_path):
                # Extract URL from info.txt
                url = extract_url_from_info(info_path)
                
                if url:
                    # Update info.txt to contain only the URL
                    with open(info_path, 'w') as f:
                        f.write(url)
                    print(f"  Updated info.txt to contain only URL: {url}")
                    
                    # Get domain from URL
                    domain = get_domain(url)
                    
                    if domain and domain != folder:
                        # Create new folder path
                        new_folder_path = os.path.join(base_path, domain)
                        
                        # Handle case where target folder already exists
                        if os.path.exists(new_folder_path):
                            print(f"  Warning: Target folder {domain} already exists. Using {domain}_duplicate")
                            domain = f"{domain}_duplicate"
                            new_folder_path = os.path.join(base_path, domain)
                        
                        # Rename folder
                        shutil.move(folder_path, new_folder_path)
                        print(f"  Renamed folder from {folder} to {domain}")
                        
                        # Record the change with label=1
                        csv_writer.writerow([folder, domain, url, label])
                    else:
                        # Record no change if domain is the same as folder name
                        if domain == folder:
                            print(f"  No renaming needed for {folder} (already named by domain)")
                            csv_writer.writerow([folder, folder, url, label])
                        else:
                            print(f"  Could not extract domain from URL: {url}")
                            csv_writer.writerow([folder, "ERROR: Invalid domain", url, label])
                else:
                    # Manual mapping for specific folders
                    manual_urls = {
                        "TiffanyTestForDynamic": "https://tiffanybao.netlify.app/#work",
                        "Absa Group+2020-09-14-16`49`20": "https://absagroup.co.za",
                        "1&1 Ionos+2019-07-28-22`34`40": "https://ionos.com"
                    }
                    
                    if folder in manual_urls:
                        url = manual_urls[folder]
                        # Update info.txt to contain only the URL
                        with open(info_path, 'w') as f:
                            f.write(url)
                        print(f"  Used manual mapping. Updated info.txt to contain URL: {url}")
                        
                        # Get domain from URL
                        domain = get_domain(url)
                        
                        if domain:
                            # Create new folder path
                            new_folder_path = os.path.join(base_path, domain)
                            
                            # Handle case where target folder already exists
                            if os.path.exists(new_folder_path):
                                print(f"  Warning: Target folder {domain} already exists. Using {domain}_duplicate")
                                domain = f"{domain}_duplicate"
                                new_folder_path = os.path.join(base_path, domain)
                            
                            # Rename folder
                            shutil.move(folder_path, new_folder_path)
                            print(f"  Renamed folder from {folder} to {domain}")
                            
                            # Record the change with label=1
                            csv_writer.writerow([folder, domain, url, label])
                    else:
                        print(f"  Couldn't extract URL from info.txt")
                        csv_writer.writerow([folder, "ERROR: No URL found", "", label])
            else:
                print(f"  info.txt not found in {folder}")
                csv_writer.writerow([folder, "ERROR: No info.txt found", "", label])

# Set paths

# test_sites_path1 = "datasets/No_Logo_Phishing"
# test_sites_record1 = "datasets/No_Logo_Phishing.csv"

# print(f"Starting to process folders in {test_sites_path1}...")
# update_folders(test_sites_path1, test_sites_record1)
# print(f"Processing complete! Changes recorded in {test_sites_record1}")
# Define all dataset paths and their corresponding record files
dataset_pairs = [
    # ("datasets/No_Logo_Phishing", "datasets/No_Logo_Phishing.csv"),
    # ("datasets/Fresh_Logo_Phishing", "datasets/Fresh_Logo_Phishing.csv"),
    # ("datasets/Learned_Logo_Phishing", "datasets/Learned_Logo_Phishing.csv"),
    # ("datasets/benign_without_logo", "datasets/benign_without_logo.csv"),
    ("datasets/benign_with_logo", "datasets/benign_with_logo.csv")
]

# Process each dataset
for test_sites_path, test_sites_record in dataset_pairs:
    print(f"Starting to process folders in {test_sites_path}...")
    update_folders(test_sites_path, test_sites_record)
    print(f"Processing complete! Changes recorded in {test_sites_record}")