import pandas as pd
from binance.client import Client


# Binance Futures client (публічний, без ключів)
client = Client()


def get_historical_futures_klines(symbol: str, interval: str, limit: int = 100) -> pd.DataFrame:
    """
    Завантажує історичні свічки з Binance Futures (USDT-M).
    """
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=limit)

    df = pd.DataFrame(klines, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base", "taker_buy_quote", "ignore"
    ])

    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)

    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df
