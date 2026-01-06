# strategies/macd_strategy.py

import pandas as pd
import numpy as np
from core.backtester import VectorizedBacktester

class MACDStrategy(VectorizedBacktester):
    """
    Implements MACD Oscillator Strategy inheriting from VectorizedBacktester.
    """
    
    def __init__(self, symbol: str, data: pd.DataFrame, short_window=12, long_window=26, signal_window=9, tc=0.0):
        super().__init__(symbol, data, tc)
        self.short_window = short_window
        self.long_window = long_window
        self.signal_window = signal_window

    def generate_signals(self):
        """
        Specific logic for MACD.
        """
        data = self.data
        
        # Calculate EMAs
        ema_short = data['Close'].ewm(span=self.short_window, adjust=False).mean()
        ema_long = data['Close'].ewm(span=self.long_window, adjust=False).mean()
        
        # MACD Line & Signal Line
        data['MACD'] = ema_short - ema_long
        data['Signal_Line'] = data['MACD'].ewm(span=self.signal_window, adjust=False).mean()
        
        # Vectorized Signal Logic
        # Long (1) when MACD > Signal Line
        # Short (-1) when MACD < Signal Line
        data['signal'] = np.where(data['MACD'] > data['Signal_Line'], 1, -1)
        
        self.data = data
