from HTML_Analyzer import (
    load_html_file,
    analyze_html_with_openai,
    convert_to_vector,
)
from Web_Crawling import crawl_url,sanitize_url
from crp_locator import keyword_heuristic, crp_locator
import os
import json

from modules.crp_classifier import html_heuristic

if __name__ == "__main__":
    url = input("Please enter the URL you want to test：\n> ").strip()

    html_path, screenshot = crawl_url(url)

    if not html_path:
        print("[ERROR] HTML file not found")
        exit()


    html = load_html_file(html_path)
    gpt_result = analyze_html_with_openai(html)
    cre_pred = html_heuristic(html_path)
    if cre_pred == 1:
        

    if not gpt_result:
        print("[ERROR] Cannot get result from GPT-4")
        exit()


    text_vector = convert_to_vector(gpt_result)
    print("\n[GPT-4 JSON OUTPUT]")
    print(json.dumps(gpt_result, indent=2))
    print("\n[Text Feature Vector]", text_vector)
