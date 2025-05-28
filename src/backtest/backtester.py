import pandas as pd
from src.indicators import calculate_ema, calculate_rsi, calculate_bollinger_bands

class Backtester:
    def __init__(self, historical_data: pd.DataFrame):
        self.data = historical_data.copy()

    def apply_strategy(self, strategy_func, **kwargs):
        """
        Applies a strategy function to the historical data. The strategy function should accept a DataFrame and return buy/sell signals.
        """
        signals = strategy_func(self.data, **kwargs)
        self.data['Signal'] = signals
        return self.data

    def run_backtest(self, initial_balance=10000, position_size=0.1):
        """
        Simple backtesting loop based on generated signals.
        """
        balance = initial_balance
        position = 0
        trade_log = []
        for i, row in self.data.iterrows():
            if row['Signal'] == 'buy' and position == 0:
                position = position_size
                entry_price = row['Close']
                trade_log.append({'type': 'buy', 'price': entry_price, 'index': i})
            elif row['Signal'] == 'sell' and position > 0:
                exit_price = row['Close']
                pnl = (exit_price - entry_price) * position
                balance += pnl
                trade_log.append({'type': 'sell', 'price': exit_price, 'pnl': pnl, 'index': i})
                position = 0
        return {'final_balance': balance, 'trade_log': trade_log}

# Example strategy template
def simple_ema_crossover_strategy(df, short_window=10, long_window=21):
    df['EMA_short'] = calculate_ema(df['Close'], window=short_window)
    df['EMA_long'] = calculate_ema(df['Close'], window=long_window)
    signals = []
    for i in range(len(df)):
        if df['EMA_short'].iloc[i] > df['EMA_long'].iloc[i]:
            signals.append('buy')
        else:
            signals.append('sell')
    return signals
