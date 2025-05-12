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
from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

# 建立忽略 SSL 驗證的 Session
session = requests.Session()
session.verify = False

# 替換成你的 Channel access token
YOUR_CHANNEL_ACCESS_TOKEN = 'aR3GEe7B4hzK58ir/halgz4d58ZArkeXBa5XXK6BBBvIgqkgCq7unGsRK3r1nHK8a9qHQTGynl2QDrcJ+CqAov/iafn6ic9rldDQMkKuRZocElxMRK3wcju7Bp8lEnRo8CHr448jEqZDI97ovWJS4gdB04t89/1O/w1cDnyilFU='

# 替換成接收訊息的 User ID、Group ID 或 Room ID
TARGET_ID = 'Ue29e2eb096538c363367923715c6d0da'

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)

def get_company_info_data(url):
    res = requests.get(url, verify=False)
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
        stock_codes_1 = df1.apply(lambda x: (x['有價證券代號']+'.TW', x['有價證券名稱'], x['產業別']), axis=1).tolist()
        stock_codes_2 = df2.apply(lambda x: (x['有價證券代號']+'.TWO', x['有價證券名稱'], x['產業別']), axis=1).tolist()
        stock_codes = stock_codes_1 + stock_codes_2
        return stock_codes
    except Exception as e:
        print(str(e))
        return str(e)

def analyze_stock(stock_code, stock_name, industry):
    try:
        # df = yf.Ticker(stock_code).history(period='max')
        
        ticker = yf.Ticker(stock_code, session=session)
        # 檢查基本信息
        info = ticker.info
        print(f"{stock_code} 的基本信息: {info}")

        df = ticker.history(period='max')
        print(df)

        if df is None or df.empty:
            print(f"{stock_code}: 無法獲取數據，可能已退市或代碼無效。")
            return False, '-', '-', stock_name, industry
    except Exception as e:
        print(f"{stock_code}: 發生錯誤 - {e}")
        return False, '-', '-', stock_name, industry
    
    df_info = yf.Ticker(stock_code).info
    recommendation_mean = df_info.get('recommendationMean', '-')
    recommendationKey = df_info.get('recommendationKey', '-')

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
    adx_result = talib.ADX(df.High, df.Low, df.Close, timeperiod = 14)

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

    df_monthly = df.resample('M').agg({
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

    result_df['RSI_5'] = rsi_5
    result_df['RSI_10'] = rsi_10
    result_df['+DI_increase'] = result_df['+DI'] > result_df['+DI'].shift(1)
    result_df['-DI_decrease'] = result_df['-DI'] < result_df['-DI'].shift(1)
    result_df['ADX_less_than_50'] = result_df['ADX'] < 50
    result_df['Volume_increase'] = df['Volume'] > 2 * df['Volume'].shift(1)
    result_df['Volume_1000'] = df['Volume'] / 1000
    result_df['Close_less_than_200'] = df['Close']
    result_df['Close_greater_than_SMA20'] = df['Close'] > sma_20
    result_df['RSI_14_greater_than_50'] = rsi_14 > 50
    result_df['RSI_5_greater_than_RSI_10'] = rsi_5 > rsi_10
    result_df['+RSI_5_increase'] = result_df['RSI_5'] > result_df['RSI_5'].shift(1)
    result_df['+RSI_10_increase'] = result_df['RSI_10'] > result_df['RSI_10'].shift(1)
    result_df['RSI_Pre_Gold_Cross'] = (result_df['RSI_5'] > result_df['RSI_10']) & (result_df['RSI_5'].shift(1) < result_df['RSI_10'].shift(1))
    result_df['Bullish_MA'] = (df['SMA_5'] > df['SMA_10']) & (df['SMA_5'] > df['SMA_20']) & (df['SMA_5'] > df['SMA_20']) & (df['SMA_10'] > df['SMA_20']) & (df['SMA_10'] > df['SMA_60']) & (df['SMA_20'] > df['SMA_60'])
    result_df['red'] = df['Close'] > df['Open']

    if not result_df.empty:
        last_row = result_df.iloc[-1]
        last_row_weekly = result_df_weekly.iloc[-1]
        last_row_monthly = result_df_monthly.iloc[-1]
        if (last_row['ADX_increase'] and last_row['+DI_greater_than_-DI'] and
           last_row_weekly['ADX_increase_weekly'] and last_row_weekly['+DI_greater_than_-DI_weekly'] and
           last_row_monthly['ADX_increase_monthly'] and last_row_monthly['+DI_greater_than_-DI_monthly'] and
           last_row['Volume_1000'] > 100
        ):
            return True, recommendation_mean, recommendationKey, stock_name, industry
        else:
            return False, recommendation_mean, recommendationKey, stock_name, industry
    else:
        return False, recommendation_mean, recommendationKey, stock_name, industry

# ====== 這裡開始是分批處理的重點修改 ======
def get_matched_stocks(stock_codes, batch_size=50):
    matched_stocks = []
    count = 0
    for i in range(0, len(stock_codes), batch_size):
        batch = stock_codes[i:i + batch_size]
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = {executor.submit(analyze_stock, stock_code, stock_name, industry): (stock_code, stock_name, industry) for stock_code, stock_name, industry in batch}
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), ncols=70):
                stock_code, stock_name, industry = futures[future]
                try:
                    time.sleep(1)  # 每支股票延遲 1 秒
                    match, recommendation_mean, recommendationKey, stock_name, industry = future.result()
                    if match:
                        count += 1
                        print(f' 股票代號 : {stock_code} 今天符合規則.')
                        matched_stocks.append((stock_code, stock_name, industry, recommendation_mean, recommendationKey))
                except Exception as exc:
                    print(f'{stock_code} generated an exception: {exc}')
    return matched_stocks, count
# ====== 分批處理結束 ======

def format_matched_stocks(matched_stocks):
    industry_stocks = defaultdict(list)
    for code, name, industry, recommendation_mean, recommendationKey in matched_stocks:
        code = code.split('.')[0]
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

def send_text_message(target_id, message):
    try:
        line_bot_api.push_message(
            target_id,
            TextSendMessage(text=message)
        )
        print(f"成功向 {target_id} 發送訊息: {message}")
    except LineBotApiError as e:
        print(f"發送訊息失敗: {e}")

def main():
    stock_codes = get_stock_codes()
    matched_stocks, count = get_matched_stocks(stock_codes)
    matched_stocks_str = format_matched_stocks(matched_stocks)

    msg = f'發送時間 : {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n'
    msg += '''
選股策略如下 : 
1. 日,週,月 DI+ > DI-
2. 日,週,月 ADX 紅色
    '''
    msg += f'\n{matched_stocks_str} 共 {count} 檔'
    print(msg)

    send_text_message(TARGET_ID, msg)

if __name__ == "__main__":
    main()