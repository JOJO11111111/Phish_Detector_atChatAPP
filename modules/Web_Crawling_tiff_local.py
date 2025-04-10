# web crawling
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
import re


# Set up the headless Chrome driver
def setup_driver():
    # chrome_options = Options()
    options = Options()

    options.binary_location = '/usr/bin/chromium-browser'  # Explicit path to Chromium

    options.binary_location = '/usr/bin/chromium-browser'  # Explicit path to Chromium

    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument('--remote-debugging-port=9222')

    # # Create ChromeDriver service using WebDriver Manager
    # service = Service(ChromeDriverManager().install())
    # # Initialize the WebDriver with service and options
    # driver = webdriver.Chrome(service=service, options=chrome_options)

    # Use the same ChromeDriver path as my local working version
    service = Service(executable_path='/home/tiffanybao/chrome_driver/chromedriver-linux64/chromedriver')
    driver = webdriver.Chrome(service=service, options=options)

    return driver


# Sanitize a URL to create a safe folder name
def sanitize_url(url):
    # Remove http(s) and replace all non-alphanumeric characters with underscores
    return re.sub(r'[^a-zA-Z0-9]', '_', url.replace('http://', '').replace('https://', ''))

# Extract domain to use as folder name
def extract_domain(url):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return domain



# modified crawl func for multimodal test case, excluded single url test

def crawl_url(url, base_dir='datasets/test_sites'):
    driver = setup_driver()  # Assuming this initializes the WebDriver
    
    try:
        # Extract domain and set up save directory
        domain_folder = extract_domain(url)
        save_dir = os.path.join(base_dir, domain_folder)
        os.makedirs(save_dir, exist_ok=True)

        # Define expected file paths
        html_path = os.path.join(save_dir, 'html.txt')
        screenshot_path = os.path.join(save_dir, 'shot.png')
        info_path = os.path.join(save_dir, 'info.txt')

        # Check if either file already exists
        if os.path.exists(html_path) or os.path.exists(screenshot_path):
            print(f"[INFO] Found existing files for {url}. Skipping crawl.")
            return html_path, screenshot_path

        # If files don't exist, proceed with crawling
        print(f"[INFO] Crawling URL: {url}")
        driver.get(url)
        time.sleep(5)

        # Save HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

        # Save screenshot
        driver.save_screenshot(screenshot_path)

        # Save current URL (optional)
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(driver.current_url)

        print(f"[SUCCESS] Saved HTML and screenshot to {save_dir}")
        return html_path, screenshot_path

    except Exception as e:
        print(f"[ERROR] Failed to crawl URL: {e}")
        return None, None

    finally:
        driver.quit()