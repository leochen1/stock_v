import requests
import pandas as pd
import numpy as np
import talib
import yfinance as yf
from tqdm import tqdm
from datetime import datetime
from collections import defaultdict
import concurrent.futures
import time

LINE_NOTIFY_TOKEN = 'boHMgzAvRReM6BADCyM3eodXmqkgrkrwlRD2P4Utf0b'
LINE_NOTIFY_API = 'https://notify-api.line.me/api/notify'

def get_company_info_data(url):
    res = requests.get(url)
    df = pd.read_html(res.text)[0]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df = df[['有價證券代號', '有價證券名稱', '產業別']]
    df = df.dropna()
    return df

def get_stock_codes():
    try:
        df1 = get_company_info_data("https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=1&issuetype=1&industry_code=&Page=1&chklike=Y")
        df2 = get_company_info_data("https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=2&issuetype=4&industry_code=&Page=1&chklike=Y")
        stock_codes_1 = df1.apply(lambda x: (x['有價證券代號']+'.TW', x['有價證券名稱'], x['產業別']), axis=1).tolist()  # TWSE 上市
        stock_codes_2 = df2.apply(lambda x: (x['有價證券代號']+'.TWO', x['有價證券名稱'], x['產業別']), axis=1).tolist()  # TWSE 上櫃
        stock_codes = stock_codes_1 + stock_codes_2
        return stock_codes
    except Exception as e:
        return str(e)

def analyze_stock(stock_code, stock_name, industry):
    df = yf.Ticker(stock_code).history(period = 'max')
    df_info = yf.Ticker(stock_code).info
    recommendation_mean = df_info.get('recommendationMean', '-')  # 取得股票推薦值
    recommendationKey = df_info.get('recommendationKey', '-') # 取得股票投資建議

    plus_di_result = talib.PLUS_DI(df.High, df.Low, df.Close, timeperiod=14)
    minux_di_result = talib.MINUS_DI(df.High, df.Low, df.Close, timeperiod=14)
    adx_result = talib.ADX(df.High, df.Low, df.Close, timeperiod = 14)
    sma_20 = talib.SMA(df['Close'].values, timeperiod=20)  # 計算20日均線
    rsi_5 = talib.RSI(df['Close'].values, timeperiod=5)  # 計算5日RSI
    rsi_10 = talib.RSI(df['Close'].values, timeperiod=10)  # 計算10日RSI
    rsi_14 = talib.RSI(df['Close'].values, timeperiod=14)  # 計算14日RSI

    df['SMA_5'] = talib.SMA(df['Close'], timeperiod=5)  # 計算5日均線 
    df['SMA_10'] = talib.SMA(df['Close'], timeperiod=10)  # 計算10日均線
    df['SMA_20'] = talib.SMA(df['Close'], timeperiod=22)  # 計算月均線，假設一個月有20個交易日
    df['SMA_60'] = talib.SMA(df['Close'], timeperiod=60)  # 計算60日均線

  
    result_df = pd.DataFrame(index=df.index)
    result_df['+DI'] = plus_di_result
    result_df['-DI'] = minux_di_result
    result_df['ADX'] = adx_result
    result_df['RSI_5'] = rsi_5
    result_df['RSI_10'] = rsi_10

    result_df['+DI_increase'] = result_df['+DI'] > result_df['+DI'].shift(1)
    result_df['-DI_decrease'] = result_df['-DI'] < result_df['-DI'].shift(1)
    result_df['ADX_increase'] = result_df['ADX'] > result_df['ADX'].shift(1)
    result_df['+DI_greater_than_-DI'] = result_df['+DI'] > result_df['-DI']
    result_df['ADX_less_than_50'] = result_df['ADX'] < 50
    result_df['Volume_increase'] = df['Volume'] > 2 * df['Volume'].shift(1)
    result_df['Volume_1000'] = df['Volume'] / 1000 
    result_df['Close_less_than_200'] = df['Close']
    result_df['Close_greater_than_SMA20'] = df['Close'] > sma_20  # 收盤價是否大於20日均線
    result_df['RSI_14_greater_than_50'] = rsi_14 > 50  # 14日RSI是否大於50
    result_df['RSI_5_greater_than_RSI_10'] = rsi_5 > rsi_10  # 5日RSI是否大於10日RSI
    result_df['+RSI_5_increase'] = result_df['RSI_5'] > result_df['RSI_5'].shift(1)  # 5日RSI是否大於昨日5日RSI
    result_df['+RSI_10_increase'] = result_df['RSI_10'] > result_df['RSI_10'].shift(1)  # 10日RSI是否大於昨日10日RSI
    result_df['RSI_Pre_Gold_Cross'] = (result_df['RSI_5'] > result_df['RSI_10']) & (result_df['RSI_5'].shift(1) < result_df['RSI_10'].shift(1))  # 5日RSI是否大於10日RSI且昨日5日RSI小於昨日10日RSI

    result_df['Bullish_MA'] = (df['SMA_5'] > df['SMA_10']) & (df['SMA_5'] > df['SMA_20']) & (df['SMA_5'] > df['SMA_20']) & (df['SMA_10'] > df['SMA_20']) & (df['SMA_10'] > df['SMA_60']) & (df['SMA_20'] > df['SMA_60'])  # 判斷是否呈現均線多頭排列

    result_df['red'] = df['Close'] > df['Open']  # 判斷當日K線是否紅K

    # 檢查最後一個日期是否符合規則
    if not result_df.empty:
        last_row = result_df.iloc[-1]
        if last_row['+DI_increase'] and last_row['-DI_decrease'] and last_row['ADX_increase'] and last_row['+DI_greater_than_-DI'] and last_row['ADX_less_than_50'] and last_row['Volume_increase'] and last_row['Volume_1000'] > 1000 and last_row['Close_less_than_200'] < 200 and last_row['Close_greater_than_SMA20'] and last_row['RSI_14_greater_than_50'] and last_row['Bullish_MA'] and last_row['red']:
            return True, recommendation_mean, recommendationKey, stock_name, industry
        else:
            return False, recommendation_mean, recommendationKey, stock_name, industry
    else:
        return False, recommendation_mean, recommendationKey, stock_name, industry

