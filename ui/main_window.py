# ui/main_window.py
import tkinter as tk
from tkinter import ttk, scrolledtext
import customtkinter as ctk
from binance import ThreadedWebsocketManager
import pandas as pd
import time
from core import signals

from core.binance_api import get_historical_futures_klines
# from core import config
from ui.chart import create_candlestick_chart
from core.database import get_settings, save_settings


def _symbol_to_label(symbol: str) -> str:
    s = symbol.upper()
    return f"{s[:-4]}/USDT (Futures)" if s.endswith("USDT") else f"{s} (Futures)"


class DogeTradeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DogeTrade Signals (Futures)")
        self.geometry("1000x600")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.running = True

        # === settings from DB (fallback to config) ===
        s = get_settings() or {}
        self.symbol = s.get("trading_pair", "DOGEUSDT")
        default_tf = s.get("default_timeframe", "1m")
        self.api_key = s.get("api_key", "")
        self.api_secret = s.get("api_secret", "")

        self.df = None
        self.kline_socket_key = None
        self.ticker_socket_key = None
        self.selected_strategy = "EMA"  # 🔹 стратегія за замовчуванням

        # === top bar ===
        top = ctk.CTkFrame(self, height=50)
        top.pack(side="top", fill="x", padx=5, pady=5)

        self.pair_label = ctk.CTkLabel(top, text=_symbol_to_label(self.symbol), font=("Arial", 18, "bold"))
        self.pair_label.pack(side="left", padx=10)

        self.price_label = ctk.CTkLabel(top, text="Last Price: 0.00000", font=("Arial", 16))
        self.price_label.pack(side="left", padx=20)

        self.signal_label = ctk.CTkLabel(top, text="Signal: HOLD", font=("Arial", 16), text_color="gray")
        self.signal_label.pack(side="left", padx=20)

        # right side order: Test Log | 1m | ⚙️
        self.interval_var = tk.StringVar(value=default_tf)
        intervals = ["1m", "5m", "15m", "1h", "4h", "1d"]

        settings_btn = ctk.CTkButton(top, text="⚙️", width=40, command=self.open_settings_window)
        settings_btn.pack(side="right", padx=10)

        interval_menu = ctk.CTkOptionMenu(top, variable=self.interval_var, values=intervals, command=self.change_interval)
        interval_menu.pack(side="right", padx=10)

        test_btn = ctk.CTkButton(top, text="Test Log", command=self.test_log)
        test_btn.pack(side="right", padx=10)

        # === panes ===
        vpane = tk.PanedWindow(self, orient=tk.VERTICAL, sashrelief="raised", sashwidth=6, bg="gray30")
        vpane.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        hpane = tk.PanedWindow(vpane, orient=tk.HORIZONTAL, sashrelief="raised", sashwidth=6, bg="gray30")
        vpane.add(hpane, stretch="always")

        # chart (left)
        self.chart_frame = ctk.CTkFrame(hpane)
        hpane.add(self.chart_frame, stretch="always")

        self.df = get_historical_futures_klines(self.symbol, self.interval_var.get(), 100)
        self.chart_canvas = create_candlestick_chart(self.chart_frame, self.df)

        # signal history (right)
        right = ctk.CTkFrame(hpane, width=250)
        hpane.add(right)

        ctk.CTkLabel(right, text="Signal History", font=("Arial", 14, "bold")).pack(pady=5)

        self.tree = ttk.Treeview(right, columns=("time", "signal", "price"), show="headings", height=15)
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

        sbar = ttk.Scrollbar(right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sbar.set)
        sbar.pack(side="right", fill="y")

        # logs (bottom)
        bottom = ctk.CTkFrame(vpane, height=100)
        vpane.add(bottom)

        # Ліва частина (для логів)
        logs_frame = ctk.CTkFrame(bottom)
        logs_frame.pack(side="left", fill="both", expand=True)

        self.log_text = scrolledtext.ScrolledText(
            logs_frame, height=5, bg="#1e1e1e", fg="white", font=("Consolas", 13)
        )
        self.log_text.pack(fill="both", expand=True)

        # Права частина (для кнопок)
        right_controls = ctk.CTkFrame(bottom, width=120)
        right_controls.pack(side="right", fill="y", padx=5, pady=5)

        # Кнопка очистки логів (свій колір)
        self.clear_btn = ctk.CTkButton(
            right_controls,
            text="Clear Logs",
            width=100,
            fg_color="gray30",  # темно-сірий фон
            hover_color="gray40",  # трохи світліший при наведенні
            command=self.clear_logs
        )
        self.clear_btn.pack(side="top", padx=5, pady=5)

        # Кнопки вибору стратегії
        self.ema_button = ctk.CTkButton(
            right_controls, text="EMA", width=100,
            command=lambda: self.set_strategy("EMA")
        )
        self.ema_button.pack(side="top", padx=5, pady=5)

        self.rsi_button = ctk.CTkButton(
            right_controls, text="RSI", width=100,
            command=lambda: self.set_strategy("RSI")
        )
        self.rsi_button.pack(side="top", padx=5, pady=5)

        self.macd_button = ctk.CTkButton(
            right_controls, text="MACD", width=100,
            command=lambda: self.set_strategy("MACD")
        )
        self.macd_button.pack(side="top", padx=5, pady=5)

        self.highlight_strategy_button("EMA")
        self.last_log_time = 0

        # websockets (start once)
        self.twm = ThreadedWebsocketManager(api_key=self.api_key, api_secret=self.api_secret)
        self.twm.start()
        self._start_sockets()

        self.add_log("Connected to Binance Futures WebSocket", force=True)

    # ===== strategy controls =====
    def set_strategy(self, strategy: str):
        self.selected_strategy = strategy
        self.highlight_strategy_button(strategy)
        self.add_log(f"Strategy switched to {strategy}", force=True)

    def highlight_strategy_button(self, strategy: str):
        # Скидаємо стилі
        self.ema_button.configure(fg_color="transparent")
        self.rsi_button.configure(fg_color="transparent")
        self.macd_button.configure(fg_color="transparent")

        # Виділяємо активну
        if strategy == "EMA":
            self.ema_button.configure(fg_color="blue")
        elif strategy == "RSI":
            self.rsi_button.configure(fg_color="blue")
        elif strategy == "MACD":
            self.macd_button.configure(fg_color="blue")

    # ===== sockets =====
    def _start_sockets(self):
        interval = self.interval_var.get()
        sym = self.symbol.lower()

        # stop old
        if self.ticker_socket_key:
            try:
                self.twm.stop_socket(self.ticker_socket_key)
            except KeyError:
                pass
            except Exception:
                pass
            self.ticker_socket_key = None

        if self.kline_socket_key:
            try:
                self.twm.stop_socket(self.kline_socket_key)
            except KeyError:
                pass
            except Exception:
                pass
            self.kline_socket_key = None

        # start new
        self.ticker_socket_key = self.twm.start_futures_multiplex_socket(
            callback=self.handle_ticker,
            streams=[f"{sym}@ticker"]
        )
        self.kline_socket_key = self.twm.start_futures_multiplex_socket(
            callback=self.handle_kline,
            streams=[f"{sym}@kline_{interval}"]
        )

    # ===== logs & ui =====
    def add_log(self, message: str, force: bool = False):
        now = time.time()
        if force or now - self.last_log_time >= 5:
            self.log_text.insert("end", message + "\n")
            self.last_log_time = now

    def clear_logs(self):
        self.log_text.delete("1.0", tk.END)

    def test_log(self):
        import random
        sig = random.choice(["BUY", "SELL", "HOLD"])
        self.update_signal(sig, price=0.12345)
        self.add_log(f"Test log message: {sig}", force=True)

    # ===== handlers =====
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
        self.tree.insert("", "end",
                         values=(pd.Timestamp.now().strftime("%H:%M:%S"), signal, f"{price:.5f}"),
                         tags=(tag,))
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
            if k["x"]:  # свічка закрита
                self.df.loc[t] = [o, h, l, c, v]

                self.after(0, self.update_chart)

                # 🔹 вибір стратегії
                if self.selected_strategy == "EMA":
                    signal = signals.ema_crossover(self.df, fast=9, slow=21)
                elif self.selected_strategy == "RSI":
                    signal = signals.rsi_strategy(self.df, period=14)
                elif self.selected_strategy == "MACD":
                    signal = signals.macd_strategy(self.df, fast=12, slow=26, signal=9)
                else:
                    signal = "HOLD"

                self.after(0, self.update_signal, signal, c)
                self.after(0, self.add_log, f"New Futures candle: {t} Close={c:.5f}", True)
        except Exception as e:
            if self.running:
                self.after(0, self.add_log, f"Kline error: {e}", True)

    def update_chart(self):
        self.chart_canvas.get_tk_widget().destroy()
        self.chart_canvas = create_candlestick_chart(self.chart_frame, self.df)

    def change_interval(self, new_interval):
        self.add_log(f"Changing timeframe to {new_interval}", force=True)
        self.df = get_historical_futures_klines(self.symbol, new_interval, 100)
        self.update_chart()
        self._start_sockets()

    # ===== settings modal =====
    def _attach_paste_support(self, entry: ctk.CTkEntry):
        """Надійна підтримка вставки: Ctrl+V, Shift+Insert, <<Paste>>, правий клік."""
        def paste_from_clipboard(_=None):
            try:
                txt = self.clipboard_get()
            except Exception:
                return "break"
            entry.insert(tk.INSERT, txt)
            return "break"

        for ev in ("<Control-v>", "<Control-V>", "<<Paste>>", "<Shift-Insert>"):
            entry.bind(ev, lambda e, f=paste_from_clipboard: f())

        try:
            inner = entry._entry  # type: ignore[attr-defined]
            for ev in ("<Control-v>", "<Control-V>", "<<Paste>>", "<Shift-Insert>"):
                inner.bind(ev, lambda e, f=paste_from_clipboard: f())
        except Exception:
            pass

        menu = tk.Menu(entry, tearoff=0)
        menu.add_command(label="Paste", command=paste_from_clipboard)

        def show_menu(e):
            try:
                menu.tk_popup(e.x_root, e.y_root)
            finally:
                menu.grab_release()

        entry.bind("<Button-3>", show_menu)

    def open_settings_window(self):
        s = get_settings() or {
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "trading_pair": self.symbol,
            "default_timeframe": self.interval_var.get(),
        }

        win = ctk.CTkToplevel(self)
        win.title("Налаштування")
        win.geometry("420x360")
        win.grab_set()
        win.focus_set()

        ctk.CTkLabel(win, text="Application Settings", font=("Arial", 18, "bold")).pack(pady=12)

        ctk.CTkLabel(win, text="API Key:").pack(anchor="w", padx=20, pady=(8, 0))
        api_key_entry = ctk.CTkEntry(win, show="")
        api_key_entry.insert(0, s.get("api_key", ""))
        api_key_entry.pack(fill="x", padx=20)
        self._attach_paste_support(api_key_entry)

        ctk.CTkLabel(win, text="API Secret:").pack(anchor="w", padx=20, pady=(8, 0))
        api_secret_entry = ctk.CTkEntry(win, show="*")
        api_secret_entry.insert(0, s.get("api_secret", ""))
        api_secret_entry.pack(fill="x", padx=20)
        self._attach_paste_support(api_secret_entry)

        ctk.CTkLabel(win, text="Trading Pair:").pack(anchor="w", padx=20, pady=(8, 0))
        tp_var = tk.StringVar(value=s.get("trading_pair", "DOGEUSDT"))
        ctk.CTkOptionMenu(win, variable=tp_var,
                          values=["DOGEUSDT", "SOLUSDT", "BTCUSDT", "ETHUSDT"]).pack(fill="x", padx=20)

        ctk.CTkLabel(win, text="Default Timeframe:").pack(anchor="w", padx=20, pady=(8, 0))
        tf_var = tk.StringVar(value=s.get("default_timeframe", "1m"))
        ctk.CTkOptionMenu(win, variable=tf_var,
                          values=["1m", "5m", "15m", "1h", "4h", "1d"]).pack(fill="x", padx=20)

        def save_and_close():
            new_api_key = api_key_entry.get().strip()
            new_api_secret = api_secret_entry.get().strip()
            new_symbol = tp_var.get().strip()
            new_tf = tf_var.get().strip()

            win.destroy()
            self.after(100, lambda: self.apply_new_settings(new_api_key, new_api_secret, new_symbol, new_tf))

        ctk.CTkButton(win, text="Зберегти", command=save_and_close).pack(pady=16)

    def apply_new_settings(self, new_api_key, new_api_secret, new_symbol, new_tf):
        save_settings(new_api_key, new_api_secret, new_symbol, new_tf)

        self.api_key = new_api_key
        self.api_secret = new_api_secret
        self.symbol = new_symbol
        self.interval_var.set(new_tf)
        self.pair_label.configure(text=_symbol_to_label(self.symbol))

        self.df = get_historical_futures_klines(self.symbol, self.interval_var.get(), 100)
        self.update_chart()
        self._start_sockets()
        self.add_log(f"Settings applied: {self.symbol} @ {self.interval_var.get()}", True)

    # ===== closing =====
    def on_closing(self):
        self.running = False
        try:
            if self.kline_socket_key:
                try:
                    self.twm.stop_socket(self.kline_socket_key)
                except KeyError:
                    pass
                except Exception:
                    pass
                self.kline_socket_key = None
            if self.ticker_socket_key:
                try:
                    self.twm.stop_socket(self.ticker_socket_key)
                except KeyError:
                    pass
                except Exception:
                    pass
                self.ticker_socket_key = None
        except Exception:
            pass
        time.sleep(0.2)
        if self.twm is not None:
            try:
                self.twm.stop()
            except Exception:
                pass
        self.destroy()
