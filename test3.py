import twstock
import pandas as pd
import time
import os

# 解決 SSL 問題（臨時方案）
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

# 新增：讓 requests 忽略 SSL 驗證
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
old_request = requests.Session.request
def new_request(self, *args, **kwargs):
    kwargs['verify'] = False
    return old_request(self, *args, **kwargs)
requests.Session.request = new_request

DATA_DIR = "data/history"
os.makedirs(DATA_DIR, exist_ok=True)

def fetch_and_save_history(stock_code, max_retry=3):
    """下載並儲存歷史資料，失敗自動重試"""
    for attempt in range(max_retry):
        try:
            stock = twstock.Stock(stock_code)
            stock.fetch_from(2000, 1)
            if not stock.date or len(stock.date) < 60:
                print(f"{stock_code}: 無法獲取數據，可能已退市或代碼無效。")
                return False
            df = pd.DataFrame({
                '日期': stock.date,
                '開盤價': stock.open,
                '最高價': stock.high,
                '最低價': stock.low,
                '收盤價': stock.price,
                '成交量': stock.capacity
            })
            df = df.dropna()
            df.to_csv(f"{DATA_DIR}/{stock_code}.csv", index=False, encoding="utf-8-sig")
            print(f"{stock_code} 歷史資料已下載並儲存至 {DATA_DIR}/{stock_code}.csv")
            return True
        except Exception as e:
            print(f"{stock_code}: 下載歷史資料失敗 - {e} (第{attempt+1}次)")
            time.sleep(5)
    return False

if __name__ == "__main__":
    stock_code = input("請輸入股票代號：").strip()
    fetch_and_save_history(stock_code)