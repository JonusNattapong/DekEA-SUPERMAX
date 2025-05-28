import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union
from src.price_utils import fetch_gold_price_data
from src.risk_utils import calculate_risk_metrics

class TradingAlgorithm:
    """Base class for all trading algorithms"""
    def __init__(self, name: str):
        self.name = name
        self.signals = []
        self.current_position = "NEUTRAL"  # LONG, SHORT, or NEUTRAL
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        """Generate buy/sell signal based on the algorithm
        Returns: 'BUY', 'SELL', or 'HOLD'
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics for the algorithm"""
        return {
            "name": self.name,
            "signals_generated": len(self.signals)
        }


class MACrossover(TradingAlgorithm):
    """Moving Average Crossover Strategy"""
    def __init__(self, short_window: int = 10, long_window: int = 50):
        super().__init__(f"MA_Crossover_{short_window}_{long_window}")
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.long_window:
            return "HOLD"  # Not enough data
        
        # Calculate moving averages
        data['short_ma'] = data['Close'].rolling(window=self.short_window).mean()
        data['long_ma'] = data['Close'].rolling(window=self.long_window).mean()
        
        # Generate signals
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2] if len(data) > 1 else None
        
        # Check for crossover
        if prev_row is not None:
            # Bullish crossover (short MA crosses above long MA)
            if (prev_row['short_ma'] <= prev_row['long_ma']) and (last_row['short_ma'] > last_row['long_ma']):
                signal = "BUY"
                self.current_position = "LONG"
            # Bearish crossover (short MA crosses below long MA)
            elif (prev_row['short_ma'] >= prev_row['long_ma']) and (last_row['short_ma'] < last_row['long_ma']):
                signal = "SELL"
                self.current_position = "SHORT"
            else:
                signal = "HOLD"
        else:
            signal = "HOLD"
        
        self.signals.append({
            'timestamp': last_row.name,
            'signal': signal,
            'price': last_row['Close'],
            'short_ma': last_row['short_ma'],
            'long_ma': last_row['long_ma']
        })
        
        return signal


class RSIStrategy(TradingAlgorithm):
    """Relative Strength Index Strategy"""
    def __init__(self, period: int = 14, overbought: int = 70, oversold: int = 30):
        super().__init__(f"RSI_{period}_{overbought}_{oversold}")
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def calculate_rsi(self, data: pd.DataFrame) -> pd.Series:
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.period).mean()
        loss = -delta.where(delta < 0, 0).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.period + 1:
            return "HOLD"  # Not enough data
        
        # Calculate RSI
        data['rsi'] = self.calculate_rsi(data)
        
        # Generate signals based on RSI values
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2] if len(data) > 1 else None
        
        if prev_row is not None:
            # Oversold to Normal (Buy signal)
            if prev_row['rsi'] < self.oversold and last_row['rsi'] >= self.oversold:
                signal = "BUY"
                self.current_position = "LONG"
            # Overbought to Normal (Sell signal)
            elif prev_row['rsi'] > self.overbought and last_row['rsi'] <= self.overbought:
                signal = "SELL"
                self.current_position = "SHORT"
            else:
                signal = "HOLD"
        else:
            signal = "HOLD"
        
        self.signals.append({
            'timestamp': last_row.name,
            'signal': signal,
            'price': last_row['Close'],
            'rsi': last_row['rsi']
        })
        
        return signal


class BollingerBandsStrategy(TradingAlgorithm):
    """Bollinger Bands Strategy"""
    def __init__(self, window: int = 20, num_std: float = 2.0):
        super().__init__(f"Bollinger_{window}_{num_std}")
        self.window = window
        self.num_std = num_std
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.window:
            return "HOLD"  # Not enough data
        
        # Calculate Bollinger Bands
        data['sma'] = data['Close'].rolling(window=self.window).mean()
        data['std'] = data['Close'].rolling(window=self.window).std()
        data['upper_band'] = data['sma'] + (data['std'] * self.num_std)
        data['lower_band'] = data['sma'] - (data['std'] * self.num_std)
        
        # Generate signals
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2] if len(data) > 1 else None
        
        if prev_row is not None:
            # Price crosses below lower band (Buy signal)
            if prev_row['Close'] <= prev_row['lower_band'] and last_row['Close'] > last_row['lower_band']:
                signal = "BUY"
                self.current_position = "LONG"
            # Price crosses above upper band (Sell signal)
            elif prev_row['Close'] >= prev_row['upper_band'] and last_row['Close'] < last_row['upper_band']:
                signal = "SELL"
                self.current_position = "SHORT"
            else:
                signal = "HOLD"
        else:
            signal = "HOLD"
        
        self.signals.append({
            'timestamp': last_row.name,
            'signal': signal,
            'price': last_row['Close'],
            'upper_band': last_row['upper_band'],
            'lower_band': last_row['lower_band'],
            'sma': last_row['sma']
        })
        
        return signal


