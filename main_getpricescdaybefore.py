import os
import pandas as pd
import playwright.sync_api as pw
from scraping.utils.Utils import parse_vietnamese_date
import logging
import time

logging.basicConfig(level=logging.INFO)

def main(start_row: int = 1):
    # Load dataframe from /data/get_eps_date_sec_code.csv
    df = pd.read_csv('./data/get_cp_datebefore_repdate.csv')
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
            report_date = row['report_date']
            get_date = row['get_date']

            # if open_price is not None and open_price > 0:
            #     logging.info(f"Skipping {sec_code} on {report_date} as open_price is already available: {open_price}")
            #     continue
            
            # Navigate to the website
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
            
            # Navigate to the historical prices section
            day, month, year = parse_vietnamese_date(get_date)
            
            # Handle if day is 0, minus one day
            if day == 0:
                if month == 1:
                    month = 12
                    year -= 1
                else:
                    month -= 1
                # Get last day of the previous month
                if month in [1, 3, 5, 7, 8, 10, 12]:
                    day = 31
                elif month in [4, 6, 9, 11]:
                    day = 30
                else:
                    # February, check for leap year
                    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
                        day = 29
                    else:
                        day = 28
            else:
                logging.info(f"Already have a valid day: {day}")
                continue
            
            get_price_date = f"{day}/{month}/{year}"
            logging.info(f"Parsed date for {report_date}: day={day}, month={month}, year={year}")

            page.fill('input#date-inp-disclosure', f"{get_price_date} - {get_price_date}")

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
                logging.info(f"Extracted closing price for {sec_code} on {report_date}: {closing_price}")
            except Exception as e:
                logging.error(f"Error extracting closing price for {sec_code} on {report_date}: {e}")
                closing_price = None
            
            # Append result to list
            result = ({
                'sec_code': sec_code,
                'report_date': report_date,
                'price_day_before': closing_price,
                'get_date': get_date
            })
            
            # Write intermediate result to csv
            pd.DataFrame([result]).to_csv('./output/get_cp_datebefore_repdate_v2.csv', mode='a', header=not os.path.exists('./output/get_cp_datebefore_repdate.csv'), index=False)
            # time.sleep(5)
        # Close the browser
        browser.close()
    
    
if __name__ == "__main__":
    main()