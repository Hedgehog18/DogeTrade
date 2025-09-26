import argparse
import pandas as pd
from core.binance_api import get_historical_futures_klines
from core import signals


def run_backtest(strategy, symbol, interval, limit, capital=1000, **kwargs):
    df = get_historical_futures_klines(symbol, interval, limit)
    balance = capital
    position = None
    entry_price = 0
    trades = []

    for i in range(len(df)):
        sub_df = df.iloc[: i + 1]

        # Виклик потрібної стратегії
        if strategy == "EMA":
            sig = signals.ema_crossover(sub_df, fast=kwargs.get("fast", 9), slow=kwargs.get("slow", 21))
        elif strategy == "RSI":
            sig = signals.rsi_strategy(sub_df, period=kwargs.get("period", 14))
        elif strategy == "MACD":
            sig = signals.macd_strategy(
                sub_df,
                fast=kwargs.get("fast", 12),
                slow=kwargs.get("slow", 26),
                signal=kwargs.get("signal", 9),
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

        price = sub_df["close"].iloc[-1]

        if sig == "BUY" and position is None:
            position = "LONG"
            entry_price = price
            trades.append(("BUY", price))
        elif sig == "SELL" and position == "LONG":
            balance *= price / entry_price
            trades.append(("SELL", price))
            position = None

    if position == "LONG":  # закриваємо позицію в кінці
        balance *= df["close"].iloc[-1] / entry_price
        trades.append(("SELL (final)", df["close"].iloc[-1]))

    return balance, trades


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", choices=["EMA", "RSI", "MACD"], required=True, help="Стратегія для тесту")
    parser.add_argument("--symbol", default="DOGEUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--capital", type=float, default=1000)
    parser.add_argument("--fast", type=int, default=12)
    parser.add_argument("--slow", type=int, default=26)
    parser.add_argument("--signal", type=int, default=9)
    parser.add_argument("--period", type=int, default=14)
    args = parser.parse_args()

    final_balance, trades = run_backtest(
        args.strategy,
        args.symbol,
        args.interval,
        args.limit,
        capital=args.capital,
        fast=args.fast,
        slow=args.slow,
        signal=args.signal,
        period=args.period,
    )

    print(f"\n📊 Backtest Results ({args.strategy})")
    print(f"Symbol: {args.symbol} | Interval: {args.interval} | Candles: {args.limit}")
    print(f"Initial Capital: {args.capital}")
    print(f"Final Balance: {final_balance}")
    print(f"Net Profit: {final_balance - args.capital}")
    print(f"Return %: {(final_balance - args.capital) / args.capital * 100:.2f}")
    print(f"Trades Count: {len(trades)}")
