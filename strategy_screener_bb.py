

import pandas as pd
import talib
import glob
import os

# Strategy: Bollinger Band Squeeze Breakout
def apply_bb_strategy(df):
    if len(df) < 30: # Need enough data for BBands and lookback
        return False

    upper, middle, lower = talib.BBANDS(df['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    df['BB_Width'] = (upper - lower) / middle

    # Lookback period for the squeeze
    lookback_period = 10
    if len(df) < lookback_period + 1:
        return False
        
    df['Min_BB_Width'] = df['BB_Width'].rolling(window=lookback_period).min()

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    if pd.isna(latest['BB_Width']) or pd.isna(previous['Min_BB_Width']):
        return False

    # Conditions
    is_squeezed = previous['BB_Width'] == previous['Min_BB_Width']
    is_breakout = latest['Close'] > upper.iloc[-1]

    return is_squeezed and is_breakout

# --- Main execution ---
twse_files = glob.glob('data/history/*.csv')
tpex_files = glob.glob('data/tpex_history/*.csv')
all_files = twse_files + tpex_files

selected_stocks = []

for file_path in all_files:
    try:
        df = pd.read_csv(file_path)
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
        if 'Turnover' in df.columns and 'Volume' not in df.columns:
            df.rename(columns={'Turnover': 'Volume'}, inplace=True)
        if 'Trading_Volume' in df.columns and 'Volume' not in df.columns:
            df.rename(columns={'Trading_Volume': 'Volume'}, inplace=True)
        if 'Close' not in df.columns:
            continue

        if apply_bb_strategy(df):
            stock_id = os.path.basename(file_path).replace('.csv', '')
            selected_stocks.append(stock_id)

    except Exception as e:
        continue

output_file = 'out_bb.txt'
with open(output_file, 'w') as f:
    if selected_stocks:
        f.write('\n'.join(selected_stocks))
    else:
        f.write('No stocks matched the Bollinger Band strategy today.')

print(f"Strategy 2 (Bollinger Bands) Complete. Found {len(selected_stocks)} stocks. Results in {output_file}")

