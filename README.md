# DogeTrade v1.0

Програма з графічним інтерфейсом (Python + CustomTkinter), яка відображає:
- Графік DOGE/USDT (тестовий)
- Історію сигналів (заглушка)
- Панель статусу
- Лог повідомлень

Це **базова версія (1.0)** — основа для подальшої розробки:
- ✅ GUI працює (PyCharm / Windows / Linux / macOS)
- ✅ Чисте закриття без помилок
- 🚧 Наступні кроки: підключення Binance API, генерація сигналів, ШІ

## 🚀 Запуск

1. Клонувати репозиторій:
   ```bash
   git clone https://github.com/<твій-юзернейм>/DogeTrade.git
   cd DogeTrade
2. Створити віртуальне середовище (рекомендується):
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
3. Встановити залежності:
   ```bash
   pip install -r requirements.txt
4. Запустити програму:
   ```bash
   python main_window.py
