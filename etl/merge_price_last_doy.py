import pandas as pd

def merge_closing_price():
    df = pd.read_csv('./data/data-ver2.csv')
    df = df[['sec_code', 'year']]
    df_last_doy = pd.read_csv('./output/get_cp_lastdoy_minus1.csv')
    df_last_doy = df_last_doy[['sec_code', 'year', 'closing_price_last_doy']]
    
    # Remove duplicate rows if any
    df_last_doy = df_last_doy.drop_duplicates(subset=['sec_code', 'year'])
    # df_closing_price = pd.read_csv('./data/get_cp_datebefore_repdate.csv')

    # Change sec_code to upper case to match
    df_last_doy['sec_code'] = df_last_doy['sec_code'].str.upper()

    df = df.merge(df_last_doy, on=['sec_code', 'year'], how='left')
    df.to_csv('./data/data-ver2_cp_last_doy_minus1.csv', index=False)
    print("Merged closing price and saved to ./data/data-ver2_cp_last_doy_minus1.csv")

if __name__ == "__main__":
    merge_closing_price()