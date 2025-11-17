# Load filtered year, clean_year, eps, is_forecast = True, report date and sec_code from ./data/filtered_eps_fc.csv
import pandas as pd
# This function loads data from `filtered_eps_fc.csv` and maps the columns to a new DataFrame.
def load_filtered_eps_fc(file_path, output_dir):
    
    print(f"Loading data from {file_path}...")
    
    # Read excel file with all sheets
    df = pd.read_csv(file_path)
    
    # Filter out only get col: clean_year, sec_code, report_date
    filtered_df = df[['clean_year', 'report_date', 'sec_code']]
    
    # Remove duplicates of report_date, sec_codes
    filtered_df = filtered_df.drop_duplicates(subset=['report_date', 'sec_code'])
    
    # Save to output directory
    output_path = f"{output_dir}"
    filtered_df.to_csv(output_path, index=False)
    print(f"Filtered data saved to {output_path}")

def main():
    file_path = './data/tonghop.csv'
    output_dir = './output/get_eps_date_sec_code.csv'
    load_filtered_eps_fc(file_path, output_dir)

if __name__ == "__main__":
    main()