#!/usr/bin/env bash
set -e

# Start the data crawler in the background (populates data/stocks.db every 5 min).
python src/crawler.py &

# Start the Streamlit dashboard in the foreground, bound to Railway's $PORT.
exec streamlit run src/app.py \
  --server.port "${PORT:-8501}" \
  --server.address 0.0.0.0 \
  --server.headless true
