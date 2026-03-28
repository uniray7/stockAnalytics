#!/usr/bin/env python3
"""
US Stock Data Crawler — Yahoo Finance

Usage:
    python crawl.py                              # all tickers, all data types
    python crawl.py --type ohlcv                 # OHLCV only
    python crawl.py --group ai                   # AI tickers only
    python crawl.py --tickers AAPL MSFT GOOG     # specific tickers
    python crawl.py --start 2020-01-01           # OHLCV start date
"""
import argparse
import time

from crawler.fetch import fetch_fundamentals, fetch_ohlcv, fetch_quote
from crawler.storage import save_fundamentals, save_ohlcv, save_quote
from crawler.tickers import (
    AI_TICKERS,
    EXTRA_TICKERS,
    NUCLEAR_TICKERS,
    get_all_tickers,
    get_sp500,
)

GROUPS = {
    "all": get_all_tickers,
    "sp500": get_sp500,
    "ai": lambda: AI_TICKERS,
    "nuclear": lambda: NUCLEAR_TICKERS,
    "extra": lambda: EXTRA_TICKERS,
}


def crawl(tickers: list[str], fetch_type: str, start: str) -> None:
    total = len(tickers)
    errors = []

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{total}] {ticker}", end="  ", flush=True)
        try:
            if fetch_type in ("ohlcv", "all"):
                save_ohlcv(ticker, fetch_ohlcv(ticker, start=start))
                print("ohlcv✓", end="  ", flush=True)
            if fetch_type in ("fundamentals", "all"):
                save_fundamentals(ticker, fetch_fundamentals(ticker))
                print("fundamentals✓", end="  ", flush=True)
            if fetch_type in ("quotes", "all"):
                save_quote(ticker, fetch_quote(ticker))
                print("quotes✓", end="  ", flush=True)
            print()
        except Exception as e:
            msg = f"{ticker}: {e}"
            errors.append(msg)
            print(f"ERROR: {e}")

        time.sleep(0.3)  # polite rate limiting

    print(f"\nDone. {total - len(errors)}/{total} succeeded.")
    if errors:
        print(f"\nFailed ({len(errors)}):")
        for e in errors:
            print(f"  {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="US Stock Data Crawler (Yahoo Finance)")
    parser.add_argument(
        "--type",
        choices=["ohlcv", "fundamentals", "quotes", "all"],
        default="all",
        help="Data type to fetch (default: all)",
    )
    parser.add_argument(
        "--group",
        choices=list(GROUPS),
        default="all",
        help="Ticker group to crawl (default: all)",
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        metavar="TICKER",
        help="Override with specific tickers (e.g. --tickers AAPL MSFT)",
    )
    parser.add_argument(
        "--start",
        default="2000-01-01",
        metavar="YYYY-MM-DD",
        help="Start date for OHLCV history (default: 2000-01-01)",
    )
    args = parser.parse_args()

    if args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        print(f"Resolving ticker group '{args.group}'...")
        tickers = GROUPS[args.group]()

    print(f"Crawling {len(tickers)} tickers | type={args.type}\n")
    crawl(tickers, args.type, args.start)


if __name__ == "__main__":
    main()
