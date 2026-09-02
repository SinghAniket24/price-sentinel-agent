from tools.scraper_tool import search_product_across_stores, is_valid_result, web_search_fallback

def test_filters():
    print("--- Testing Validation Filters ---")
    
    # Test 1: Title missing query intent
    valid, reason = is_valid_result("iphone 17", "Generic Smartphone Black", 900, "Amazon")
    print(f"Test 1 (Missing Intent): Valid={valid}, Reason='{reason}'")
    assert not valid and "missing query intent" in reason

    # Test 2: Irrelevant accessory
    valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 Silicone Case", 50, "Amazon")
    print(f"Test 2 (Irrelevant Accessory): Valid={valid}, Reason='{reason}'")
    assert not valid and "exclusion keyword" in reason

    # Test 3: Valid flagship price (USD)
    valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 (128GB)", 899, "Amazon")
    print(f"Test 3 (Valid Flagship USD): Valid={valid}, Reason='{reason}'")
    assert valid

    # Test 4: Valid flagship price (INR)
    valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 (128GB)", 89900, "Flipkart")
    print(f"Test 4 (Valid Flagship INR): Valid={valid}, Reason='{reason}'")
    assert valid

    # Test 5: Outlier low price (INR flagship)
    valid, reason = is_valid_result("iphone 17", "Apple iPhone 17 (128GB)", 1500, "Flipkart")
    print(f"Test 5 (Outlier Low INR): Valid={valid}, Reason='{reason}'")
    assert not valid and "too low" in reason

    # Test 6: Accessory query should allow low prices
    valid, reason = is_valid_result("iphone 17 case", "Apple iPhone 17 Silicone Case", 49, "Amazon")
    print(f"Test 6 (Accessory Query): Valid={valid}, Reason='{reason}'")
    assert valid

    # Test 7: Valid mid-range price (INR)
    # Using 'inr' heuristic threshold (price > 3000 -> treated as INR)
    valid, reason = is_valid_result("redmi 13 5g", "Redmi 13 5G (6GB RAM)", 13999, "Amazon")
    print(f"Test 7 (Valid Mid-Range INR): Valid={valid}, Reason='{reason}'")
    assert valid

    # Test 8: Outlier high price for mid-range (INR)
    valid, reason = is_valid_result("redmi 13 5g", "Redmi 13 5G", 60000, "Amazon")
    print(f"Test 8 (Outlier High Mid-Range INR): Valid={valid}, Reason='{reason}'")
    assert not valid and "too high" in reason

    print("All filter tests passed!\n")

def test_fallback():
    print("--- Testing Web Search Fallback ---")
    test_query = "iphone 15"
    results = web_search_fallback(test_query)
    print(f"Fallback results for '{test_query}':")
    for r in results:
        print(r)
    assert isinstance(results, list)
    print("Fallback test passed!\n")

if __name__ == "__main__":
    test_filters()
    test_fallback()
    
    print("--- Running End-to-End Scraper Tool ---")
    # Using a popular phone that will definitely have results to test both direct and fallback (if needed)
    test_query = "iphone 15"
    print(f"Testing scraper tool with query: '{test_query}'\n")

    results = search_product_across_stores(test_query)
    print("--- Scraped Result Preview ---")
    for result in results:
        print(result)