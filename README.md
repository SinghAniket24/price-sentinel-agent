# Price Sentinel

A tool that tracks and compares product prices across Amazon India and Flipkart. It uses `smolagents` to orchestrate searches, stores price history in SQLite, and provides a Streamlit dashboard for data visualization.

## Features

- Scrapes prices from Amazon India and Flipkart using asynchronous Playwright.
- Falls back to DuckDuckGo search if direct scraping is blocked.
- Stores historical price data and currency in a local SQLite database.
- Provides a Streamlit dashboard to run new searches and visualize price trends.
- Uses `Qwen/Qwen2.5-Coder-32B-Instruct` (via `smolagents`) to orchestrate searches and validate data.

## Prerequisites

- Python 3.9+
- Hugging Face API token (`HF_TOKEN`)

## Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Linux/macOS
   source venv/bin/activate  
   # Windows
   venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Playwright browser binaries:
   ```bash
   playwright install chromium
   ```

4. Add your Hugging Face token to a `.env` file in the project root:
   ```env
   HF_TOKEN=your_token_here
   ```

## Usage

### Dashboard

Start the Streamlit interface to search products and view price history:

```bash
streamlit run app.py
```

### CLI

Run a single search from the command line:

```bash
python run_agent.py "iphone 15"
```

## Testing

Run the included unit tests:

```bash
python -m unittest test_db.py test_scraper.py
```

## Stack

- **Agent Framework**: `smolagents`
- **Model**: `Qwen/Qwen2.5-Coder-32B-Instruct`
- **Web Scraping**: Playwright, DuckDuckGo Search (`ddgs`)
- **Storage**: SQLite3
- **Frontend**: Streamlit, Pandas, Altair
