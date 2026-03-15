# TopFlix Crawler

Automated crawler for `topflix.online` to collect movies and TV series data.

## Features
- **Movies & TV Series**: Crawls both categories.
- **Detailed Info**: Extracts title, year, rating, quality (HD/4K), poster, and player URL.
- **Episodes**: Captures season and episode numbers (e.g., S01E01) from URLs.
- **Incremental Updates**: Updates existing records with new data (quality, episodes).
- **Anti-Scraping**: Uses random User-Agents and delays.
- **Export**: Exports data to CSV files in `exports/YYYY-MM-DD/`.

## Requirements
- Python 3.10+
- Dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

### Run Crawler
To run the crawler with a limit (default 500):
```bash
python spider_main.py [limit]
```

Example (Full Crawl - e.g., 10,000 items):
```bash
python spider_main.py 10000
```

### Data Output
- Database: `topflix.db` (SQLite)
- CSV Exports: `exports/` folder (generated automatically after crawl).

## Project Structure
- `spider_main.py`: Main crawler logic.
- `db_manager.py`: Database operations (SQLite).
- `exporters.py`: CSV export functionality.
- `requirements.txt`: Python dependencies.

## Notes
- The crawler uses `detail_url` as a unique key.
- Re-running the crawler will update existing records if quality/episodes info improves.