class MACDStrategy(TradingAlgorithm):
    """Moving Average Convergence Divergence Strategy"""
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__(f"MACD_{fast_period}_{slow_period}_{signal_period}")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
    
    def calculate_macd(self, data: pd.DataFrame) -> Tuple[pd.Series, pd.Series, pd.Series]:
        # Calculate EMA values
        ema_fast = data['Close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=self.slow_period, adjust=False).mean()
        
        # Calculate MACD line and signal line
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        
        # Calculate histogram
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.slow_period + self.signal_period:
            return "HOLD"  # Not enough data
        
        # Calculate MACD values
        macd_line, signal_line, histogram = self.calculate_macd(data)
        data['macd_line'] = macd_line
        data['signal_line'] = signal_line
        data['histogram'] = histogram
        
        # Generate signals
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2] if len(data) > 1 else None
        
        if prev_row is not None:
            # MACD line crosses above signal line (Buy signal)
            if (prev_row['macd_line'] <= prev_row['signal_line']) and (last_row['macd_line'] > last_row['signal_line']):
                signal = "BUY"
                self.current_position = "LONG"
            # MACD line crosses below signal line (Sell signal)
            elif (prev_row['macd_line'] >= prev_row['signal_line']) and (last_row['macd_line'] < last_row['signal_line']):
                signal = "SELL"
                self.current_position = "SHORT"
            else:
                signal = "HOLD"
        else:
            signal = "HOLD"
        
        self.signals.append({
            'timestamp': last_row.name,
            'signal': signal,
            'price': last_row['Close'],
            'macd_line': last_row['macd_line'],
            'signal_line': last_row['signal_line'],
            'histogram': last_row['histogram']
        })
        
        return signal


class AlgorithmManager:
    """Manages multiple trading algorithms and combines their signals"""
    def __init__(self):
        self.algorithms = {}
        self.voting_weights = {}
    
    def add_algorithm(self, algorithm: TradingAlgorithm, weight: float = 1.0):
        """Add a trading algorithm with an optional weight"""
        self.algorithms[algorithm.name] = algorithm
        self.voting_weights[algorithm.name] = weight
    
    def remove_algorithm(self, algorithm_name: str):
        """Remove an algorithm by name"""
        if algorithm_name in self.algorithms:
            del self.algorithms[algorithm_name]
            del self.voting_weights[algorithm_name]
    
    def get_combined_signal(self, data: pd.DataFrame, method: str = "weighted_vote") -> Dict:
        """Combine signals from all algorithms
        
        Args:
            data: Price data
            method: How to combine signals ('majority_vote', 'weighted_vote', 'strongest_signal')
            
        Returns:
            Dict with combined signal and metadata
        """
        signals = {}
        for name, algorithm in self.algorithms.items():
            signals[name] = algorithm.generate_signal(data)
        
        if method == "majority_vote":
            return self._majority_vote(signals)
        elif method == "weighted_vote":
            return self._weighted_vote(signals)
        elif method == "strongest_signal":
            return self._strongest_signal(signals)
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _majority_vote(self, signals: Dict[str, str]) -> Dict:
        """Simple majority voting"""
        buy_count = sum(1 for signal in signals.values() if signal == "BUY")
        sell_count = sum(1 for signal in signals.values() if signal == "SELL")
        hold_count = sum(1 for signal in signals.values() if signal == "HOLD")
        
        if buy_count > sell_count and buy_count > hold_count:
            decision = "BUY"
        elif sell_count > buy_count and sell_count > hold_count:
            decision = "SELL"
        else:
            decision = "HOLD"
        
        return {
            "signal": decision,
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
            "total_algorithms": len(signals),
            "individual_signals": signals
        }
    
    def _weighted_vote(self, signals: Dict[str, str]) -> Dict:
        """Weighted voting based on algorithm weights"""
        buy_weight = sum(self.voting_weights[algo] for algo, signal in signals.items() if signal == "BUY")
        sell_weight = sum(self.voting_weights[algo] for algo, signal in signals.items() if signal == "SELL")
        hold_weight = sum(self.voting_weights[algo] for algo, signal in signals.items() if signal == "HOLD")
        
        if buy_weight > sell_weight and buy_weight > hold_weight:
            decision = "BUY"
        elif sell_weight > buy_weight and sell_weight > hold_weight:
            decision = "SELL"
        else:
            decision = "HOLD"
        
        return {
            "signal": decision,
            "buy_weight": buy_weight,
            "sell_weight": sell_weight,
            "hold_weight": hold_weight,
            "total_weight": sum(self.voting_weights.values()),
            "individual_signals": signals
        }
    
    def _strongest_signal(self, signals: Dict[str, str]) -> Dict:
        """Choose the strongest signal based on predefined hierarchy"""
        # Priority: BUY > SELL > HOLD
        if any(signal == "BUY" for signal in signals.values()):
            decision = "BUY"
        elif any(signal == "SELL" for signal in signals.values()):
            decision = "SELL"
        else:
            decision = "HOLD"
        
        return {
            "signal": decision,
            "reason": "strongest_signal_hierarchy",
            "individual_signals": signals
        }
    
    def get_algorithm_metrics(self) -> List[Dict]:
        """Get performance metrics for all algorithms"""
        return [algo.calculate_metrics() for algo in self.algorithms.values()]


