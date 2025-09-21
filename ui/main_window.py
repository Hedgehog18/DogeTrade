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

        # === Правий блок з кнопками ===
        right_frame = ctk.CTkFrame(top_frame)
        right_frame.pack(side="right")

        # Кнопка тестових логів
        test_button = ctk.CTkButton(right_frame, text="Test Log", command=self.test_log)
        test_button.pack(side="left", padx=5)

        # Таймфрейм селектор
        self.interval_var = tk.StringVar(value="1m")
        intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]

        interval_menu = ctk.CTkOptionMenu(
            right_frame, variable=self.interval_var, values=intervals,
            command=self.change_interval
        )
        interval_menu.pack(side="left", padx=5)

        # Кнопка ⚙️ (налаштування)
        settings_button = ctk.CTkButton(
            right_frame, text="⚙️", width=40,
            command=self.open_settings
        )
        settings_button.pack(side="left", padx=5)

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

        # 🔹 Збільшення шрифту в таблиці
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 13))
        style.configure("Treeview.Heading", font=("Arial", 14, "bold"))

        self.tree.heading("time", text="Time")
        self.tree.heading("signal", text="Signal")
        self.tree.heading("price", text="Price")

        self.tree.column("time", width=100)
        self.tree.column("signal", width=70)
        self.tree.column("price", width=80)

        self.tree.pack(side="left", fill="both", expand=True)

        # 🔹 Додаємо бокову прокрутку
        tree_scrollbar = ttk.Scrollbar(signals_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=tree_scrollbar.set)
        tree_scrollbar.pack(side="right", fill="y")

        # Нижня частина (логи + кнопки)
        bottom_frame = ctk.CTkFrame(vertical_pane, height=100)
        vertical_pane.add(bottom_frame)

        # Логи
        self.log_text = scrolledtext.ScrolledText(
            bottom_frame, height=5, bg="#1e1e1e", fg="white", font=("Consolas", 13)
        )
        self.log_text.pack(fill="both", expand=True, side="left")

        # Кнопка очищення логів
        clear_button = ctk.CTkButton(bottom_frame, text="Clear Logs", command=self.clear_logs)
        clear_button.pack(side="right", padx=5, pady=5)

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

    # ================== SETTINGS MODAL ==================
    def open_settings(self):
        """Відкрити вікно налаштувань"""
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x350")
        settings_window.grab_set()  # робимо модальним

        title_label = ctk.CTkLabel(settings_window, text="Application Settings", font=("Arial", 18, "bold"))
        title_label.pack(pady=15)

        # API Key
        ctk.CTkLabel(settings_window, text="API Key:").pack(anchor="w", padx=20, pady=(5, 0))
        api_key_entry = ctk.CTkEntry(settings_window, width=300)
        api_key_entry.pack(padx=20, pady=5)

        # API Secret
        ctk.CTkLabel(settings_window, text="API Secret:").pack(anchor="w", padx=20, pady=(5, 0))
        api_secret_entry = ctk.CTkEntry(settings_window, width=300, show="*")
        api_secret_entry.pack(padx=20, pady=5)

        # Trading Pair
        ctk.CTkLabel(settings_window, text="Trading Pair:").pack(anchor="w", padx=20, pady=(5, 0))
        trading_pair = ctk.CTkOptionMenu(
            settings_window, values=["DOGEUSDT", "BTCUSDT", "ETHUSDT", "SOLUSDT"]
        )
        trading_pair.set("DOGEUSDT")
        trading_pair.pack(padx=20, pady=5)

        # Save Button
        save_button = ctk.CTkButton(settings_window, text="Save", command=lambda: self.save_settings(
            api_key_entry.get(),
            api_secret_entry.get(),
            trading_pair.get()
        ))
        save_button.pack(pady=20)

    def save_settings(self, api_key, api_secret, pair):
        """Збереження налаштувань (поки що тільки в лог)"""
        self.add_log(f"Settings saved: API_KEY={api_key}, API_SECRET={'*' * len(api_secret)}, PAIR={pair}", force=True)

    # ===================================================

    def _start_sockets(self):
        interval = self.interval_var.get()
        self.ticker_socket_key = self.twm.start_futures_multiplex_socket(
            callback=self.handle_ticker,
            streams=["dogeusdt@ticker"]
        )
        self.kline_socket_key = self.twm.start_futures_multiplex_socket(
            callback=self.handle_kline,
            streams=[f"dogeusdt@kline_{interval}"]
        )

    def add_log(self, message: str, force: bool = False):
        now = time.time()
        if force or now - self.last_log_time >= 5:
            self.log_text.insert("end", message + "\n")
            self.last_log_time = now

    def clear_logs(self):
        self.log_text.delete("1.0", tk.END)

    def test_log(self):
        import random
        signals = ["BUY", "SELL", "HOLD"]
        sig = random.choice(signals)
        self.update_signal(sig, price=0.12345)
        self.add_log(f"Test log message: {sig}", force=True)

    def handle_ticker(self, msg):
        if not self.running:
            return
        try:
            data = msg.get("data", msg)
            price = float(data["c"])
            self.after(0, self.update_price_label, price)
        except Exception as e:
            if self.running:
                self.after(0, self.add_log, f"Ticker error: {e}", True)

    def update_price_label(self, price: float):
        self.price_label.configure(text=f"Last Price: {price:.5f}")
        self.add_log(f"Futures Price updated: {price:.5f}")

    def update_signal(self, signal: str, price: float):
        colors = {"BUY": "green", "SELL": "red", "HOLD": "gray"}
        self.signal_label.configure(text=f"Signal: {signal}", text_color=colors.get(signal, "gray"))

        tag = signal.lower()
        self.tree.insert(
            "", "end",
            values=(pd.Timestamp.now().strftime("%H:%M:%S"), signal, f"{price:.5f}"),
            tags=(tag,)
        )
        self.tree.yview_moveto(1.0)
        self.tree.tag_configure("buy", foreground="green")
        self.tree.tag_configure("sell", foreground="red")
        self.tree.tag_configure("hold", foreground="gray")

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
                self.after(0, self.update_signal, "HOLD", c)
                self.after(0, self.add_log, f"New Futures candle: {t} Close={c:.5f}", True)

        except Exception as e:
            if self.running:
                self.after(0, self.add_log, f"Kline error: {e}", True)

    def update_chart(self):
        self.chart_canvas.get_tk_widget().destroy()
        self.chart_canvas = create_candlestick_chart(self.chart_frame, self.df)

    def change_interval(self, new_interval):
        self.add_log(f"Changing timeframe to {new_interval}", force=True)
        self.df = get_historical_futures_klines("DOGEUSDT", new_interval, 100)
        self.update_chart()
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
