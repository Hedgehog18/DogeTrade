import argparse
from core import binance_api, backtest

def main():
    parser = argparse.ArgumentParser(description="Backtest EMA crossover strategy")
    parser.add_argument("--symbol", type=str, default="DOGEUSDT", help="Trading pair symbol (default: DOGEUSDT)")
    parser.add_argument("--interval", type=str, default="15m", help="Kline interval, e.g. 1m, 5m, 15m, 1h (default: 15m)")
    parser.add_argument("--limit", type=int, default=500, help="Number of candles to fetch (default: 500)")
    parser.add_argument("--fast", type=int, default=9, help="Fast EMA period (default: 9)")
    parser.add_argument("--slow", type=int, default=21, help="Slow EMA period (default: 21)")
    parser.add_argument("--capital", type=float, default=1000.0, help="Initial capital in USDT (default: 1000.0)")
    args = parser.parse_args()

    # Завантажуємо історичні дані
    df = binance_api.get_historical_futures_klines(args.symbol, args.interval, args.limit)

    # Запускаємо backtest
    results = backtest.backtest_ema_crossover(df, fast=args.fast, slow=args.slow, initial_capital=args.capital)

    # Виводимо результат
    print("\n📊 Backtest Results")
    print(f"Symbol: {args.symbol} | Interval: {args.interval} | Candles: {args.limit}")
    for k, v in results.items():
        print(f"{k}: {v}")

if __name__ == "__main__":
    main()
