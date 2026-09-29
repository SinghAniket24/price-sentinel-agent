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

    {history_context}

    Your task MUST be executed in a SINGLE, cohesive execution block of code:
    1. Call `search_product_across_stores(product_name="{product_name}")`.
    2. Immediately loop through the returned list. Treat a listing as valid if and only if it has a valid numeric `price` and its `error` is `None`.
    3. If zero valid listings are returned across all primary stores, ONLY THEN call `web_search_fallback(product_name="{product_name}")` and loop through its results.
    4. Save ALL valid listings to the database by executing:
       `from storage.database import save_best_price`
       For each valid listing, call:
       `save_best_price(product_query="{product_name}", store_name=listing['store_name'], title=listing['title'], price=listing['price'], url=listing['url'], currency=listing['currency'])`
    5. Find the absolute lowest valid price across all valid listings to declare the winner.
    6. Formulate your final answer. Your final answer MUST explicitly state:
       - The winning store and winning price.
       - A comparison against the historical price to evaluate market shifts.
       - A strict confirmation that ALL valid results were saved to the database.
    """
    
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            result = agent.run(prompt)
            return result
        except Exception as e:
            if attempt < max_retries:
                print(f"Agent execution failed on attempt {attempt + 1}. Retrying... ({str(e)})")
            else:
                raise RuntimeError(f"Agent execution completely failed after {max_retries + 1} attempts. Last error: {str(e)}")