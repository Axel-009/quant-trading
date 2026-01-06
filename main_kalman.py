import pandas as pd
import yfinance as yf
from strategies.kalman_pair_strategy import KalmanPairStrategy

def main():
    # 1. Fetch Pair Data (e.g., Gold (GLD) and Gold Miners (GDX))
    asset_x = "GDX" # Independent
    asset_y = "GLD" # Dependent
    print(f"Fetching data for {asset_x} and {asset_y}...")
    
    start_date = "2020-01-01"
    end_date = "2023-01-01"
    
    df_x = yf.download(asset_x, start=start_date, end=end_date, progress=False)['Close']
    df_y = yf.download(asset_y, start=start_date, end=end_date, progress=False)['Close']
    
    # Merge into one DataFrame
    df = pd.DataFrame({asset_x: df_x, asset_y: df_y})
    
    # Handle multi-index if yfinance returns it
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Drop NaNs
    df.dropna(inplace=True)
    
    # Hack: The Backtester expects a 'Close' column for market return calculation. 
    # For a pair, 'Close' is the PnL of the portfolio, but for simplicity here,
    # we will just map the PnL logic inside the strategy or pass a dummy 'Close'.
    # A cleaner way for the base class is to define 'Close' as the spread value or Y asset.
    # Let's use Asset Y as the primary 'Close' proxy for base metrics, 
    # but the specific PnL is handled in the strategy logic usually.
    # For this simplified architecture, we set 'Close' to Asset Y to allow the base class to run without errors.
    df['Close'] = df[asset_y]

    # 2. Instantiate Strategy
    # We want to see if the spread reverts.
    kalman = KalmanPairStrategy(
        symbol=f"{asset_y}/{asset_x}", 
        data=df, 
        asset_x=asset_x, 
        asset_y=asset_y,
        entry_z=1.5,
        exit_z=0.0,
        tc=0.001
    )

    # 3. Run Engine
    print("Running Kalman Filter Backtest...")
    kalman.run_backtest()

    # 4. Print Metrics
    metrics = kalman.get_performance_metrics()
    print("\n" + "="*40)
    print(f" KALMAN PAIR STRATEGY: {asset_y} vs {asset_x}")
    print("="*40)
    for k, v in metrics.items():
        print(f"{k:<20}: {v}")
    print("="*40)

    # 5. Plot
    kalman.plot_results()

if __name__ == "__main__":
    main()
