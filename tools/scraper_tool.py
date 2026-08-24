from smolagents import tool
import urllib.request
import urllib.error

@tool
def get_webpage_content(url: str) -> str:
    """
    A custom tool that fetches the raw text content of a given product URL 
    so the agent can read prices and product details.

    Args:
        url: The full web URL of the product page to scrape.
    """
    try:
        # Add a realistic user-agent header to avoid getting instantly blocked
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8', errors='ignore')
            # Return a trimmed version of the HTML/text to keep token usage low
            return html_content[:15000]
    except urllib.error.URLError as e:
        return f"Error fetching the webpage: {e.reason}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"