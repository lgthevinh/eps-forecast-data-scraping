import pandas as pd

def merge_stock_exchanges():
    # Read the CSV files
    bank_df = pd.read_csv('bank.csv')
    securities_df = pd.read_csv('securities.csv')
    electricity_df = pd.read_csv('electric.csv')
    
    # Remove the STT column from both dataframes
    bank_df = bank_df.drop('STT', axis=1)
    securities_df = securities_df.drop('STT', axis=1)
    electricity_df = electricity_df.drop('STT', axis=1)
    
    # Match column names for consistency
    bank_df.columns = ['sec_code', 'name', 'stock_exchange']
    securities_df.columns = ['sec_code', 'name', 'stock_exchange']
    electricity_df.columns = ['name', 'sec_code', 'stock_exchange']
    
    # Merge the dataframes
    merged_df = pd.concat([bank_df, securities_df, electricity_df], ignore_index=True)
    
    # Sort by exchange and then by company name for better organization
    merged_df = merged_df.sort_values(['stock_exchange', 'name'])
    
    # Reset index and add a new sequential number
    merged_df.reset_index(drop=True, inplace=True)
    merged_df.index += 1  # Start from 1 instead of 0
    
    # Save to a new CSV file
    merged_df.to_csv('merged_delimeter.csv', index=True, index_label='STT')

    print(f"Successfully merged {len(bank_df)} Bank companies and {len(securities_df)} Securities companies")
    print(f"Total companies: {len(merged_df)}")
    print("Merged file saved as 'merged_delimeter.csv'")
    
    return merged_df

if __name__ == "__main__":
    merged_data = merge_stock_exchanges()
    
    # Display first few rows to verify
    print("\nFirst 5 rows of merged data:")
    print(merged_data.head())