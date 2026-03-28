# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
pip install -r requirements.txt
```

## Running the crawler

```bash
# Fetch everything (all tickers, all data types)
python crawl.py

# Fetch specific data type
python crawl.py --type ohlcv
python crawl.py --type fundamentals
python crawl.py --type quotes

# Fetch specific ticker group
python crawl.py --group ai
python crawl.py --group nuclear
python crawl.py --group sp500

# Fetch specific tickers
python crawl.py --tickers AAPL MSFT NVDA

# Custom OHLCV start date
python crawl.py --type ohlcv --start 2020-01-01
```

## Architecture

```
crawl.py              # CLI entry point
crawler/
  tickers.py          # Ticker lists (AI_TICKERS, NUCLEAR_TICKERS, EXTRA_TICKERS, get_sp500())
  fetch.py            # yfinance wrappers: fetch_ohlcv, fetch_fundamentals, fetch_quote
  storage.py          # CSV persistence: save_ohlcv, save_fundamentals, save_quote
data/                 # gitignored
  ohlcv/{ticker}.csv
  fundamentals/{ticker}.csv
  quotes/{ticker}.csv
```

**Data flow:** `crawl.py` resolves ticker list → calls `fetch.py` per ticker → passes DataFrames to `storage.py` for CSV merge/append.

**OHLCV storage** merges incrementally (new rows only), preserving full history. **Fundamentals** and **quotes** append a new timestamped row each run.

**S&P 500 list** is fetched live from Wikipedia on each run via `pandas.read_html`.

## Ticker groups

| Group | Contents |
|-------|----------|
| `sp500` | Live S&P 500 constituents from Wikipedia |
| `ai` | AI ETFs (BOTZ, AIQ, CHAT, ARKQ, ROBO) + AI stocks (NVDA, AMD, MSFT, GOOGL, META, AMZN, TSLA, PLTR, AI, SMCI, ARM) |
| `nuclear` | Nuclear ETFs (NLR, URA, URNM) + nuclear stocks (CCJ, CEG, VST, LEU, NNE, SMR, OKLO) |
| `extra` | VOO, VT, NVDA |
| `all` | Union of all above |
