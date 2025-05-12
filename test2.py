import twstock
import pandas as pd
import time
from datetime import datetime

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

# 獲取台積電歷史資料
stock = twstock.Stock('2330')
stock.fetch_from(2025, 1)
df_historical = pd.DataFrame({
    '日期': stock.date,
    '開盤價': stock.open,
    '最高價': stock.high,
    '最低價': stock.low,
    '收盤價': stock.price,
    '成交量': stock.capacity
})

# 獲取即時資料
realtime = twstock.realtime.get('2330')
if realtime['success']:
    rt = realtime['realtime']
    # 正確取得日期字串：在 info 裡的 time
    time_str = realtime['info']['time']  # 格式: '2025-05-09 13:30:00'
    today_str = time_str.split(' ')[0]   # 只取 '2025-05-09'
    # 轉換資料型態
    open_price = float(rt['open']) if rt['open'] else None
    high_price = float(rt['high']) if rt['high'] else None
    low_price = float(rt['low']) if rt['low'] else None
    close_price = float(rt['latest_trade_price']) if rt['latest_trade_price'] else None
    volume = int(realtime['成交量']) if '成交量' in realtime and realtime['成交量'] else 0

    # 檢查今天是否已存在於歷史資料
    if not (df_historical['日期'] == today_str).any():
        # 新增今天的一筆資料
        new_row = {
            '日期': today_str,
            '開盤價': open_price,
            '最高價': high_price,
            '最低價': low_price,
            '收盤價': close_price,
            '成交量': volume
        }
        df_historical = pd.concat([df_historical, pd.DataFrame([new_row])], ignore_index=True)
    print(df_historical.tail())
else:
    print("即時資料獲取失敗")