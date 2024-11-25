import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import ta  # Technical Analysis library
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(0, 1))

    def preprocess_data(self, df):
        if df.empty:
            logger.error("DataFrame is empty.")
            return None

        # Ensure column names are in lowercase
        df.columns = df.columns.str.lower()

        # Adding technical indicators
        df = self.add_technical_indicators(df)

        # Selecting the features for training
        feature_columns = df.columns.tolist()
        data = df[feature_columns].values

        # Z-score normalization
        mean = np.mean(data, axis=0)
        std = np.std(data, axis=0)
        std[std == 0] = 1  # Avoid division by zero
        normalized_data = (data - mean) / std

        # Store mean and std for inverse transformations if needed
        self.mean = mean
        self.std = std

        return normalized_data


    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)

    def create_sequences(self, data, sequence_length, forecast_horizon=1):
        X = []
        y = []
        for i in range(len(data) - sequence_length - forecast_horizon + 1):
            X.append(data[i:(i + sequence_length)])
            # **Shift labels to predict the next time step**
            y.append(data[(i + sequence_length):(i + sequence_length + forecast_horizon)])
        X = np.array(X)
        y = np.array(y)
        return X, y


    def split_data(self, X, y, train_size=0.8):
        split_index = int(len(X) * train_size)
        X_train, X_val = X[:split_index], X[split_index:]
        y_train, y_val = y[:split_index], y[split_index:]
        return X_train, X_val, y_train, y_val

    def add_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to the DataFrame.
        """
        try:
            logger.debug("Adding technical indicators.")

            # Moving Averages
            data['ma5'] = data['close'].rolling(window=5).mean()
            data['ma10'] = data['close'].rolling(window=10).mean()
            data['ma20'] = data['close'].rolling(window=20).mean()

            # Exponential Moving Average
            data['ema50'] = data['close'].ewm(span=50, adjust=False).mean()

            # Stochastic Oscillator
            stochastic = ta.momentum.StochasticOscillator(
                high=data['high'], low=data['low'], close=data['close'], window=14
            )
            data['stochastic_k'] = stochastic.stoch()

            # Relative Strength Index (RSI)
            rsi = ta.momentum.RSIIndicator(close=data['close'], window=14)
            data['rsi'] = rsi.rsi()

            # Moving Average Convergence Divergence (MACD)
            macd = ta.trend.MACD(close=data['close'])
            data['macd'] = macd.macd()
            data['macd_diff'] = macd.macd_diff()
            data['macd_signal'] = macd.macd_signal()

            # Bollinger Bands
            bollinger = ta.volatility.BollingerBands(close=data['close'], window=20)
            data['bb_h'] = bollinger.bollinger_hband()
            data['bb_l'] = bollinger.bollinger_lband()
            
            # **Add Bollinger Band Width**
            data['bb_width'] = data['bb_h'] - data['bb_l']

            # **Add Rate of Change (ROC)**
            data['roc'] = ta.momentum.ROCIndicator(close=data['close'], window=14).roc()
            # Close Price Difference
            data['close_diff'] = data['close'].diff()
            data['close_diff'].fillna(0, inplace=True)

            # Percent Change in Close Price
            data['percent_change_close'] = data['close'].pct_change() * 100
            data['percent_change_close'].fillna(0, inplace=True)

            # Handling NaN values after adding indicators
            data.bfill(inplace=True)
            data.ffill(inplace=True)


            logger.info("Technical indicators added.")
            return data

        except Exception as e:
            logger.exception("Error adding technical indicators.")
            raise e
