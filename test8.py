import requests
import pandas as pd
from datetime import datetime, timedelta
import os
import urllib3
import time
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = "data/tpex_history"
os.makedirs(DATA_DIR, exist_ok=True)

def get_company_info_data(url):
    res = requests.get(url, verify=False)
    if res.status_code != 200:
        raise Exception(f"HTTP error: {res.status_code}")
    tables = pd.read_html(res.text)
    if not tables:
        raise Exception("No tables found in HTML.")
    df = tables[0]
    df.columns = df.iloc[0]
    df = df.iloc[1:]
    df = df[['有價證券代號', '有價證券名稱', '產業別']]
    df = df.dropna()
    return df

def get_stock_codes():
    try:
        df2 = get_company_info_data("https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=2&issuetype=4&industry_code=&Page=1&chklike=Y")
        stock_codes_2 = df2.apply(lambda x: (x['有價證券代號'], x['有價證券名稱'], x['產業別']), axis=1).tolist()
        stock_codes = stock_codes_2
        print(f"共取得 {len(stock_codes)} 檔上櫃股票")
        return stock_codes
    except Exception as e:
        print(str(e))
        return []

def fetch_tpex_by_date(date_str):
    url = "https://www.tpex.org.tw/www/zh-tw/afterTrading/dailyQuotes"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    data = {
        'date': date_str
    }
    response = requests.post(url, headers=headers, data=data, verify=False, timeout=20)
    response.raise_for_status()
    data = response.json()
    if 'tables' in data and data['tables']:
        table = data['tables'][0]
        fields = table['fields']
        rows = table['data']
        df = pd.DataFrame(rows, columns=fields)
        return df
    return None

def append_to_stock_csv(stock_code, row):
    csv_path = os.path.join(DATA_DIR, f"{stock_code}.csv")
    columns = ["日期", "開盤價", "最高價", "最低價", "收盤價", "成交量"]
    row_df = pd.DataFrame([row], columns=columns)
    try:
        if os.path.exists(csv_path):
            old_df = pd.read_csv(csv_path, encoding="utf-8-sig")
            # 移除同日期的舊資料，再加入新資料
            old_df = old_df[old_df["日期"] != row["日期"]]
            combined = pd.concat([old_df, row_df], ignore_index=True)
            combined = combined.sort_values("日期")
            combined.to_csv(csv_path, index=False, encoding="utf-8-sig")
        else:
            row_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    except PermissionError:
        print(f"檔案被佔用，無法寫入：{csv_path}，請關閉該檔案後再試。")

if __name__ == "__main__":
    stock_list = get_stock_codes()
    stock_code_set = set([code for code, name, industry in stock_list])
    start_date = datetime(2023, 3, 1)
    end_date = datetime.today()
    delta = timedelta(days=1)

    while start_date <= end_date:
        date_str = start_date.strftime("%Y/%m/%d")
        print(f"抓取 {date_str} ...")
        try:
            df_all = fetch_tpex_by_date(date_str)
            if df_all is not None and not df_all.empty:
                for idx, row in df_all.iterrows():
                    code = row['代號']
                    if code in stock_code_set:
                        row_data = {
                            "日期": date_str,
                            "開盤價": row.get("開盤", ""),
                            "最高價": row.get("最高", ""),
                            "最低價": row.get("最低", ""),
                            "收盤價": row.get("收盤", ""),
                            "成交量": row.get("成交股數", "").replace(",", "")
                        }
                        append_to_stock_csv(code, row_data)
            else:
                print(f"{date_str} 無資料")
        except Exception as e:
            print(f"{date_str} 發生錯誤: {e}")
        # 建議加上延遲，避免被官方封鎖
        time.sleep(0.1)
        start_date += delta

    print("歷史資料下載完成。")