import os
import re
import requests
import logging
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import pandas as pd

from scraping.eps_scraping_pdf import extract_clean_eps_v6
from scraping.utils.Utils import parse_vietnamese_date, extract_report_date

ROOT_URL = "https://www.yuanta.com.vn"
BASE_URL = "https://yuanta.com.vn/analysis-category/phan-tich-doanh-nghiep/page/"
DATE_RANGE = ""
PAGE_PARAM = ""
        
def scraping_ysvn_all(download_dir="downloads", valid_codes=None, max_pages=20, start_page=1, output_dir="output/eps_rep_ysvn.csv", blacklist_code=None, firm="SSV"):
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(BASE_URL + "1", timeout=60000)
        page.wait_for_load_state("networkidle")

        for page_num in range(start_page, max_pages + 1):
            url = f"{BASE_URL}{page_num}"
            logging.info(f"Loading page {page_num}: {url}")
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            report_items = page.query_selector_all("article.phan-tich")
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
                    sec_code_tag = report_item.query_selector("a.title")
                    report_date_tag = report_item.query_selector("div.meta-item.date")
                    logging.info(f"Report item {idx} on page {page_num} - sec_code_tag: {sec_code_tag}, report_date_tag: {report_date_tag}")

                    if sec_code_tag:
                        sec_code = sec_code_tag.text_content().strip()[:3].upper()
                        is_sec_code_tagged = True
                    else:
                        logging.warning(f"Could not find sec_code for report {idx} on page {page_num}, fallback to sec code tickets.")

                    if not report_date_tag:
                        logging.warning(f"Could not find report date for report {idx} on page {page_num}, skipping.")
                        continue
                    
                    report_date = extract_report_date(report_date_tag.text_content().strip())
                    logging.info(f"[Page {page_num} - Report {idx}] {sec_code} ({report_date})")
                    
                except Exception as e:
                    logging.error(f"Error detecting sec_code or date for report {idx} on page {page_num}: {e}")
                    continue
                
                # Get pdf link and download
                local_path = None
                new_page = None
                try:
                    new_page = browser.new_page()
                    content = report_item.query_selector("a.title")
                    new_page.goto(content.get_attribute("href"), timeout=60000)
                    new_page.wait_for_load_state("networkidle")
                    
                    pdf_link_tag = new_page.query_selector("a[href$='.pdf']")
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
                #     with requests.get(pdf_url, stream=True, allow_redirects=True) as r:
                #         r.raise_for_status()

                #         # Try to get filename from Content-Disposition header
                #         cd = r.headers.get("content-disposition")
                #         if cd:
                #             fname_match = re.findall('filename="?([^"]+)"?', cd)
                #             if fname_match:
                #                 filename = fname_match[0]
                #             else:
                #                 filename = os.path.basename(pdf_url) + ".pdf"
                #         else:
                #             filename = os.path.basename(pdf_url) + ".pdf"

                #         local_path = os.path.join(download_dir, filename)
                #         logging.info(f"Downloading PDF {pdf_url} -> {local_path}")

                #         with open(local_path, "wb") as f:
                #             for chunk in r.iter_content(8192):
                #                 f.write(chunk)

                except Exception as e:
                    logging.error(f"Error finding PDF link for report {idx} on page {page_num}: {e}")
                    continue
                
                finally:
                    if new_page:
                        new_page.close()
                
                # # Get pdf link and download
                # local_path = None
                # pdf_url = None
                # try:
                #     pdf_link_tag = report_item.query_selector("div.chart__content__item__time > a")
                #     pdf_url = urljoin(BASE_URL, pdf_link_tag.get_attribute("href"))
                #     if not pdf_link_tag:
                #         logging.warning(f"No PDF link in report {idx} on page {page_num}, skipping.")
                #         continue

                #     logging.info(f"Found PDF link for report {idx} on page {page_num}")

                #     # Use Playwright download API
                #     with page.expect_download() as download_info:
                #         pdf_link_tag.click()   # triggers the download
                #     download = download_info.value

                #     # Playwright suggests the real filename (from server headers)
                #     filename = download.suggested_filename
                #     local_path = os.path.join(download_dir, filename)

                #     logging.info(f"Saving PDF -> {local_path}")
                #     download.save_as(local_path)

                # except Exception as e:
                #     logging.error(f"Error downloading PDF for report {idx} on page {page_num}: {e}")
                #     continue
                
                # Extract EPS
                try:
                    eps_results = extract_clean_eps_v6(local_path, report_date, valid_codes=valid_codes, blacklist_codes=blacklist_code, firm=firm, url=pdf_url, already_detected_sc=sec_code)
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
