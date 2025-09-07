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

ROOT_URL = "https://www.vdsc.com.vn"
BASE_URL = "https://www.vdsc.com.vn/trung-tam-phan-tich/doanh-nghiep?page="
DATE_RANGE = ""
PAGE_PARAM = ""
        
def scraping_vds_all(download_dir="downloads", valid_codes=None, max_pages=20, start_page=1, output_dir="output/eps_rep_vds.csv", blacklist_code=None, firm="SSV"):
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        time.sleep(60)  # Initial wait before starting
        page.wait_for_load_state("domcontentloaded")

        
        page.goto(BASE_URL + "1", timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        for page_num in range(start_page, max_pages + 1):
            url = f"{BASE_URL}{page_num}"
            logging.info(f"Loading page {page_num}: {url}")
            page.goto(url, timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            
            content = page.query_selector("div.list-report")
            report_items = content.query_selector_all(" div.col-6.col-md-3")
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
                    sec_code_tag = report_item.query_selector("h3")
                    date = report_item.query_selector("h2.title")
                    month = report_item.query_selector("h4.title")
                    logging.info(f"Report {idx} title: {sec_code_tag.text_content().strip() if sec_code_tag else 'N/A'}")
                    logging.info(f"Extracted date: {date.text_content().strip() if date else 'N/A'}, month: {month.text_content().strip() if month else 'N/A'}")

                    if sec_code_tag:
                        sec_code = sec_code_tag.text_content().strip()[:3].upper()
                        is_sec_code_tagged = True
                    else:
                        logging.warning(f"Could not find sec_code for report {idx} on page {page_num}, fallback to sec code tickets.")

                    if not date or not month:
                        logging.warning(f"Could not find report date for report {idx} on page {page_num}, skipping.")
                        continue
                    # Replace 'Tháng' in month with ''
                    month_text = month.text_content().lower().replace("tháng", "").replace("-", "/").replace(" ", "").strip()

                    report_date = f"{date.text_content().strip()}/{month_text}"
                    logging.info(f"[Page {page_num} - Report {idx}] {sec_code} ({report_date})")
                    
                except Exception as e:
                    logging.error(f"Error detecting sec_code or date for report {idx} on page {page_num}: {e}")
                    continue
                
                # Get pdf link and download
                # local_path = None
                # try:
                #     pdf_link_tag = report_item.query_selector("div.chart__content__item__time > a")
                #     if not pdf_link_tag:
                #         logging.warning(f"No PDF link in report {idx} on page {page_num}, skipping.")
                #         continue
                #     logging.info(f"Found PDF link for report {idx} on page {page_num}")
                    
                #     pdf_url = urljoin(BASE_URL, pdf_link_tag.get_attribute("href"))
                #     # filename = os.path.basename(pdf_url)
                #     # local_path = os.path.join(download_dir, filename) + ".pdf"
                #     # logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
                #     # response = requests.get(pdf_url)
                #     # with open(local_path, "wb") as f:
                #     #     f.write(response.content)
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

                # except Exception as e:
                #     logging.error(f"Error finding PDF link for report {idx} on page {page_num}: {e}")
                #     continue
                
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
                local_path = None
                pdf_link_tag = report_item
                try:
                    # Step 1: Catch popup
                    with page.expect_popup() as popup_info:
                        pdf_link_tag.click()
                    popup = popup_info.value
                    popup.wait_for_load_state("networkidle")

                    # Step 2: Get PDF URL
                    pdf_url = popup.url
                    logging.info(f"Popup opened with PDF URL: {pdf_url}")

                    # Step 3: Extract filename and set local path
                    filename = os.path.basename(pdf_url.split("?")[0])  # strip query params
                    local_path = os.path.join(download_dir, filename)

                    # Step 4: Download using requests with cookies (to handle auth)
                    cookies = page.context.cookies()
                    session = requests.Session()
                    for c in cookies:
                        session.cookies.set(c["name"], c["value"], domain=c["domain"])

                    response = session.get(pdf_url, stream=True)
                    response.raise_for_status()

                    with open(local_path, "wb") as f:
                        for chunk in response.iter_content(8192):
                            f.write(chunk)

                    logging.info(f"PDF saved to {local_path}")
                    popup.close()

                except Exception as e:
                    logging.error(f"Error downloading PDF from popup: {e}")
                    return None
                
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