# --- SUPER ALGORITHMS ---

class SuperTrend(TradingAlgorithm):
    """SuperTrend Algorithm"""
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        super().__init__(f"SuperTrend_{period}_{multiplier}")
        self.period = period
        self.multiplier = multiplier
    def calculate_atr(self, data: pd.DataFrame) -> pd.Series:
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(self.period).mean()
        return atr
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.period + 1:
            return "HOLD"
        atr = self.calculate_atr(data)
        hl2 = (data['High'] + data['Low']) / 2
        upperband = hl2 - (self.multiplier * atr)
        lowerband = hl2 + (self.multiplier * atr)
        close = data['Close']
        # Supertrend logic
        st = pd.Series(index=data.index, dtype=float)
        st.iloc[0] = upperband.iloc[0]
        for i in range(1, len(data)):
            if close.iloc[i-1] <= st.iloc[i-1]:
                st.iloc[i] = min(upperband.iloc[i], st.iloc[i-1])
            else:
                st.iloc[i] = max(lowerband.iloc[i], st.iloc[i-1])
        last = close.iloc[-1]
        last_st = st.iloc[-1]
        prev = close.iloc[-2]
        prev_st = st.iloc[-2]
        if prev <= prev_st and last > last_st:
            signal = "BUY"
        elif prev >= prev_st and last < last_st:
            signal = "SELL"
        else:
            signal = "HOLD"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'price': last, 'supertrend': last_st})
        return signal

class DonchianChannelBreakout(TradingAlgorithm):
    """Donchian Channel Breakout"""
    def __init__(self, window: int = 20):
        super().__init__(f"Donchian_{window}")
        self.window = window
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.window:
            return "HOLD"
        high = data['High'].rolling(self.window).max()
        low = data['Low'].rolling(self.window).min()
        last_close = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        last_high = high.iloc[-1]
        last_low = low.iloc[-1]
        signal = "HOLD"
        if prev_close < high.iloc[-2] and last_close >= last_high:
            signal = "BUY"
        elif prev_close > low.iloc[-2] and last_close <= last_low:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'price': last_close, 'donchian_high': last_high, 'donchian_low': last_low})
        return signal

class ADXTrend(TradingAlgorithm):
    """ADX Trend Strength"""
    def __init__(self, period: int = 14, threshold: float = 25):
        super().__init__(f"ADX_{period}_{threshold}")
        self.period = period
        self.threshold = threshold
    def calculate_adx(self, data: pd.DataFrame) -> pd.Series:
        high = data['High']
        low = data['Low']
        close = data['Close']
        plus_dm = high.diff()
        minus_dm = low.diff().abs()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = tr.rolling(self.period).mean()
        plus_di = 100 * (plus_dm.rolling(self.period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(self.period).mean() / atr)
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(self.period).mean()
        return adx, plus_di, minus_di
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < self.period + 1:
            return "HOLD"
        adx, plus_di, minus_di = self.calculate_adx(data)
        last_adx = adx.iloc[-1]
        last_plus = plus_di.iloc[-1]
        last_minus = minus_di.iloc[-1]
        signal = "HOLD"
        if last_adx > self.threshold:
            if last_plus > last_minus:
                signal = "BUY"
            elif last_minus > last_plus:
                signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'adx': last_adx, 'plus_di': last_plus, 'minus_di': last_minus})
        return signal

