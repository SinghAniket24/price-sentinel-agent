from smolagents import tool
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import urllib.parse
import re
import time

@tool
def search_product_across_stores(product_name: str) -> list:
    """
    Dynamically searches for a product across major e-commerce platforms (Amazon, Flipkart) 
    and returns a structured list of found product listings with their prices.
    
    Args:
        product_name: The generic name of the product to search for (e.g. 'iphone 17').
        
    Returns:
        list: A list of dictionaries containing 'store', 'title', 'price' (float), and 'error' (if any).
    """
    encoded_query = urllib.parse.quote_plus(product_name)
    stores = [
        {
            "name": "Amazon",
            "url": f"https://www.amazon.com/s?k={encoded_query}",
        },
        {
            "name": "Flipkart",
            "url": f"https://www.flipkart.com/search?q={encoded_query}",
        }
    ]
    
    results = []
    
    try:
        with sync_playwright() as p:
            # Use stealthy browser arguments to avoid basic bot protections
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
                }
            )
            
            for store in stores:
                page = context.new_page()
                try:
                    # Navigate and wait for DOM, with a robust timeout
                    page.goto(store["url"], wait_until="domcontentloaded", timeout=15000)
                    # Slight sleep to allow dynamic JS frameworks to populate prices
                    time.sleep(2)
                    
                    page_title = page.title()
                    
                    price_text = None
                    numeric_price = None
                    
                    # Try specific robust selectors first for Amazon and Flipkart
                    for selector in [".a-price .a-offscreen", ".a-price-whole", "div.Nx9bqj"]:
                        try:
                            elements = page.locator(selector)
                            if elements.count() > 0:
                                price_text = elements.first.inner_text()
                                break
                        except Exception:
                            continue
                            
                    if price_text:
                        # Extract number from the found selector text
                        matches = re.findall(r'([\d,]+(?:\.\d+)?)', price_text)
                        if matches:
                            numeric_price = float(matches[0].replace(',', ''))
                    
                    # Fallback to aggressive regex across the whole body if selectors fail
                    if numeric_price is None:
                        body_text = page.locator("body").inner_text()
                        prices = re.findall(r'[\$£₹]\s*([\d,]+(?:\.\d+)?)', body_text)
                        if prices:
                            numeric_price = float(prices[0].replace(',', ''))
                    
                    results.append({
                        "store": store["name"],
                        "title": page_title[:60] + "..." if len(page_title) > 60 else page_title,
                        "price": numeric_price,
                        "error": None
                    })
                    
                except PlaywrightTimeoutError:
                    results.append({"store": store["name"], "title": None, "price": None, "error": "Timeout or blocked by bot protection."})
                except Exception as e:
                    results.append({"store": store["name"], "title": None, "price": None, "error": str(e)})
                finally:
                    page.close()
                    
            browser.close()
            return results
            
    except Exception as e:
        return [{"store": "System", "title": None, "price": None, "error": f"Critical Playwright failure: {str(e)}"}]