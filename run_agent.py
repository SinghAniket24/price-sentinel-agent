import os
import sys
from agent.orchestrator import compare_and_monitor

def main():
    if not os.environ.get("HF_TOKEN"):
        print("Warning: HF_TOKEN environment variable is not set. Execution may fail.", file=sys.stderr)

    # Dynamic CLI input handling
    if len(sys.argv) > 1:
        product_query = " ".join(sys.argv[1:])
    else:
        print("Enter a product to search across stores (e.g., 'iphone 17' or 'sony wh-1000xm5'):")
        try:
            product_query = input("> ").strip()
        except KeyboardInterrupt:
            print("\nExiting.")
            sys.exit(0)
            
    if not product_query:
        print("Error: Product query cannot be empty.")
        sys.exit(1)
        
    print(f"\n--- Starting the Autonomous Price Sentinel Agent ---")
    print(f"Target Product : {product_query}")
    print(f"Scanning Stores: Amazon, Flipkart")
    print("----------------------------------------------------\n")
    
    try:
        result = compare_and_monitor(product_query)
        print("\n--- Final Agent Comparative Summary ---")
        print(result)
        sys.exit(0)
    except Exception as e:
        print(f"\nExecution failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()