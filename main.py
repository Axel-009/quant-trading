# main.py

import pandas as pd
import yfinance as yf
from strategies.macd_strategy import MACDStrategy

def main():
    # 1. Fetch Data
    symbol = "AAPL"
    print(f"Fetching data for {symbol}...")
    df = yf.download(symbol, start="2020-01-01", end="2023-01-01", progress=False)
    
    # Check if data structure is multi-index (common with new yfinance) and flatten if needed
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. Instantiate Strategy
    # We add a transaction cost of 0.1% per trade (0.001) to be realistic
    macd = MACDStrategy(symbol, df, short_window=12, long_window=26, signal_window=9, tc=0.001)

    # 3. Run Engine
    print("Running Backtest...")
    macd.run_backtest()

    # 4. Print "Top 1%" Metrics
    metrics = macd.get_performance_metrics()
    print("\n" + "="*30)
    print(f" PERFORMANCE REPORT: {symbol}")
    print("="*30)
    for k, v in metrics.items():
        print(f"{k:<20}: {v}")
    print("="*30)

    # 5. Plot
    macd.plot_results()

if __name__ == "__main__":
    main()
