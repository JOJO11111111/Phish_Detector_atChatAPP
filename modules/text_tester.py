from HTML_Analyzer import (
    load_html_file,
    analyze_html_with_openai,
    convert_to_vector,
)
from Web_Crawling import crawl_url,sanitize_url
from crp_locator import keyword_heuristic, crp_locator
import os
import json

from modules.HTML_Analyzer import analyze_html_pipeline
from modules.crp_classifier import html_heuristic

if __name__ == "__main__":
    url = input("Please enter the URL you want to test：\n> ").strip()

    html_path, screenshot = crawl_url(url)

    if not html_path:
        print("[ERROR] HTML file not found")
        exit()


    # html = load_html_file(html_path)
    analyze_html_pipeline(html_path, base_url=url)