class HeikinAshiTrend(TradingAlgorithm):
    """Heikin-Ashi Trend Following"""
    def __init__(self):
        super().__init__("HeikinAshi")
    def heikin_ashi(self, data: pd.DataFrame) -> pd.DataFrame:
        ha = pd.DataFrame(index=data.index)
        ha['Close'] = (data['Open'] + data['High'] + data['Low'] + data['Close']) / 4
        ha['Open'] = (data['Open'].shift() + data['Close'].shift()) / 2
        ha['Open'].iloc[0] = data['Open'].iloc[0]
        ha['High'] = data[['High', 'Open', 'Close']].max(axis=1)
        ha['Low'] = data[['Low', 'Open', 'Close']].min(axis=1)
        return ha
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 2:
            return "HOLD"
        ha = self.heikin_ashi(data)
        last = ha.iloc[-1]
        prev = ha.iloc[-2]
        signal = "HOLD"
        # Uptrend: HA Close > HA Open (2 bars in a row)
        if prev['Close'] > prev['Open'] and last['Close'] > last['Open']:
            signal = "BUY"
        # Downtrend: HA Close < HA Open (2 bars in a row)
        elif prev['Close'] < prev['Open'] and last['Close'] < last['Open']:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'ha_close': last['Close'], 'ha_open': last['Open']})
        return signal

class IchimokuStrategy(TradingAlgorithm):
    """Ichimoku Kinko Hyo"""
    def __init__(self):
        super().__init__("Ichimoku")
    def calculate_ichimoku(self, data: pd.DataFrame):
        high9 = data['High'].rolling(window=9).max()
        low9 = data['Low'].rolling(window=9).min()
        tenkan = (high9 + low9) / 2
        high26 = data['High'].rolling(window=26).max()
        low26 = data['Low'].rolling(window=26).min()
        kijun = (high26 + low26) / 2
        senkou_a = ((tenkan + kijun) / 2).shift(26)
        high52 = data['High'].rolling(window=52).max()
        low52 = data['Low'].rolling(window=52).min()
        senkou_b = ((high52 + low52) / 2).shift(26)
        chikou = data['Close'].shift(-26)
        return tenkan, kijun, senkou_a, senkou_b, chikou
    def generate_signal(self, data: pd.DataFrame) -> str:
        if len(data) < 52:
            return "HOLD"
        tenkan, kijun, senkou_a, senkou_b, chikou = self.calculate_ichimoku(data)
        last_close = data['Close'].iloc[-1]
        last_tenkan = tenkan.iloc[-1]
        last_kijun = kijun.iloc[-1]
        last_senkou_a = senkou_a.iloc[-1]
        last_senkou_b = senkou_b.iloc[-1]
        last_chikou = chikou.iloc[-1]
        signal = "HOLD"
        # Buy if price above cloud, Tenkan > Kijun, and Chikou above price
        if (last_close > last_senkou_a and last_close > last_senkou_b and
            last_tenkan > last_kijun and last_chikou > last_close):
            signal = "BUY"
        # Sell if price below cloud, Tenkan < Kijun, and Chikou below price
        elif (last_close < last_senkou_a and last_close < last_senkou_b and
              last_tenkan < last_kijun and last_chikou < last_close):
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'tenkan': last_tenkan, 'kijun': last_kijun, 'senkou_a': last_senkou_a, 'senkou_b': last_senkou_b, 'chikou': last_chikou})
        return signal

# --- ML ALGORITHMS ---

try:
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, GRU, Dense, Dropout
    from tensorflow.keras.optimizers import Adam
    from tensorflow.keras.utils import to_categorical
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.neighbors import KNeighborsClassifier
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False


from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

