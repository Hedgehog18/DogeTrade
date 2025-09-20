import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import customtkinter as ctk


class DogeTradeApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Налаштування головного вікна
        self.title("DogeTrade Signals")
        self.geometry("1000x600")

        # Обробка закриття (коректне завершення matplotlib + Tk)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Верхня панель (поточна інформація)
        top_frame = ctk.CTkFrame(self, height=50)
        top_frame.pack(side="top", fill="x", padx=5, pady=5)

        self.pair_label = ctk.CTkLabel(top_frame, text="DOGE/USDT", font=("Arial", 18, "bold"))
        self.pair_label.pack(side="left", padx=10)

        self.price_label = ctk.CTkLabel(top_frame, text="Last Price: 0.0000", font=("Arial", 16))
        self.price_label.pack(side="left", padx=20)

        self.signal_label = ctk.CTkLabel(top_frame, text="Signal: HOLD", font=("Arial", 16), text_color="gray")
        self.signal_label.pack(side="left", padx=20)

        # Центральна частина (графік + історія сигналів)
        center_frame = ctk.CTkFrame(self)
        center_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        # Ліва частина - графік
        chart_frame = ctk.CTkFrame(center_frame)
        chart_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot([1, 2, 3, 4, 5], [10, 12, 8, 14, 11])  # заглушка графіка
        ax.set_title("DOGE/USDT Chart")

        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        # Права частина - історія сигналів
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

        # Додаємо тестові дані
        self.tree.insert("", "end", values=("12:00", "BUY", "0.1425"))
        self.tree.insert("", "end", values=("12:05", "SELL", "0.1410"))

        # Нижня панель (логи)
        bottom_frame = ctk.CTkFrame(self, height=100)
        bottom_frame.pack(side="bottom", fill="x", padx=5, pady=5)

        self.log_text = tk.Text(bottom_frame, height=5, bg="#1e1e1e", fg="white")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.insert("end", "Connected to Binance API (demo mode)\n")
        self.log_text.insert("end", "Signal generated: BUY at 0.1425\n")

    def on_closing(self):
        """Коректне закриття програми"""
        self.destroy()


if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  # dark/light/system
    ctk.set_default_color_theme("blue")  # теми: blue, dark-blue, green

    app = DogeTradeApp()
    app.mainloop()
