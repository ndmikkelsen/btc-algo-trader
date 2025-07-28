import asyncio
from datetime import datetime, timedelta
from loguru import logger

from src.strategy.sma_crossover import SMACrossoverStrategy
from src.backtest.engine import BacktestEngine


async def main():
    logger.info("Starting Bitcoin Trading Bot Strategy Test")
    
    # Create strategy
    strategy = SMACrossoverStrategy(
        short_window=20,
        long_window=50,
        position_size_pct=0.1,
        initial_balance=10000.0
    )
    
    # Create backtest engine
    backtest_engine = BacktestEngine(
        strategy=strategy,
        initial_balance=10000.0,
        commission_rate=0.001
    )
    
    # Define backtest period (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        # Run backtest (using BTC-USD for Coinbase Pro)
        results = await backtest_engine.run_backtest(
            symbol="BTC/USD",
            start_date=start_date,
            end_date=end_date,
            timeframe="1h"
        )
        
        # Print detailed report
        print(backtest_engine.generate_report())
        
    except Exception as e:
        logger.error(f"Backtest failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())