class LSTMClassifierSignal(TradingAlgorithm):
    """LSTM Neural Network for Trading Signals (Keras/TensorFlow)"""
    def __init__(self, feature_cols=None, lookback=30, epochs=20, batch_size=16):
        super().__init__("LSTMClassifier")
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.lookback = lookback
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.is_trained = False
        self.n_features = len(self.feature_cols)

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)

    def create_sequences(self, data: pd.DataFrame):
        X, y = [], []
        values = data[self.feature_cols].values
        labels = data['label'].values
        for i in range(self.lookback, len(data)):
            X.append(values[i-self.lookback:i])
            y.append(labels[i])
        return np.array(X), np.array(y)

    def train(self, data: pd.DataFrame):
        if not TENSORFLOW_AVAILABLE:
            raise ImportError('tensorflow is not installed')
        df = self.prepare_features(data).copy()
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = 2  # 2=Sell, 1=Buy, 0=Hold
        df = df.dropna()
        X, y = self.create_sequences(df)
        y_cat = to_categorical(y, num_classes=3)
        self.model = Sequential([
            LSTM(32, input_shape=(self.lookback, self.n_features), return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')
        ])
        self.model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
        self.model.fit(X, y_cat, epochs=self.epochs, batch_size=self.batch_size, verbose=0)
        self.is_trained = True
        # ประเมิน accuracy บนเทรนเซ็ต
        loss, acc = self.model.evaluate(X, y_cat, verbose=0)
        self.train_accuracy = acc
        return acc

    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data).copy()
        if len(df) < self.lookback:
            return "HOLD"
        X = df[self.feature_cols].values[-self.lookback:]
        X = X.reshape((1, self.lookback, self.n_features))
        pred = self.model.predict(X, verbose=0)[0]
        idx = np.argmax(pred)
        signal = "HOLD"
        if idx == 1:
            signal = "BUY"
        elif idx == 2:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'probs': pred.tolist()})
        return signal

