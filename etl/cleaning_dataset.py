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
    
    # Change 'firm' column values from 'BSC' to 'PSI'
    if 'firm' in df.columns:
        df['firm'] = df['firm'].replace('BSC', 'KBVS_23_toall')
        logging.info("Replaced 'BSC' with '*_23_toall' in 'firm' column.")

    # Remove the "downloads/bvs\" and only keep file name in the file_name column
    # if 'file_name' in df.columns:
    #     df['file_name'] = df['file_name'].apply(lambda x: os.path.basename(x) if isinstance(x, str) else x)
    #     logging.info("Cleaned 'file_name' column to keep only the file name.")

    # Get only first duplicate based on sec_code, clean_year, report_date, eps
    if {"clean_year", "sec_code", "report_date", "eps"}.issubset(df.columns):
        df = df.drop_duplicates(subset=["clean_year", "sec_code", "report_date", "eps"])
        logging.info(f"After dropping duplicates, dataset has {df.shape[0]} rows.")

    # Delete row if length of year is more than 8 or less than 4
    if 'year' in df.columns:
        df = df[df['year'].astype(str).str.len().between(4, 8)]
    logging.info(f"After filtering by year length, dataset has {df.shape[0]} rows.")
    
    df.to_csv(f'output/cleaned_eps_rep_{TAG}.csv', index=False)
    logging.info("Data cleaning complete. Cleaned dataset saved.")
    
    # Remove duplicate based on url column
    if 'url' in df.columns:
        df = df.drop_duplicates(subset=['url'])
        logging.info(f"After dropping duplicates based on 'url', dataset has {df.shape[0]} rows.")

    df.to_csv(f'output/cleaned_eps_rep_{TAG}_removeduplicateurl.csv', index=False)
    logging.info("Data cleaning complete. Cleaned dataset saved.")

if __name__ == "__main__":
    main(TAG="vcbs")