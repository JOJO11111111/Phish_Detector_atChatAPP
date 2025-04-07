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

    # chrome_options.add_argument("--headless")
    # chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--window-size=1920,1080")
    # chrome_options.add_argument("--no-sandbox")
    # chrome_options.add_argument("--disable-dev-shm-usage")
    # chrome_options.add_argument('--remote-debugging-port=9222') 
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


# Crawl the given URL and save HTML + screenshot
def crawl_url(url, output_dir='outputs'):
    driver = setup_driver()

    try:
        print(f"[INFO] Crawling URL: {url}")
        # Load the webpage
        driver.get(url)
        time.sleep(3)

        html_content = driver.page_source

        # Create a folder to save the output files
        folder_name = sanitize_url(url)
        save_dir = os.path.join(output_dir, folder_name)
        os.makedirs(save_dir, exist_ok=True)

        # Save the HTML file
        html_path = os.path.join(save_dir, 'page.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Take and save a full-page screenshot
        screenshot_path = os.path.join(save_dir, 'screenshot.png')
        driver.save_screenshot(screenshot_path)

        print(f"[SUCCESS] Saved to {save_dir}")
        return html_path, screenshot_path

    except Exception as e:
        print(f"[ERROR] Failed to crawl URL: {e}")
        return None, None
        exit()

    finally:
        driver.quit()
