import logging
import pandas as pd

from scraping.vcbs.vcbs_scraping import scraping_vcbs_all

def main(TAG: str, size: int = None):
    """
    Run DSC scraping for all reports, save results into CSV.
    Args:
        TAG (str): firm label (e.g., "AGR")
        size (int): maximum number of rows to save (optional)
    """
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    output_dir = f"output/eps_rep_{TAG.lower()}.csv"
    download_dir = f"downloads_{TAG.lower()}"
    logging.info(f"Starting {TAG} scraping...")
    
    scraping_vcbs_all(output_dir=output_dir, max_pages=81, start_page=24, firm=TAG, download_dir=download_dir)

if __name__ == "__main__":
    main("VCBS")
