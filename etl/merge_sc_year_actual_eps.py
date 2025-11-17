import pandas as pd

def merge_actual_eps():
    df = pd.read_csv('./data/data-ver2.csv')
    df = df[['sec_code', 'year']]
    df_actual_eps = pd.read_csv('./data/actual_eps.csv')
    # df_closing_price = pd.read_csv('./data/get_cp_datebefore_repdate.csv')

    # Change sec_code to upper case to match
    df_actual_eps['sec_code'] = df_actual_eps['sec_code'].str.upper()

    df = df.merge(df_actual_eps, on=['sec_code', 'year'], how='left')
    df.to_csv('./data/data-ver2_actual_eps.csv', index=False)
    print("Merged actual EPS and saved to ./data/data-ver2_actual_eps.csv")
    
if __name__ == "__main__":
    merge_actual_eps()