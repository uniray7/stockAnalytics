import time
import schedule
import yfinance as yf
import pandas as pd
import logging
from datetime import datetime

from database import get_session, StockData

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Target tickers (Top Tech stocks as example)
TICKERS = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]

def fetch_and_save_data():
    """Fetches the latest 5-minute data from Yahoo Finance and saves it."""
    logger.info("Starting data fetch for tickers: %s", ", ".join(TICKERS))

    session = get_session()

    try:
        # Download recent 5m interval data.
        # Using period='1d' means we get today's data.
        data = yf.download(
            tickers=TICKERS,
            period="1d",
            interval="5m",
            group_by='ticker',
            progress=False
        )

        records_added = 0

        # If there's only one ticker, yfinance doesn't use MultiIndex for columns
        if len(TICKERS) == 1:
            ticker = TICKERS[0]
            ticker_data = data.dropna()

            for timestamp, row in ticker_data.iterrows():
                # Check if it already exists to avoid duplicates
                exists = session.query(StockData).filter(
                    StockData.ticker == ticker,
                    StockData.timestamp == timestamp
                ).first()

                if not exists:
                    record = StockData(
                        ticker=ticker,
                        timestamp=timestamp,
                        open=row['Open'],
                        high=row['High'],
                        low=row['Low'],
                        close=row['Close'],
                        volume=row['Volume']
                    )
                    session.add(record)
                    records_added += 1

        else:
            # Handle multiple tickers
            for ticker in TICKERS:
                if ticker not in data:
                    continue

                ticker_data = data[ticker].dropna()

                for timestamp, row in ticker_data.iterrows():
                    # Handle tz-aware timestamps if needed
                    ts = pd.to_datetime(timestamp)
                    if ts.tzinfo is not None:
                        # SQLite doesn't handle tz-aware well, convert to naive UTC
                        ts = ts.tz_convert('UTC').tz_localize(None)

                    exists = session.query(StockData).filter(
                        StockData.ticker == ticker,
                        StockData.timestamp == ts
                    ).first()

                    if not exists:
                        # Ensure volume is scalar, sometimes yf returns NaN for missing volume
                        vol = row['Volume']
                        if pd.isna(vol):
                            vol = 0

                        record = StockData(
                            ticker=ticker,
                            timestamp=ts,
                            open=row['Open'],
                            high=row['High'],
                            low=row['Low'],
                            close=row['Close'],
                            volume=vol
                        )
                        session.add(record)
                        records_added += 1

        session.commit()
        logger.info(f"Successfully added {records_added} new records to database.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error fetching data: {e}", exc_info=True)
    finally:
        session.close()

def main():
    logger.info("Stock Crawler Started. Initial fetch running now...")
    fetch_and_save_data()

    # Schedule to run every 5 minutes
    schedule.every(5).minutes.do(fetch_and_save_data)

    logger.info("Scheduler running. Press Ctrl+C to exit.")
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Crawler stopped by user.")

if __name__ == "__main__":
    main()
