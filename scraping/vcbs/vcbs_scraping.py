import os
import re
import requests
import logging
import time
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import pandas as pd
from PyPDF2 import PdfReader

from scraping.eps_scraping_pdf import extract_clean_eps_v6
from scraping.utils.Utils import parse_vietnamese_date, extract_report_date

ROOT_URL = "https://www.vcbs.com.vn"
BASE_URL = "https://www.vcbs.com.vn/trung-tam-phan-tich/bao-cao-chi-tiet?code=BCDN&page="
DATE_RANGE = ""
PAGE_PARAM = ""
        
def scraping_vcbs_all(download_dir="downloads", valid_codes=None, max_pages=20, start_page=1, output_dir="output/eps_rep_vcbs.csv", blacklist_code=None, firm="SSV"):
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        page.goto(BASE_URL, timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(5)  # wait for JS to load content

        for page_num in range(1, max_pages + 1):
            # Handle skip page from 1 to start_page
            if page_num < start_page:
                logging.info(f"Skipping page {page_num} to reach start_page {start_page}")
                next_button = page.query_selector("a.link-page.link-next")
                next_button.click()
                page.wait_for_load_state("domcontentloaded")
                time.sleep(0.5)  # wait for 0.5 seconds to ensure the next page is loaded
                continue
            
            logging.info(f"Loading page {page_num}")

            report_items = page.query_selector_all("div.t-acReportList_list > div.t-acReportList_list-item")
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
                    sec_code_tag = report_item.query_selector("div.o-simpleReportCard_title > h3")
                    logging.info(f"Report {idx} title: {sec_code_tag.text_content().strip() if sec_code_tag else 'N/A'}")

                    if sec_code_tag:
                        sec_code = sec_code_tag.text_content().strip()[:3].upper()
                        is_sec_code_tagged = True
                    else:
                        logging.warning(f"Could not find sec_code for report {idx} on page {page_num}, fallback to sec code tickets.")

                    logging.info(f"[Page {page_num} - Report {idx}] {sec_code} ({report_date})")
                    
                except Exception as e:
                    logging.error(f"Error detecting sec_code or date for report {idx} on page {page_num}: {e}")
                    continue
                
                # Get pdf link and download and get report date from pdf property create at attribute
                local_path = None
                report_date = None
                try:
                    pdf_page = report_item.query_selector("div.o-simpleReportCard_icon")
                    
                    with page.expect_popup() as popup_info:
                        pdf_page.click()
                    
                    popup_info.value.wait_for_load_state("networkidle")
                    time.sleep(0.4)  # wait for JS to load content
                    
                    pdf_url = popup_info.value.url
                    logging.info(f"Popup opened with PDF URL: {pdf_url}")

                    filename = os.path.basename(f"{sec_code}_page{page_num}") + ".pdf"
                    local_path = os.path.join(download_dir, filename)
                    logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
                    response = requests.get(pdf_url)
                    with open(local_path, "wb") as f:
                        f.write(response.content)
                        
                    pdf = PdfReader(local_path)
                    report_date = pdf.metadata.creation_date
                    
                    # Convert to dd/mm/yyyy format, report date is a datetime object
                    if report_date:
                        report_date = report_date.strftime("%d/%m/%Y")
                    
                    logging.info(f"Extracted report date from PDF metadata: {report_date}")
                        
                    # with requests.get(pdf_url, stream=True, allow_redirects=True) as r:
                    #     r.raise_for_status()
                    #     # Try to get filename from Content-Disposition header
                    #     cd = r.headers.get("content-disposition")
                    #     if cd:
                    #         fname_match = re.findall('filename="?([^"]+)"?', cd)
                    #         if fname_match:
                    #             filename = fname_match[0]
                    #         else:
                    #             filename = os.path.basename(pdf_url) + ".pdf"
                    #     else:
                    #         filename = os.path.basename(pdf_url) + ".pdf"

                    #     local_path = os.path.join(download_dir, filename)
                    #     logging.info(f"Downloading PDF {pdf_url} -> {local_path}")

                    #     with open(local_path, "wb") as f:
                    #         for chunk in r.iter_content(8192):
                    #             f.write(chunk)
                    popup_info.value.close()
                except Exception as e:
                    logging.error(f"Error finding PDF link for report {idx} on page {page_num}: {e}")
                    continue
                finally:
                    try:
                        popup_info.value.close()
                    except:
                        pass
                
                # Get pdf link and download
                # local_path = None
                # pdf_url = None
                # try:
                #     pdf_link_tag = report_item
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
                
                # Get pdf link and download
                # local_path = None
                # pdf_link_tag = report_item
                # try:
                #     # Step 1: Catch popup
                #     with page.expect_popup() as popup_info:
                #         pdf_link_tag.click()
                #     popup = popup_info.value
                #     popup.wait_for_load_state("networkidle")

                #     # Step 2: Get PDF URL
                #     pdf_url = popup.url
                #     logging.info(f"Popup opened with PDF URL: {pdf_url}")

                #     # Step 3: Extract filename and set local path
                #     filename = os.path.basename(pdf_url.split("?")[0])  # strip query params
                #     local_path = os.path.join(download_dir, filename)

                #     # Step 4: Download using requests with cookies (to handle auth)
                #     cookies = page.context.cookies()
                #     session = requests.Session()
                #     for c in cookies:
                #         session.cookies.set(c["name"], c["value"], domain=c["domain"])

                #     response = session.get(pdf_url, stream=True)
                #     response.raise_for_status()

                #     with open(local_path, "wb") as f:
                #         for chunk in response.iter_content(8192):
                #             f.write(chunk)

                #     logging.info(f"PDF saved to {local_path}")
                #     popup.close()

                # except Exception as e:
                #     logging.error(f"Error downloading PDF from popup: {e}")
                #     return None
                
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
                
            page.click("a.link-page.link-next")
            page.wait_for_load_state("domcontentloaded")
            time.sleep(2)  # wait for JS to load content
                
        browser.close()
