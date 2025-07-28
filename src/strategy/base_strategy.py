from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class Signal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Trade:
    timestamp: datetime
    signal: Signal
    price: float
    quantity: float
    reason: str = ""

@dataclass
class Position:
    symbol: str
    quantity: float
    entry_price: float
    entry_time: datetime
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    
    def update_price(self, current_price: float):
        self.current_price = current_price
        self.unrealized_pnl = (current_price - self.entry_price) * self.quantity


class BaseStrategy(ABC):
    def __init__(self, name: str, initial_balance: float = 10000.0):
        self.name = name
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.indicators: Dict[str, pd.Series] = {}
        
    @abstractmethod
    def generate_signal(
        self, 
        ohlcv_data: pd.DataFrame,
        order_book_data: Optional[Dict[str, Any]] = None
    ) -> Signal:
        pass
        
    @abstractmethod
    def calculate_position_size(
        self, 
        signal: Signal,
        current_price: float,
        available_balance: float
    ) -> float:
        pass
        
    def add_indicator(self, name: str, values: pd.Series):
        self.indicators[name] = values
        
    def get_indicator(self, name: str) -> Optional[pd.Series]:
        return self.indicators.get(name)
        
    def execute_trade(
        self,
        signal: Signal,
        price: float,
        timestamp: datetime,
        symbol: str = "BTC/USDT"
    ) -> Optional[Trade]:
        if signal == Signal.HOLD:
            return None
            
        quantity = self.calculate_position_size(signal, price, self.current_balance)
        
        if quantity <= 0:
            return None
            
        trade = Trade(
            timestamp=timestamp,
            signal=signal,
            price=price,
            quantity=quantity,
            reason=f"Signal: {signal.value}"
        )
        
        if signal == Signal.BUY:
            cost = price * quantity
            if cost <= self.current_balance:
                self.current_balance -= cost
                if symbol in self.positions:
                    # Average down/up existing position
                    existing = self.positions[symbol]
                    total_cost = (existing.entry_price * existing.quantity) + cost
                    total_quantity = existing.quantity + quantity
                    avg_price = total_cost / total_quantity
                    
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=total_quantity,
                        entry_price=avg_price,
                        entry_time=existing.entry_time,
                        current_price=price
                    )
                else:
                    self.positions[symbol] = Position(
                        symbol=symbol,
                        quantity=quantity,
                        entry_price=price,
                        entry_time=timestamp,
                        current_price=price
                    )
                    
        elif signal == Signal.SELL:
            if symbol in self.positions:
                position = self.positions[symbol]
                sell_quantity = min(quantity, position.quantity)
                revenue = price * sell_quantity
                self.current_balance += revenue
                
                position.quantity -= sell_quantity
                if position.quantity <= 0:
                    del self.positions[symbol]
                    
                trade.quantity = sell_quantity
                
        self.trades.append(trade)
        return trade
        
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        portfolio_value = self.current_balance
        
        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position.update_price(current_prices[symbol])
                portfolio_value += position.quantity * current_prices[symbol]
                
        return portfolio_value
        
    def get_performance_metrics(self, current_prices: Dict[str, float]) -> Dict[str, float]:
        portfolio_value = self.get_portfolio_value(current_prices)
        total_return = (portfolio_value - self.initial_balance) / self.initial_balance
        
        # Calculate trade metrics
        winning_trades = [t for t in self.trades if self._is_winning_trade(t, current_prices)]
        total_trades = len(self.trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.current_balance,
            'portfolio_value': portfolio_value,
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'unrealized_pnl': sum(pos.unrealized_pnl for pos in self.positions.values())
        }
        
    def _is_winning_trade(self, trade: Trade, current_prices: Dict[str, float]) -> bool:
        # Simplified winning trade calculation
        # In practice, this would need more sophisticated tracking
        return True  # Placeholder