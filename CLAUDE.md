# Stock Analytics Project Context

## Architecture
- **Crawler**: `src/crawler.py` uses `yfinance` to fetch real-time stock data (5-minute intervals) for Top Tech stocks (AAPL, MSFT, GOOGL, AMZN, NVDA, TSLA, META). Scheduled using the `schedule` library.
- **Database**: `src/database.py` connects to **PostgreSQL** via `SQLAlchemy`, reading the connection string from the `DATABASE_PUBLIC_URL` env var (user, password, host/fqdn, port, db name all embedded). The app refuses to start if it is unset. Stores OHLCV data. Locally, Postgres runs as a Docker container (`docker-compose.yml`); in production it points at a managed Postgres instance.
- **Web App**: `src/app.py` runs a `Streamlit` dashboard, pulling data from Postgres and visualizing it via `Plotly` (Candlestick and Volume charts).
- **Backtesting**: `src/backtest.py` integrates `backtrader` with the Streamlit app. It supports `SMA Crossover` and `MACD` strategies.

## Commands
- **Run the service (local or Railway)**: `./start.sh` — single entrypoint for both environments. Locally it creates/activates `venv`, installs deps, sets dev creds, brings up the local PostgreSQL Docker container and exports `DATABASE_PUBLIC_URL`, starts the crawler in the background, and runs the dashboard on `localhost`. On Railway (detected via `$RAILWAY_ENVIRONMENT`) it skips local setup and binds `0.0.0.0` headless, using the `DATABASE_PUBLIC_URL` from the dashboard.
- **Local PostgreSQL** (manual): `docker compose up -d postgres` (connection: `postgresql://stocks:stocks@localhost:5432/stocks`).
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
- **Database**: Set `DATABASE_PUBLIC_URL` in the Railway dashboard (Variables tab) to point at a PostgreSQL instance (e.g. a Railway Postgres plugin). Data persists in Postgres across redeploys, independent of the app container's ephemeral filesystem.

## Development Guidelines
- Always use the `venv` for running commands (`source venv/bin/activate`).
- Ensure `PYTHONPATH` allows imports from `src/` when necessary.
- Database operations store naive UTC timestamps (the `timestamp` column is a tz-naive `DateTime`); convert tz-aware values to naive UTC before persisting.
- Keep real-time crawler resilient against missing `yfinance` fields (like missing Volume).