# Bitcoin Trading Bot Strategy Framework

A comprehensive Python framework for developing, backtesting, and analyzing Bitcoin trading strategies using historical OHLCV and order book data.

## Features

- **Modular Strategy Framework**: Easy-to-extend base classes for implementing custom trading strategies
- **Historical Data Integration**: Fetches real-time OHLCV and order book data from cryptocurrency exchanges via CCXT
- **Comprehensive Backtesting**: Full backtesting engine with performance metrics, trade tracking, and portfolio management
- **Risk Management**: Built-in position sizing, commission handling, and portfolio value tracking
- **Performance Analytics**: Sharpe ratio, maximum drawdown, win rate, and other key trading metrics
- **Async Architecture**: Efficient data fetching and processing using async/await patterns
- **Modern Python**: Built for Python 3.13+ with latest dependency versions
- **Fast Development Tools**: Includes Ruff for ultra-fast linting and formatting

## Project Structure

```
src/
├── data/
│   ├── __init__.py
│   └── market_data.py          # OHLCV and order book data providers
├── strategy/
│   ├── __init__.py
│   ├── base_strategy.py        # Abstract base strategy class
│   └── sma_crossover.py        # Example SMA crossover strategy
├── backtest/
│   ├── __init__.py
│   └── engine.py               # Backtesting engine with metrics
└── utils/
    └── __init__.py
main.py                         # Example usage and strategy testing
pyproject.toml                  # Poetry dependencies and configuration
```

## Installation

### Prerequisites

- Python 3.13 or higher
- Poetry (for dependency management)

### Installing Python 3.13 on macOS

Choose one of the following methods to install Python 3.13:

#### Option 1: Homebrew (Recommended for system-wide installation)

```bash
# Install Homebrew if you don't have it
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.13
brew install python@3.13

# Verify installation
python3.13 --version
```

#### Option 2: pyenv (Best for multiple Python versions)

```bash
# Install pyenv
brew install pyenv

# Add to your shell profile (~/.zshrc or ~/.bash_profile)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
echo 'eval "$(pyenv init -)"' >> ~/.zshrc

# Restart your shell or run:
source ~/.zshrc

# Install Python 3.13
pyenv install 3.13.1
pyenv global 3.13.1

# Verify
python --version
```

#### Option 3: Official Python.org Installer

1. Visit https://www.python.org/downloads/
2. Download Python 3.13.1 for macOS
3. Run the installer package
4. Verify with `python3.13 --version`

**Recommendation**: Use **pyenv** if you work with multiple Python projects as it allows easy version switching. Use **Homebrew** for a simple system-wide installation.

### Project Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd bitcoin-trading-bot
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Configure Poetry to use Python 3.13** (if you installed it with a specific name):
   ```bash
   poetry env use python3.13
   # or if using pyenv:
   poetry env use python
   ```

4. **Install dependencies**:
   ```bash
   poetry install
   ```

5. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

6. **Verify Poetry is using the correct Python version**:
   ```bash
   poetry run python --version
   ```

## Quick Start

### Running the Example Strategy

The framework includes a Simple Moving Average (SMA) crossover strategy as an example:

```bash
poetry run python main.py
```

This will:
- Fetch 30 days of BTC/USDT hourly data from Binance
- Run the SMA crossover strategy (20/50 period)
- Display comprehensive backtest results

### Example Output

```
=== BACKTEST REPORT ===
Strategy: SMA Crossover Strategy
Symbol: BTC/USDT
Period: 2024-06-28 to 2024-07-28
Timeframe: 1h

=== PERFORMANCE METRICS ===
Initial Balance: $10,000.00
Final Portfolio Value: $10,847.32
Total Return: 8.47%
Max Drawdown: -3.21%
Sharpe Ratio: 1.245

=== TRADING METRICS ===
Total Trades: 12
Win Rate: 58.33%
Commission Paid: $12.47
Unrealized P&L: $234.56
```

## Creating Custom Strategies

### 1. Inherit from BaseStrategy

```python
from src.strategy.base_strategy import BaseStrategy, Signal
import pandas as pd

class MyCustomStrategy(BaseStrategy):
    def __init__(self, param1: float = 0.1, initial_balance: float = 10000.0):
        super().__init__("My Custom Strategy", initial_balance)
        self.param1 = param1
    
    def generate_signal(self, ohlcv_data: pd.DataFrame, order_book_data=None) -> Signal:
        # Implement your trading logic here
        # Return Signal.BUY, Signal.SELL, or Signal.HOLD
        pass
    
    def calculate_position_size(self, signal: Signal, current_price: float, available_balance: float) -> float:
        # Implement your position sizing logic
        pass
```

