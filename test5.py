import requests
import pandas as pd
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_tpex_daily_data(stock_no, date):
    date_str = date.strftime("%Y/%m/%d")
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={date_str}&se=EW"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()
        print("JSON keys:", data.keys())
        if 'tables' in data and data['tables']:
            table = data['tables'][0]
            fields = table['fields']
            rows = table['data']
            df = pd.DataFrame(rows, columns=fields)
            df['代號'] = df['代號'].astype(str).str.strip()
            stock_no = str(stock_no).strip()
            df = df[df['代號'] == stock_no]
            if df.empty:
                print(f"{stock_no} 在 {date_str} 沒有資料。")
                return None
            return df
        print(f"{date_str} 沒有資料，或回傳資料格式不符預期。")
        return None
    except Exception as e:
        print(f"爬取股票 {stock_no} 在 {date_str} 資料時發生錯誤: {e}")
        return None

# 範例
stock_id = '6223'
query_date = datetime(2025, 5, 14)
df_daily = fetch_tpex_daily_data(stock_id, query_date)
if df_daily is not None:
    print(df_daily)