import os
import requests
import logging
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import pandas as pd

from scraping.eps_scraping_pdf import extract_clean_eps_v6
from scraping.utils.Utils import parse_vietnamese_date, extract_report_date

ROOT_URL = "https://shinhansec.com.vn"
BASE_URL = "https://shinhansec.com.vn/vi/trung-tam-nghien-cuu/bao-cao-doanh-nghiep.html"
DATE_RANGE = ""
PAGE_PARAM = ""
        
def scraping_ssv_all(download_dir="downloads", valid_codes=None, max_pages=20, start_page=1, output_dir="output/eps_rep_ssv.csv", blacklist_code=None, firm="SSV"):
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        time.sleep(20)  # wait for 20 seconds to ensure the page is fully loaded after date range input
        # Click outside to close the date picker
                
        for page_num in range(start_page, max_pages + 1):
            page.wait_for_load_state("domcontentloaded")
            logging.info(f"Loading page {page_num}")
            
            tbody = page.query_selector("table > tbody")
            report_items = tbody.query_selector_all("tr")  # Updated selector for SSV
            if not report_items:
                logging.info(f"No reports found on page {page_num}, stopping.")
                continue
            logging.info(f"Found {len(report_items)} reports on page {page_num}")
            for idx, report_item in enumerate(report_items, start=1):
                row = report_item.query_selector_all("td")
                sec_code = row[1].text_content().strip().upper()[:3]  # Assuming the sec_code is in the second column
                report_date = row[0].text_content().strip().replace("(", "").replace(")", "")
                
                logging.info(f"[Page {page_num} - Report {idx}] {sec_code} ({report_date})")

                # Get pdf link and download
                local_path = None
                try:
                    pdf_link_tag = row[-1].query_selector("li > a")
                    if not pdf_link_tag:
                        logging.warning(f"No PDF link in report {idx} on page {page_num}, skipping.")
                        continue
                    logging.info(f"Found PDF link for report {idx} on page {page_num}")
                    
                    pdf_url = urljoin(BASE_URL, pdf_link_tag.get_attribute("href"))
                    filename = os.path.basename(pdf_url)
                    local_path = os.path.join(download_dir, filename) + ".pdf"
                    logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
                    response = requests.get(pdf_url)
                    with open(local_path, "wb") as f:
                        f.write(response.content)

                except Exception as e:
                    logging.error(f"Error finding PDF link for report {idx} on page {page_num}: {e}")
                    continue
            
                # Extract EPS
                try:
                    eps_results = extract_clean_eps_v6(local_path, report_date, valid_codes=valid_codes, blacklist_codes=blacklist_code, firm=firm, url=pdf_url, already_detected_sc=sec_code)
                    logging.info(f"Extracted {len(eps_results)} EPS entries from {local_path}")
                    logging.info(f"EPS Results: {eps_results}")
                    if not eps_results:
                        logging.info(f"No EPS data extracted from {local_path}")
                        continue
                    
                    result_df = pd.DataFrame(eps_results)
                    os.makedirs("output", exist_ok=True)
                    if not os.path.exists(output_dir):
                        result_df.to_csv(output_dir, index=False)
                        logging.info(f"Results saved to {output_dir}")
                    else:
                        result_df.to_csv(output_dir, mode="a", header=False, index=False)
                        logging.info(f"Results appended to {output_dir}")

                except Exception as e:
                    logging.error(f"Error processing report {idx} on page {page_num}: {e}")
                    continue
                
            page.wait_for_load_state("domcontentloaded")
            next_button = page.query_selector("li.page-item.next")
            next_button.click()
                
        browser.close()
