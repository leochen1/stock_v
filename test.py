import twstock
import pandas as pd
import time

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
stock.fetch_from(2025, 1)  # 2000 年 1 月至今
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
    latest_price = realtime['realtime']['latest_trade_price']
    print(f"即時收盤價：{latest_price}")
else:
    print("即時資料獲取失敗")

# 合併資料
df_historical['即時價'] = latest_price
print(df_historical.tail())