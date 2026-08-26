from storage.database import init_db, save_best_price, get_last_best_price

def main():
    print("Initializing database...")
    init_db()

    query = "iphone 17"
    store = "Amazon"
    title = "Apple iPhone 17 (128GB) - Midnight"
    initial_price = 1000.0

    print(f"Saving initial price: {initial_price}")
    save_best_price(query, store, title, initial_price)

    result = get_last_best_price(query)
    print(f"Retrieved from DB -> Store: {result['store_name']}, Title: {result['title']}, Price: {result['price']}")

    # Test update (upsert)
    updated_price = 850.0
    print(f"Updating price to: {updated_price}")
    save_best_price(query, store, title, updated_price)

    result_updated = get_last_best_price(query)
    print(f"Retrieved updated price: {result_updated['price']}")

if __name__ == "__main__":
    main()