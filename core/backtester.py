# core/backtester.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Dict

class VectorizedBacktester(ABC):
    """
    A base class for vectorized backtesting of trading strategies.
    
    Attributes:
        symbol (str): The ticker symbol.
        data (pd.DataFrame): The market data (OHLCV).
        tc (float): Transaction costs as a percentage (e.g., 0.001 for 0.1%).
    """

    def __init__(self, symbol: str, data: pd.DataFrame, tc: float = 0.0):
        self.symbol = symbol
        self.data = data.copy()
        self.tc = tc
        self.results = None

    @abstractmethod
    def generate_signals(self):
        """
        Logic to define 'signal' column. 1 for long, -1 for short, 0 for neutral.
        Must be implemented by the child class.
        """
        pass

    def run_backtest(self):
        """
        Executes the backtest engine.
        """
        if 'signal' not in self.data.columns:
            self.generate_signals()
        
        # Calculate Returns
        # Strategy Return = Signal(t-1) * Market Return(t)
        self.data['market_return'] = np.log(self.data['Close'] / self.data['Close'].shift(1))
        self.data['strategy_return'] = self.data['signal'].shift(1) * self.data['market_return']
        
        # Adjust for Transaction Costs (only when position changes)
        trades = self.data['signal'].diff().fillna(0).abs()
        self.data['strategy_return_net'] = self.data['strategy_return'] - (trades * self.tc)
        
        # Cumulative Returns
        self.data['creturns_market'] = self.data['market_return'].cumsum().apply(np.exp)
        self.data['creturns_strategy'] = self.data['strategy_return_net'].cumsum().apply(np.exp)
        
        self.results = self.data
        return self.results

    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Calculates key financial metrics: Sharpe, Drawdown, CAGR.
        """
        if self.results is None:
            self.run_backtest()
            
        strategy_rets = self.results['strategy_return_net']
        
        # Annualized Sharpe Ratio (assuming 252 trading days)
        sharpe = np.sqrt(252) * strategy_rets.mean() / strategy_rets.std()
        
        # Max Drawdown
        cum_rets = self.results['creturns_strategy']
        running_max = cum_rets.cummax()
        drawdown = (cum_rets - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Total Return
        total_return = cum_rets.iloc[-1] - 1
        
        metrics = {
            "Sharpe Ratio": round(sharpe, 2),
            "Max Drawdown": round(max_drawdown * 100, 2),
            "Total Return (%)": round(total_return * 100, 2)
        }
        return metrics

    def plot_results(self):
        """
        Visualizes the performance against the benchmark.
        """
        if self.results is None:
            print("Run backtest first.")
            return
            
        plt.figure(figsize=(12, 8))
        plt.title(f"Backtest Results: {self.symbol}")
        plt.plot(self.results['creturns_market'], label="Market (Buy & Hold)", alpha=0.6)
        plt.plot(self.results['creturns_strategy'], label="Strategy (Net of Fees)", linewidth=2)
        plt.legend()
        plt.grid(True)
        plt.show()
