# XZ8.cc Spider Project

Based on the architecture report, this project implements a multi-threaded spider to crawl video resources from xz8.cc.

## Project Structure

- `xz8_spider.py`: Core spider logic, including `MediaRepository` (DB), `XZ8Spider` (Crawler), and `DataExporter` (Excel Export).
- `main.py`: Entry point for running tests and crawls.
- `requirements.txt`: Python dependencies.
- `output_full/`: Directory containing the final exported Excel files from full crawl.
- `xz8_media_full.db`: Main database for full crawl data.
- `spider_full_state.json`: State file for resuming full crawl.

## Features

- **Multi-threaded**: Optimized for speed with configurable workers.
- **Resumable**: Automatically saves progress (page number per category) to `spider_full_state.json`. You can stop and restart the script anytime.
- **Deduplication**: Checks if a detail page URL has already been crawled to avoid redundant requests.
- **Robustness**: Includes retry logic for network errors and handles database concurrency.
- **Data Cleaning**: Improved logic for `status` and `quality` field extraction.

## How to Run

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Start Full Crawl**:
    The script defaults to a batch of 5 pages per category for safety.
    ```bash
    python main.py full
    ```
    
    To run a larger batch (e.g., 100 pages per category):
    ```bash
    python main.py full 100
    ```

    To run **Unlimited** (True Full Crawl):
    ```bash
    python main.py full 0
    ```

3.  **Resume Crawl**:
    Just run the same command again. The spider will read `spider_full_state.json` and continue from where it left off.

## Output

The data is saved to `xz8_media_full.db` (SQLite) and exported to `output_full/*.xlsx` after each batch.
