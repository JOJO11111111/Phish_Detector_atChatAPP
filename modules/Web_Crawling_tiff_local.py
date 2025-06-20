# web crawling
# from selenium import webdriver
from seleniumwire import webdriver  # Use seleniumwire's webdriver, not regular selenium

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import helium

import time
import os
import re

# this one conflicts with my device, use the one from the web_utils.py instead 
# # Set up the headless Chrome driver
# def setup_driver():
#     # chrome_options = Options()
#     options = Options()

#     # options.binary_location = '/usr/bin/chromium-browser'  # Explicit path to Chromium
#     options.binary_location = '/snap/bin/chromium'
#     options.add_argument("--headless")
#     options.add_argument("--disable-gpu")
#     options.add_argument("--window-size=1920,1080")
#     options.add_argument("--no-sandbox")
#     options.add_argument("--disable-dev-shm-usage")
#     options.add_argument('--remote-debugging-port=9422')

 

#     # Use the same ChromeDriver path as my local working version
#     service = Service(executable_path='/home/tiffanybao/chrome_driver/chromedriver-linux64/chromedriver')
#     driver = webdriver.Chrome(service=service, options=options)

#     return driver



def initialize_chrome_settings():
    '''
    initialize chrome settings
    '''
    options = webdriver.ChromeOptions()
    options.binary_location = '/usr/bin/chromium-browser'  # Add this line
    options.add_argument('--user-data-dir=/tmp/chrome-user-data')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--remote-debugging-port=9229')  # Different port than default

    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    )
    options.add_argument("--headless") #: do not disable browser (have some issues: https://github.com/mherrmann/selenium-python-helium/issues/47)
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    options.add_argument('--ignore-certificate-errors')  # ignore errors
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--no-proxy-server')
    options.add_argument("--proxy-server='direct://'")
    options.add_argument("--proxy-bypass-list=*")

    options.add_argument("--start-maximized")
    options.add_argument('--window-size=1920,1080')  # fix screenshot size
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36')
    options.set_capability('unhandledPromptBehavior', 'dismiss')  # dismiss

    return options


def setup_driver():
    '''
    load chrome driver
    '''

    seleniumwire_options = {
        'seleniumwire_options': {
            'enable_console_log': True,
            'log_level': 'DEBUG',
        }
    }

    options = initialize_chrome_settings()
    capabilities = DesiredCapabilities.CHROME
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # chromedriver 75+
    # capabilities["unexpectedAlertBehaviour"] = "dismiss"  # handle alert
    capabilities["pageLoadStrategy"] = "eager"  # eager mode #FIXME: set eager mode, may load partial webpage

    # driver = webdriver.Chrome(ChromeDriverManager().install())
    # service = Service(executable_path=ChromeDriverManager().install())
    
    service = Service(executable_path='/home/tiffanybao/chrome_driver/chromedriver-linux64/chromedriver')
    driver = webdriver.Chrome(options=options, service=service, seleniumwire_options=seleniumwire_options)
    # driver = webdriver.Chrome(options=options, service=service, seleniumwire_options=seleniumwire_options)
    
    driver.set_page_load_timeout(30)  # set timeout to avoid wasting time
    driver.set_script_timeout(30)  # set timeout to avoid wasting time
    helium.set_driver(driver)
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

def crawl_url(url, base_dir='datasets/benign_with_logo'):
    driver = setup_driver()  # Assuming this initializes the WebDriver
    # file_exists = False
    
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
        if os.path.exists(html_path) or os.path.exists(screenshot_path) or os.path.exists('new_'+html_path) or os.path.exists('new_'+screenshot_path):
            print(f"[INFO] Found existing files for {url} at {html_path}. Skipping crawl.")
            # file_exists = True
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