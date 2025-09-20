import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import customtkinter as ctk
from binance.client import Client
from binance import ThreadedWebsocketManager
import time

import config  # файл з твоїми API ключами


class DogeTradeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування головного вікна
        self.title("DogeTrade Signals")
        self.geometry("1000x600")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Binance клієнт
        self.client = Client(config.BINANCE_API_KEY, config.BINANCE_API_SECRET)

        # Прапорець для завершення
        self.running = True

        # Верхня панель
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.pair_label = ctk.CTkLabel(top_frame, text="DOGE/USDT", font=("Arial", 18, "bold"))
        self.pair_label.pack(side="left", padx=10)

        self.price_label = ctk.CTkLabel(top_frame, text="Last Price: 0.0000", font=("Arial", 16))
        self.price_label.pack(side="left", padx=20)

        self.signal_label = ctk.CTkLabel(top_frame, text="Signal: HOLD", font=("Arial", 16), text_color="gray")
        self.signal_label.pack(side="left", padx=20)

        # Кнопка для тесту логів
        test_button = ctk.CTkButton(top_frame, text="Test Log", command=self.test_log)
        test_button.pack(side="right", padx=10)

        # Центральна частина
        center_frame = ctk.CTkFrame(self)
        center_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        chart_frame = ctk.CTkFrame(center_frame)
        chart_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3, 4, 5], [10, 12, 8, 14, 11])  # заглушка графіка
        ax.set_title("DOGE/USDT Chart")

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Історія сигналів
        signals_frame = ctk.CTkFrame(center_frame, width=250)
        signals_frame.pack(side="right", fill="y", padx=5, pady=5)

        history_label = ctk.CTkLabel(signals_frame, text="Signal History", font=("Arial", 14, "bold"))
        history_label.pack(pady=5)

        self.tree = ttk.Treeview(signals_frame, columns=("time", "signal", "price"), show="headings", height=15)
        self.tree.heading("time", text="Time")
        self.tree.heading("signal", text="Signal")
        self.tree.heading("price", text="Price")

        self.tree.column("time", width=100)
        self.tree.column("signal", width=70)
        self.tree.column("price", width=80)

        self.tree.pack(fill="y", expand=True)

        # Логи з прокруткою
        bottom_frame = ctk.CTkFrame(self, height=100)
        bottom_frame.pack(side="bottom", fill="x", padx=5, pady=5)

        self.log_text = scrolledtext.ScrolledText(bottom_frame, height=5, bg="#1e1e1e", fg="white")
        self.log_text.pack(fill="both", expand=True)

        # Обмеження частоти логів
        self.last_log_time = 0

        # Запускаємо WebSocket
        self.twm = ThreadedWebsocketManager(api_key=config.BINANCE_API_KEY,
                                            api_secret=config.BINANCE_API_SECRET)
        self.twm.start()
        self.twm.start_symbol_ticker_socket(callback=self.handle_ticker, symbol="DOGEUSDT")

        self.add_log("Connected to Binance WebSocket", force=True)

    def add_log(self, message: str, force: bool = False):
        """Додає повідомлення в лог (не частіше ніж 1 раз на 5 сек, якщо не force)"""
        now = time.time()
        if force or now - self.last_log_time >= 5:
            self.log_text.insert("end", message + "\n")
            self.last_log_time = now

    def test_log(self):
        """Метод для кнопки Test Log"""
        self.add_log("Test log message", force=True)

    def handle_ticker(self, msg):
        """Обробка повідомлень з WebSocket (у фоновому потоці)"""
        if not self.running:
            return
        try:
            price = float(msg["c"])
            self.after(0, self.update_price_label, price)
        except Exception as e:
            if self.running:
                self.after(0, self.add_log, f"WebSocket error: {e}", True)

    def update_price_label(self, price: float):
        """Оновлює ціну у GUI (викликається у головному потоці)"""
        self.price_label.configure(text=f"Last Price: {price:.4f}")
        self.add_log(f"Price updated: {price:.4f}")

    def on_closing(self):
        """Коректне закриття програми"""
        self.running = False
        if self.twm is not None:
            try:
                self.twm.stop()
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = DogeTradeApp()
    app.mainloop()
