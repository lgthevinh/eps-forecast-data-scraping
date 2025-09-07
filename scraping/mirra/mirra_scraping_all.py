import os
import requests
import logging
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import pandas as pd

from scraping.eps_scraping_pdf import extract_clean_eps_v6
from scraping.utils.Utils import parse_vietnamese_date, extract_report_date, convert_vietnamese_charmonth_int, validate_sec_code

ROOT_URL = "https://masvn.com"
BASE_URL = "https://masvn.com/cate/nganh-doanh-nghiep-56"
DATE_RANGE = ""
PAGE_PARAM = ""

def scraping_mirra_all(download_dir="downloads", valid_codes=None, max_pages=20, start_page=1, output_dir="output/eps_rep_mirra.csv", blacklist_code=None, firm="MirraAsset"):
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        for page_num in range(start_page, max_pages + 1):
            page.wait_for_load_state("domcontentloaded")
            logging.info(f"Loading page {page_num}")
            
            content = page.query_selector("div.news__latest")
            report_items = content.query_selector_all("div.news__article.hover-line")  # Updated selector for BVS
            if not report_items:
                logging.info(f"No reports found on page {page_num}, stopping.")
                continue
            logging.info(f"Found {len(report_items)} reports on page {page_num}")
            # time.sleep(5)  # wait for 5 seconds to ensure all items are fully loaded
            for idx, report_item in enumerate(report_items, start=1):
                sec_code = None
                report_date = None
                is_sec_code_tagged = False
                
                # Detect sec_code
                try:
                    sec_code_tag = None
                    report_date_tag = report_item.query_selector("span")
                    
                    if sec_code_tag:
                        sec_code = sec_code_tag.text_content().strip()[:3] # Get first 3 characters as sec_code
                        is_sec_code_tagged = True
                    else:
                        logging.warning(f"Could not find sec_code for report {idx} on page {page_num}, fallback to sec code tickets.")

                    if not report_date_tag:
                        logging.warning(f"Could not find report date for report {idx} on page {page_num}, skipping.")
                        continue

                    report_date = report_date_tag.text_content().strip().replace(" Thg ", "/").replace(" ", "/")
                    _, _, year = parse_vietnamese_date(report_date)
                    # if year > 2023 or year < 2018:
                    #     logging.warning(f"Report date '{report_date}' for report {idx} on page {page_num} is out of range, skipping.")
                    #     continue
                    logging.info(f"[Page {page_num} - Report {idx}] {sec_code} ({report_date})")
                    
                except Exception as e:
                    logging.error(f"Error detecting sec_code or date for report {idx} on page {page_num}: {e}")
                    continue               
                    
                # # Get pdf link and download
                # local_path = None
                # pdf_url = None
                # try:
                #     pdf_link_tag = report_item.query_selector("text.fileAttach_name")
                #     pdf_url = urljoin(BASE_URL, "/" + str(page_num))
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
                #     local_path = os.path.join(download_dir, filename) + ".pdf"

                #     logging.info(f"Saving PDF -> {local_path}")
                #     download.save_as(local_path)

                # except Exception as e:
                #     logging.error(f"Error downloading PDF for report {idx} on page {page_num}: {e}")
                #     continue
                
                                # Get pdf link and download
                local_path = None
                try:
                    pdf_link_tag = report_item.query_selector("a")
                    if not pdf_link_tag:
                        logging.warning(f"No PDF link in report {idx} on page {page_num}, skipping.")
                        continue
                    logging.info(f"Found PDF link for report {idx} on page {page_num}")
                    
                    pdf_url = urljoin(BASE_URL, pdf_link_tag.get_attribute("href"))
                    filename = os.path.basename(pdf_url)
                    local_path = os.path.join(download_dir, filename)
                    logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
                    response = requests.get(pdf_url)
                    with open(local_path, "wb") as f:
                        f.write(response.content)

                except Exception as e:
                    logging.error(f"Error finding PDF link for report {idx} on page {page_num}: {e}")
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
                
            # page.wait_for_load_state("domcontentloaded")
            # next_button = page.query_selector("button.btn.btn-outline-primary.btnNext")
            # next_button.click()
            # page.wait_for_load_state("domcontentloaded")
            # time.sleep(3)  # wait for 3 seconds to ensure the next page is loaded
            
            # Delete old div to prevent accumulation
            page.evaluate("""
                () => {
                    const container = document.querySelector("div.news__latest");
                    if (container) container.innerHTML = "";
                }
            """)
            page.click("a.mgt--60.btn.btn--more.learn-more")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1)  # wait for 3 seconds to ensure the next page is loaded

        browser.close()
