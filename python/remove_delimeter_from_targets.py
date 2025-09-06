import pandas as pd

def remove_delimeter_from_targets():
    
    delimeter_df = pd.read_csv('merged_delimeter.csv')
    target_df = pd.read_csv('merged_coporates.csv')
    
    delimeter_df = delimeter_df.drop('STT', axis=1)
    delimeter_df.columns = ['sec_code', 'name', 'stock_exchange']

    target_df = target_df.drop('STT', axis=1)
    target_df.columns = ['name', 'sec_code', 'stock_exchange']

    # Remove all companies in target that have there sec_code in delimeter
    target_df = target_df[~target_df['sec_code'].isin(delimeter_df['sec_code'])]
    target_df.to_csv('merged_coporates_cleaned.csv', index=True, index_label='STT')
    
    print(f"Successfully removed {len(delimeter_df)} companies from targets")
    print(f"Total companies in cleaned targets: {len(target_df)}")
    print("Cleaned file saved as 'merged_coporates_cleaned.csv'")
    print("All operations completed successfully.") 
    
if __name__ == "__main__":
    remove_delimeter_from_targets()
    
    # Display first few rows to verify
    cleaned_data = pd.read_csv('merged_coporates_cleaned.csv')
    print("\nFirst 5 rows of cleaned data:")
    print(cleaned_data.head())
