import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from database import get_session, StockData
import datetime
import hashlib
import hmac
import os
import time
from backtest import run_backtest
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="US Stock Real-time Analysis", layout="wide")

# --- Authentication (simple username/password from environment variables) ---
APP_USERNAME = os.environ.get("APP_USERNAME", "")
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")

# Keep a successful login valid for this long, even across browser refreshes.
SESSION_TTL_SECONDS = 60 * 60  # 1 hour
_COOKIE_NAME = "sa_auth"
# Key used to sign the session cookie. Defaults to the credentials so no extra
# config is needed; changing the password invalidates existing sessions.
_COOKIE_SECRET = (os.environ.get("APP_SECRET") or f"{APP_USERNAME}:{APP_PASSWORD}").encode()

# Reads/writes the browser cookie that persists the login across refreshes.
controller = CookieController()


def _sign(message: str) -> str:
    return hmac.new(_COOKIE_SECRET, message.encode(), hashlib.sha256).hexdigest()


def _make_session_token() -> str:
    """Build a signed `<expiry>.<signature>` token for the auth cookie."""
    expiry = str(int(time.time()) + SESSION_TTL_SECONDS)
    return f"{expiry}.{_sign(expiry)}"


def _token_is_valid(token) -> bool:
    """True if the cookie token is well-formed, correctly signed, and unexpired."""
    if not token or "." not in token:
        return False
    expiry, signature = token.rsplit(".", 1)
    if not hmac.compare_digest(signature, _sign(expiry)):
        return False
    try:
        return int(expiry) > time.time()
    except ValueError:
        return False


def require_auth():
    """Gate the app behind a username/password login defined via env vars."""
    if not APP_USERNAME or not APP_PASSWORD:
        st.title("🔒 US Stock Real-time Analysis")
        st.error("Authentication is not configured. Set APP_USERNAME and APP_PASSWORD.")
        st.stop()

    if st.session_state.get("authenticated"):
        return

    # Restore a prior login from the signed cookie (survives page refresh).
    if _token_is_valid(controller.get(_COOKIE_NAME)):
        st.session_state["authenticated"] = True
        return

    st.title("🔒 US Stock Real-time Analysis")
    st.markdown("This service is private. Please sign in to continue.")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        # Constant-time comparison to avoid leaking length/content via timing.
        if hmac.compare_digest(username, APP_USERNAME) and hmac.compare_digest(password, APP_PASSWORD):
            st.session_state["authenticated"] = True
            # Persist the login so a refresh within the next hour stays signed in.
            controller.set(_COOKIE_NAME, _make_session_token(), max_age=SESSION_TTL_SECONDS)
            # Give the browser a moment to actually write the cookie before the
            # rerun tears down this run; otherwise the write can be dropped.
            time.sleep(0.3)
            st.rerun()
        else:
            st.error("Invalid username or password.")
    st.stop()

require_auth()

def load_data(ticker, time_range):
    """Load stock data from SQLite DB"""
    session = get_session()

    # Calculate start time based on time_range
    now = datetime.datetime.utcnow()
    if time_range == "1 Day":
        start_time = now - datetime.timedelta(days=1)
    elif time_range == "1 Week":
        start_time = now - datetime.timedelta(days=7)
    elif time_range == "1 Month":
        start_time = now - datetime.timedelta(days=30)
    else:
        start_time = now - datetime.timedelta(days=1) # Default

    query = session.query(StockData).filter(
        StockData.ticker == ticker,
        StockData.timestamp >= start_time
    ).order_by(StockData.timestamp.asc())

    df = pd.read_sql(query.statement, session.bind)
    session.close()
    return df

def _logout():
    st.session_state["authenticated"] = False
    # Drop the persisted cookie so the session does not auto-restore.
    if controller.get(_COOKIE_NAME) is not None:
        controller.remove(_COOKIE_NAME)

with st.sidebar:
    st.caption(f"Signed in as {APP_USERNAME}")
    st.button("Log out", on_click=_logout, use_container_width=True)

st.title("📈 US Stock Real-time Analysis")
st.markdown("Real-time data fetched every 5 minutes from Yahoo Finance.")

col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    ticker = st.selectbox(
        "Select Stock Ticker",
        ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META"]
    )

with col2:
    time_range = st.selectbox(
        "Time Range",
        ["1 Day", "1 Week", "1 Month"]
    )

# Refresh button
if st.button("🔄 Refresh Data"):
    st.rerun()

df = load_data(ticker, time_range)

if df.empty:
    st.warning(f"No data available for {ticker} in the selected time range. Ensure the crawler is running.")
else:
    # Display latest metrics
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest

    price_change = latest['close'] - prev['close']
    pct_change = (price_change / prev['close']) * 100

    colA, colB, colC, colD = st.columns(4)
    colA.metric("Latest Price", f"${latest['close']:.2f}", f"{price_change:.2f} ({pct_change:.2f}%)")
    colB.metric("High", f"${latest['high']:.2f}")
    colC.metric("Low", f"${latest['low']:.2f}")
    colD.metric("Volume", f"{int(latest['volume']):,}")

    # Candlestick chart
    st.subheader(f"{ticker} Candlestick Chart (5-min intervals)")

    fig = go.Figure(data=[go.Candlestick(
        x=df['timestamp'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name="Price"
    )])

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        height=600,
        margin=dict(l=0, r=0, t=30, b=0),
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Volume chart
    st.subheader("Trading Volume")
    fig_vol = go.Figure(data=[go.Bar(
        x=df['timestamp'],
        y=df['volume'],
        name="Volume",
        marker_color='lightblue'
    )])

    fig_vol.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=30, b=0),
        template="plotly_dark"
    )
    st.plotly_chart(fig_vol, use_container_width=True)

    # Raw Data Table
    with st.expander("View Raw Data"):
        st.dataframe(df.sort_values('timestamp', ascending=False).set_index('timestamp'))

    st.markdown("---")
    st.header("⚙️ Strategy Backtesting")
    st.markdown("Test trading strategies on the historical data fetched.")

    st.sidebar.header("Backtest Settings")
    strategy = st.sidebar.selectbox("Select Strategy", ["SMA Crossover", "MACD"])

    params = {}
    if strategy == "SMA Crossover":
        params['fast_period'] = st.sidebar.slider("Fast SMA Period", 5, 20, 10)
        params['slow_period'] = st.sidebar.slider("Slow SMA Period", 20, 60, 30)

    if st.sidebar.button("Run Backtest"):
        with st.spinner('Running Backtest...'):
            metrics, error = run_backtest(df, strategy, **params)

            if error:
                st.error(f"Backtest failed: {error}")
            else:
                st.success("Backtest Completed Successfully!")

                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                metrics_col1.metric("Final Portfolio Value", f"${metrics['final_value']:.2f}", f"{metrics['pnl_pct']:.2f}%")
                metrics_col2.metric("Total PnL", f"${metrics['pnl']:.2f}")
                metrics_col3.metric("Win Rate", f"{metrics['win_rate']:.1f}%", f"{metrics['total_trades']} Trades", delta_color="off")
                metrics_col4.metric("Max Drawdown", f"{metrics['max_drawdown']:.2f}%")

                if metrics['total_trades'] == 0:
                    st.info("No trades were executed during this period with the given parameters.")
