import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "dogetrade.db")


def init_db():
    """Створює таблицю settings, якщо її ще немає."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key TEXT,
            api_secret TEXT,
            trading_pair TEXT DEFAULT 'DOGEUSDT',
            default_timeframe TEXT DEFAULT '1m'
        )
    """)
    # Якщо таблиця щойно створена і пуста – додаємо дефолтні налаштування
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO settings (api_key, api_secret, trading_pair, default_timeframe)
            VALUES (?, ?, ?, ?)
        """, ("", "", "DOGEUSDT", "1m"))
    conn.commit()
    conn.close()


def save_settings(api_key: str, api_secret: str, trading_pair: str, timeframe: str):
    """Зберігає нові налаштування у таблицю settings (завжди 1 запис)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM settings")  # завжди тримаємо тільки 1 рядок
    cursor.execute("""
        INSERT INTO settings (api_key, api_secret, trading_pair, default_timeframe)
        VALUES (?, ?, ?, ?)
    """, (api_key, api_secret, trading_pair, timeframe))
    conn.commit()
    conn.close()


def get_settings():
    """Повертає збережені налаштування (dict)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT api_key, api_secret, trading_pair, default_timeframe FROM settings LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "api_key": row[0],
            "api_secret": row[1],
            "trading_pair": row[2],
            "default_timeframe": row[3],
        }
    return None


# Виконуємо ініціалізацію при імпорті
init_db()