class GRUClassifierSignal(TradingAlgorithm):
    """GRU Neural Network for Trading Signals (Keras/TensorFlow)"""
    def __init__(self, feature_cols=None, lookback=30, epochs=20, batch_size=16):
        super().__init__("GRUClassifier")
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.lookback = lookback
        self.epochs = epochs
        self.batch_size = batch_size
        self.model = None
        self.is_trained = False
        self.n_features = len(self.feature_cols)

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)

    def create_sequences(self, data: pd.DataFrame):
        X, y = [], []
        values = data[self.feature_cols].values
        labels = data['label'].values
        for i in range(self.lookback, len(data)):
            X.append(values[i-self.lookback:i])
            y.append(labels[i])
        return np.array(X), np.array(y)

    def train(self, data: pd.DataFrame):
        if not TENSORFLOW_AVAILABLE:
            raise ImportError('tensorflow is not installed')
        df = self.prepare_features(data).copy()
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = 2  # 2=Sell, 1=Buy, 0=Hold
        df = df.dropna()
        X, y = self.create_sequences(df)
        y_cat = to_categorical(y, num_classes=3)
        self.model = Sequential([
            GRU(32, input_shape=(self.lookback, self.n_features), return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(3, activation='softmax')
        ])
        self.model.compile(optimizer=Adam(learning_rate=0.001), loss='categorical_crossentropy', metrics=['accuracy'])
        self.model.fit(X, y_cat, epochs=self.epochs, batch_size=self.batch_size, verbose=0)
        self.is_trained = True
        # ประเมิน accuracy บนเทรนเซ็ต
        loss, acc = self.model.evaluate(X, y_cat, verbose=0)
        self.train_accuracy = acc
        return acc

    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data).copy()
        if len(df) < self.lookback:
            return "HOLD"
        X = df[self.feature_cols].values[-self.lookback:]
        X = X.reshape((1, self.lookback, self.n_features))
        pred = self.model.predict(X, verbose=0)[0]
        idx = np.argmax(pred)
        signal = "HOLD"
        if idx == 1:
            signal = "BUY"
        elif idx == 2:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'probs': pred.tolist()})
        return signal


    """CatBoost Classifier for Trading Signals"""
    def __init__(self, feature_cols=None, iterations=100, random_state=42):
        super().__init__(f"CatBoost_{iterations}")
        self.iterations = iterations
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        if CATBOOST_AVAILABLE:
            self.model = CatBoostClassifier(iterations=iterations, random_state=random_state, verbose=0)
        else:
            self.model = None
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        if not CATBOOST_AVAILABLE:
            raise ImportError('catboost is not installed')
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class ExtraTreesSignal(TradingAlgorithm):
    """Extra Trees Classifier for Trading Signals"""
    def __init__(self, feature_cols=None, n_estimators=100, random_state=42):
        super().__init__(f"ExtraTrees_{n_estimators}")
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.model = ExtraTreesClassifier(n_estimators=n_estimators, random_state=random_state)
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class KNNClassifierSignal(TradingAlgorithm):
    """k-Nearest Neighbors Classifier for Trading Signals"""
    def __init__(self, feature_cols=None, n_neighbors=5):
        super().__init__(f"KNN_{n_neighbors}")
        self.n_neighbors = n_neighbors
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.model = KNeighborsClassifier(n_neighbors=n_neighbors)
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class ProphetForecastSignal(TradingAlgorithm):
    """Prophet Forecasting for Price Direction (not direct signal, but up/down)"""
    def __init__(self, periods=1):
        super().__init__(f"Prophet_{periods}")
        self.periods = periods
        self.model = Prophet() if PROPHET_AVAILABLE else None
        self.is_trained = False
        self.last_forecast = None
    def train(self, data: pd.DataFrame):
        if not PROPHET_AVAILABLE:
            raise ImportError('prophet is not installed')
        df = data.reset_index()[['index', 'Close']].rename(columns={'index': 'ds', 'Close': 'y'})
        self.model.fit(df)
        self.is_trained = True
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        last_date = data.index[-1]
        future = pd.DataFrame({'ds': pd.date_range(start=last_date, periods=self.periods+1, freq='D')[1:]})
        forecast = self.model.predict(future)
        last_close = data['Close'].iloc[-1]
        next_close = forecast['yhat'].iloc[0]
        self.last_forecast = next_close
        if next_close > last_close:
            signal = "BUY"
        elif next_close < last_close:
            signal = "SELL"
        else:
            signal = "HOLD"
        self.signals.append({'timestamp': future['ds'].iloc[0], 'signal': signal, 'forecast': next_close})
        return signal


    """Random Forest Classifier for Trading Signals"""
    def __init__(self, feature_cols=None, n_estimators=100, random_state=42):
        super().__init__(f"RandomForest_{n_estimators}")
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        # Add technical features if not present
        if 'EMA_10' not in df:
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        if 'EMA_21' not in df:
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        if 'RSI_14' not in df:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI_14'] = 100 - (100 / (1 + rs))
        if 'BB_upper' not in df or 'BB_lower' not in df:
            sma = df['Close'].rolling(window=20).mean()
            std = df['Close'].rolling(window=20).std()
            df['BB_upper'] = sma + (std * 2)
            df['BB_lower'] = sma - (std * 2)
        return df
    def train(self, data: pd.DataFrame):
        df = self.prepare_features(data)
        # สร้าง label: 1=Buy, -1=Sell, 0=Hold (เช่น ใช้ EMA cross)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            # ต้อง train ก่อน
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class XGBoostSignal(TradingAlgorithm):
    """XGBoost Classifier for Trading Signals"""
    def __init__(self, feature_cols=None, n_estimators=100, random_state=42):
        super().__init__(f"XGBoost_{n_estimators}")
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        if XGBOOST_AVAILABLE:
            self.model = xgb.XGBClassifier(n_estimators=n_estimators, random_state=random_state, use_label_encoder=False, eval_metric='mlogloss')
        else:
            self.model = None
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        if not XGBOOST_AVAILABLE:
            raise ImportError('xgboost is not installed')
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class LightGBMSignal(TradingAlgorithm):
    """LightGBM Classifier for Trading Signals"""
    def __init__(self, feature_cols=None, n_estimators=100, random_state=42):
        super().__init__(f"LightGBM_{n_estimators}")
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        if LIGHTGBM_AVAILABLE:
            self.model = lgb.LGBMClassifier(n_estimators=n_estimators, random_state=random_state)
        else:
            self.model = None
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        if not LIGHTGBM_AVAILABLE:
            raise ImportError('lightgbm is not installed')
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class SVMSignal(TradingAlgorithm):
    """Support Vector Machine for Trading Signals"""
    def __init__(self, feature_cols=None, random_state=42):
        super().__init__("SVM")
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.model = SVC(probability=True, random_state=random_state)
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class LogisticRegressionSignal(TradingAlgorithm):
    """Logistic Regression for Trading Signals"""
    def __init__(self, feature_cols=None, random_state=42):
        super().__init__("LogisticRegression")
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.model = LogisticRegression(random_state=random_state, max_iter=1000)
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

