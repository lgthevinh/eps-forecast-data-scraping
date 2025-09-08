import logging
import pandas as pd

from scraping.acbs.acbs_scraping import scraping_acbs_all

def main(TAG: str, size: int = None):
    """
    Run MBS scraping for all reports, save results into CSV.
    Args:
        TAG (str): firm label (e.g., "MBS")
        size (int): maximum number of rows to save (optional)
    """
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    output_dir = f"output/eps_rep_{TAG.lower()}.csv"
    logging.info(f"Starting {TAG} scraping...")
    download_dir = f"downloads_{TAG.lower()}"
    
    # sec_code_list = pd.read_csv('data/merged_coporates_cleaned.csv')['sec_code'].dropna().unique().tolist()
    sec_code_list_test = ['VHM', 'VNM', 'IDC'] # Example stock codes for testing

    # scraping_acbs_all(output_dir=output_dir, max_pages=127, start_page=60, download_dir=download_dir)
    scraping_acbs_all(output_dir=output_dir, max_pages=60, start_page=1, download_dir=download_dir, firm=TAG)

if __name__ == "__main__":
    main("ACBS_23_toall")
