import pandas as pd
import talib
import glob
import os

# Define the strategy conditions
def apply_strategy(df):
    # Ensure the dataframe has enough data
    if len(df) < 21:
        return False

    # Calculate technical indicators
    df['MA20'] = talib.SMA(df['Close'], timeperiod=20)
    df['Volume_MA20'] = talib.SMA(df['Volume'], timeperiod=20)
    df['RSI14'] = talib.RSI(df['Close'], timeperiod=14)

    # Get the latest two data points
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    # Strategy conditions
    condition1 = latest['Close'] > latest['MA20'] and previous['Close'] < previous['MA20']  # Golden cross
    condition2 = latest['Volume'] > latest['Volume_MA20'] * 1.5  # Volume surge
    condition3 = latest['RSI14'] < 70  # Not overbought

    return condition1 and condition2 and condition3

# Get all stock data files
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

# Process each stock file
for file_path in all_files:
    try:
        # Read stock data
        df = pd.read_csv(file_path)
        
        # --- FIX: Rename columns ---
        df.rename(columns=column_mapping, inplace=True)

        # Pre-process data
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
        # Handle different column names for volume
        if 'Turnover' in df.columns and 'Volume' not in df.columns:
            df.rename(columns={'Turnover': 'Volume'}, inplace=True)
        if 'Trading_Volume' in df.columns and 'Volume' not in df.columns:
            df.rename(columns={'Trading_Volume': 'Volume'}, inplace=True)
        
        # Ensure required columns exist
        if not all(col in df.columns for col in ['Close', 'Volume', 'Low', 'High', 'Open']):
            # print(f"Skipping {file_path}: Missing one of the required columns.")
            continue

        # Apply the strategy
        if apply_strategy(df):
            stock_id = os.path.basename(file_path).replace('.csv', '')
            selected_stocks.append(stock_id)

    except Exception as e:
        # print(f"Error processing {file_path}: {e}")
        continue

# Output the results
output_file = 'out.txt'
with open(output_file, 'w') as f:
    if selected_stocks:
        f.write('\n'.join(selected_stocks))
    else:
        f.write('No stocks matched the strategy today.')

print(f"Screening complete. Found {len(selected_stocks)} stocks. Results are in {output_file}")
