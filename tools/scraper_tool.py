from smolagents import tool
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import urllib.parse
import re
import time
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

def is_valid_result(query: str, title: str, price: float, store: str) -> tuple[bool, str]:
    if not title:
        return False, "Missing title"
    if price is None:
        return False, "Missing price"
        
    query_lower = query.lower()
    title_lower = title.lower()
    
    exclude_words = ["case", "cover", "charger", "cable", "protector", "screen", "refurbished", "dummy", "box"]
    for word in exclude_words:
        if word in title_lower and word not in query_lower:
            return False, f"Irrelevant item: matched exclusion keyword '{word}'"
            
    query_words = re.findall(r'\b\w+\b', query_lower)
    if query_words:
        match_count = sum(1 for w in query_words if w in title_lower)
        if match_count == 0:
            return False, "Title missing query intent"

    is_inr = (store.lower() in ["flipkart", "croma"]) or ("inr" in store.lower()) or (price > 3000)
    is_accessory_query = any(word in query_lower for word in exclude_words)
    is_flagship = any(brand in query_lower for brand in ["iphone", "macbook", "galaxy s", "galaxy z", "pixel", "ipad", "fold"])
    is_mid_range = any(brand in query_lower for brand in ["redmi", "poco", "moto", "realme", "iqoo", "galaxy a", "galaxy m", "nord", "nothing"])
    
    if is_inr:
        if is_accessory_query:
            min_price, max_price = 50, 20000
        elif is_flagship:
            min_price, max_price = 30000, 300000
        elif is_mid_range:
            min_price, max_price = 8000, 45000
        else:
            min_price, max_price = 500, 500000
    else:
        if is_accessory_query:
            min_price, max_price = 1, 200
        elif is_flagship:
            min_price, max_price = 300, 3000
        elif is_mid_range:
            min_price, max_price = 100, 600
        else:
            min_price, max_price = 10, 5000

    if price < min_price:
        return False, f"Outlier price: {price} is too low (min: {min_price})"
    if price > max_price:
        return False, f"Outlier price: {price} is too high (max: {max_price})"
            
    return True, ""

@tool
def web_search_fallback(product_name: str) -> list:
    """
    Uses a live web search (DuckDuckGo) to find prices from web search.
    Use this fallback tool if direct store scraping fails or returns invalid prices.
    
    Args:
        product_name: The generic name of the product to search for.
        
    Returns:
        list: A list of dictionaries containing 'store', 'title', 'price' (float), and 'error' (if any).
    """
    if not DDGS:
        return []
    results = []
    try:
        ddgs = DDGS()
        # Search for query + price targeting major stores
        search_results = ddgs.text(f"{product_name} price Amazon Flipkart Croma site:amazon.in OR site:flipkart.com OR site:croma.com", max_results=5)
        for res in search_results:
            title = res.get("title", "")
            snippet = res.get("body", "")
            href = res.get("href", "")
            
            # Extract price from snippet or title
            text_to_search = title + " " + snippet
            prices = re.findall(r'[\$£₹]\s*([\d,]+(?:\.\d+)?)', text_to_search)
            if not prices:
                prices = re.findall(r'(?:Rs\.?|INR)\s*([\d,]+(?:\.\d+)?)', text_to_search, re.IGNORECASE)
                
            if prices:
                numeric_price = float(prices[0].replace(',', ''))
                
                store_name = "WebSearch"
                if "amazon" in href.lower() or "amazon" in title.lower():
                    store_name = "Amazon"
                elif "flipkart" in href.lower() or "flipkart" in title.lower():
                    store_name = "Flipkart"
                elif "croma" in href.lower() or "croma" in title.lower():
                    store_name = "Croma"
                    
                is_valid, reason = is_valid_result(product_name, title, numeric_price, store_name)
                if is_valid:
                    results.append({
                        "store": f"{store_name} (Fallback)",
                        "title": title[:60] + "..." if len(title) > 60 else title,
                        "price": numeric_price,
                        "error": None
                    })
    except Exception as e:
        pass
    return results

@tool
def search_product_across_stores(product_name: str) -> list:
    """
    Dynamically searches for a product across major e-commerce platforms (Amazon, Flipkart) 
    and returns a structured list of found product listings with their prices.
    If direct scraping fails, it falls back to live web search.
    
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
            browser = p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html"
                }
            )
            
            for store in stores:
                page = context.new_page()
                try:
                    page.goto(store["url"], wait_until="domcontentloaded", timeout=15000)
                    time.sleep(2)
                    
                    page_title = page.title()
                    price_text = None
                    numeric_price = None
                    
                    for selector in [".a-price .a-offscreen", ".a-price-whole", "div.Nx9bqj"]:
                        try:
                            elements = page.locator(selector)
                            if elements.count() > 0:
                                price_text = elements.first.inner_text()
                                break
                        except Exception:
                            continue
                            
                    if price_text:
                        matches = re.findall(r'([\d,]+(?:\.\d+)?)', price_text)
                        if matches:
                            numeric_price = float(matches[0].replace(',', ''))
                    
                    if numeric_price is None:
                        body_text = page.locator("body").inner_text()
                        prices = re.findall(r'[\$£₹]\s*([\d,]+(?:\.\d+)?)', body_text)
                        if prices:
                            numeric_price = float(prices[0].replace(',', ''))
                    
                    short_title = page_title[:60] + "..." if len(page_title) > 60 else page_title
                    
                    is_valid, reason = is_valid_result(product_name, page_title, numeric_price, store["name"])
                    if not is_valid:
                        results.append({
                            "store": store["name"],
                            "title": short_title,
                            "price": None,
                            "error": f"Filtered out: {reason}",
                            "original_price": numeric_price
                        })
                    else:
                        results.append({
                            "store": store["name"],
                            "title": short_title,
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
            
    except Exception as e:
        results.append({"store": "System", "title": None, "price": None, "error": f"Critical Playwright failure: {str(e)}"})

    # Check if we need fallback
    valid_results = [r for r in results if r.get("price") is not None and r.get("error") is None]
    if not valid_results:
        # Pivot to fallback
        fallback_results = web_search_fallback(product_name)
        if fallback_results:
            results.extend(fallback_results)

    return results