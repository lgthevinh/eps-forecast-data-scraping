import os
import requests
import logging
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import pandas as pd

from scraping.eps_scraping_pdf import extract_clean_eps_v6
from scraping.utils.Utils import parse_vietnamese_date, extract_report_date, convert_vietnamese_charmonth_int, validate_sec_code

ROOT_URL = "https://ezadvisorselect.fpts.com.vn"
BASE_URL = "https://ezadvisorselect.fpts.com.vn/investmentadvisoryreport"
DATE_RANGE = ""
PAGE_PARAM = ""
        
def scraping_fpts_all(download_dir="downloads", valid_codes=None, max_pages=20, start_page=1, output_dir="output/eps_rep_fpts.csv", blacklist_code=None, firm="FPTS"):
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        time.sleep(40)  # wait for 35 seconds to ensure the page is fully loaded after date range input
        # Click outside to close the date picker
                
        for page_num in range(1, max_pages + 1):
            
            # Handle skip page from 1 to start_page
            if page_num < start_page:
                logging.info(f"Skipping page {page_num} to reach start_page {start_page}")
                next_button = page.query_selector("a.page-link > a.backgroundNext")
                next_button.click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(0.5)  # wait for 0.5 seconds to ensure the next page is loaded
                continue

            # Navigate to the desired page
            page.goto(f"{BASE_URL}?page={page_num}", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            logging.info(f"Loading page {page_num}")
            
            content = page.query_selector("#tableGetReport")
            report_items = content.query_selector_all("#tablePaging > tr")  # Updated selector for FPTS
            if not report_items:
                logging.info(f"No reports found on page {page_num}, stopping.")
                continue
            logging.info(f"Found {len(report_items)} reports on page {page_num}")
            for idx, report_item in enumerate(report_items, start=1):
                sec_code = None
                report_date = None
                is_sec_code_tagged = False
                
                # Detect sec_code
                try:
                    sec_code_tag = report_item.query_selector("td:first-child")  # Assuming the first column contains the sec_code
                    if sec_code_tag:
                        sec_code = sec_code_tag.text_content().strip()
                        is_sec_code_tagged = True
                    else:
                        logging.warning(f"Could not find sec_code for report {idx} on page {page_num}, fallback to sec code tickets.")

                    report_date_tag = report_item.query_selector("td:nth-child(3)")
                    logging.info(report_date_tag)

                    if not report_date_tag:
                        logging.warning(f"Could not find report date for report {idx} on page {page_num}, skipping.")
                        continue

                    report_date = report_date_tag.text_content().strip()
                    # _, _, year = parse_vietnamese_date(report_date)
                    # logging.info(f"Extracted date: {report_date} (year: {year})")
                    # if year < 2019 or year > 2023:
                    #     logging.info(f"Report date {report_date} is before 2019 for report {idx} on page {page_num}, skipping.")
                    #     continue
                    logging.info(f"[Page {page_num} - Report {idx}] {sec_code} ({report_date})")
                    
                except Exception as e:
                    logging.error(f"Error detecting sec_code or date for report {idx} on page {page_num}: {e}")
                    continue             
                    
                # # Get pdf link and download
                local_path = None
                pdf_url = None
                try:
                    content_link_tag = report_item.query_selector("td:nth-child(2) a")  # Assuming the PDF link is in the 2nd column
                    
                    # New tab popup handling
                    with page.expect_popup() as popup_info:
                        content_link_tag.click()
                    new_page = popup_info.value
                    new_page.wait_for_load_state("domcontentloaded")
                    
                    with new_page.expect_navigation() as popup_info2:
                        new_page.click("#DownloadFile")  # Click the download button
                    pdf_page = popup_info2.value
                    pdf_url = pdf_page.url
                    logging.info(f"Found PDF link for report {idx} on page {page_num}: {pdf_url}")
                    filename = os.path.basename(pdf_url)
                    local_path = os.path.join(download_dir, filename) + ".pdf"
                    logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
                    response = requests.get(pdf_url)
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                        
                    new_page.close()
                    logging.info(f"Downloaded PDF {pdf_url} -> {local_path}")
                    
                except Exception as e:
                    logging.error(f"Error downloading PDF for report {idx} on page {page_num}: {e}")
                    continue
            
                # # Extract EPS
                try:
                    eps_results = extract_clean_eps_v6(local_path, report_date, valid_codes=valid_codes, blacklist_codes=blacklist_code, firm=firm, url=pdf_url, already_detected_sc=sec_code)
                    logging.info(f"Extracted {len(eps_results)} EPS entries from {local_path}")
                    logging.info(f"EPS Results: {eps_results}")
                    if not eps_results:
                        logging.info(f"No EPS data extracted from {local_path}")
                        continue
                    
                    result_df = pd.DataFrame(eps_results)
                    result_df["sc_tag"] = is_sec_code_tagged
                    result_df["file_name"] = local_path
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
            next_button = page.query_selector("a.page-link > a.backgroundNext")
            next_button.click()
            page.wait_for_load_state("domcontentloaded")
            time.sleep(3)  # wait for 3 seconds to ensure the next page is loaded

        browser.close()
