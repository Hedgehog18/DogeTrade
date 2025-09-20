import pandas as pd
from binance.client import Client


def get_historical_klines(client: Client, symbol="DOGEUSDT", interval="1m", limit=100) -> pd.DataFrame:
    """
    Отримати історичні свічки (OHLCV) з Binance.
    Повертає pandas.DataFrame у форматі для mplfinance.

    :param client: Binance Client
    :param symbol: Торгова пара (наприклад, "DOGEUSDT")
    :param interval: Інтервал свічки ("1m", "5m", "15m", "1h" тощо)
    :param limit: Кількість свічок (до 1000)
    :return: DataFrame з колонками [Open, High, Low, Close, Volume], індекс - DateTime
    """
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)

    df = pd.DataFrame(klines, columns=[
        "timestamp", "Open", "High", "Low", "Close", "Volume",
        "Close_time", "Quote_asset_volume", "Number_of_trades",
        "Taker_buy_base", "Taker_buy_quote", "Ignore"
    ])

    # Конвертуємо типи
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    df = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return df