class MLPNeuralNetSignal(TradingAlgorithm):
    """MLP Neural Network for Trading Signals"""
    def __init__(self, feature_cols=None, random_state=42):
        super().__init__("MLPNeuralNet")
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.model = MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=500, random_state=random_state)
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        return RandomForestSignal().prepare_features(data)
    def train(self, data: pd.DataFrame):
        df = self.prepare_features(data)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal


    """Random Forest Classifier for Trading Signals"""
    def __init__(self, feature_cols=None, n_estimators=100, random_state=42):
        super().__init__(f"RandomForest_{n_estimators}")
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.feature_cols = feature_cols if feature_cols else ['Close', 'EMA_10', 'EMA_21', 'RSI_14', 'BB_upper', 'BB_lower']
        self.model = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state)
        self.is_trained = False
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        # Add technical features if not present
        if 'EMA_10' not in df:
            df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()
        if 'EMA_21' not in df:
            df['EMA_21'] = df['Close'].ewm(span=21, adjust=False).mean()
        if 'RSI_14' not in df:
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI_14'] = 100 - (100 / (1 + rs))
        if 'BB_upper' not in df or 'BB_lower' not in df:
            sma = df['Close'].rolling(window=20).mean()
            std = df['Close'].rolling(window=20).std()
            df['BB_upper'] = sma + (std * 2)
            df['BB_lower'] = sma - (std * 2)
        return df
    def train(self, data: pd.DataFrame):
        df = self.prepare_features(data)
        # สร้าง label: 1=Buy, -1=Sell, 0=Hold (เช่น ใช้ EMA cross)
        df['label'] = 0
        df.loc[df['EMA_10'] > df['EMA_21'], 'label'] = 1
        df.loc[df['EMA_10'] < df['EMA_21'], 'label'] = -1
        df = df.dropna()
        X = df[self.feature_cols]
        y = df['label']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=self.random_state)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        y_pred = self.model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        self.train_accuracy = acc
        return acc
    def generate_signal(self, data: pd.DataFrame) -> str:
        if not self.is_trained:
            # ต้อง train ก่อน
            return "HOLD"
        df = self.prepare_features(data)
        X = df[self.feature_cols].iloc[[-1]]
        pred = self.model.predict(X)[0]
        signal = "HOLD"
        if pred == 1:
            signal = "BUY"
        elif pred == -1:
            signal = "SELL"
        self.signals.append({'timestamp': data.index[-1], 'signal': signal, 'features': X.to_dict('records')[0]})
        return signal

# Example usage function
def execute_algorithm_trading(timeframe='1d', lookback_days=60):
    """
    Execute algorithmic trading using multiple strategies
    
    Args:
        timeframe: Data timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
        lookback_days: Number of days of historical data to analyze
    
    Returns:
        Trading recommendation with signals from different algorithms
    """
    # Fetch historical data
    price_data = fetch_gold_price_data(timeframe=timeframe, days=lookback_days)
    
    # Initialize algorithm manager
    manager = AlgorithmManager()
    
    # Add different algorithms with weights
    manager.add_algorithm(MACrossover(short_window=10, long_window=50), weight=1.0)
    manager.add_algorithm(RSIStrategy(period=14, overbought=70, oversold=30), weight=1.2)
    manager.add_algorithm(BollingerBandsStrategy(window=20, num_std=2.0), weight=1.0)
    manager.add_algorithm(MACDStrategy(fast_period=12, slow_period=26, signal_period=9), weight=1.5)
    
    # Get combined trading signal
    recommendation = manager.get_combined_signal(price_data, method="weighted_vote")
    
    # Add current price information
    current_price = price_data.iloc[-1]['Close'] if not price_data.empty else None
    recommendation['current_price'] = current_price
    
    # Add risk management if it's a trading signal
    if recommendation['signal'] in ['BUY', 'SELL']:
        account_balance = 10000  # Example value, should be fetched from account settings
        risk_percent = 2  # Example risk percentage
        risk_metrics = calculate_risk_metrics(
            entry_price=current_price,
            account_balance=account_balance,
            risk_percent=risk_percent,
            trade_direction="LONG" if recommendation['signal'] == 'BUY' else "SHORT"
        )
        recommendation['risk_metrics'] = risk_metrics
    
    return recommendation
