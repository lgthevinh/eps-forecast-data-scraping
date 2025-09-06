import logging
import os
import pandas as pd

logging.basicConfig(level=logging.INFO)

def main(TAG: str):
    dataset_file = f'output/eps_rep_{TAG}.csv'
    df = pd.read_csv(dataset_file)
    logging.info(f"Loaded dataset with {df.shape[0]} rows and {df.shape[1]} columns.")
    # Perform data cleaning and preprocessing here
    df.dropna(inplace=True)
    
    # Get only first duplicate based on sec_code, clean_year, report_date, eps
    if {"clean_year", "sec_code", "report_date", "eps"}.issubset(df.columns):
        df = df.drop_duplicates(subset=["clean_year", "sec_code", "report_date", "eps"])
        logging.info(f"After dropping duplicates, dataset has {df.shape[0]} rows.")

    df.to_csv(f'output/cleaned_eps_rep_{TAG}.csv', index=False)
    logging.info("Data cleaning complete. Cleaned dataset saved.")

if __name__ == "__main__":
    main(TAG="agr")