import backtrader as bt
import pandas as pd
from database import get_session, StockData

class PandasData(bt.feeds.PandasData):
    """
    Custom Data Feed for Backtrader to handle Pandas DataFrame properly
    """
    lines = ('volume',)
    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )

class SMACrossover(bt.Strategy):
    """
    Simple Moving Average Crossover Strategy
    Buys when fast SMA crosses above slow SMA.
    Sells when fast SMA crosses below slow SMA.
    """
    params = (
        ('fast_period', 10),
        ('slow_period', 30),
    )

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.fast_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.fast_period)
        self.slow_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.slow_period)

        self.crossover = bt.indicators.CrossOver(self.fast_sma, self.slow_sma)

    def next(self):
        # If we are not in the market, check if we should buy
        if not self.position:
            if self.crossover > 0: # Fast crosses above Slow
                self.buy()
        # If we are in the market, check if we should sell
        elif self.crossover < 0: # Fast crosses below Slow
            self.close()

class MACDStrategy(bt.Strategy):
    """
    MACD Strategy
    Buys when MACD line crosses above signal line.
    Sells when MACD line crosses below signal line.
    """
    params = (
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.datas[0],
            period_me1=self.params.macd1,
            period_me2=self.params.macd2,
            period_signal=self.params.macdsig
        )
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()
        elif self.crossover < 0:
            self.close()

def run_backtest(df, strategy_name, initial_cash=10000.0, **kwargs):
    """
    Run backtrader backtest with the given DataFrame and strategy
    """
    if df.empty or len(df) < 50: # Need enough data for moving averages
        return None, "Not enough data for backtesting."

    # Prepare DataFrame for Backtrader
    df = df.copy()
    df.set_index('timestamp', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']]

    cerebro = bt.Cerebro()

    # Set initial cash
    cerebro.broker.setcash(initial_cash)

    # Add Data Feed
    data = PandasData(dataname=df)
    cerebro.adddata(data)

    # Add Strategy
    if strategy_name == "SMA Crossover":
        fast = kwargs.get('fast_period', 10)
        slow = kwargs.get('slow_period', 30)
        cerebro.addstrategy(SMACrossover, fast_period=fast, slow_period=slow)
    elif strategy_name == "MACD":
        cerebro.addstrategy(MACDStrategy)
    else:
        return None, "Unknown Strategy"

    # Add Analyzers
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.0)

    # Run backtest
    try:
        results = cerebro.run()
        strat = results[0]

        # Extract Results
        final_value = cerebro.broker.getvalue()
        pnl = final_value - initial_cash

        trades_dict = strat.analyzers.trades.get_analysis()
        total_trades = trades_dict.get('total', {}).get('closed', 0)
        won_trades = trades_dict.get('won', {}).get('total', 0)
        win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0

        max_drawdown = strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 0)

        metrics = {
            'initial_cash': initial_cash,
            'final_value': final_value,
            'pnl': pnl,
            'pnl_pct': (pnl / initial_cash) * 100,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'max_drawdown': max_drawdown
        }

        return metrics, None
    except Exception as e:
        return None, str(e)
