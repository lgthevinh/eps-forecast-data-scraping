import logging
import pandas as pd

from scraping.mbs.eps_mbs_scrapingv2 import scraping_mbs_all as scraping_mbs

def main(TAG: str, size: int = None):
    """
    Run MBS scraping for all reports, save results into CSV.
    Args:
        TAG (str): firm label (e.g., "MBS")
        size (int): maximum number of rows to save (optional)
    """
    output_dir = f"output/eps_rep_{TAG.lower()}.csv"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    valid_codes = pd.read_csv('data/merged_coporates_cleaned.csv')['sec_code'].dropna().unique().tolist()

    logging.info("Starting MBS scraping...")
    scraping_mbs(max_pages=61, output_dir=output_dir, valid_codes=None)

if __name__ == "__main__":
    main("MBS")
