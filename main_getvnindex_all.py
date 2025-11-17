import os
import pandas as pd
import playwright.sync_api as pw
from scraping.utils.Utils import parse_vietnamese_date
import logging
import time
import threading

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

DATE_2018 = "28/12/2018"
DATE_2019 = "31/12/2019"
DATE_2020 = "31/12/2020"
DATE_2021 = "31/12/2021"
DATE_2022 = "30/12/2022"
DATE_2023 = "29/12/2023"
DATE_2024 = "31/12/2024"

def main(sec_code: str, output_dir: str, page_num: int = 1):
    # Initialize Playwright and open a browser
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        URL = f"https://cafef.vn/du-lieu/lich-su-giao-dich-{sec_code}-1.chn"
        page.goto(URL)
        page.fill('input#date-inp-disclosure', f"01/01/2017 - {DATE_2024}")

        time.sleep(0.6)
        page.mouse.click(10, 10)
        page.click('div#owner-find')
        time.sleep(0.6)
        for i in range(1, page_num):
            result = []
            table = page.query_selector('table#owner-contents-table tbody')
            for row in table.query_selector_all('tr'):
                cols = row.query_selector_all('td')
                
                date = cols[0].inner_text().strip()
                closing_price = cols[1].inner_text().strip()
                adjusted_price = cols[2].inner_text().strip()
                changes_percent = cols[3].inner_text().strip()
                auction_volume = cols[4].inner_text().strip()
                auction_value = cols[5].inner_text().strip()
                settlement_volume = cols[6].inner_text().strip()
                settlement_value = cols[7].inner_text().strip()
                opening_price = cols[8].inner_text().strip()
                highest_price = cols[9].inner_text().strip()
                lowest_price = cols[10].inner_text().strip()

                logging.info(f"Page [{i}] Date: {date}, Closing Price: {closing_price}, Adjusted Price: {adjusted_price}, Changes Percent: {changes_percent}, Auction Volume: {auction_volume}, Auction Value: {auction_value}, Settlement Volume: {settlement_volume}, Settlement Value: {settlement_value}, Opening Price: {opening_price}, Highest Price: {highest_price}, Lowest Price: {lowest_price}")
                result.append({
                    'sec_code': sec_code,
                    'date': date,
                    'closing_price': closing_price,
                    'adjusted_price': adjusted_price,
                    'changes_percent': changes_percent,
                    'auction_volume': auction_volume,
                    'auction_value': auction_value,
                    'settlement_volume': settlement_volume,
                    'settlement_value': settlement_value,
                    'opening_price': opening_price,
                    'highest_price': highest_price,
                    'lowest_price': lowest_price
                })
            
            # Write intermediate result to csv
            pd.DataFrame(result).to_csv(output_dir, mode='a', header=not os.path.exists(output_dir), index=False)
        
            next_button = page.query_selector('i#paging-right')
            next_button.click()
            time.sleep(1.2)
            
        # Close the browser
        browser.close()

def drop_duplicates(input_csv: str, output_csv: str):
    df = pd.read_csv(input_csv)
    df.drop_duplicates(keep='first', inplace=True)
    df.to_csv(output_csv, index=False)
    
if __name__ == "__main__":
    # threading.Thread(target=main, args=("vnindex", "./output/vnindex_price_2017_2024.csv", 101)).start()
    # threading.Thread(target=main, args=("hnx-index", "./output/hnx_price_2017_2024.csv", 247)).start()
    drop_duplicates("./output/vnindex_price_2017_2024.csv", "./output/vnindex_price_2017_2024_cleaned.csv")
    drop_duplicates("./output/hnx_price_2017_2024.csv", "./output/hnx_price_2017_2024_cleaned.csv")