import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = "data/history"
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_otc_daily_history(stock_code, start_date, end_date):
    date = start_date
    all_data = []
    while date <= end_date:
        ymd = date.strftime("%Y/%m/%d")
        url = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={ymd}&se=EW&s={stock_code}"
        for attempt in range(3):
            try:
                res = requests.get(url, verify=False, timeout=10)
                res.encoding = 'utf-8'
                json_data = res.json()
                if json_data.get("aaData"):
                    df = pd.DataFrame(json_data["aaData"])
                    all_data.append(df)
                    print(f"{stock_code} {ymd}: 下載成功")
                else:
                    print(f"{stock_code} {ymd}: 沒有資料")
                break  # 成功或沒資料都跳出 retry
            except Exception as e:
                print(f"{stock_code} {ymd}: 下載失敗 - {e} (第{attempt+1}次)")
                time.sleep(3)
        date += timedelta(days=1)
        time.sleep(2)  # 每天間隔2秒，避免被擋
    if all_data:
        result = pd.concat(all_data, ignore_index=True)
        result.to_csv(f"{DATA_DIR}/{stock_code}_otc_daily.csv", index=False, encoding="utf-8-sig")
        print(f"已儲存 {stock_code} 歷史資料到 {DATA_DIR}/{stock_code}_otc_daily.csv")

# 用法
fetch_otc_daily_history("8111", datetime(2024, 5, 5), datetime(2024, 5, 9))

# https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw