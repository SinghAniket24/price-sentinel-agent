# Price Sentinel Agent

A multi-store price comparator agent powered by `smolagents`. It scrapes major e-commerce platforms (Amazon India and Flipkart) to find the lowest prices, tracks historical price observations, and visualizes the data via a Streamlit dashboard.

## Features

- **Agent Orchestration**: Uses `smolagents` (with `Qwen/Qwen2.5-Coder-32B-Instruct`) to execute multi-store searches and data validation.
- **Dynamic Scraping**: Uses asynchronous Playwright to extract prices and product details from Amazon India (amazon.in) and Flipkart.
- **Web Search Fallback**: Falls back to DuckDuckGo web searches if direct scraping is blocked or returns invalid values.
- **Historical Price Tracking**: Stores each successful price observation as a new timestamped record in a local SQLite database, maintaining a true price history. Includes explicit currency tracking.
- **Streamlit Dashboard**: A UI to trigger live scrapes, view price histories, and compare prices across platforms.

## Prerequisites

- Python 3.9+
- A Hugging Face account and API token (`HF_TOKEN`) for the agent model.

## Installation

1. **Set up a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

4. **Configure environment variables**:
   Create a `.env` file in the root directory and add your Hugging Face token:
   ```env
   HF_TOKEN=your_hugging_face_token_here
   ```

## Usage

### 1. Streamlit Dashboard (Recommended)

Launch the interactive dashboard to trigger live searches and view price analytics.

```bash
streamlit run app.py
```

### 2. CLI Agent

Run the agent directly from the command line for a quick price check.

```bash
python run_agent.py "iphone 15"
```

## Testing

The project includes deterministic unit tests for database functions and scraper validation logic.

To run the tests:
```bash
python -m unittest test_db.py test_scraper.py
```

## Architecture

- **Agent Framework**: `smolagents`
- **Model**: `Qwen/Qwen2.5-Coder-32B-Instruct` (Inference API)
- **Web Scraping**: Playwright (Async), DuckDuckGo Search (`ddgs`)
- **Database**: SQLite3
- **Frontend**: Streamlit, Pandas, Altair
