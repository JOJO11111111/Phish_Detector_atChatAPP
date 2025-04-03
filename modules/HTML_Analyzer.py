from openai import OpenAI
import json
import os
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "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"))
from crp_locator import keyword_heuristic



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
        return [0]*12

    return [
        int(gpt_result.get("has_login_form", False)),
        int(gpt_result.get("form_action_suspicious", False)),
        int(gpt_result.get("uses_obfuscated_script", False)),
        int(gpt_result.get("suspicious_text_patterns", False)),
        0 if gpt_result.get("mentioned_brand", "").lower() == "unknown" else 1,
        float(gpt_result.get("phishing_score", 0.0)),
        int(gpt_result.get("potentail_page_has_login_form", False)),
        int(gpt_result.get("potentail_page_form_action_suspicious", False)),
        int(gpt_result.get("potentail_page_uses_obfuscated_script", False)),
        int(gpt_result.get("potentail_page_suspicious_text_patterns", False)),
        0 if gpt_result.get("potentail_page_mentioned_brand", "").lower() == "unknown" else 1,
        float(gpt_result.get("potentail_page_phishing_score", 0.0))
    ]


def load_html_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
