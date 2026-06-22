# Stock Analytics Project Context

## Architecture
- **Crawler**: `src/crawler.py` uses `yfinance` to fetch real-time stock data (5-minute intervals) for Top Tech stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META). Scheduled using the `schedule` library.
- **Database**: `src/database.py` sets up a local SQLite database at `data/stocks.db` using `SQLAlchemy`. Stores OHLCV data.
- **Web App**: `src/app.py` runs a `Streamlit` dashboard, pulling data from SQLite and visualizing it via `Plotly` (Candlestick and Volume charts).
- **Backtesting**: `src/backtest.py` integrates `backtrader` with the Streamlit app. It supports `SMA Crossover` and `MACD` strategies.

## Commands
- **Run the service (local or Railway)**: `./start.sh` — single entrypoint for both environments. Locally it creates/activates `venv`, installs deps, sets dev creds, starts the crawler in the background, and runs the dashboard on `localhost`. On Railway (detected via `$RAILWAY_ENVIRONMENT`) it skips local setup and binds `0.0.0.0` headless.
- **Activate Virtual Environment** (manual): `source venv/bin/activate`
- **Run Crawler** (manual): `python src/crawler.py`
- **Run Web App** (manual): `streamlit run src/app.py`

## Authentication
- **Mechanism**: Simple username/password login. `src/app.py` gates every page via `require_auth()`, which renders a login form and tracks state in `st.session_state["authenticated"]`. Credentials are compared with `hmac.compare_digest` (constant time).
- **Persistent session**: On successful login a signed `<expiry>.<hmac-sha256>` token is stored in a browser cookie (`sa_auth`) via `streamlit-cookies-controller`, with a 1-hour TTL (`SESSION_TTL_SECONDS`). A refresh restores the session from the cookie instead of re-prompting; a forged or expired token fails the signature/expiry check. The signing key is `APP_SECRET` if set, otherwise derived from `APP_USERNAME`/`APP_PASSWORD` (so changing the password invalidates existing sessions). "Log out" clears both the session and the cookie.
- **Credentials**: Read from environment variables `APP_USERNAME` and `APP_PASSWORD`. If either is unset, the app refuses to load (no default/open access).
- **Local dev**: `./start.sh` defaults to `me`/`secret`; override by exporting first (`APP_USERNAME=… APP_PASSWORD=… ./start.sh`).
- **Production (Railway)**: Set `APP_USERNAME` and `APP_PASSWORD` in the Railway dashboard (Variables tab).

## Deployment
- **Platform**: Deployed on [Railway](https://railway.app), a PaaS (Platform as a Service) that builds and runs the app from this repo.
- **Config**: `railway.json` defines the build and deploy settings. Builder is `RAILPACK`; restart policy is `ON_FAILURE` with up to 5 retries.
- **Start command**: `bash start.sh` (also mirrored in `Procfile`). The same `start.sh` serves local dev and Railway, branching on `$RAILWAY_ENVIRONMENT`. It launches `src/crawler.py` in the background and runs the Streamlit dashboard in the foreground.
- **Port binding**: Streamlit binds to Railway's injected `$PORT` (defaults to `8501` locally), on address `0.0.0.0` in headless mode.
- **Persistence note**: SQLite data at `data/stocks.db` lives on the container's ephemeral filesystem and is reset on redeploy unless a Railway volume is mounted.

## Development Guidelines
- Always use the `venv` for running commands (`source venv/bin/activate`).
- Ensure `PYTHONPATH` allows imports from `src/` when necessary.
- Database operations should handle timezone conversion cleanly, as SQLite does not natively support tz-aware timestamps natively (convert to naive UTC).
- Keep real-time crawler resilient against missing `yfinance` fields (like missing Volume).