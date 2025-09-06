import pandas as pd

def merge_stock_exchanges():
    # Read the CSV files
    hnx_df = pd.read_csv('hnx_coporates.csv')
    hose_df = pd.read_csv('hose_coporates.csv')
    
    # Remove the STT column from both dataframes
    hnx_df = hnx_df.drop('STT', axis=1)
    hose_df = hose_df.drop('STT', axis=1)
    
    # Merge the dataframes
    merged_df = pd.concat([hnx_df, hose_df], ignore_index=True)
    
    # Sort by exchange and then by company name for better organization
    merged_df = merged_df.sort_values(['Sàn niêm yết', 'Tên đầy đủ'])
    
    # Reset index and add a new sequential number
    merged_df.reset_index(drop=True, inplace=True)
    merged_df.index += 1  # Start from 1 instead of 0
    
    # Save to a new CSV file
    merged_df.to_csv('merged_coporates.csv', index=True, index_label='STT')
    
    print(f"Successfully merged {len(hnx_df)} HNX companies and {len(hose_df)} HOSE companies")
    print(f"Total companies: {len(merged_df)}")
    print("Merged file saved as 'merged_coporates.csv'")
    
    return merged_df

if __name__ == "__main__":
    merged_data = merge_stock_exchanges()
    
    # Display first few rows to verify
    print("\nFirst 5 rows of merged data:")
    print(merged_data.head())