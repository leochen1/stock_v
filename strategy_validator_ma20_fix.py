import pandas as pd
import talib
import glob
import os

# Validation Strategy A: Price is simply above MA20 (with column name fix)
def validate_ma20(df):
    if len(df) < 21:
        return False

    # Use the correct English column name 'Close' which we have mapped
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

# Define the column name mapping
column_mapping = {
    '日期': 'Date',
    '開盤價': 'Open',
    '最高價': 'High',
    '最低價': 'Low',
    '收盤價': 'Close',
    '成交量': 'Volume'
}

for file_path in all_files:
    try:
        df = pd.read_csv(file_path)
        
        # --- FIX: Rename columns ---
        df.rename(columns=column_mapping, inplace=True)

        # Standard pre-processing
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
        if 'Turnover' in df.columns and 'Volume' not in df.columns:
            df.rename(columns={'Turnover': 'Volume'}, inplace=True)
        if 'Trading_Volume' in df.columns and 'Volume' not in df.columns:
            df.rename(columns={'Trading_Volume': 'Volume'}, inplace=True)
        
        # Ensure required columns exist after renaming
        if 'Close' not in df.columns:
            continue

        if validate_ma20(df):
            stock_id = os.path.basename(file_path).replace('.csv', '')
            selected_stocks.append(stock_id)

    except Exception as e:
        # print(f"Error processing {file_path}: {e}")
        continue

output_file = 'out_validator_ma20_fix.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    if selected_stocks:
        f.write('\n'.join(selected_stocks))
    else:
        f.write('Validation Failed even after fix. Check data integrity.')

print(f"Validation A (FIXED) Complete. Found {len(selected_stocks)} stocks. Results in {output_file}")
