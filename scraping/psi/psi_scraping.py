import os
import requests
import logging
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import pandas as pd

from scraping.eps_scraping_pdf import extract_clean_eps_v6
from scraping.utils.Utils import parse_vietnamese_date

BASE_URL = "https://www.psi.vn/vi/trung-tam-phan-tich/bao-cao-phan-tich-doanh-nghiep?page="
# DATE_RANGE = "&fromdate=01%2F01%2F2019&todate=31%2F12%2F2023"
# PAGE_PARAM = "&post_page="

def scraping_psi_all(download_dir="downloads", valid_codes=None, max_pages=20, start_page=1, output_dir="output/eps_rep_psi.csv", blacklist_code=None):
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for page_num in range(start_page, max_pages + 1):
            url = f"{BASE_URL}{page_num}"
            logging.info(f"Loading page {page_num}: {url}")
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")

            report_items = page.query_selector_all("div.row.article-cell.article-cell--lg.pl-0")
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
                    head_card_tag = report_item.query_selector("div.date-tag.date-tag--sm")
                    sec_code_tag = None
                    date = head_card_tag.query_selector("div.date-tag__date").text_content().strip()
                    month_year = head_card_tag.query_selector("div.date-tag__month-year").text_content().strip()
                    
                    if sec_code_tag:
                        sec_code = sec_code_tag.text_content().strip().upper()
                        is_sec_code_tagged = True
                    else:
                        logging.warning(f"Could not find sec_code for report {idx} on page {page_num}, fallback to sec code tickets.")

                    if not date and not month_year:
                        logging.warning(f"Could not find report date for report {idx} on page {page_num}, skipping.")
                        continue
                    
                    report_date = date + "/" + month_year
                    logging.info(f"[Page {page_num} - Report {idx}] {sec_code} ({report_date})")
                
                except Exception as e:
                    logging.error(f"Error detecting sec_code or date for report {idx} on page {page_num}: {e}")
                    continue

                # Get pdf link and download
                local_path = None
                try:
                    pdf_link_tag = report_item.query_selector("div.d-flex.flex-column.align-items-center > a")
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
                    eps_results = extract_clean_eps_v6(local_path, report_date, valid_codes=valid_codes, blacklist_codes=blacklist_code, firm="BSC", url=pdf_url, already_detected_sc=sec_code)
                    logging.info(f"Extracted {len(eps_results)} EPS entries from {local_path}")
                    logging.info(f"EPS Results: {eps_results}")
                    if not eps_results:
                        logging.info(f"No EPS data extracted from {local_path}")
                        continue
                    
                    result_df = pd.DataFrame(eps_results)
                    result_df["sc_tag"] = is_sec_code_tagged
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
                
        browser.close()
