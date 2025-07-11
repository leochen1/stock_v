

import pandas as pd
import talib
import glob
import os
from tqdm import tqdm

# --- Strategy Definition ---
def check_buy_signal(df, index):
    if index < 21 or index >= len(df) - 1:
        return False

    # Use data up to the signal day `index`
    current_slice = df.iloc[:index + 1]
    
    # Calculate indicators on the slice
    close_prices = current_slice['Close']
    volumes = current_slice['Volume']
    
    ma20 = talib.SMA(close_prices, timeperiod=20).iloc[-1]
    prev_ma20 = talib.SMA(close_prices, timeperiod=20).iloc[-2]
    volume_ma20 = talib.SMA(volumes, timeperiod=20).iloc[-1]
    rsi14 = talib.RSI(close_prices, timeperiod=14).iloc[-1]

    # Get the latest two data points from the original df
    latest = df.iloc[index]
    previous = df.iloc[index - 1]

    # Strategy conditions
    condition1 = latest['Close'] > ma20 and previous['Close'] < prev_ma20
    condition2 = latest['Volume'] > volume_ma20 * 1.5
    condition3 = rsi14 < 70

    return condition1 and condition2 and condition3

# --- Main Backtesting Logic ---
twse_files = glob.glob('data/history/*.csv')
tpex_files = glob.glob('data/tpex_history/*.csv')
all_files = twse_files + tpex_files

trade_log = []
HOLDING_PERIOD = 5

column_mapping = {
    '日期': 'Date',
    '開盤價': 'Open',
    '最高價': 'High',
    '最低價': 'Low',
    '收盤價': 'Close',
    '成交量': 'Volume'
}

print("Starting backtest...")
for file_path in tqdm(all_files, desc="Processing stocks"):
    try:
        stock_id = os.path.basename(file_path).replace('.csv', '')
        df = pd.read_csv(file_path)
        df.rename(columns=column_mapping, inplace=True)

        if not all(col in df.columns for col in ['Date', 'Open', 'Close', 'Volume']):
            continue

        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)
        
        # Convert volume to numeric, coercing errors
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce').fillna(0)

        if len(df) < 21 + HOLDING_PERIOD:
            continue

        # Iterate through the history of the stock
        for i in range(20, len(df) - HOLDING_PERIOD - 1):
            # Check for buy signal on day `i`
            if check_buy_signal(df, i):
                buy_day_index = i + 1
                sell_day_index = buy_day_index + HOLDING_PERIOD

                buy_price = df.loc[buy_day_index, 'Open']
                sell_price = df.loc[sell_day_index, 'Open']

                # Ensure prices are valid numbers
                if pd.isna(buy_price) or pd.isna(sell_price) or buy_price == 0:
                    continue

                pct_change = (sell_price - buy_price) / buy_price
                
                trade_log.append({
                    'Stock': stock_id,
                    'Buy_Date': df.loc[buy_day_index, 'Date'],
                    'Buy_Price': buy_price,
                    'Sell_Date': df.loc[sell_day_index, 'Date'],
                    'Sell_Price': sell_price,
                    'PnL_pct': pct_change
                })

    except Exception as e:
        # print(f"Error processing {file_path}: {e}")
        continue

print("Backtest complete. Analyzing results...")

# --- Performance Analysis ---
if not trade_log:
    print("No trades were executed during the backtest period.")
else:
    log_df = pd.DataFrame(trade_log)
    log_df.to_csv('backtest_log.csv', index=False, encoding='utf-8-sig')

    total_trades = len(log_df)
    winning_trades = log_df[log_df['PnL_pct'] > 0]
    losing_trades = log_df[log_df['PnL_pct'] <= 0]

    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    avg_pl = log_df['PnL_pct'].mean() * 100
    avg_win = winning_trades['PnL_pct'].mean() * 100 if len(winning_trades) > 0 else 0
    avg_loss = losing_trades['PnL_pct'].mean() * 100 if len(losing_trades) > 0 else 0
    profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')

    print("\n--- Backtest Performance Report ---")
    print(f"Strategy: MA20 Golden Cross + Volume Surge + RSI < 70")
    print(f"Holding Period: {HOLDING_PERIOD} trading days")
    print("-------------------------------------")
    print(f"Total Trades:         {total_trades}")
    print(f"Win Rate:             {win_rate:.2f}%")
    print(f"Avg. P/L per Trade:   {avg_pl:.2f}%")
    print(f"Avg. Win:             {avg_win:.2f}%")
    print(f"Avg. Loss:            {avg_loss:.2f}%")
    print(f"Profit/Loss Ratio:    {profit_loss_ratio:.2f}")
    print("-------------------------------------")
    print("Detailed log saved to backtest_log.csv")

