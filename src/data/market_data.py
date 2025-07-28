import ccxt
import pandas as pd
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import concurrent.futures
from loguru import logger


class MarketDataProvider:
    def __init__(self, exchange_id: str = 'binance', sandbox: bool = False):
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
    async def fetch_ohlcv(
        self, 
        symbol: str = 'BTC/USDT',
        timeframe: str = '1h',
        since: Optional[datetime] = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        try:
            since_timestamp = None
            if since:
                since_timestamp = int(since.timestamp() * 1000)
            
            # Run synchronous CCXT method in thread pool
            loop = asyncio.get_event_loop()
            ohlcv = await loop.run_in_executor(
                self.executor,
                lambda: self.exchange.fetch_ohlcv(symbol, timeframe, since_timestamp, limit)
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Fetched {len(df)} OHLCV records for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            raise
            
    async def fetch_historical_data(
        self,
        symbol: str = 'BTC/USDT',
        timeframe: str = '1h',
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
            
        all_data = []
        current_date = start_date
        
        while current_date < end_date:
            try:
                data = await self.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=timeframe,
                    since=current_date,
                    limit=1000
                )
                
                if data.empty:
                    break
                    
                all_data.append(data)
                current_date = data.index[-1] + timedelta(hours=1)
                
                await asyncio.sleep(0.1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error fetching data for {current_date}: {e}")
                break
                
        if all_data:
            combined_df = pd.concat(all_data)
            combined_df = combined_df[~combined_df.index.duplicated(keep='first')]
            combined_df.sort_index(inplace=True)
            
            # Filter by date range
            mask = (combined_df.index >= start_date) & (combined_df.index <= end_date)
            combined_df = combined_df[mask]
            
            logger.info(f"Combined historical data: {len(combined_df)} records")
            return combined_df
        
        return pd.DataFrame()
        
    async def close(self):
        if hasattr(self.exchange, 'close'):
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.exchange.close
            )
        self.executor.shutdown(wait=True)


class OrderBookProvider:
    def __init__(self, exchange_id: str = 'binance', sandbox: bool = False):
        self.exchange_id = exchange_id
        self.exchange = getattr(ccxt, exchange_id)({
            'sandbox': sandbox,
            'enableRateLimit': True,
        })
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        
    async def fetch_order_book(
        self, 
        symbol: str = 'BTC/USDT',
        limit: int = 100
    ) -> Dict[str, Any]:
        try:
            # Run synchronous CCXT method in thread pool
            loop = asyncio.get_event_loop()
            order_book = await loop.run_in_executor(
                self.executor,
                lambda: self.exchange.fetch_order_book(symbol, limit)
            )
            
            # Convert to DataFrame for easier analysis
            bids_df = pd.DataFrame(order_book['bids'], columns=['price', 'amount'])
            asks_df = pd.DataFrame(order_book['asks'], columns=['price', 'amount'])
            
            return {
                'timestamp': pd.to_datetime(order_book['timestamp'], unit='ms'),
                'bids': bids_df,
                'asks': asks_df,
                'spread': asks_df.iloc[0]['price'] - bids_df.iloc[0]['price'] if not asks_df.empty and not bids_df.empty else 0
            }
            
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            raise
            
    async def close(self):
        if hasattr(self.exchange, 'close'):
            await asyncio.get_event_loop().run_in_executor(
                self.executor, self.exchange.close
            )
        self.executor.shutdown(wait=True)