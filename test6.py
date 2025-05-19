import time
import requests
import pandas as pd
from datetime import datetime
import os
import urllib3
from io import StringIO
from tqdm import tqdm
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

DATA_DIR = "data/tpex_history"
os.makedirs(DATA_DIR, exist_ok=True)

def get_company_info_data(url):
    res = requests.get(url, verify=False)
    if res.status_code != 200:
        raise Exception(f"HTTP error: {res.status_code}")
    tables = pd.read_html(StringIO(res.text))
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

def fetch_tpex_daily_data(stock_no, date, max_retry=3, sleep_sec=2):
    date_str = date.strftime("%Y/%m/%d")
    url = f"https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={date_str}&se=EW"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    for attempt in range(max_retry):
        try:
            response = requests.get(url, headers=headers, verify=False, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'tables' in data and data['tables']:
                table = data['tables'][0]
                fields = table['fields']
                rows = table['data']
                df = pd.DataFrame(rows, columns=fields)
                df['代號'] = df['代號'].astype(str).str.strip()
                stock_no = str(stock_no).strip()
                df = df[df['代號'] == stock_no]
                if df.empty:
                    return None
                df['日期'] = date.strftime("%Y-%m-%d")  # 確保日期正確加入
                return df
            return None
        except Exception as e:
            print(f"爬取股票 {stock_no} 在 {date_str} 資料時發生錯誤: {e} (第{attempt+1}次)")
            time.sleep(sleep_sec)
    return None

def fetch_and_save_history(stock_no, start_date=datetime(2024, 1, 1)):
    """下載並儲存歷史資料（只需執行一次，或定期更新）"""
    today = datetime.today()
    all_data = []
    date = start_date
    while date <= today:
        df = fetch_tpex_daily_data(stock_no, date)
        if df is not None and not df.empty:
            all_data.append(df)
        date += pd.Timedelta(days=1)
    if all_data:
        df_all = pd.concat(all_data, ignore_index=True)
        df_all = df_all.drop_duplicates(subset=['日期'])  # 確保日期唯一
        csv_path = f"{DATA_DIR}/{stock_no}.csv"
        df_all.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"{stock_no} 歷史資料已儲存到 {csv_path}")
        return True
    else:
        print(f"{stock_no} 無法取得任何歷史資料。")
        return False

def update_history_all(stock_codes):
    """批次讀取本地歷史資料，補最新資料"""
    for code, name, industry in tqdm(stock_codes, desc="更新歷史資料"):
        csv_path = f"{DATA_DIR}/{code}.csv"
        if not os.path.exists(csv_path):
            print(f"{code} 無歷史資料，開始下載...")
            fetch_and_save_history(code)
        try:
            df = pd.read_csv(csv_path, dtype=str)
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
            else:
                print(f"{code} 歷史資料缺少日期欄位。")
                continue
            last_date = df['日期'].max()
            today = pd.Timestamp(datetime.now().date())
            if last_date >= today:
                continue
            # 補今日資料
            new_df = fetch_tpex_daily_data(code, today)
            if new_df is not None and not new_df.empty:
                new_df['日期'] = pd.to_datetime(new_df['日期'])
                df = pd.concat([df, new_df], ignore_index=True)
                df = df.drop_duplicates(subset=['日期'])
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        except Exception as e:
            print(f"{code}: 更新歷史資料失敗 - {e}")

# 範例：批次下載所有上櫃公司歷史資料並補今日資料
if __name__ == "__main__":
    stock_codes = get_stock_codes()
    # 下載歷史資料（如已下載可註解）
    for code, name, industry in tqdm(stock_codes, desc="下載歷史資料"):
        fetch_and_save_history(code, start_date=datetime(2025, 5, 1))
        # break  # 測試單檔可加 break
    # 補今日資料
    update_history_all(stock_codes)