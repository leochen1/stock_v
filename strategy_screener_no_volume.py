import pandas as pd
import talib
import glob
import os

# Strategy: Price above MA20 and RSI < 80 (No Volume Filter)
def apply_no_volume_strategy(df):
    if len(df) < 21:
        return False

    df['MA20'] = talib.SMA(df['Close'], timeperiod=20)
    df['RSI14'] = talib.RSI(df['Close'], timeperiod=14)

    latest = df.iloc[-1]

    if pd.isna(latest['MA20']) or pd.isna(latest['RSI14']):
        return False

    condition1 = latest['Close'] > latest['MA20']
    condition2 = latest['RSI14'] < 80

    return condition1 and condition2

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

        if apply_no_volume_strategy(df):
            stock_id = os.path.basename(file_path).replace('.csv', '')
            selected_stocks.append(stock_id)

    except Exception as e:
        continue

output_file = 'out_no_volume.txt'
with open(output_file, 'w') as f:
    if selected_stocks:
        f.write('\n'.join(selected_stocks))
    else:
        f.write('No stocks matched the no-volume strategy today.')

print(f"Strategy 1 (No Volume) Complete. Found {len(selected_stocks)} stocks. Results in {output_file}")
