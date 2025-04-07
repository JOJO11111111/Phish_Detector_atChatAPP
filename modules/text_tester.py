from modules.HTML_Analyzer_tiff_locsl import (
    load_html_file,
    analyze_html_with_openai,
    convert_to_vector,
)
from modules.Web_Crawling_tiff_local import crawl_url,sanitize_url
from crp_locator import keyword_heuristic, crp_locator
import os
import json

from modules.HTML_Analyzer_tiff_locsl import HTML_Analyzer
from modules.crp_classifier import html_heuristic
from helium import set_driver
from modules.Web_Crawling_tiff_local import setup_driver

driver = setup_driver()
set_driver(driver)


if __name__ == "__main__":
    import sys
    sys.stdout.write("Please enter the URL you want to test:\n> ")
    sys.stdout.flush()
    url = input().strip()

    html_path, screenshot = crawl_url(url)

    if not html_path:
        print("[ERROR] HTML file not found")
        exit()
    # html = load_html_file(html_path)
    analyzer = HTML_Analyzer()
    analyzer.analyze_html_pipeline(html_path, base_url=url, screenshot_path=screenshot)


