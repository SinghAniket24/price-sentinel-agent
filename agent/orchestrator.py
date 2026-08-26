import os
from smolagents import CodeAgent, InferenceClientModel
from tools.scraper_tool import search_product_across_stores
from storage.database import init_db, get_last_best_price

def create_agent() -> CodeAgent:
    """Initializes the CodeAgent with the multi-store search tool."""
    init_db()
    
    model = InferenceClientModel(model_id="Qwen/Qwen2.5-Coder-32B-Instruct")
    
    agent = CodeAgent(
        tools=[search_product_across_stores],
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
    2. Analyze the returned list. Identify which store currently offers the absolute lowest numeric `price` (ignore None or error results).
    3. {history_context}
    4. Compare the new lowest price against the historical lowest price (if it exists) to evaluate market shifts (e.g. Price Dropped, Increased, or New Record).
    5. Execute EXACTLY the following Python code to save the data:
       `from storage.database import save_best_price`
       `save_best_price(product_query="{product_name}", store_name=..., title=..., price=...)`
    6. Return a comprehensive structured summary detailing the stores checked, the winning store, the price comparison, and your market shift evaluation.
    """
    
    result = agent.run(prompt)
    return result