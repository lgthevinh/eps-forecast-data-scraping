import os
import pandas as pd
import playwright.sync_api as pw
from scraping.utils.Utils import parse_vietnamese_date
import logging
import time

logging.basicConfig(level=logging.INFO)

DATE_2018 = "28/12/2018"
DATE_2019 = "31/12/2019"
DATE_2020 = "31/12/2020"
DATE_2021 = "31/12/2021"
DATE_2022 = "30/12/2022"
DATE_2023 = "29/12/2023"
DATE_2024 = "31/12/2024"

def main(start_row: int = 0):
    # Load dataframe from /data/get_eps_date_sec_code.csv
    df = pd.read_csv('./data/data-ver2_cp_last_doy_minus1.csv')

    # Remove all columns except sec_code and year
    df = df[['sec_code', 'year', 'closing_price_last_doy']]
    last_sec_code = None

    # Initialize Playwright and open a browser
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        for index, row in df.iterrows():
            if index < start_row:
                continue
            
            logging.info(f"Processing row {index}: {row.to_dict()}")
            sec_code = row['sec_code']
            year = row['year']
            cp = row['closing_price_last_doy']
            
            # Skip if closing price is already present
            if pd.notna(cp):
                logging.info(f"Closing price already exists for {sec_code} in {year}, skipping.")
                continue

            if year == 2019:
                get_date = DATE_2018
            elif year == 2020:
                get_date = DATE_2019
            elif year == 2021:
                get_date = DATE_2020
            elif year == 2022:
                get_date = DATE_2021
            elif year == 2023:
                get_date = DATE_2022
            elif year == 2024:
                get_date = DATE_2023
            else:
                logging.warning(f"Year {year} is out of expected range. Skipping row {index}.")
                continue
            
            sec_code = sec_code.lower()
            if sec_code != last_sec_code:
                last_sec_code = sec_code
                logging.info(f"Navigating to page for {sec_code}")
                URL = f"https://cafef.vn/du-lieu/lich-su-giao-dich-{sec_code}-1.chn"
                page.goto(URL)
            
                # Wait for navigation to complete
                page.wait_for_load_state('domcontentloaded')
            else:
                logging.info(f"Reusing page for {sec_code}")
            time.sleep(0.2)  # Wait for the page to load

            page.fill('input#date-inp-disclosure', f"{get_date} - {get_date}")

            time.sleep(0.6)  # Wait for the date input to be filled
            page.mouse.click(10, 10)  # Focus on the date input
            # page.click('button.applyBtn.btn.btn-sm.btn-primary')
            time.sleep(0.6)  # Wait for the date filter to apply
            page.click('div#owner-find')
            page.wait_for_load_state('domcontentloaded')
            time.sleep(0.6)  # Wait for the table to load
            
            # Extract the closing price from the table
            try:
                closing_price = page.query_selector('table#owner-contents-table tbody tr:nth-child(1) td:nth-child(2)').inner_text()
                closing_price = closing_price.replace(',', '')  # Remove commas if any
                closing_price = float(closing_price)
                logging.info(f"Extracted closing price for {sec_code} on {get_date}: {closing_price}")
            except Exception as e:
                logging.error(f"Error extracting closing price for {sec_code} on {get_date}: {e}")
                closing_price = None
            
            # Append result to list
            result = ({
                'sec_code': sec_code,
                'closing_price_last_doy': closing_price,
                'get_date': get_date
            })
            
            # Write intermediate result to csv
            pd.DataFrame([result]).to_csv('./output/get_cp_lastdoy_minus1.csv', mode='a', header=not os.path.exists('./output/get_cp_lastdoy_minus1.csv'), index=False)
            # time.sleep(5)
        # Close the browser
        browser.close()


def remove_duplicates():
    df = pd.read_csv('./output/get_cp_lastdoy_minus1.csv')
    df = df.drop_duplicates(subset=['sec_code', 'get_date'])
    df.to_csv('./output/get_cp_lastdoy_minus1.csv', index=False)
    logging.info("Removed duplicates and saved to ./output/get_cp_lastdoy_minus1.csv")
    
if __name__ == "__main__":
    # main()
    remove_duplicates()