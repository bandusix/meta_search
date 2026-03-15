# PelicineHD Crawler

A specialized web crawler for extracting movie and TV series data from `pelicinehd.com`.

## Features
- **Movies**: Scrapes movies by year (e.g., 2025, 2024...), extracts Spanish/Original titles, rating, quality, and year.
- **TV Series**: Scrapes all TV series, handling multiple seasons via AJAX, extracting all episodes.
- **Database**: SQLite storage with automatic deduplication (`movies` and `tv_episodes` tables).
- **Resilience**: Random User-Agent rotation, retries, and delay to avoid blocking.

## Installation
Ensure you have Python 3.8+ and install dependencies:
```bash
pip install requests beautifulsoup4
```

## Usage

### 1. Scrape Movies
To scrape movies for a specific year:
```bash
# Scrape year 2025 (limit to 1 page for testing)
python -m pelicinehd.main movie --year 2025 --pages 1

# Scrape year 2024 (all pages)
python -m pelicinehd.main movie --year 2024
```

### 2. Scrape TV Series
To scrape all TV series:
```bash
# Scrape first page of series list
python -m pelicinehd.main tv --pages 1

# Scrape ALL series (all pages)
python -m pelicinehd.main tv
```

## Data Output
Data is stored in `pelicinehd_data.db` (SQLite).
- Table `movies`: Stores movie metadata.
- Table `tv_episodes`: Stores individual episode data linked to series.

## Project Structure
- `pelicinehd/`
  - `main.py`: Entry point.
  - `database.py`: Database management.
  - `fetcher.py`: Request handling with retries/headers.
  - `movie_scraper.py`: Movie scraping logic.
  - `tv_scraper.py`: TV scraping logic.
  - `config.py`: Settings (User Agents, Timeouts).
