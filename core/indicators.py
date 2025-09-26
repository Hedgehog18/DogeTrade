import pandas as pd

def sma(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
    """Проста ковзна середня (Simple Moving Average)."""
    return df[column].rolling(window=period).mean()

def ema(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
    """Експоненціальна ковзна середня (Exponential Moving Average)."""
    return df[column].ewm(span=period, adjust=False).mean()

def rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
    """Індекс відносної сили (Relative Strength Index)."""
    delta = df[column].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, column: str = "close") -> pd.DataFrame:
    """MACD (Moving Average Convergence Divergence)."""
    ema_fast = ema(df, fast, column)
    ema_slow = ema(df, slow, column)
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal_line,
        "hist": histogram
    }, index=df.index)

def bollinger_bands(df: pd.DataFrame, period: int = 20, std_factor: float = 2.0, column: str = "close") -> pd.DataFrame:
    """Смуги Боллінджера (Bollinger Bands)."""
    sma_ = sma(df, period, column)
    std = df[column].rolling(window=period).std()
    upper = sma_ + (std_factor * std)
    lower = sma_ - (std_factor * std)
    return pd.DataFrame({
        "middle": sma_,
        "upper": upper,
        "lower": lower
    }, index=df.index)


def macd(df, fast=12, slow=26, signal=9):
    """
    Обчислює MACD (Moving Average Convergence Divergence).
    Повертає три Series: macd_line, signal_line, histogram
    """
    if len(df) < slow:
        return None, None, None

    fast_ema = df["close"].ewm(span=fast, adjust=False).mean()
    slow_ema = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram
