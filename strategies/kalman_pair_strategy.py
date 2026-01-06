import pandas as pd
import numpy as np
from core.backtester import VectorizedBacktester

class KalmanPairStrategy(VectorizedBacktester):
    """
    Implements a Pairs Trading Strategy using a Kalman Filter to estimate
    the dynamic hedge ratio (beta) between two cointegrated assets.
    
    This is superior to static linear regression as it adapts to structural
    changes in the market relationship between the pairs.
    """
    
    def __init__(self, symbol: str, data: pd.DataFrame, asset_x: str, asset_y: str, 
                 entry_z=2.0, exit_z=0.0, tc=0.0):
        """
        :param asset_x: Name of the column for the independent variable (Stock X)
        :param asset_y: Name of the column for the dependent variable (Stock Y)
        :param entry_z: Z-score threshold to enter a trade
        :param exit_z: Z-score threshold to exit a trade
        """
        super().__init__(symbol, data, tc)
        self.asset_x = asset_x
        self.asset_y = asset_y
        self.entry_z = entry_z
        self.exit_z = exit_z

    def _run_kalman_filter(self, x, y):
        """
        Pure Python implementation of a 1D Kalman Filter for regression.
        Model: y = alpha + beta * x + epsilon
        Returns time-series of alpha (intercept) and beta (slope/hedge ratio).
        """
        delta = 1e-5  # System noise
        trans_cov = delta / (1 - delta) * np.eye(2) # Process noise covariance
        obs_mat = np.vstack([x, np.ones(x.shape)]).T[:, np.newaxis] # Observation matrix
        
        # Initial values
        state_mean = np.zeros(2) 
        state_cov = np.ones((2, 2))
        
        means = []
        
        for i in range(len(x)):
            # Observation matrix for current step
            H = obs_mat[i] 
            
            # Prediction Step (Random Walk assumption)
            # state_mean_pred = state_mean
            state_cov_pred = state_cov + trans_cov
            
            # Measurement Step
            y_pred = H.dot(state_mean)
            y_actual = y[i]
            innovation = y_actual - y_pred
            
            innovation_cov = H.dot(state_cov_pred).dot(H.T) + 1e-3 # Add measurement noise
            kalman_gain = state_cov_pred.dot(H.T) / innovation_cov
            
            # Update Step
            state_mean = state_mean + kalman_gain.flatten() * innovation
            state_cov = state_cov_pred - kalman_gain.dot(H).dot(state_cov_pred)
            
            means.append(state_mean)
            
        return np.array(means)

    def generate_signals(self):
        data = self.data.copy()
        x = data[self.asset_x].values
        y = data[self.asset_y].values
        
        # 1. Calculate Dynamic Hedge Ratio using Kalman Filter
        state_means = self._run_kalman_filter(x, y)
        data['hr'] = state_means[:, 0]     # Dynamic Slope (Beta)
        data['intercept'] = state_means[:, 1] # Dynamic Intercept (Alpha)
        
        # 2. Calculate Spread and Z-Score
        # Spread = Y - (Beta * X + Alpha)
        data['spread'] = y - (data['hr'] * x + data['intercept'])
        
        # Rolling Z-Score of the spread (Standardizing)
        # We use a rolling window to estimate spread volatility
        window = 30
        spread_mean = data['spread'].rolling(window=window).mean()
        spread_std = data['spread'].rolling(window=window).std()
        data['z_score'] = (data['spread'] - spread_mean) / spread_std
        
        # 3. Generate Signals
        # Short Spread (Short Y, Long X) when Z > Entry
        # Long Spread (Long Y, Short X) when Z < -Entry
        # Exit when Z crosses zero
        
        data['signal'] = 0
        
        # Vectorized Logic for position holding
        # This is a simplification. For robust 'state machine' logic, we often use loops, 
        # but for vectorized speed we use np.select or simple masking.
        # Here we use a simple threshold approach:
        
        long_condition = data['z_score'] < -self.entry_z
        short_condition = data['z_score'] > self.entry_z
        exit_condition = abs(data['z_score']) < 0.5 # Near mean reversion
        
        # 1 = Long Spread (Long Y, Short X)
        # -1 = Short Spread (Short Y, Long X)
        
        curr_pos = 0
        signals = []
        for i in range(len(data)):
            z = data['z_score'].iloc[i]
            
            if curr_pos == 0:
                if z < -self.entry_z: curr_pos = 1
                elif z > self.entry_z: curr_pos = -1
            elif curr_pos == 1:
                if z > -self.exit_z: curr_pos = 0 # Exit long
            elif curr_pos == -1:
                if z < self.exit_z: curr_pos = 0 # Exit short
            signals.append(curr_pos)
            
        data['signal'] = signals
        self.data = data
