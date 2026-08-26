from tools.scraper_tool import search_product_across_stores

# Test with a sample product query
test_query = "iphone 17"
print(f"Testing scraper tool with query: '{test_query}'\n")

results = search_product_across_stores(test_query)
print("--- Scraped Result Preview ---")
for result in results:
    print(result)