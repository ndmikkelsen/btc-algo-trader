import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

from .base_strategy import BaseStrategy, Signal


class SMACrossoverStrategy(BaseStrategy):
    def __init__(
        self,
        short_window: int = 20,
        long_window: int = 50,
        position_size_pct: float = 0.03,
        initial_balance: float = 10000.0
    ):
        super().__init__("SMA Crossover Strategy", initial_balance)
        self.short_window = short_window
        self.long_window = long_window
        self.position_size_pct = position_size_pct
        
    def generate_signal(
        self, 
        ohlcv_data: pd.DataFrame,
        order_book_data: Optional[Dict[str, Any]] = None
    ) -> Signal:
        if len(ohlcv_data) < self.long_window:
            return Signal.HOLD
            
        # Calculate SMAs
        short_sma = ohlcv_data['close'].rolling(window=self.short_window).mean()
        long_sma = ohlcv_data['close'].rolling(window=self.long_window).mean()
        
        # Store indicators for analysis
        self.add_indicator('short_sma', short_sma)
        self.add_indicator('long_sma', long_sma)
        
        # Get latest values
        current_short = short_sma.iloc[-1]
        current_long = long_sma.iloc[-1]
        prev_short = short_sma.iloc[-2] if len(short_sma) > 1 else current_short
        prev_long = long_sma.iloc[-2] if len(long_sma) > 1 else current_long
        
        # Generate signals based on crossover
        if prev_short <= prev_long and current_short > current_long:
            # Golden cross - buy signal
            return Signal.BUY
        elif prev_short >= prev_long and current_short < current_long:
            # Death cross - sell signal
            return Signal.SELL
        else:
            return Signal.HOLD
            
    def calculate_position_size(
        self, 
        signal: Signal,
        current_price: float,
        available_balance: float
    ) -> float:
        if signal == Signal.BUY:
            # Risk a percentage of available balance
            risk_amount = available_balance * self.position_size_pct
            return risk_amount / current_price
        elif signal == Signal.SELL:
            # Sell all available position
            symbol = "BTC/USDT"  # Assuming BTC/USDT for now
            if symbol in self.positions:
                return self.positions[symbol].quantity
            return 0.0
        else:
            return 0.0