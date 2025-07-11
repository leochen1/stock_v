import pandas as pd
import talib
import glob
import os

# Strategy: Support on 60-day Moving Average (Quarterly Line)
def apply_ma60_strategy(df):
    if len(df) < 65: # Need enough data for MA60 and lookback
        return False

    df['MA60'] = talib.SMA(df['Close'], timeperiod=60)
    df['Low_5D'] = df['Low'].rolling(window=5).min()

    latest = df.iloc[-1]

    if pd.isna(latest['MA60']) or pd.isna(latest['Low_5D']):
        return False

    # Conditions
    is_near_ma60 = abs(latest['Close'] - latest['MA60']) / latest['MA60'] < 0.03 # Close is within 3% of MA60
    tested_ma60 = latest['Low_5D'] < latest['MA60'] # Price dipped below MA60 recently
    rebounded = latest['Close'] > latest['MA60'] # Price has rebounded above MA60

    return is_near_ma60 and tested_ma60 and rebounded

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
        if not all(col in df.columns for col in ['Close', 'Low']):
            continue

        if apply_ma60_strategy(df):
            stock_id = os.path.basename(file_path).replace('.csv', '')
            selected_stocks.append(stock_id)

    except Exception as e:
        continue

output_file = 'out_ma60.txt'
with open(output_file, 'w') as f:
    if selected_stocks:
        f.write('\n'.join(selected_stocks))
    else:
        f.write('No stocks matched the MA60 support strategy today.')

print(f"Strategy 3 (MA60 Support) Complete. Found {len(selected_stocks)} stocks. Results in {output_file}")
