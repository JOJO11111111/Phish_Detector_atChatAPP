# html analyzer
from datetime import datetime
from openai import OpenAI
import json

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from configs import load_config

from modules.crp_locator import crp_locator
from modules.Web_Crawling_tiff_local import setup_driver
from modules import crp_classifier

from modules.HTML_crp_locator import static_crp_locator
from utils.web_utils import get_page_text, visit_url

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "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"))
from modules.crp_locator import keyword_heuristic
import requests
from bs4 import BeautifulSoup
import re

log_file_path = '/home/tiffanybao/PhishIntention/results/txt_log_print/log.txt' #change to your own path

os.makedirs(os.path.dirname(log_file_path), exist_ok=True)


def log_print(*args, **kwargs):
    # Get the original print output as a string
    import sys
    from io import StringIO

    # First, print to console as normal
    print(*args, **kwargs)

    # Now, capture what would have been printed to a string
    temp_out = StringIO()
    print(*args, file=temp_out, **kwargs)
    output = temp_out.getvalue()

    # Append to the log file
    with open(log_file_path, 'a') as f:
        f.write(output)




def extract_json_from_response(response_text):
    """Extract JSON data from a response that might contain markdown and explanations"""
    # Look for json block in markdown
    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except:
            pass
    
    # Try to find JSON object directly
    json_match = re.search(r'({[\s\S]*?})', response_text)
    if json_match:
        json_str = json_match.group(1).strip()
        try:
            return json.loads(json_str)
        except:
            pass
    
    # Last resort - try to parse the entire response as JSON
    try:
        return json.loads(response_text.strip())
    except:
        return None

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
            keywords = ["login", "sign in", "signin", "log in", "log on", "sign up", "signup", "register", "registration", "create.*account", "open an account", "get free.*now", "join now", "new user", "my account", "come in", "become a member", "customer centre", "登入","登錄", "登録", "注册", "Anmeldung", "iniciar sesión", "identifier", "ログインする", "サインアップ", "ログイン", "로그인", "가입하기", "시작하기", "регистрация", "войти", "вход", "accedered", "gabung", "daftar", "masuk", "girişi", "Giriş", "สมัครสม", "وارد", "regístrate", "acceso", "acessar", "entrar", "ingresa","new account", "join us", "new", "enter password", "access your account", "create account", "登陆"]
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

    def analyze_html_pipeline(self, html_path, base_url=None, screenshot_path=None, using_dead_url=True):
        """
        Main analysis pipeline: analyzes HTML + (optional) redirected CRP page.
        :param html_path: Path to original HTML file
        :param base_url: For resolving relative redirect links
        :return: vector1, vector2
        """
        print("\n===========================================")
        print("ANALYSIS PIPELINE STARTED")
        print(f"Analyzing HTML: {html_path}")
        print(f"Base URL: {base_url}")
        print("===========================================\n")
        
        with open(log_file_path, 'w') as f:
            f.write(f"=== New Run Started at {datetime.now()} ===\n")
        html = load_html_file(html_path)

        print("[STEP 1] Analyze original HTML...")
        gpt_result_1 = analyze_html_with_openai(html)
        vector_1 = convert_to_vector(gpt_result_1)
        vector_2 = None
        print("Vector 1:", vector_1)
        print(f"STEP 1 SUMMARY:")
        
        # Check if gpt_result_1 is None before accessing it
        if gpt_result_1 is None:
            print(f"  - ERROR: GPT-4 analysis failed. Using default values.")
            print(f"  - Has login form: False")
            print(f"  - Form action suspicious: False")
            print(f"  - Obfuscated script: False")
            print(f"  - Suspicious text: False")
            print(f"  - Mentioned brand: Unknown")
            print(f"  - is_domain_match: True")
        else:
            print(f"  - Has login form: {gpt_result_1.get('has_login_form', False)}")
            print(f"  - Form action suspicious: {gpt_result_1.get('form_action_suspicious', False)}")
            print(f"  - Obfuscated script: {gpt_result_1.get('uses_obfuscated_script', False)}")
            print(f"  - Suspicious text: {gpt_result_1.get('suspicious_text_patterns', False)}")
            print(f"  - Mentioned brand: {gpt_result_1.get('mentioned_brand', 'Unknown')}")
            print(f"  - is_domain_match: {gpt_result_1.get('is_domain_match', True)}")
        print("-------------------------------------------")

        print("\n[STEP 2] Checking for Credential Revealing Page (CRP)...")
        is_crp, redirect_url = static_crp_locator(html, base_url=base_url)

        if is_crp:
            print("  Static analysis result: Found CRP in original page")
        else:
            print("  Static analysis result: Not a CRP page")


        if not using_dead_url: #real world alive websites
            print("  Using real world alive websites for redirect analysis, do some dynamic analysis")

            if redirect_url:
                print(f"  Static analysis found redirect URL: {redirect_url}")
                print("\n[STEP 2.1] Following static redirect URL...")
            
                try:
                    # Create paths for new files from static redirect
                    print("  Setting up paths for static redirect analysis...")
                    new_html_path = screenshot_path.replace("shot.png", "new_html.txt")
                    new_info_path = screenshot_path.replace("shot.png", "new_info.txt")
                    new_screenshot_path = screenshot_path.replace("shot.png", "new_shot.png")
                    
                    print("  Setting up driver to follow redirect...")
                    driver = setup_driver()
                    print(f"  Visiting redirect URL: {redirect_url}")
                    driver.get(redirect_url)
                    
                    # Wait for page to load
                    import time
                    time.sleep(3)
                    
                    # Save the HTML
                    print("  Saving HTML from redirected page...")
                    with open(new_html_path, 'w', encoding='utf-8') as f:
                        f.write(driver.page_source)
                        
                    # Save screenshot
                    print("  Taking screenshot of redirected page...")
                    driver.save_screenshot(new_screenshot_path)
                    
                    # Save current URL
                    with open(new_info_path, 'w', encoding='utf-8') as f:
                        f.write(driver.current_url)
                        
                    redirected_html = driver.page_source
                    redirect_url = driver.current_url
                    
                    print(f"[STEP 3] Analyzing static redirect page: {redirect_url}")
                    gpt_result_2 = analyze_html_with_openai(redirected_html)
                    vector_2 = convert_to_vector(gpt_result_2)
                    print("Vector 2:", vector_2)
                    print(f"STEP 3 SUMMARY:")
                    
                    # Check if gpt_result_2 is None before accessing it
                    if gpt_result_2 is None:
                        print(f"  - ERROR: GPT-4 analysis failed for redirected page. Using default values.")
                        print(f"  - Has login form: False")
                        print(f"  - Form action suspicious: False")
                        print(f"  - Obfuscated script: False")
                        print(f"  - Suspicious text: False")
                        print(f"  - Mentioned brand: Unknown")
                        print(f"  - is_domain_match: True")
                    else:
                        print(f"  - Has login form: {gpt_result_2.get('has_login_form', False)}")
                        print(f"  - Form action suspicious: {gpt_result_2.get('form_action_suspicious', False)}")
                        print(f"  - Obfuscated script: {gpt_result_2.get('uses_obfuscated_script', False)}")
                        print(f"  - Suspicious text: {gpt_result_2.get('suspicious_text_patterns', False)}")
                        print(f"  - Mentioned brand: {gpt_result_2.get('mentioned_brand', 'Unknown')}")
                        print(f"  - is_domain_match: {gpt_result_2.get('is_domain_match', True)}")
                        
                    # Clean up
                    driver.quit()
                
                except Exception as e:
                    print(f"\n[ERROR] Failed to follow static redirect: {e}")
                    print("  Will try dynamic analysis instead...")
                    redirect_url = None  # Reset to trigger dynamic analysis
        
             # If no redirect URL found by static analysis, try dynamic analysis
            else: # if not redirect_url:
                print("  Static analysis did not find redirect URL or failed to follow it")
                print("\n[STEP 2.2] Trying dynamic analysis with crp_locator()...")

                try:
                    print("  Setting up driver...")
                    driver = setup_driver()
                    print("  Visiting original URL...")
                    visit_success, driver = visit_url(driver, base_url)

                    if not visit_success:
                        print("[ERROR] Failed to revisit original URL")
                        print("  Vector 2 will remain None")
                        driver.quit()
                        return vector_1, vector_2

                    print("  Getting page text...")
                    page_text = get_page_text(driver).split("\n")

                    print("  Setting up paths for dynamic analysis...")
                    new_html_path = screenshot_path.replace("shot.png", "new_html.txt")
                    new_info_path = screenshot_path.replace("shot.png", "new_info.txt")
                    new_screenshot_path = screenshot_path.replace("shot.png", "new_shot.png")

                    print("  Running keyword_heuristic (this may take a moment)...")
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

                    redirect_url = driver.current_url
                    print(f"  Current URL after dynamic analysis: {redirect_url}")
                    print(f"  Heuristic score: {reached}")

                    if reached:
                        print("  [STEP 2.3] Dynamic analysis detected a CRP")
                        print(f"  Checking for new HTML file: {new_html_path}")
                        
                        # Check if the file exists before trying to read it
                        if os.path.exists(new_html_path):
                            print(f"  Reading HTML from redirected page: {new_html_path}")
                            with open(new_html_path, 'r', encoding='utf-8') as f:
                                redirected_html = f.read()

                            print(f"[STEP 3] Analyzing dynamically found CRP page: {redirect_url}")
                            gpt_result_2 = analyze_html_with_openai(redirected_html)
                            vector_2 = convert_to_vector(gpt_result_2)
                            print("Vector 2:", vector_2)
                            print(f"STEP 3 SUMMARY:")
                            
                            # Check if gpt_result_2 is None before accessing it
                            if gpt_result_2 is None:
                                print(f"  - ERROR: GPT-4 analysis failed for redirected page. Using default values.")
                                print(f"  - Has login form: False")
                                print(f"  - Form action suspicious: False")
                                print(f"  - Obfuscated script: False")
                                print(f"  - Suspicious text: False")
                                print(f"  - Mentioned brand: Unknown")
                                print(f"  - is_domain_match: True")
                            else:
                                print(f"  - Has login form: {gpt_result_2.get('has_login_form', False)}")
                                print(f"  - Form action suspicious: {gpt_result_2.get('form_action_suspicious', False)}")
                                print(f"  - Obfuscated script: {gpt_result_2.get('uses_obfuscated_script', False)}")
                                print(f"  - Suspicious text: {gpt_result_2.get('suspicious_text_patterns', False)}")
                                print(f"  - Mentioned brand: {gpt_result_2.get('mentioned_brand', 'Unknown')}")
                                print(f"  - is_domain_match: {gpt_result_2.get('is_domain_match', True)}")
                        else:
                            print(f"  WARNING: New HTML file not found even though CRP was detected.")
                            print(f"  Creating files manually from current browser state...")
                            
                            # Create files manually from current browser state
                            try:
                                # Save HTML
                                with open(new_html_path, 'w', encoding='utf-8') as f:
                                    f.write(driver.page_source)
                                
                                # Save screenshot
                                driver.save_screenshot(new_screenshot_path)
                                
                                # Save URL
                                with open(new_info_path, 'w', encoding='utf-8') as f:
                                    f.write(driver.current_url)
                                    
                                print(f"  Successfully created files manually.")
                                
                                # Now analyze the HTML
                                redirected_html = driver.page_source
                                print(f"[STEP 3] Analyzing current browser page: {redirect_url}")
                                gpt_result_2 = analyze_html_with_openai(redirected_html)
                                vector_2 = convert_to_vector(gpt_result_2)
                                print("Vector 2:", vector_2)
                                print(f"STEP 3 SUMMARY:")
                                
                                # Check if gpt_result_2 is None before accessing it
                                if gpt_result_2 is None:
                                    print(f"  - ERROR: GPT-4 analysis failed for redirected page. Using default values.")
                                    print(f"  - Has login form: False")
                                    print(f"  - Form action suspicious: False")
                                    print(f"  - Obfuscated script: False")
                                    print(f"  - Suspicious text: False")
                                    print(f"  - Mentioned brand: Unknown")
                                    print(f"  - is_domain_match: True")
                                else:
                                    print(f"  - Has login form: {gpt_result_2.get('has_login_form', False)}")
                                    print(f"  - Form action suspicious: {gpt_result_2.get('form_action_suspicious', False)}")
                                    print(f"  - Obfuscated script: {gpt_result_2.get('uses_obfuscated_script', False)}")
                                    print(f"  - Suspicious text: {gpt_result_2.get('suspicious_text_patterns', False)}")
                                    print(f"  - Mentioned brand: {gpt_result_2.get('mentioned_brand', 'Unknown')}")
                                    print(f"  - is_domain_match: {gpt_result_2.get('is_domain_match', True)}")
                            except Exception as e:
                                print(f"  ERROR creating files manually: {e}")
                                print("  Vector 2 will remain None")

                    else:
                        print("\n[STEP 3] Dynamic analysis did not reach CRP")
                        print("  Vector 2 will remain None")
                        print("  vector2 is: ", vector_2)

                    # Clean up
                    driver.quit()

                except Exception as e:
                    print(f"\n[ERROR] Dynamic analysis failed: {e}")
                    print("  Vector 2 will remain None")
        else: #dead url
            print("  Using dead URLs for redirect analysis, do some dynamic analysis")
            print("\n[STEP 3] This is a dead URL, will not follow redirect since it may not exist.")
            print("Will add 0.2 to the score of vector 2 score ")


        print("\n[STEP 4] Computing final text score...")
        if vector_2 is None:
            if not using_dead_url:
                print("  No Vector 2 found. Using zeros for calculation.")
                vector_2 = [0] * len(vector_1)
                print("  Initialized Vector 2:", vector_2)
                text_score = compute_text_score(vector_1, vector_2)
                print("  [FINAL TEXT SCORE]:", text_score)

            else:
                print("  This is deal url, for fairness, add 0.2 to the entire score")
                vector_2 = [0] * len(vector_1)
                text_score = compute_text_score(vector_1, vector_2)+0.2
                print("  [FINAL TEXT SCORE]:", text_score)
        else:
            print("  Vector 2 found. Computing text score...")
            text_score = compute_text_score(vector_1, vector_2)
            print("  [FINAL TEXT SCORE]:", text_score)

        print("\n[STEP 5] Building final text vector...")
        text_vector = vector_1 + vector_2
        text_vector.append(text_score)
        print("  Final text vector (Vector1 + Vector2 + Score):", text_vector)
        if text_score > 0.5:
            verdict = "Phishing"
        else:
            verdict = "Benign"

        print(f"\n[FINAL VERDICT]: {verdict}")
        print("  [VECTOR 1]:", vector_1)
        print("  [VECTOR 2]:", vector_2)
        print("  [SCORE]:", text_score)
        print("  [FINAL TEXT VECTOR]:", text_vector)
        print("\n===========================================")
        print("ANALYSIS PIPELINE COMPLETED")
        print("===========================================\n")
        

        return text_vector, verdict
        


