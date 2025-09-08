import logging
import pandas as pd

from scraping.agrisco.agrisco_scraping import scraping_agr_all

def main(TAG: str, size: int = None):
    """
    Run AGR scraping for all reports, save results into CSV.
    Args:
        TAG (str): firm label (e.g., "AGR")
        size (int): maximum number of rows to save (optional)
    """
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    output_dir = f"output/eps_rep_{TAG.lower()}.csv"
    logging.info(f"Starting {TAG} scraping...")
    download_dir = f"downloads/{TAG.lower()}"
    
    # sec_code_list = pd.read_csv('data/merged_coporates_cleaned.csv')['sec_code'].dropna().unique().tolist()
    sec_code_list_test = ['VHM', 'VNM', 'IDC'] # Example stock codes for testing

    scraping_agr_all(output_dir=output_dir, max_pages=111, start_page=1, firm=TAG, download_dir=download_dir)

if __name__ == "__main__":
    main("AGR_23_toall")
