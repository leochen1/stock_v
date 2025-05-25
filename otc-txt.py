import os
import pandas as pd
import numpy as np
import talib
from tqdm import tqdm
from datetime import datetime
from collections import defaultdict
import requests

DATA_DIR = "data/tpex_history"
os.makedirs(DATA_DIR, exist_ok=True)

def get_company_info_data(url):
    res = requests.get(url, verify=False)
    tables = pd.read_html(res.text)
    df = tables[0]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df = df[['有價證券代號', '有價證券名稱', '產業別']]
    df = df.dropna()
    return df

def get_stock_info_dict():
    url = "https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=2&issuetype=4&industry_code=&Page=1&chklike=Y"
    df = get_company_info_data(url)
    return {row['有價證券代號']: (row['有價證券名稱'], row['產業別']) for _, row in df.iterrows()}

def get_stock_codes_from_csv(stock_info_dict):
    stock_codes = []
    for file in os.listdir(DATA_DIR):
        if file.endswith(".csv"):
            code = file.split(".")[0]
            name, industry = stock_info_dict.get(code, ("", ""))
            stock_codes.append((code, name, industry))
    return stock_codes

def analyze_stock(stock_code, stock_name, industry):
    csv_path = os.path.join(DATA_DIR, f"{stock_code}.csv")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"{stock_code}: 讀取歷史資料失敗 - {e}")
        return False, '-', '-', stock_name, industry

    if len(df) < 60:
        print(f"{stock_code}: 資料不足60筆，略過。")
        return False, '-', '-', stock_name, industry

    df = df.dropna()
    df = df.rename(columns={'開盤價': 'Open', '最高價': 'High', '最低價': 'Low', '收盤價': 'Close', '成交量': 'Volume'})
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])
    df.index = pd.to_datetime(df['日期'])

    sma_20 = talib.SMA(df['Close'].values, timeperiod=20)
    rsi_5 = talib.RSI(df['Close'].values, timeperiod=5)
    rsi_10 = talib.RSI(df['Close'].values, timeperiod=10)
    rsi_14 = talib.RSI(df['Close'].values, timeperiod=14)

    df['SMA_5'] = talib.SMA(df['Close'], timeperiod=5)
    df['SMA_10'] = talib.SMA(df['Close'], timeperiod=10)
    df['SMA_20'] = talib.SMA(df['Close'], timeperiod=22)
    df['SMA_60'] = talib.SMA(df['Close'], timeperiod=60)

    plus_di_result = talib.PLUS_DI(df.High, df.Low, df.Close, timeperiod=14)
    minux_di_result = talib.MINUS_DI(df.High, df.Low, df.Close, timeperiod=14)
    adx_result = talib.ADX(df.High, df.Low, df.Close, timeperiod=14)

    df_weekly = df.resample('W').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    plus_di_weekly = talib.PLUS_DI(df_weekly.High, df_weekly.Low, df_weekly.Close, timeperiod=14)
    minux_di_weekly = talib.MINUS_DI(df_weekly.High, df_weekly.Low, df_weekly.Close, timeperiod=14)
    adx_weekly = talib.ADX(df_weekly.High, df_weekly.Low, df_weekly.Close, timeperiod=14)

    df_monthly = df.resample('ME').agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    }).dropna()
    plus_di_monthly = talib.PLUS_DI(df_monthly.High, df_monthly.Low, df_monthly.Close, timeperiod=14)
    minux_di_monthly = talib.MINUS_DI(df_monthly.High, df_monthly.Low, df_monthly.Close, timeperiod=14)
    adx_monthly = talib.ADX(df_monthly.High, df_monthly.Low, df_monthly.Close, timeperiod=14)

    result_df = pd.DataFrame(index=df.index)
    result_df['+DI'] = plus_di_result
    result_df['-DI'] = minux_di_result
    result_df['ADX'] = adx_result
    result_df['+DI_greater_than_-DI'] = result_df['+DI'] > result_df['-DI']
    result_df['ADX_increase'] = result_df['ADX'] > result_df['ADX'].shift(1)
    result_df['Volume_1000'] = df['Volume'] / 1000

    result_df_weekly = pd.DataFrame(index=df_weekly.index)
    result_df_weekly['+DI_weekly'] = plus_di_weekly
    result_df_weekly['-DI_weekly'] = minux_di_weekly
    result_df_weekly['ADX_weekly'] = adx_weekly
    result_df_weekly['+DI_greater_than_-DI_weekly'] = result_df_weekly['+DI_weekly'] > result_df_weekly['-DI_weekly']
    result_df_weekly['ADX_increase_weekly'] = result_df_weekly['ADX_weekly'] > result_df_weekly['ADX_weekly'].shift(1)

    result_df_monthly = pd.DataFrame(index=df_monthly.index)
    result_df_monthly['+DI_monthly'] = plus_di_monthly
    result_df_monthly['-DI_monthly'] = minux_di_monthly
    result_df_monthly['ADX_monthly'] = adx_monthly
    result_df_monthly['+DI_greater_than_-DI_monthly'] = result_df_monthly['+DI_monthly'] > result_df_monthly['-DI_monthly']
    result_df_monthly['ADX_increase_monthly'] = result_df_monthly['ADX_monthly'] > result_df_monthly['ADX_monthly'].shift(1)

    if not result_df.empty:
        last_row = result_df.iloc[-1]
        last_row_weekly = result_df_weekly.iloc[-1]
        last_row_monthly = result_df_monthly.iloc[-1]
        if (last_row['ADX_increase'] and last_row['+DI_greater_than_-DI'] and
           last_row_weekly['ADX_increase_weekly'] and last_row_weekly['+DI_greater_than_-DI_weekly'] and
           last_row_monthly['ADX_increase_monthly'] and last_row_monthly['+DI_greater_than_-DI_monthly'] and
           last_row['Volume_1000'] > 100
        ):
            return True, '-', '-', stock_name, industry
        else:
            return False, '-', '-', stock_name, industry
    else:
        return False, '-', '-', stock_name, industry

def get_matched_stocks(stock_codes, batch_size=50):
    matched_stocks = []
    count = 0

    for i in range(0, len(stock_codes), batch_size):
        batch = stock_codes[i:i + batch_size]
        for stock_code, stock_name, industry in tqdm(batch, ncols=70):
            try:
                match, recommendation_mean, recommendationKey, stock_name, industry = analyze_stock(stock_code, stock_name, industry)
                if match:
                    count += 1
                    print(f' 股票代號 : {stock_code} 今天符合規則.')
                    matched_stocks.append((stock_code, stock_name, industry, recommendation_mean, recommendationKey))
            except Exception as exc:
                print(f'{stock_code} generated an exception: {exc}')
    return matched_stocks, count

def save_txt(filename, matched_stocks):
    # 只輸出 1210.TW 這種格式，每行一檔
    with open(filename, "w", encoding="utf-8") as f:
        for code, name, industry, recommendation_mean, recommendationKey in matched_stocks:
            f.write(f"{code}.TW\n")
    print(f"已輸出結果到 {filename}")

def main():
    stock_info_dict = get_stock_info_dict()
    stock_codes = get_stock_codes_from_csv(stock_info_dict)
    matched_stocks, count = get_matched_stocks(stock_codes)

    # 只輸出代號.TW，每行一檔
    save_txt("otc_matched_stocks.txt", matched_stocks)

if __name__ == "__main__":
    main()