# Stock Analytics Project Context

## Architecture
- **Crawler**: `src/crawler.py` uses `yfinance` to fetch real-time stock data (5-minute intervals) for Top Tech stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META). Scheduled using the `schedule` library.
- **Database**: `src/database.py` sets up a local SQLite database at `data/stocks.db` using `SQLAlchemy`. Stores OHLCV data.
- **Web App**: `src/app.py` runs a `Streamlit` dashboard, pulling data from SQLite and visualizing it via `Plotly` (Candlestick and Volume charts).
- **Backtesting**: `src/backtest.py` integrates `backtrader` with the Streamlit app. It supports `SMA Crossover` and `MACD` strategies.

## Commands
- **Activate Virtual Environment**: `source venv/bin/activate`
- **Run Crawler**: `python src/crawler.py`
- **Run Web App**: `streamlit run src/app.py`

## Development Guidelines
- Always use the `venv` for running commands (`source venv/bin/activate`).
- Ensure `PYTHONPATH` allows imports from `src/` when necessary.
- Database operations should handle timezone conversion cleanly, as SQLite does not natively support tz-aware timestamps natively (convert to naive UTC).
- Keep real-time crawler resilient against missing `yfinance` fields (like missing Volume).