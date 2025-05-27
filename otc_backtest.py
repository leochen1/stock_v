import os
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = "data/tpex_history"
OTC_DIR = "otc_output"
HOLDING_DAYS = 5  # 可自行調整

def load_stock_data(stock_code):
    file_path = os.path.join(DATA_DIR, f"{stock_code}.csv")
    if not os.path.exists(file_path):
        return None
    try:
        df = pd.read_csv(file_path, parse_dates=["日期"])
        df = df.sort_values("日期")
        return df
    except Exception:
        return None

def calculate_performance(stock_code, start_date, holding_days):
    df = load_stock_data(stock_code)
    if df is None:
        return None
    start_row = df[df["日期"] == start_date]
    if start_row.empty:
        return None
    start_price = start_row.iloc[0]["收盤價"]
    end_date = start_date + timedelta(days=holding_days)
    end_row = df[df["日期"] >= end_date]
    if end_row.empty:
        return None
    end_price = end_row.iloc[0]["收盤價"]
    return (end_price - start_price) / start_price

def backtest_all(otc_dir, holding_days):
    files = sorted([f for f in os.listdir(otc_dir) if f.startswith("otc_") and f.endswith(".txt")])
    all_results = []
    for fname in files:
        date_str = fname.split("_")[-1].replace(".txt", "")
        try:
            start_date = pd.to_datetime(date_str, format="%Y%m%d")
        except Exception:
            continue
        # 跳過未來的檔案
        if start_date + timedelta(days=holding_days) > datetime.now():
            continue
        with open(os.path.join(otc_dir, fname), "r", encoding="utf-8") as f:
            stock_list = [line.strip() for line in f if line.strip()]
        results = []
        for stock_code in stock_list:
            code = stock_code.replace(".TW", "")
            perf = calculate_performance(code, start_date, holding_days)
            if perf is not None:
                results.append(perf)
        if results:
            win_rate = sum(1 for r in results if r > 0) / len(results)
            print(f"{fname} 持有 {holding_days} 天勝率: {win_rate:.2%} (樣本數: {len(results)})")
            all_results.append(win_rate)
        else:
            print(f"{fname} 無法計算績效")
    if all_results:
        print(f"\n所有檔案平均勝率: {sum(all_results)/len(all_results):.2%}")
    else:
        print("沒有任何可計算績效的檔案")

if __name__ == "__main__":
    backtest_all(OTC_DIR, HOLDING_DAYS)