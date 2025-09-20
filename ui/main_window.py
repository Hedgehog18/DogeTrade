import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
from binance import ThreadedWebsocketManager
import pandas as pd
import time

from core.binance_api import get_historical_futures_klines
from core import config
from ui.chart import create_candlestick_chart


class DogeTradeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування головного вікна
        self.title("DogeTrade Signals (Futures)")
        self.geometry("1000x600")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Прапорець для завершення
        self.running = True

        # DataFrame для свічок
        self.df = None

        # Ключі сокетів
        self.kline_socket_key = None
        self.ticker_socket_key = None

        # === Верхня панель ===
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.pair_label = ctk.CTkLabel(top_frame, text="DOGE/USDT (Futures)", font=("Arial", 18, "bold"))
        self.pair_label.pack(side="left", padx=10)

        self.price_label = ctk.CTkLabel(top_frame, text="Last Price: 0.00000", font=("Arial", 16))
        self.price_label.pack(side="left", padx=20)

        self.signal_label = ctk.CTkLabel(top_frame, text="Signal: HOLD", font=("Arial", 16), text_color="gray")
        self.signal_label.pack(side="left", padx=20)

        # Таймфрейм селектор
        self.interval_var = tk.StringVar(value="1m")
        intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]

        interval_menu = ctk.CTkOptionMenu(
            top_frame, variable=self.interval_var, values=intervals,
            command=self.change_interval
        )
        interval_menu.pack(side="right", padx=10)

        test_button = ctk.CTkButton(top_frame, text="Test Log", command=self.test_log)
        test_button.pack(side="right", padx=10)

        # === Основний розподіл (вертикальний) ===
        vertical_pane = tk.PanedWindow(
            self, orient=tk.VERTICAL, sashrelief="raised", sashwidth=6, bg="gray30"
        )
        vertical_pane.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # === Горизонтальний розподіл (графік ↔ сигнали) ===
        horizontal_pane = tk.PanedWindow(
            vertical_pane, orient=tk.HORIZONTAL, sashrelief="raised", sashwidth=6, bg="gray30"
        )
        vertical_pane.add(horizontal_pane, stretch="always")

        # Ліва частина (графік)
        self.chart_frame = ctk.CTkFrame(horizontal_pane)
        horizontal_pane.add(self.chart_frame, stretch="always")

        # Історичні дані з Futures
        self.df = get_historical_futures_klines("DOGEUSDT", "1m", 100)

        # Малюємо свічковий графік
        self.chart_canvas = create_candlestick_chart(self.chart_frame, self.df)

        # Права частина (історія сигналів)
        signals_frame = ctk.CTkFrame(horizontal_pane, width=250)
        horizontal_pane.add(signals_frame)

        history_label = ctk.CTkLabel(signals_frame, text="Signal History", font=("Arial", 14, "bold"))
        history_label.pack(pady=5)

        self.tree = ttk.Treeview(signals_frame, columns=("time", "signal", "price"), show="headings", height=15)
        self.tree.heading("time", text="Time")
        self.tree.heading("signal", text="Signal")
        self.tree.heading("price", text="Price")

        self.tree.column("time", width=100)
        self.tree.column("signal", width=70)
        self.tree.column("price", width=80)

        self.tree.pack(fill="both", expand=True)

        # Нижня частина (логи)
        bottom_frame = ctk.CTkFrame(vertical_pane, height=100)
        vertical_pane.add(bottom_frame)

        self.log_text = scrolledtext.ScrolledText(
            bottom_frame, height=5, bg="#1e1e1e", fg="white", font=("Consolas", 13)
        )
        self.log_text.pack(fill="both", expand=True)

        # Логування (затримка)
        self.last_log_time = 0

        # Запускаємо WebSocket
        self.twm = ThreadedWebsocketManager(
            api_key=config.BINANCE_API_KEY,
            api_secret=config.BINANCE_API_SECRET
        )
        self.twm.start()

        # Запуск futures сокетів
        self._start_sockets()

        self.add_log("Connected to Binance Futures WebSocket", force=True)

    def _start_sockets(self):
        """Запуск futures ticker та kline через multiplex"""
        interval = self.interval_var.get()

        # Ціна (ticker)
        self.ticker_socket_key = self.twm.start_futures_multiplex_socket(
            callback=self.handle_ticker,
            streams=["dogeusdt@ticker"]
        )

        # Свічки (kline)
        self.kline_socket_key = self.twm.start_futures_multiplex_socket(
            callback=self.handle_kline,
            streams=[f"dogeusdt@kline_{interval}"]
        )

    def add_log(self, message: str, force: bool = False):
        now = time.time()
        if force or now - self.last_log_time >= 5:
            self.log_text.insert("end", message + "\n")
            self.last_log_time = now

    def test_log(self):
        self.add_log("Test log message", force=True)

    def handle_ticker(self, msg):
        if not self.running:
            return
        try:
            data = msg.get("data", msg)  # multiplex повертає {"stream":..., "data":...}
            price = float(data["c"])
            self.after(0, self.update_price_label, price)
        except Exception as e:
            if self.running:
                self.after(0, self.add_log, f"Ticker error: {e}", True)

    def update_price_label(self, price: float):
        self.price_label.configure(text=f"Last Price: {price:.5f}")
        self.add_log(f"Futures Price updated: {price:.5f}")

    def handle_kline(self, msg):
        if not self.running:
            return
        try:
            data = msg.get("data", msg)
            k = data["k"]
            t = pd.to_datetime(k["t"], unit="ms")
            o, h, l, c, v = map(float, [k["o"], k["h"], k["l"], k["c"], k["v"]])
            closed = k["x"]

            if closed:
                self.df.loc[t] = [o, h, l, c, v]
                self.after(0, self.update_chart)
                self.after(0, self.add_log, f"New Futures candle: {t} Close={c:.5f}", True)

        except Exception as e:
            if self.running:
                self.after(0, self.add_log, f"Kline error: {e}", True)

    def update_chart(self):
        self.chart_canvas.get_tk_widget().destroy()
        self.chart_canvas = create_candlestick_chart(self.chart_frame, self.df)

    def change_interval(self, new_interval):
        """Перезапуск kline socket для нового таймфрейму"""
        self.add_log(f"Changing timeframe to {new_interval}", force=True)

        # Оновлюємо історичні дані
        self.df = get_historical_futures_klines("DOGEUSDT", new_interval, 100)
        self.update_chart()

        # Перезапуск kline socket
        if self.kline_socket_key is not None:
            self.twm.stop_socket(self.kline_socket_key)

        self.kline_socket_key = self.twm.start_futures_multiplex_socket(
            callback=self.handle_kline,
            streams=[f"dogeusdt@kline_{new_interval}"]
        )

    def on_closing(self):
        self.running = False
        if self.twm is not None:
            try:
                self.twm.stop()
            except Exception:
                pass
        self.destroy()
