import os
import pandas as pd
import playwright.sync_api as pw
from scraping.utils.Utils import parse_vietnamese_date, extract_report_date
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    # Initialize Playwright and open a browser
    df = pd.read_csv('./data/sec_code_with_year_1509025.csv')
    df = df[['sec_code', 'year']]
    last_sec_code = None
    
    with pw.sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        URL = f"https://congbothongtin.ssc.gov.vn/faces/NewsSearch"
        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")

        time.sleep(5)  # wait for 5 seconds to ensure page is fully loaded

        for index, df_row in df.iterrows():
            sec_code = df_row['sec_code']
            year = df_row['year']
            
            page.locator("input#pt9\\:it8112\\:\\:content").fill(sec_code)
            page.locator("input#pt9\\:id1\\:\\:content").fill("01/01/" + str(int(year)+1))
            page.locator("input#pt9\\:id2\\:\\:content").fill("31/12/" + str(int(year)+1))

            page.click("div#pt9\\:b1 a")

            time.sleep(1)
            
            table = page.query_selector("table.x14q.x15f")
            rows = table.query_selector_all("tbody tr")
            results = []
            for row in rows:
                flag = False
                cols = row.query_selector_all("td")
                reference = cols[3].inner_text().strip().lower()
                
                # Check if reference have "hợp nhất" and "kiểm toán" in it
                if "hợp nhất" in reference and "kiểm toán" in reference:
                    date_str = cols[4].inner_text().strip()
                    extracted_date = extract_report_date(date_str)
                    
                    # If date is after 31/03/year, flag = True
                    if extracted_date:
                        repday, repmonth, repyear = parse_vietnamese_date(extracted_date)
                        if repmonth > 3 or (repmonth == 3 and repday > 31):
                            flag = True
                            
                    results.append({
                        'sec_code': sec_code,
                        'year': year,
                        'reference': reference,
                        'date': extracted_date,
                        'flag': flag
                    })
                    logging.info(f"Found report for {sec_code} in year {year}: {reference} on {extracted_date}, flag={flag}") 
            
            pd.DataFrame(results).to_csv(f"./output/finrepdate.csv", index=False, mode='a', header=not os.path.exists(f"./output/finrepdate.csv"))
        
        # Close the browser
        browser.close()

def drop_duplicates(input_csv: str, output_csv: str):
    df = pd.read_csv(input_csv)
    df.drop_duplicates(keep='first', inplace=True)
    
    # Minus one from year column
    df['year'] = df['year'] - 1
    
    df.to_csv(output_csv, index=False)
    
if __name__ == "__main__":
    # main()
    drop_duplicates('./output/finrepdate.csv', './output/finrepdate.csv')
