import unittest
import os
import sqlite3
import time
from storage.database import init_db, save_best_price, get_last_best_price, get_db_connection, DB_PATH

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # We will use the actual DB path but clear it out for testing
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
        init_db()

    def tearDown(self):
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)

    def test_init_db(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='price_history'")
            self.assertIsNotNone(cursor.fetchone(), "Table price_history should exist")

    def test_save_and_get_best_price(self):
        query = "iphone 17"
        store = "Amazon"
        title = "Apple iPhone 17 (128GB) - Midnight"
        
        # Insert first record
        save_best_price(query, store, title, 1000.0, "http://amazon.in/iphone", "INR")
        time.sleep(0.1) # to ensure different timestamp if needed
        
        # Insert second record (different price)
        save_best_price(query, store, title, 850.0, "http://amazon.in/iphone", "INR")
        
        result = get_last_best_price(query)
        self.assertIsNotNone(result)
        # get_last_best_price returns the historically lowest price for that product
        self.assertEqual(result['price'], 850.0)
        self.assertEqual(result['currency'], "INR")
        
        # Insert a higher price later
        save_best_price(query, store, title, 900.0, "http://amazon.in/iphone", "INR")
        
        # get_last_best_price should still return the lowest historical price
        result2 = get_last_best_price(query)
        self.assertEqual(result2['price'], 850.0)
        
        # Let's verify we have 3 records in the history for this store/query
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM price_history WHERE product_query=?", (query,))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 3, "Should preserve history, not overwrite")

if __name__ == '__main__':
    unittest.main()