

import pandas as pd
import talib
import glob
import os
from tqdm import tqdm

# --- Strategy Definition (remains the same) ---
def check_buy_signal(df, index):
    if index < 21 or index >= len(df) - 1:
        return False

    current_slice = df.iloc[:index + 1]
    close_prices = current_slice['Close']
    volumes = current_slice['Volume']
    
    ma20 = talib.SMA(close_prices, timeperiod=20).iloc[-1]
    prev_ma20 = talib.SMA(close_prices, timeperiod=20).iloc[-2]
    volume_ma20 = talib.SMA(volumes, timeperiod=20).iloc[-1]
    rsi14 = talib.RSI(close_prices, timeperiod=14).iloc[-1]

    latest = df.iloc[index]
    previous = df.iloc[index - 1]

    condition1 = latest['Close'] > ma20 and previous['Close'] < prev_ma20
    condition2 = latest['Volume'] > volume_ma20 * 1.5
    condition3 = rsi14 < 70

    return condition1 and condition2 and condition3

# --- Backtesting Function for a given holding period ---
def run_backtest(all_files, holding_period, column_mapping):
    trade_log = []
    for file_path in tqdm(all_files, desc=f"Testing HP={holding_period}"):
        try:
            stock_id = os.path.basename(file_path).replace('.csv', '')
            df = pd.read_csv(file_path)
            df.rename(columns=column_mapping, inplace=True)

            if not all(col in df.columns for col in ['Date', 'Open', 'Close', 'Volume']):
                continue

            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date').reset_index(drop=True)
            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)

            if len(df) < 21 + holding_period:
                continue

            for i in range(20, len(df) - holding_period - 1):
                if check_buy_signal(df, i):
                    buy_day_index = i + 1
                    sell_day_index = buy_day_index + holding_period

                    buy_price = df.loc[buy_day_index, 'Open']
                    sell_price = df.loc[sell_day_index, 'Open']

                    if pd.isna(buy_price) or pd.isna(sell_price) or buy_price == 0:
                        continue

                    pct_change = (sell_price - buy_price) / buy_price
                    trade_log.append({'PnL_pct': pct_change})

        except Exception as e:
            continue
    return trade_log

# --- Main Execution ---
twse_files = glob.glob('data/history/*.csv')
tpex_files = glob.glob('data/tpex_history/*.csv')
all_files = twse_files + tpex_files

column_mapping = {
    '日期': 'Date', '開盤價': 'Open', '最高價': 'High', '最低價': 'Low', '收盤價': 'Close', '成交量': 'Volume'
}

HOLDING_PERIODS_TO_TEST = [3, 5, 10, 20]

print("--- Backtest Performance Report (Optimized Holding Periods) ---")
print(f"Strategy: MA20 Golden Cross + Volume Surge + RSI < 70")
print("=============================================================")

for hp in HOLDING_PERIODS_TO_TEST:
    trade_log = run_backtest(all_files, hp, column_mapping)

    if not trade_log:
        print(f"\n--- Holding Period: {hp} trading days ---")
        print("No trades were executed.")
        continue

    log_df = pd.DataFrame(trade_log)
    total_trades = len(log_df)
    winning_trades = log_df[log_df['PnL_pct'] > 0]
    losing_trades = log_df[log_df['PnL_pct'] <= 0]

    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    avg_pl = log_df['PnL_pct'].mean() * 100
    avg_win = winning_trades['PnL_pct'].mean() * 100 if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['PnL_pct'].mean() * 100 if len(losing_trades) > 0 else 0
    profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')

    print(f"\n--- Holding Period: {hp} trading days ---")
    print(f"Total Trades:         {total_trades}")
    print(f"Win Rate:             {win_rate:.2f}%")
    print(f"Avg. P/L per Trade:   {avg_pl:.2f}%")
    print(f"Avg. Win:             {avg_win:.2f}%")
    print(f"Avg. Loss:            {avg_loss:.2f}%")
    print(f"Profit/Loss Ratio:    {profit_loss_ratio:.2f}")
    print("-------------------------------------")

print("\nOptimization analysis complete.")

