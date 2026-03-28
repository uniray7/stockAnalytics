from datetime import datetime
import pandas as pd
import yfinance as yf


def fetch_ohlcv(ticker: str, start: str = "2000-01-01", end: str | None = None) -> pd.DataFrame:
    """Fetch daily OHLCV data (auto-adjusted for splits/dividends)."""
    if end is None:
        end = datetime.today().strftime("%Y-%m-%d")
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.index.name = "Date"
    return df


def fetch_fundamentals(ticker: str) -> pd.DataFrame:
    """Fetch fundamental info snapshot (valuation, financials, metadata)."""
    info = yf.Ticker(ticker).info
    row = {k: v for k, v in info.items() if not isinstance(v, (dict, list))}
    row["fetched_at"] = datetime.utcnow().isoformat()
    row["ticker"] = ticker
    return pd.DataFrame([row])


def fetch_quote(ticker: str) -> pd.DataFrame:
    """Fetch real-time quote snapshot."""
    t = yf.Ticker(ticker)
    fi = t.fast_info
    row = {
        "ticker": ticker,
        "timestamp": datetime.utcnow().isoformat(),
        "price": fi.last_price,
        "open": fi.open,
        "day_high": fi.day_high,
        "day_low": fi.day_low,
        "volume": fi.last_volume,
        "market_cap": getattr(fi, "market_cap", None),
        "52w_high": fi.fifty_two_week_high,
        "52w_low": fi.fifty_two_week_low,
    }
    return pd.DataFrame([row])
