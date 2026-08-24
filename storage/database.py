import sqlite3
import os

DB_PATH = "data/price_watch.db"

def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tracked_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                last_price REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_product_state(url: str, title: str, price: float) -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO tracked_products (url, title, last_price, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                last_price = excluded.last_price,
                updated_at = CURRENT_TIMESTAMP
        """, (url, title, price))
        conn.commit()

def get_last_price(url: str) -> tuple[float | None, str | None]:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT last_price, title FROM tracked_products WHERE url = ?", (url,))
        row = cursor.fetchone()
        return row if row else (None, None)