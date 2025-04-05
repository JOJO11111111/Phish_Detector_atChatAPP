from openai import OpenAI
import json
import os

from configs import load_config
from crp_locator import crp_locator
from Web_Crawling import setup_driver
from modules import crp_classifier

from modules.HTML_crp_locator import static_crp_locator
from utils.web_utils import get_page_text, visit_url

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "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"))
from crp_locator import keyword_heuristic
import requests
from bs4 import BeautifulSoup
import re
class HTML_Analyzer:
    def __init__(self, crp_locator_model=None, awl_model=None, crp_classifier=None):
        self.CRP_LOCATOR_MODEL = crp_locator_model
        self.AWL_MODEL = awl_model
        self.CRP_CLASSIFIER = crp_classifier

    def _load_config(self):
        self.AWL_MODEL, self.CRP_CLASSIFIER, self.CRP_LOCATOR_MODEL, self.SIAMESE_MODEL, self.OCR_MODEL, \
            self.SIAMESE_THRE, self.LOGO_FEATS, self.LOGO_FILES, self.DOMAIN_MAP_PATH = load_config()

    def detect_crp_and_extract_target(html_content, base_url=None):
        soup = BeautifulSoup(html_content, 'html.parser')
        is_crp = False
        target_url = None

        for form in soup.find_all('form'):
            input_types = [inp.get('type', '').lower() for inp in form.find_all('input')]
            if 'password' in input_types:
                is_crp = True
                target_url = form.get('action')
                break

        if not is_crp:
            if soup.find('input', {'type': 'password'}):
                is_crp = True

        if not is_crp:
            text = soup.get_text(separator=' ').lower()
            keywords = ["login", "sign in", "log in", "enter password", "access your account"]
            if any(k in text for k in keywords):
                is_crp = True

        if not target_url:
            meta = soup.find('meta', attrs={'http-equiv': re.compile("refresh", re.I)})
            if meta and 'content' in meta.attrs:
                match = re.search(r'url=(.+)', meta['content'], re.IGNORECASE)
                if match:
                    target_url = match.group(1).strip()

        if not target_url:
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string:
                    match = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', script.string)
                    if match:
                        target_url = match.group(1).strip()
                        break

        if base_url and target_url and not re.match(r'^https?://', target_url):
            from urllib.parse import urljoin
            target_url = urljoin(base_url, target_url)

        return is_crp, target_url


    def analyze_html_pipeline(self, html_path, base_url=None, screenshot_path=None):
        """
        Main analysis pipeline: analyzes HTML + (optional) redirected CRP page.
        :param html_path: Path to original HTML file
        :param base_url: For resolving relative redirect links
        :return: vector1, vector2
        """
        html = load_html_file(html_path)

        print("[STEP 1] Analyze original HTML...")
        gpt_result_1 = analyze_html_with_openai(html)
        vector_1 = convert_to_vector(gpt_result_1)
        vector_2 = None
        print("Vector 1:", vector_1)

        is_crp, redirect_url = static_crp_locator(html, base_url=base_url)

        if not is_crp:
            print("Not a CRP page.")
            return vector_1, vector_2

        if not redirect_url:
            if not redirect_url:
                print("Static CRP analysis failed to find redirect.")
                print("[Trying dynamic analysis with crp_locator()]")

                try:
                    driver = setup_driver()
                    visit_success, driver = visit_url(driver, base_url)

                    if not visit_success:
                        print("[ERROR] Failed to revisit original URL")
                        return vector_1, vector_2

                    page_text = get_page_text(driver).split("\n")


                    new_html_path = screenshot_path.replace("screenshot.png", "new_page.html")
                    new_info_path = screenshot_path.replace("screenshot.png", "new_info.txt")
                    new_screenshot_path = screenshot_path.replace("screenshot.png", "new_screenshot.png")


                    current_url, reached = keyword_heuristic(
                        driver=driver,
                        orig_url=base_url,
                        page_text=page_text,
                        new_screenshot_path=new_screenshot_path,
                        new_html_path=new_html_path,
                        new_info_path=new_info_path,
                        ele_model=self.AWL_MODEL,
                        cls_model=self.CRP_CLASSIFIER
                    )

                    print("After keyword_heuristic:", reached)

                    if reached:

                        with open(new_html_path, 'r', encoding='utf-8') as f:
                            redirected_html = f.read()

                        print("[STEP 2] Detected CRP. Analyzing redirected page...")
                        gpt_result_2 = analyze_html_with_openai(redirected_html)
                        vector_2 = convert_to_vector(gpt_result_2)
                        print("Vector 2:", vector_2)
                        return vector_1, vector_2
                    else:
                        print("Dynamic analysis did not reach CRP.")

                except Exception as e:
                    print(f"[ERROR] Dynamic analysis failed: {e}")

                return vector_1, vector_2

        print(f"[STEP 3] Detected CRP. Attempting to access: {redirect_url}")
        try:
            response = requests.get(redirect_url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
            html2 = response.text
            print("Analyzing redirected page...")
            gpt_result_2 = analyze_html_with_openai(html2)
            vector_2 = convert_to_vector(gpt_result_2)
            print("Vector 2:", vector_2)
            return vector_1, vector_2
        except Exception as e:
            print("[ERROR] Could not fetch redirected page:", e)
            return vector_1, vector_2

# Open AI API key: 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

def analyze_html_with_openai(html_content, model="gpt-4"):
    """
    Sends HTML content to GPT-4 and receives structured JSON analysis.
    """
    max_chars = 6000  # Stay under token limit
    html_chunk = html_content[:max_chars]

    system_prompt = "You are a phishing detection assistant. Please read the given HTML file of this website and extract phishing-related features in JSON format."

    user_prompt = f"""
    You are a phishing detection assistant. Based on the following HTML, return a JSON object with these fields:

    - "has_login_form": true/false 
    - "form_action_suspicious": true/false (does the form submit credentials to an unrelated or suspicious domain?)
    - "uses_obfuscated_script": true/false (does the page contain suspicious encoded JavaScript or delay-loaded content?)
    - "suspicious_text_patterns": true/false (such as urgency, misleading instructions, or brand inconsistency)
    - "mentioned_brand": string (e.g., 'PayPal', 'Apple', or 'Unknown')
    - "phishing_score": float between 0.0 and 1.0 (likelihood it's phishing)

    Rules:
    - Consider the structure and logic of forms (e.g., where they submit to).
    - Inspect script tags and look for obfuscation or delay-based phishing injection.
    - Flag suspicious language like "your account will be locked", "verify immediately", or branding conflicts.

    Return only valid JSON, without markdown formatting or explanation.

    HTML:
    {html_chunk}
    """
    try:
        response = client.chat.completions.create(model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0)

        reply = response.choices[0].message.content

        print("[GPT-4 RAW OUTPUT]")
        print(reply)

        result = json.loads(reply)
        return result

    except Exception as e:
        print(f"[OpenAI ERROR] {e}")
        return None


def convert_to_vector(gpt_result):
    if not gpt_result:
        return [0]*6

    return [
        int(gpt_result.get("has_login_form", False)),
        int(gpt_result.get("form_action_suspicious", False)),
        int(gpt_result.get("uses_obfuscated_script", False)),
        int(gpt_result.get("suspicious_text_patterns", False)),
        0 if gpt_result.get("mentioned_brand", "").lower() == "unknown" else 1,
        float(gpt_result.get("phishing_score", 0.0))
    ]


def load_html_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