def get_matched_stocks(stock_codes):
    matched_stocks = []
    count = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(analyze_stock, stock_code, stock_name, industry): (stock_code, stock_name, industry) for stock_code, stock_name, industry in stock_codes}
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), ncols=70):
            stock_code, stock_name, industry = futures[future]
            try:
                time.sleep(0.1)  # 延遲 100 毫秒
                match, recommendation_mean, recommendationKey, stock_name, industry = future.result()
                if match:
                    count += 1
                    print(f' 股票代號 : {stock_code} 今天符合規則.')
                    matched_stocks.append((stock_code, stock_name, industry, recommendation_mean, recommendationKey))
            except Exception as exc:
                print(f'{stock_code} generated an exception: {exc}')
    return matched_stocks, count

def format_matched_stocks(matched_stocks):
    industry_stocks = defaultdict(list)
    for code, name, industry, recommendation_mean, recommendationKey in matched_stocks:
        code = code.split('.')[0]  # 只保留 "." 前面的部分
        if recommendation_mean == "-":
            industry_stocks[industry].append(f'{code}({name})')
        else:
            industry_stocks[industry].append(f'{code}({name}) ({recommendation_mean})({recommendationKey})')

    matched_stocks_str = ''
    for industry, stocks in industry_stocks.items():
        matched_stocks_str += f'* {industry}\n'
        matched_stocks_str += ',\n'.join(stocks) 
        matched_stocks_str += '\n'
    return matched_stocks_str

def send_line_notify(notification_message, stickerPackageId, stickerId):
    headers = {'Authorization': f'Bearer {LINE_NOTIFY_TOKEN}'}
    data = {
        'message': notification_message,
        'stickerPackageId': stickerPackageId,
        'stickerId': stickerId
    }
    requests.post(LINE_NOTIFY_API, headers=headers, data=data)

def main():
    stock_codes = get_stock_codes()
    matched_stocks, count = get_matched_stocks(stock_codes)
    matched_stocks_str = format_matched_stocks(matched_stocks)

    msg = f'發送時間 : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
    msg += '''
選股策略如下 : 
1. DMI(+-+), ADX<50
2. 成交量>昨日*2, >1000張
3. 股價<200, >20日均線
4. 14日RSI > 50
5. 5,10,20,60日均線多頭排列
6. 紅K棒
    '''
    msg += f'\n{matched_stocks_str} 共 {count} 檔'
    print(msg)

    send_line_notify(msg, "6632", "11825376")

if __name__ == "__main__":
    main()