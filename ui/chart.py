import mplfinance as mpf
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


def create_candlestick_chart(parent, df):
    """
    Малює свічковий графік у Tkinter Frame.
    :param parent: Tkinter Frame, у якому буде графік
    :param df: DataFrame з колонками [Open, High, Low, Close, Volume], індекс - datetime
    :return: canvas (FigureCanvasTkAgg)
    """

    # Створюємо фігуру
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    # Малюємо свічки без volume
    mpf.plot(
        df,
        type="candle",
        style="charles",
        ax=ax,
        ylabel="Price (USDT)"
    )

    # Вставляємо у Tkinter
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True)

    return canvas