# Open AI API key: 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

def analyze_html_with_openai(html_content, model="gpt-4"):
    """
    Sends HTML content to GPT-4 and receives structured JSON analysis.
    """
    max_chars = 4000  # Stay under token limit
    html_chunk = html_content[:max_chars]

    system_prompt = "You are a phishing detection expert. Please read the given HTML file of this website and extract phishing-related features in JSON format."

    user_prompt = f"""
    You are a phishing detection expert. Based on the following HTML, return a JSON object with these fields:

    - "has_login_form": true/false 
    - "form_action_suspicious": true/false (does the form submit credentials to an unrelated or suspicious domain?)
    - "uses_obfuscated_script": true/false (does the page contain suspicious encoded JavaScript or delay-loaded content?)
    - "suspicious_text_patterns": true/false (such as urgency, misleading instructions, or brand inconsistency)
    - "mentioned_brand": string (e.g., 'PayPal', 'Apple', or 'Unknown')
    - "is_domain_match": true/false (does the page's URL domain match the official domain of the brand mentioned in the content? Only evaluate if a specific brand is detected, otherwise return true)
    Rules:
    - Consider the structure and logic of forms (e.g., where they submit to).
    - Inspect script tags and look for obfuscation or delay-based phishing injection.
    - Flag suspicious language like "your account will be locked", "verify immediately", or branding conflicts.
    - When evaluating "is_domain_match":- Extract the actual domain from any brand mentions in the HTML - Compare it to known official domains (e.g., paypal.com for PayPal, apple.com for Apple)- Look for typosquatting (e.g., paypa1.com, app1e.com)- Check for subdomains that obscure the actual domain (e.g., paypal.secure-verification.com) - you should consider: true/false (Does the URL domain EXACTLY match the brand's primary official domain? For banks and financial institutions, be especially strict - verify that the domain is the primary official domain, not a regional subdomain. For Sparkasse, the official domain is "sparkasse.de", and regional variants like "s-jena.de" should be considered non-matching unless explicitly verifying a local branch.)

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

        result = extract_json_from_response(reply)
        print(reply)

        # result = json.loads(reply)
        if result is None:
            print("[ERROR] Could not extract valid JSON from GPT response")
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
        int(not gpt_result.get("is_domain_match", True))
        # This will return 1 when domains DON'T match (high risk)
        # and 0 when domains DO match (low risk)
    ]


# def load_html_file(path):
#     with open(path, 'r', encoding='utf-8') as f:
#         return f.read()
def load_html_file(path):
    """
    Load HTML file with fallback encodings for international character support
    """
    encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    for encoding in encodings_to_try:
        try:
            with open(path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            continue
    
    # If all encodings fail, try binary mode and decode with errors='replace'
    with open(path, 'rb') as f:
        binary_content = f.read()
    return binary_content.decode('utf-8', errors='replace')


def compute_text_score(vector_1, vector_2=None):
    """
    Compute phishing-related text score from GPT output vectors.

    :param vector_1: List of binary features from original HTML
    :param vector_2: List of binary features from redirected HTML (optional)
    :return: float score between 0.0 - 1.0
    """
    def score_vector(v):
        if not v:
            return 0.0

        weights = [0.25, 0.45, 0.3, 0.9, 0.1, 0.4]

        total_weight = sum(weights)
        weighted_sum = sum(w * x for w, x in zip(weights, v)) / total_weight

        # weighted_sum = sum(w * x for w, x in zip(weights, v))
        return weighted_sum

    score1 = score_vector(vector_1)
    score2 = score_vector(vector_2) if vector_2 else 0.0

    # If both exist, average with more weight on CRP (redirected)
    if vector_2 and vector_2 != [0, 0, 0, 0, 0, 0]:
        final_score = (0.2 * score1 + 0.8 * score2)
    else:
        final_score = score1

    return round(final_score, 3)