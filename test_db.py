from storage.database import init_db, save_product_state, get_last_price

def main():
    print("Initializing database...")
    init_db()

    url = "https://example.com/product-1"
    title = "Test Product"
    initial_price = 1000.0

    print(f"Saving initial price: {initial_price}")
    save_product_state(url, title, initial_price)

    price, prod_title = get_last_price(url)
    print(f"Retrieved from DB -> Title: {prod_title}, Price: {price}")

    # Test update (upsert)
    updated_price = 850.0
    print(f"Updating price to: {updated_price}")
    save_product_state(url, title, updated_price)

    new_price, _ = get_last_price(url)
    print(f"Retrieved updated price: {new_price}")

if __name__ == "__main__":
    main()