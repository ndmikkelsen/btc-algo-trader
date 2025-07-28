import pandas as pd
from typing import Dict, Any, Optional, List
from datetime import datetime
from loguru import logger

from ..strategy.base_strategy import BaseStrategy, Signal
from ..data.market_data import MarketDataProvider


class BacktestEngine:
    def __init__(
        self,
        strategy: BaseStrategy,
        initial_balance: float = 10000.0,
        commission_rate: float = 0.001,  # 0.1% commission
    ):
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.commission_rate = commission_rate
        self.results: Dict[str, Any] = {}
        
    async def run_backtest(
        self,
        symbol: str = "BTC/USDT",
        start_date: datetime = None,
        end_date: datetime = None,
        timeframe: str = "1h"
    ) -> Dict[str, Any]:
        logger.info(f"Starting backtest for strategy: {self.strategy.name}")
        
        # Fetch historical data using Coinbase Advanced (no geo restrictions)
        data_provider = MarketDataProvider(exchange_id='coinbaseadvanced', sandbox=False)
        try:
            ohlcv_data = await data_provider.fetch_historical_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if ohlcv_data.empty:
                raise ValueError("No historical data available for backtesting")
                
            logger.info(f"Running backtest on {len(ohlcv_data)} data points")
            
            # Run the backtest
            portfolio_values = []
            signals = []
            
            for i, (timestamp, row) in enumerate(ohlcv_data.iterrows()):
                # Get data up to current point for strategy
                current_data = ohlcv_data.iloc[:i+1]
                current_price = row['close']
                
                # Generate signal
                signal = self.strategy.generate_signal(current_data)
                signals.append(signal.value)
                
                # Execute trade if signal is not HOLD
                if signal != Signal.HOLD:
                    trade = self.strategy.execute_trade(
                        signal=signal,
                        price=current_price,
                        timestamp=timestamp,
                        symbol=symbol
                    )
                    
                    if trade:
                        # Apply commission
                        commission = trade.price * trade.quantity * self.commission_rate
                        self.strategy.current_balance -= commission
                        
                        logger.debug(f"Executed {trade.signal.value} at {trade.price:.2f}, qty: {trade.quantity:.6f}")
                
                # Track portfolio value
                current_prices = {symbol: current_price}
                portfolio_value = self.strategy.get_portfolio_value(current_prices)
                portfolio_values.append(portfolio_value)
            
            # Calculate final results
            final_metrics = self.strategy.get_performance_metrics({symbol: ohlcv_data.iloc[-1]['close']})
            
            # Add additional backtest metrics
            portfolio_series = pd.Series(portfolio_values, index=ohlcv_data.index)
            returns = portfolio_series.pct_change().dropna()
            
            max_drawdown = self._calculate_max_drawdown(portfolio_series)
            sharpe_ratio = self._calculate_sharpe_ratio(returns)
            
            self.results = {
                **final_metrics,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'portfolio_values': portfolio_series,
                'signals': pd.Series(signals, index=ohlcv_data.index),
                'ohlcv_data': ohlcv_data,
                'total_commission_paid': len(self.strategy.trades) * self.commission_rate,
                'start_date': start_date,
                'end_date': end_date,
                'timeframe': timeframe,
                'symbol': symbol
            }
            
            logger.info(f"Backtest completed. Final portfolio value: ${final_metrics['portfolio_value']:.2f}")
            logger.info(f"Total return: {final_metrics['total_return']:.2%}")
            logger.info(f"Total trades: {final_metrics['total_trades']}")
            logger.info(f"Win rate: {final_metrics['win_rate']:.2%}")
            logger.info(f"Max drawdown: {max_drawdown:.2%}")
            logger.info(f"Sharpe ratio: {sharpe_ratio:.3f}")
            
            return self.results
            
        finally:
            await data_provider.close()
    
    def _calculate_max_drawdown(self, portfolio_series: pd.Series) -> float:
        rolling_max = portfolio_series.expanding().max()
        drawdown = (portfolio_series - rolling_max) / rolling_max
        return drawdown.min()
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        if len(returns) == 0 or returns.std() == 0:
            return 0.0
            
        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        return excess_returns.mean() / returns.std() * (252 ** 0.5)  # Annualized
    
    def generate_report(self) -> str:
        if not self.results:
            return "No backtest results available. Run backtest first."
            
        report = f"""
=== BACKTEST REPORT ===
Strategy: {self.strategy.name}
Symbol: {self.results['symbol']}
Period: {self.results['start_date']} to {self.results['end_date']}
Timeframe: {self.results['timeframe']}

=== PERFORMANCE METRICS ===
Initial Balance: ${self.results['initial_balance']:,.2f}
Final Portfolio Value: ${self.results['portfolio_value']:,.2f}
Total Return: {self.results['total_return']:.2%}
Max Drawdown: {self.results['max_drawdown']:.2%}
Sharpe Ratio: {self.results['sharpe_ratio']:.3f}

=== TRADING METRICS ===
Total Trades: {self.results['total_trades']}
Win Rate: {self.results['win_rate']:.2%}
Commission Paid: ${self.results['total_commission_paid']:.2f}
Unrealized P&L: ${self.results['unrealized_pnl']:.2f}

=== CURRENT POSITIONS ===
"""
        for symbol, position in self.strategy.positions.items():
            report += f"{symbol}: {position.quantity:.6f} @ ${position.entry_price:.2f}\n"
            
        return report