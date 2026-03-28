from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"


def _dir(subdir: str) -> Path:
    path = DATA_DIR / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_ohlcv(ticker: str, df: pd.DataFrame) -> None:
    """Merge new OHLCV rows into existing CSV, preserving history."""
    path = _dir("ohlcv") / f"{ticker}.csv"
    if path.exists():
        existing = pd.read_csv(path, index_col="Date", parse_dates=True)
        df = pd.concat([existing, df[~df.index.isin(existing.index)]])
        df.sort_index(inplace=True)
    df.to_csv(path)


def save_fundamentals(ticker: str, df: pd.DataFrame) -> None:
    """Append fundamentals snapshot (one row per fetch) to CSV."""
    path = _dir("fundamentals") / f"{ticker}.csv"
    if path.exists():
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(path, index=False)


def save_quote(ticker: str, df: pd.DataFrame) -> None:
    """Append real-time quote snapshot to CSV."""
    path = _dir("quotes") / f"{ticker}.csv"
    if path.exists():
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(path, index=False)
