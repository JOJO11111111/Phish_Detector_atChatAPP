#!/usr/bin/env python3
import os
import pandas as pd
import re
import tldextract
from urllib.parse import urlparse

# ======================
# CONFIGURATION
# ======================
BASE_DATA_PATH = "/home/tiffanybao/PhishIntention/datasets"
OUTPUT_PATH = "/home/tiffanybao/PhishIntention/results/4.12/rule_based"
os.makedirs(OUTPUT_PATH, exist_ok=True)

# ======================
# UTILITY FUNCTIONS
# ======================
def try_read_file(filepath):
    """Attempt to read a file with multiple encodings"""
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, PermissionError) as e:
            continue
    return ""  # Return empty if all encodings fail

# ======================
# DETECTION RULES
# ======================
def check_brand_mismatch(html, url):
    """Rule 1: Check if brand names appear without matching domain"""
    if not html or not url:
        return False
        
    brands = [
        'apple', 'alibaba', '1&1', 'adobe', 'at&t', 'amazon',
        'bank of america', 'dropbox', 'ebay', 'ems', 'facebook',
        'outlook', 'office', 'microsoft', 'paypal', 'netflix',
        'wells fargo', 'chase', 'citibank', 'linkedin'
    ]
    try:
        domain = tldextract.extract(url).domain.lower()
        html_lower = html.lower()
        return any(brand in html_lower and brand not in domain for brand in brands)
    except:
        return False

def check_hidden_elements(html):
    """Rule 2: Detect hidden HTML elements"""
    if not html:
        return False
        
    patterns = [
        r'style=[\'"]display:\s*none',
        r'style=[\'"]visibility:\s*hidden',
        r'type=[\'"]hidden[\'"]',
        r'opacity:\s*0',
        r'width:\s*0(px)?;',
        r'height:\s*0(px)?;'
    ]
    try:
        return any(re.search(pattern, html, re.IGNORECASE) for pattern in patterns)
    except:
        return False

def check_suspicious_url(url):
    """Rule 3: Analyze URL structure"""
    if not url:
        return False
        
    try:
        parsed = urlparse(url)
        domain_parts = parsed.netloc.split('.')
        
        return (
            '-' in parsed.netloc or
            len(url) > 75 or
            any(char in url for char in ['@', '#', '!']) or
            sum(c.isdigit() for c in parsed.netloc) > 3 or
            len(domain_parts) > 3  # Too many subdomains
        )
    except:
        return False

def check_sensitive_fields(html):
    """Rule 4: Detect password/OTP fields"""
    if not html:
        return False
        
    try:
        return (
            'type="password"' in html.lower() or
            'name="otp"' in html.lower() or
            'name="verification_code"' in html.lower() or
            'name="credit_card"' in html.lower() or
            'name="ssn"' in html.lower()
        )
    except:
        return False

def check_external_resources(html):
    """Rule 5: Check for excessive external resources"""
    if not html:
        return False
        
    try:
        external = re.findall(r'src=["\'](http[s]?://[^"\']+)["\']', html)
        return len(external) > 3
    except:
        return False

def check_grammar_errors(text):
    """Rule 6: Detect poor grammar/spelling"""
    if not text:
        return False
        
    try:
        error_patterns = [
            r'\byour\s+bank\b',
            r'\bsecurity\s+alert\b',
            r'\bverify\s+your\b',
            r'\bclick\s+here\b',
            r'\baccount\s+update\b'
        ]
        return sum(len(re.findall(pattern, text.lower()))) > 2
    except:
        return False

# ======================
# CORE DETECTOR
# ======================
def is_phishing(html, url):
    """Combine all rules for final decision"""
    rules = [
        check_brand_mismatch(html, url),
        check_hidden_elements(html),
        check_suspicious_url(url),
        check_sensitive_fields(html),
        check_external_resources(html),
        check_grammar_errors(html)
    ]
    return sum(rules) >= 3  # At least 3 rules must trigger

# ======================
# DATA PROCESSING
# ======================
def load_dataset(base_path, label):
    """Load dataset from folder structure"""
    data = []
    if not os.path.exists(base_path):
        return pd.DataFrame(data)
        
    for folder in os.listdir(base_path):
        folder_path = os.path.join(base_path, folder)
        if not os.path.isdir(folder_path):
            continue
            
        try:
            # Read info.txt for URL
            info_file = os.path.join(folder_path, "info.txt")
            url = try_read_file(info_file).strip() if os.path.exists(info_file) else ""
            
            # Read HTML content
            html_file = os.path.join(folder_path, "html.txt")
            html = try_read_file(html_file) if os.path.exists(html_file) else ""
            
            data.append({
                'folder_name': folder,
                'url': url,
                'html': html,
                'true_label': label
            })
        except Exception as e:
            print(f"Error processing {folder}: {str(e)}")
            continue
            
    return pd.DataFrame(data)

# ======================
# MAIN EXECUTION
# ======================
if __name__ == "__main__":
    datasets = [
        ('benign_with_logo', 0),
        ('benign_without_logo', 0),
        ('Fresh_Logo_Phishing', 1),
        ('Learned_Logo_Phishing', 1),
        ('No_Logo_Phishing', 1)
    ]

    for dataset_name, label in datasets:
        print(f"\nProcessing {dataset_name}...")
        try:
            dataset_path = os.path.join(BASE_DATA_PATH, dataset_name)
            if not os.path.exists(dataset_path):
                print(f"Directory not found: {dataset_path}")
                continue
                
            df = load_dataset(dataset_path, label)
            
            if df.empty:
                print(f"No valid data found in {dataset_name}")
                continue
                
            # Apply detection rules
            df['phish_category'] = df.apply(
                lambda row: int(is_phishing(row['html'], row['url'])), 
                axis=1
            )
            
            # Calculate confidence score
            df['phish_score'] = df.apply(
                lambda row: sum([
                    check_brand_mismatch(row['html'], row['url']),
                    check_hidden_elements(row['html']),
                    check_suspicious_url(row['url']),
                    check_sensitive_fields(row['html']),
                    check_external_resources(row['html']),
                    check_grammar_errors(row['html'])
                ])/6.0,
                axis=1
            )
            
            # Save results
            output_df = df[['folder_name', 'url', 'phish_category', 'phish_score']]
            output_file = os.path.join(OUTPUT_PATH, f"{dataset_name}_predict.csv")
            output_df.to_csv(output_file, index=False)
            print(f"Successfully processed {len(df)} items")
            
        except Exception as e:
            print(f"Fatal error processing {dataset_name}: {str(e)}")
            continue

    print("\nRule-based detection completed!")
    print(f"Results saved to: {OUTPUT_PATH}")