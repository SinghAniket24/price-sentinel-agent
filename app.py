import streamlit as st
import sqlite3
import pandas as pd
import os
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()
DB_PATH = "data/price_watch.db"

st.set_page_config(page_title="Price Sentinel Dashboard", layout="wide", page_icon="📈")

# --- Sidebar: Live Agent Runner ---
st.sidebar.header("🤖 Live Agent Runner")
st.sidebar.markdown("Trigger a fresh scrape directly from the UI.")

search_query = st.sidebar.text_input("Enter Product Name", placeholder="e.g., Redmi 13 5G")

if st.sidebar.button("Run Sentinel Agent", type="primary"):
    if search_query.strip():
        if not os.environ.get("HF_TOKEN"):
            st.sidebar.error("HF_TOKEN missing in environment or .env file!")
        else:
            with st.sidebar.status(f"Running agent for '{search_query}'...", expanded=True) as status:
                st.write("Initializing orchestration...")
                
                # Prepare environment, retaining HF_TOKEN
                env = os.environ.copy()
            
                try:
                    # Execute backend script as subprocess
                    process = subprocess.run(
                        [sys.executable, "run_agent.py", search_query.strip()],
                        capture_output=True,
                        text=True,
                        env=env,
                        cwd=os.path.dirname(os.path.abspath(__file__))
                    )
                    
                    if process.returncode == 0:
                        status.update(label="Scraping completed!", state="complete", expanded=False)
                        st.sidebar.success(f"Successfully scraped '{search_query}'.")
                        
                        if "--- Final Agent Comparative Summary ---" in process.stdout:
                            summary_text = process.stdout.split("--- Final Agent Comparative Summary ---")[-1].strip()
                            st.session_state['agent_summary'] = summary_text
                            
                        with st.sidebar.expander("Agent Logs", expanded=False):
                            st.text(process.stdout)
                            if process.stderr:
                                st.text(process.stderr)
                    else:
                        status.update(label="Agent failed", state="error", expanded=True)
                        st.sidebar.error("Execution failed with non-zero exit code.")
                        with st.sidebar.expander("Error Details", expanded=True):
                            st.text(f"STDOUT:\n{process.stdout}\n\nSTDERR:\n{process.stderr}")
                except Exception as e:
                    status.update(label="Execution error", state="error", expanded=True)
                    st.sidebar.error(f"Exception: {str(e)}")
                    import traceback
                    with st.sidebar.expander("Exception Details", expanded=True):
                        st.text(traceback.format_exc())
    else:
        st.sidebar.warning("Please enter a valid product query.")

# --- Main Dashboard ---
st.title("📈 Price Sentinel Dashboard")
st.markdown("Visualize historical tracked prices and market shifts across multiple stores.")

if 'agent_summary' in st.session_state:
    st.success(f"📊 **Store Comparison Breakdown:**\n\n{st.session_state['agent_summary']}")

def load_and_sanitize_data():
    if not os.path.exists(DB_PATH):
        return pd.DataFrame()
        
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    
    query = "SELECT id, product_query, store_name, title, price, url, timestamp FROM tracked_products ORDER BY timestamp DESC"
    df = pd.read_sql(query, conn)
    conn.close()
    
    if df.empty:
        return df

    # Sanitization Filter: Drop rows with mock URLs or placeholder values
    mock_filters = ["toscrape", "example.com", "test", "mock", "placeholder"]
    
    def is_valid_row(row):
        text_to_check = f"{row['product_query']} {row['store_name']} {row['title']}".lower()
        if any(mock in text_to_check for mock in mock_filters):
            return False
        if pd.isna(row['price']):
            return False
        if pd.isna(row['url']) or not str(row['url']).startswith('http'):
            return False
        if 'search?q=' in str(row['url']) or 's?k=' in str(row['url']):
            # Filter out search result pages that aren't product pages
            return False
        return True

    df = df[df.apply(is_valid_row, axis=1)]
    
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    return df

df = load_and_sanitize_data()

if df.empty:
    st.info("No valid data found in the database. Use the Live Agent Runner in the sidebar to populate data!")
    st.stop()

# --- Product Selector ---
product_queries = sorted(df['product_query'].unique().tolist())

def on_product_change():
    if 'agent_summary' in st.session_state:
        del st.session_state['agent_summary']

selected_product = st.selectbox("🔍 Select Product to Analyze", ["-- All Products --"] + product_queries, on_change=on_product_change)

if selected_product != "-- All Products --":
    df_filtered = df[df['product_query'] == selected_product].copy()
else:
    df_filtered = df.copy()

st.divider()

if selected_product != "-- All Products --":
    # --- Metrics Row ---
    st.header("🏆 Current Best Price")
    best_overall = df_filtered.loc[df_filtered['price'].idxmin()]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Winning Store", best_overall['store_name'])
    
    # Auto-detect currency heuristically for display
    currency_symbol = "₹" if best_overall['price'] > 3000 else "$"
    col2.metric("Lowest Price", f"{currency_symbol} {best_overall['price']:,.2f}")
    
    col3.metric("Last Updated", best_overall['timestamp'].strftime('%Y-%m-%d %H:%M'))
    
    title_text = best_overall['title']
    product_url = best_overall.get('url')
    if pd.notna(product_url) and product_url:
        st.info(f"**Top Result Title:** [{title_text}]({product_url})")
    else:
        st.info(f"**Top Result Title:** {title_text}")
    
    st.divider()
    
    # --- Charts ---
    st.header("📊 Price Analytics")
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Current Prices by Store")
        # Get latest price for each store to avoid duplicate axes
        latest_per_store = df_filtered.sort_values('timestamp').groupby('store_name').last().reset_index()
        # Enforce clean mappings to prevent squished axes
        st.bar_chart(latest_per_store, x="store_name", y="price", width='stretch')
        
    with colB:
        st.subheader("Historical Timeline")
        # Line chart for historical trends, grouped by store
        st.line_chart(df_filtered, x="timestamp", y="price", color="store_name", width='stretch')
        
else:
    st.header("🏆 Overview: Lowest Prices Across All Products")
    best_per_product = df.loc[df.groupby('product_query')['price'].idxmin()].reset_index(drop=True)
    st.bar_chart(best_per_product, x="product_query", y="price", width='stretch')

st.divider()

# --- Audit Log Table ---
st.header("📋 Validated Audit Log")
st.markdown("Sanitized historical price records cleanly extracted from the database.")
display_df = df_filtered[['product_query', 'store_name', 'title', 'price', 'url', 'timestamp']].sort_values('timestamp', ascending=False)
st.dataframe(
    display_df,
    width='stretch',
    hide_index=True,
    column_config={
        "url": st.column_config.LinkColumn("Product Link", display_text="View on Store")
    }
)
