import sqlite3
import os
from contextlib import contextmanager
from typing import Optional, Tuple

DB_PATH = "data/price_watch.db"

@contextmanager
def get_db_connection():
    """Context manager for safe and reliable database connections."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db() -> None:
    """
    Initializes the SQLite database with the expanded multi-store schema.
    Uses the bulletproof table swap pattern to migrate legacy schemas safely.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tracked_products'")
        if not cursor.fetchone():
            conn.execute("""
                CREATE TABLE tracked_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_query TEXT NOT NULL,
                    store_name TEXT NOT NULL,
                    title TEXT,
                    price REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(product_query, store_name)
                )
            """)
        else:
            # Check if we need to migrate to the new multi-store schema
            cursor.execute("PRAGMA table_info(tracked_products)")
            columns = {row[1] for row in cursor.fetchall()}
            
            if 'product_query' not in columns or 'store_name' not in columns:
                # Migrate to the new dynamic schema
                conn.execute("""
                    CREATE TABLE tracked_products_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_query TEXT NOT NULL,
                        store_name TEXT NOT NULL,
                        title TEXT,
                        price REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(product_query, store_name)
                    )
                """)
                
                # We can't cleanly map single-URL legacy data to multi-store query data without assumptions.
                # Since this is a massive architecture change, we will preserve legacy data by setting 
                # generic defaults for the new non-null constraints if legacy data exists.
                if 'url' in columns:
                    price_col = "price" if "price" in columns else ("last_price" if "last_price" in columns else "NULL")
                    time_col = "timestamp" if "timestamp" in columns else ("updated_at" if "updated_at" in columns else "CURRENT_TIMESTAMP")
                    title_col = "title" if "title" in columns else "NULL"
                    
                    conn.execute(f"""
                        INSERT OR IGNORE INTO tracked_products_new (product_query, store_name, title, price, timestamp)
                        SELECT url, 'Legacy_Store', {title_col}, {price_col}, {time_col}
                        FROM tracked_products
                    """)
                
                conn.execute("DROP TABLE tracked_products")
                conn.execute("ALTER TABLE tracked_products_new RENAME TO tracked_products")
                
        conn.commit()

def save_best_price(product_query: str, store_name: str, title: str, price: float) -> None:
    """
    Upserts the best found price for a specific product query and store.
    """
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO tracked_products (product_query, store_name, title, price, timestamp)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(product_query, store_name) DO UPDATE SET
                title = excluded.title,
                price = excluded.price,
                timestamp = CURRENT_TIMESTAMP
        """, (product_query, store_name, title, price))
        conn.commit()

def get_last_best_price(product_query: str) -> Optional[dict]:
    """Retrieves the absolute lowest historical price recorded for a given query across any store."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Find the absolute minimum price recorded for this product query
        cursor.execute("""
            SELECT store_name, title, price, timestamp 
            FROM tracked_products 
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
                "timestamp": row[3]
            }
        return None