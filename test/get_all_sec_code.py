import pandas as pd
from playwright.sync_api import sync_playwright

def scrape_sec_codes(max_pages=20):
    sec_codes = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # set to True if you don’t want UI
        page = browser.new_page()

        # Go to login page
        page.goto("https://finance.vietstock.vn")


        browser.close()



if __name__ == "__main__":
    scrape_sec_codes(max_pages=100)
