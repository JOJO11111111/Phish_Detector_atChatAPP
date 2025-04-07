import os
import re
import time
from io import BytesIO

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Set up headless Chrome driver
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Extract domain to use as folder name
def extract_domain(url):
    from urllib.parse import urlparse
    domain = urlparse(url).netloc
    return domain

# Crawl the given URL and save into datasets/test_sites/domain/
def crawl_url(url, base_dir='datasets/test_sites'):
    driver = setup_driver()

    try:
        print(f"[INFO] Crawling URL: {url}")
        driver.get(url)
        time.sleep(5)

        html_content = driver.page_source
        domain_folder = extract_domain(url)
        save_dir = os.path.join(base_dir, domain_folder)
        os.makedirs(save_dir, exist_ok=True)

        # Save HTML as html.txt
        html_path = os.path.join(save_dir, 'html.txt')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Save screenshot as shot.png
        screenshot_path = os.path.join(save_dir, 'shot.png')
        driver.save_screenshot(screenshot_path)

        # Also save the current URL as info.txt
        info_path = os.path.join(save_dir, 'info.txt')
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(driver.current_url)

        print(f"[SUCCESS] Saved HTML and screenshot to {save_dir}")
        return html_path, screenshot_path

    except Exception as e:
        print(f"[ERROR] Failed to crawl URL: {e}")
        return None, None

    finally:
        driver.quit()