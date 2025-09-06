import os
import re
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
import pandas as pd

from scraping.eps_scraping_pdf import extract_clean_eps_w_sc_v5 as extract_clean_eps
from scraping.eps_scraping_pdf import extract_clean_eps_v5, extract_clean_eps_v6
from scraping.utils.Utils import parse_vietnamese_date

BASE_URL_SIMPLE = "https://mbs.com.vn"

def scraping_mbs_simple(sec_code: str, download_dir: str = "downloads"):
    url = f"{BASE_URL_SIMPLE}/?post_type=report&taxonomy=report_cat&term=bao-cao-phan-tich-co-phieu&s={sec_code}"
    r = requests.get(url)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    # no result check
    if "Chưa có bài viết nào được đăng" in r.text:
        logging.warning(f"SEC_CODE '{sec_code}' NOT FOUND.")
        return []

    results_all = []
    report_items = soup.select("div.list_content- div.relative")

    for idx, report_item in enumerate(report_items, start=1):
        link_tag = report_item.select_one("a")
        date_tag = report_item.select_one("span")

        if not link_tag or not date_tag:
            continue

        href = link_tag.get("href")
        date_span = date_tag.get_text(strip=True)

        _, _, year = parse_vietnamese_date(date_span)
        if year and int(year) < 2018:
            logging.info(f"Skipping report dated {date_span} (year < 2018)")
            continue

        report_url = urljoin(BASE_URL_SIMPLE, href)
        logging.info(f"[{idx}] Report {report_url} ({date_span})")

        # fetch report page
        r_report = requests.get(report_url)
        r_report.raise_for_status()
        report_soup = BeautifulSoup(r_report.text, "html.parser")

        # find first PDF link
        pdf_tag = report_soup.find("a", href=re.compile(r"\.pdf$"))
        if not pdf_tag:
            logging.warning(f"No PDF link in {report_url}")
            continue

        pdf_url = urljoin(report_url, pdf_tag["href"])

        # download pdf
        os.makedirs(download_dir, exist_ok=True)
        filename = f"{sec_code}_search_{idx}.pdf"
        local_path = os.path.join(download_dir, filename)

        logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
        with requests.get(pdf_url, stream=True) as r_pdf:
            r_pdf.raise_for_status()
            with open(local_path, "wb") as f:
                for chunk in r_pdf.iter_content(8192):
                    f.write(chunk)

        # extract EPS
        eps_results = extract_clean_eps(local_path, date_span, sec_code) or []
        for item in eps_results:
            item["sec_code"] = sec_code
            item["file"] = filename
        results_all.extend(eps_results)

    return results_all

def scrape_all_reports(download_dir="downloads", max_pages=61):
    os.makedirs(download_dir, exist_ok=True)
    results_all = []

    for page_num in range(1, max_pages + 1):
        url = f"{BASE_URL_SIMPLE}/bao-cao-phan-tich-co-phieu/page/{page_num}/"

        if page_num == 1:
            url = f"{BASE_URL_SIMPLE}/bao-cao-phan-tich-co-phieu"

        r = requests.get(url)
        if r.status_code != 200:
            break
        
        soup = BeautifulSoup(r.text, "html.parser")

        report_items = soup.select("div.list_content- div.relative")
        if not report_items:
            logging.info(f"No reports found on page {page_num}, stopping.")
            break

        for idx, report_item in enumerate(report_items, start=1):
            link_tag = report_item.select_one("a")
            date_tag = report_item.select_one("span")

            if not link_tag or not date_tag:
                continue

            href = link_tag.get("href")
            date_span = date_tag.get_text(strip=True)

            report_url = urljoin(BASE_URL_SIMPLE, href)
            logging.info(f"[Page {page_num}] Report {report_url} ({date_span})")

            # fetch report detail page
            r_report = requests.get(report_url)
            if r_report.status_code != 200:
                continue
            report_soup = BeautifulSoup(r_report.text, "html.parser")

            # find first PDF link
            pdf_tag = report_soup.find("a", href=re.compile(r"\.pdf$"))
            if not pdf_tag:
                logging.warning(f"No PDF link in {report_url}")
                continue

            pdf_url = urljoin(report_url, pdf_tag["href"])
            filename = os.path.basename(pdf_url)
            local_path = os.path.join(download_dir, filename)

            if not os.path.exists(local_path):
                logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
                with requests.get(pdf_url, stream=True) as r_pdf:
                    r_pdf.raise_for_status()
                    with open(local_path, "wb") as f:
                        for chunk in r_pdf.iter_content(8192):
                            f.write(chunk)
            else:
                logging.info(f"PDF already downloaded: {local_path}")


            eps_results = extract_clean_eps_v5(local_path, date_span) or []
            results_all.extend(eps_results)

    return results_all



def scraping_mbs_all(download_dir="downloads", valid_codes=None, max_pages=20, output_dir="output/eps_rep_mbs.csv", blacklist_code=None):
    BASE_URL = "https://mbs.com.vn/bao-cao-phan-tich-co-phieu/"
    os.makedirs(download_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for page_num in range(1, max_pages + 1):
            url = BASE_URL if page_num == 1 else f"{BASE_URL}?paged={page_num}"
            logging.info(f"Loading page {page_num}: {url}")
            page.goto(url, timeout=60000)
            page.wait_for_load_state("networkidle")

            report_items = page.query_selector_all("div.list_content-bao-cao-phan-tich-co-phieu > div > div")
            if not report_items:
                logging.info(f"No reports found on page {page_num}, stopping.")
                continue

            for idx, report_item in enumerate(report_items, start=1):
                try:
                    link_tag = report_item.query_selector("a")
                    date_tag = report_item.query_selector("span")

                    if not link_tag or not date_tag:
                        continue

                    href = link_tag.get_attribute("href")
                    date_span = date_tag.text_content().strip()
                    _, _, year = parse_vietnamese_date(date_span)

                    if year and int(year) < 2015:
                        logging.info(f"Skipping report dated {date_span} (year < 2015)")
                        continue

                    report_url = urljoin(BASE_URL, href)
                    logging.info(f"[Page {page_num} - Report {idx}] {report_url} ({date_span})")

                    # open report page
                    new_page = browser.new_page()
                    new_page.goto(report_url, timeout=60000)
                    new_page.wait_for_load_state("networkidle")

                    # get PDF link
                    pdf_tag = new_page.query_selector("a[href$='.pdf']")
                    if not pdf_tag:
                        logging.warning(f"No PDF link in {report_url}")
                        continue

                    pdf_url = urljoin(report_url, pdf_tag.get_attribute("href"))
                    filename = os.path.basename(pdf_url)
                    local_path = os.path.join(download_dir, filename)

                    logging.info(f"Downloading PDF {pdf_url} -> {local_path}")
                    with requests.get(pdf_url, stream=True) as r_pdf:
                        r_pdf.raise_for_status()
                        with open(local_path, "wb") as f:
                            for chunk in r_pdf.iter_content(8192):
                                f.write(chunk)
                    new_page.close()
                    
                    # extract EPS
                    eps_results = extract_clean_eps_v6(local_path, date_span, valid_codes=valid_codes, blacklist_codes=blacklist_code,firm="MBS",url=pdf_url)
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
                    
        browser.close()
