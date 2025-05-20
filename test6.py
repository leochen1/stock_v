import requests
import pandas as pd
from datetime import datetime
import os
import urllib3
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

def fetch_all_tpex_today():
    url = "https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, verify=False, timeout=10)
    response.raise_for_status()
    data = response.json()
    if 'tables' in data and data['tables']:
        table = data['tables'][0]
        fields = table['fields']
        rows = table['data']
        df = pd.DataFrame(rows, columns=fields)
        return df
    return None

def save_today_data(df):
    today_str = datetime.today().strftime("%Y%m%d")
    csv_path = f"{DATA_DIR}/tpex_{today_str}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"今日上櫃股票資料已儲存到 {csv_path}")

if __name__ == "__main__":
    stock_list = get_stock_codes()
    stock_code_set = set([code for code, name, industry in stock_list])
    df_all = fetch_all_tpex_today()
    if df_all is not None and not df_all.empty:
        df_filtered = df_all[df_all['代號'].isin(stock_code_set)].copy()
        # 合併名稱與產業別
        code2info = {code: (name, industry) for code, name, industry in stock_list}
        df_filtered['股票名稱'] = df_filtered['代號'].map(lambda x: code2info[x][0] if x in code2info else "")
        df_filtered['產業別'] = df_filtered['代號'].map(lambda x: code2info[x][1] if x in code2info else "")
        df_filtered['日期'] = datetime.today().strftime("%Y-%m-%d")
        save_today_data(df_filtered)
    else:
        print("無法取得今日上櫃股票資料。")