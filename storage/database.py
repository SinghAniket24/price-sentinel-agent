import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, List

DB_PATH = "data/price_watch.db"

@contextmanager
def get_db_connection():
    """Context manager for safe and reliable database connections."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    """
    Initializes the SQLite database.
    Migrates to a schema that supports true historical tracking and currencies.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_history'")
        if not cursor.fetchone():
            # Create the new table for true historical price tracking (no UNIQUE constraint on query+store)
            conn.execute("""
                CREATE TABLE price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_query TEXT NOT NULL,
                    store_name TEXT NOT NULL,
                    title TEXT,
                    price REAL,
                    currency TEXT DEFAULT 'Unknown',
                    url TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Check if old table exists to migrate data
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracked_products'")
            if cursor.fetchone():
                try:
                    cursor.execute("PRAGMA table_info(tracked_products)")
                    columns = {row[1] for row in cursor.fetchall()}
                    
                    price_col = "price" if "price" in columns else "NULL"
                    time_col = "timestamp" if "timestamp" in columns else "CURRENT_TIMESTAMP"
                    title_col = "title" if "title" in columns else "NULL"
                    url_col = "url" if "url" in columns else "NULL"
                    store_col = "store_name" if "store_name" in columns else "'Legacy_Store'"
                    query_col = "product_query" if "product_query" in columns else ("url" if "url" in columns else "'Unknown'")
                    
                    conn.execute(f"""
                        INSERT INTO price_history (product_query, store_name, title, price, currency, url, timestamp)
                        SELECT {query_col}, {store_col}, {title_col}, {price_col}, 'Unknown', {url_col}, {time_col}
                        FROM tracked_products
                    """)
                    conn.execute("DROP TABLE tracked_products")
                except Exception as e:
                    print(f"Migration failed: {e}")
            conn.commit()
        else:
            # Check if currency column exists in price_history
            cursor.execute("PRAGMA table_info(price_history)")
            columns = {row[1] for row in cursor.fetchall()}
            if 'currency' not in columns:
                try:
                    conn.execute("ALTER TABLE price_history ADD COLUMN currency TEXT DEFAULT 'Unknown'")
                    conn.commit()
                except Exception as e:
                    print(f"Migration to add 'currency' column failed: {e}")

def save_best_price(product_query: str, store_name: str, title: str, price: float, url: str = None, currency: str = 'Unknown') -> None:
    """
    Inserts a new price observation.
    Maintains the old function signature for compatibility but acts as an append-only log.
    """
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO price_history (product_query, store_name, title, price, currency, url, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (product_query, store_name, title, price, currency, url))
        conn.commit()

def get_last_best_price(product_query: str) -> Optional[dict]:
    """Retrieves the absolute lowest historical price recorded for a given query across any store."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT store_name, title, price, url, timestamp, currency
            FROM price_history 
            WHERE product_query = ? AND price IS NOT NULL
            ORDER BY price ASC 
            LIMIT 1
        """, (product_query,))
        row = cursor.fetchone()
        
        if row:
            return {
                "store_name": row[0],
                "title": row[1],
                "price": row[2],
                "url": row[3],
                "timestamp": row[4],
                "currency": row[5]
            }
        return None