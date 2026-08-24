from tools.scraper_tool import get_webpage_content

# Test with a simple public URL
test_url = "https://example.com"
print(f"Testing scraper tool with: {test_url}\n")

result = get_webpage_content(test_url)
print("--- Scraped Result Preview ---")
print(result[:500]) # Print the first 500 characters