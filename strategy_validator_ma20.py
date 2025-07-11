import pandas as pd
import talib
import glob
import os

# Validation Strategy A: Price is simply above MA20
def validate_ma20(df):
    if len(df) < 21:
        return False

    df['MA20'] = talib.SMA(df['Close'], timeperiod=20)
    latest = df.iloc[-1]

    if pd.isna(latest['MA20']):
        return False

    return latest['Close'] > latest['MA20']

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

        if validate_ma20(df):
            stock_id = os.path.basename(file_path).replace('.csv', '')
            selected_stocks.append(stock_id)

    except Exception as e:
        continue

output_file = 'out_validator_ma20.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    if selected_stocks:
        f.write('\n'.join(selected_stocks))
    else:
        f.write('Validation Failed: No stocks found above MA20.')

print(f"Validation A (Above MA20) Complete. Found {len(selected_stocks)} stocks. Results in {output_file}")