### 2. Key Methods to Implement

- **`generate_signal()`**: Core trading logic that returns BUY/SELL/HOLD signals
- **`calculate_position_size()`**: Risk management and position sizing logic

### 3. Available Data

- **OHLCV Data**: Open, High, Low, Close, Volume historical data
- **Order Book Data**: Real-time bid/ask data (optional)
- **Technical Indicators**: Use the `add_indicator()` method to store custom indicators

## Data Sources

### OHLCV Data
- **Source**: Live cryptocurrency exchanges via CCXT library
- **Default Exchange**: Binance (configurable)
- **File**: `src/data/market_data.py`
- **Format**: Pandas DataFrame with timestamp index

### Order Book Data
- **Source**: Real-time order book snapshots
- **Contains**: Bid/ask prices and volumes, spread calculations
- **Usage**: Advanced strategies requiring market microstructure data

### Supported Exchanges
- Binance, Coinbase Pro, Kraken, Bitfinex, and 100+ others via CCXT
- Configure in `MarketDataProvider(exchange_id='binance')`

## Configuration

### Environment Variables

Create a `.env` file for sensitive configuration:

```env
# Exchange API credentials (if needed for live trading)
EXCHANGE_API_KEY=your_api_key
EXCHANGE_SECRET=your_secret_key
EXCHANGE_SANDBOX=true

# Logging level
LOG_LEVEL=INFO
```

### Strategy Parameters

Modify strategy parameters in `main.py` or create configuration files:

```python
strategy = SMACrossoverStrategy(
    short_window=20,        # Fast SMA period
    long_window=50,         # Slow SMA period
    position_size_pct=0.1,  # Risk 10% per trade
    initial_balance=10000.0
)
```

## Backtesting

### Basic Backtesting

```python
from src.strategy.sma_crossover import SMACrossoverStrategy
from src.backtest.engine import BacktestEngine
from datetime import datetime, timedelta

# Create strategy
strategy = SMACrossoverStrategy()

# Create backtest engine
backtest = BacktestEngine(
    strategy=strategy,
    commission_rate=0.001  # 0.1% commission
)

# Run backtest
results = await backtest.run_backtest(
    symbol="BTC/USDT",
    start_date=datetime.now() - timedelta(days=90),
    end_date=datetime.now(),
    timeframe="1h"
)
```

### Performance Metrics

The backtesting engine calculates:

- **Total Return**: Overall portfolio performance
- **Sharpe Ratio**: Risk-adjusted returns
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Commission Impact**: Total trading costs

## Development

### Code Quality

The project uses several tools for code quality:

```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Lint code (traditional)
poetry run flake8

# Fast linting and formatting (recommended)
poetry run ruff check .
poetry run ruff format .

# Type checking
poetry run mypy src/
```

### Testing

```bash
# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=src/
```

### Adding New Strategies

1. Create a new file in `src/strategy/`
2. Inherit from `BaseStrategy`
3. Implement required methods
4. Add tests in `tests/strategy/`

## API Reference

### BaseStrategy

Core abstract class for all trading strategies.

**Key Methods**:
- `generate_signal(ohlcv_data, order_book_data)` → Signal
- `calculate_position_size(signal, price, balance)` → float
- `execute_trade(signal, price, timestamp)` → Trade
- `get_portfolio_value(current_prices)` → float

### BacktestEngine

Backtesting engine for strategy validation.

**Key Methods**:
- `run_backtest(symbol, start_date, end_date, timeframe)` → Dict
- `generate_report()` → str

### MarketDataProvider

Data provider for OHLCV and order book data.

**Key Methods**:
- `fetch_ohlcv(symbol, timeframe, since, limit)` → DataFrame
- `fetch_historical_data(symbol, timeframe, start_date, end_date)` → DataFrame

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-strategy`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`poetry run pytest`)
6. Commit your changes (`git commit -am 'Add amazing strategy'`)
7. Push to the branch (`git push origin feature/amazing-strategy`)
8. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This software is for educational and research purposes only. Cryptocurrency trading involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software. Always do your own research and consider consulting with a financial advisor before making investment decisions. 
