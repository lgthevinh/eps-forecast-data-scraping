import pandas as pd

#This function loads data from `merged_coporates_cleaned.csv` and maps the columns to a new DataFrame.
def load_data(file_path):
    
    print(f"Loading data from {file_path}...")
    
    df = pd.read_csv(file_path)
    df = df.drop('STT', axis=1)  # Drop the 'STT' column
    df.columns = ['name', 'sec_code', 'stock_exchange']
    
    print(f"Data loaded from {file_path} with {len(df)} records.")
    
    return df
