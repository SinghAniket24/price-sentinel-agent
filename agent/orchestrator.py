import os
from smolagents import CodeAgent, InferenceClientModel
from tools.scraper_tool import search_product_across_stores, web_search_fallback
from storage.database import init_db, get_last_best_price

def create_agent() -> CodeAgent:
    """Initializes the CodeAgent with the multi-store search tool."""
    init_db()
    
    model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct")
    
    agent = CodeAgent(
        tools=[search_product_across_stores, web_search_fallback],
        model=model,
        additional_authorized_imports=["storage", "storage.database", "re", "json"]
    )
    
    return agent

def compare_and_monitor(product_name: str) -> str:
    """
    Dynamic workflow that commands the agent to search multiple stores, 
    evaluate the lowest price, check history, and update the database.
    """
    agent = create_agent()
    
    # Pre-fetch historical lowest price context
    historical_data = get_last_best_price(product_name)
    
    if historical_data:
        history_context = f"Historical Data: The lowest price we ever recorded for '{product_name}' was {historical_data['price']} at {historical_data['store_name']}."
    else:
        history_context = f"Historical Data: No previous records for '{product_name}'. This is a new search."
        
    prompt = f"""
    You are an autonomous multi-store price comparator agent.
    
    Your task:
    1. Use the `search_product_across_stores` tool to search for the product: "{product_name}".
       This tool returns a list of dictionaries containing prices across Amazon, Flipkart, etc.
    2. Analyze the returned list. Note any listings that were filtered out (where 'error' indicates they were filtered or invalid).
    3. If direct scraping returns invalid data or no valid listings, invoke the `web_search_fallback` tool to find alternative prices before making a final decision.
    4. Identify which store currently offers the absolute lowest numeric `price` among the VALID results (ignore None or error results).
       - IMPORTANT: If ALL stores (and fallbacks) returned invalid or filtered-out prices, DO NOT save any price to the database. Instead, return a summary stating that no valid prices were found due to filtering, and gracefully halt further processing.
    4. {history_context}
    5. Compare the new lowest price against the historical lowest price (if it exists) to evaluate market shifts (e.g. Price Dropped, Increased, or New Record).
    6. Execute EXACTLY the following Python code to save the valid data:
       `from storage.database import save_best_price`
       `save_best_price(product_query="{product_name}", store_name=..., title=..., price=...)`
    7. Return a comprehensive structured summary detailing the stores checked, filtered out outliers, the winning store, the price comparison, and your market shift evaluation.
    """
    
    result = agent.run(prompt)
    return result