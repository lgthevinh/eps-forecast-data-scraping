import pandas as pd

def fill_closing_price():
    df = pd.read_csv('./data/modified_tonghop.csv')
    df_closing_price = pd.read_csv('./data/get_cp_datebefore_repdate.csv')
    
    # Remove date with day in get_date is 0
    # df_closing_price = df_closing_price[df_closing_price['get_date'].str.split('/').str[0].astype(int) != 0]
    # df_closing_price = df_closing_price[['sec_code', 'report_date', 'price_day_before', 'get_date']]
    df_closing_price = df_closing_price.drop_duplicates(subset=['sec_code', 'report_date'])
    print(f"Loaded closing prices with {df_closing_price.shape[0]} rows.")
    
    df_closing_price.to_csv('./data/get_cp_datebefore_repdate.csv', index=False)

    # # Change sec_code to upper case to match
    df_closing_price['sec_code'] = df_closing_price['sec_code'].str.upper()

    df = df.merge(df_closing_price[['sec_code', 'report_date', 'price_day_before', 'get_date']], on=['sec_code', 'report_date'], how='left')
    
    df.to_csv('./output/modified_tonghop_filled.csv', index=False)
    print("Filled closing prices and saved to ./output/modified_tonghop_filled.csv")

if __name__ == "__main__":
    fill_closing_price()