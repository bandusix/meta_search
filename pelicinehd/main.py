import argparse
import logging
import sys
import os

# Add parent directory to sys.path to allow running from pelicinehd directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from pelicinehd.database import DatabaseManager
from pelicinehd.fetcher import Fetcher
from pelicinehd.movie_scraper import MovieScraper
from pelicinehd.tv_scraper import TVScraper
from pelicinehd.config import BASE_DIR, MAX_WORKERS

# Configure logging
log_file = os.path.join(BASE_DIR, "scraper.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_export(db, output_dir, since_timestamp=None):
    os.makedirs(output_dir, exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Define file suffixes
    suffix = "incremental" if since_timestamp else "stock"
    
    # Export Movies
    filename_movies = os.path.join(output_dir, f"movies_{suffix}_{timestamp_str}.csv")
    count_movies = db.export_movies_to_csv(filename_movies, since_timestamp)
    if count_movies > 0:
        logging.info(f"Exported {count_movies} movies ({suffix}) to {filename_movies}")
    else:
        if suffix == "incremental":
            logging.info(f"No new movies to export ({suffix}).")
            if os.path.exists(filename_movies):
                os.remove(filename_movies) # Remove empty file if created by some other process or just avoid creating it. 
                # Actually db.export... creates it. 
                # Wait, pandas to_csv creates it even if empty dataframe? Yes. 
                # Let's keep it simple. If count is 0, user might verify empty file.
    
    # Export TV
    filename_tv = os.path.join(output_dir, f"tv_episodes_{suffix}_{timestamp_str}.csv")
    count_tv = db.export_tv_episodes_to_csv(filename_tv, since_timestamp)
    if count_tv > 0:
        logging.info(f"Exported {count_tv} TV episodes ({suffix}) to {filename_tv}")
    else:
        if suffix == "incremental":
             logging.info(f"No new TV episodes to export ({suffix}).")

def main():
    parser = argparse.ArgumentParser(description="PelicineHD Crawler")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Movie Command
    movie_parser = subparsers.add_parser('movie', help='Scrape movies')
    movie_parser.add_argument('--year', type=int, help="Specific year to scrape")
    movie_parser.add_argument('--year-range', nargs=2, type=int, metavar=('START', 'END'), help="Range of years to scrape (e.g. 2020 2025)")
    movie_parser.add_argument('--pages', type=int, default=None, help="Max pages to scrape per year")
    movie_parser.add_argument('--threads', type=int, default=MAX_WORKERS, help=f"Number of threads (default: {MAX_WORKERS})")

    # TV Command
    tv_parser = subparsers.add_parser('tv', help='Scrape TV series')
    tv_parser.add_argument('--pages', type=int, default=None, help="Max pages to scrape")
    tv_parser.add_argument('--max-series', type=int, default=None, help="Max number of series to scrape")
    tv_parser.add_argument('--threads', type=int, default=MAX_WORKERS, help=f"Number of threads (default: {MAX_WORKERS})")

    # Export Command
    export_parser = subparsers.add_parser('export', help='Export data to CSV')
    export_parser.add_argument('--type', choices=['movies', 'tv', 'all'], default='all', help="Type of data to export")
    export_parser.add_argument('--output-dir', default='exports', help="Directory to save CSV files")
    export_parser.add_argument('--since', help="Export data since timestamp (YYYY-MM-DD HH:MM:SS)")

    # Stats Command
    subparsers.add_parser('stats', help='Show database statistics')

    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return

    db = DatabaseManager()
    
    # Record start time for incremental export
    # SQLite CURRENT_TIMESTAMP is UTC.
    # We should use UTC for query comparison.
    start_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

    if args.command == 'movie':
        fetcher = Fetcher()
        scraper = MovieScraper(fetcher, db, max_workers=args.threads)
        
        if args.year_range:
            start_year, end_year = args.year_range
            scraper.scrape_year_range(start_year, end_year)
        elif args.year:
            scraper.scrape_year(args.year, max_pages=args.pages)
        else:
            print("Error: Either --year or --year-range must be provided for movie mode")
            return

        # Auto Export after scrape
        logging.info("Starting automatic data export...")
        export_dir = os.path.join(BASE_DIR, 'exports')
        run_export(db, export_dir) # Stock
        run_export(db, export_dir, since_timestamp=start_time) # Incremental
            
    elif args.command == 'tv':
        fetcher = Fetcher()
        scraper = TVScraper(fetcher, db, max_workers=args.threads)
        scraper.scrape_all(max_pages=args.pages, max_series=args.max_series)
        
        # Auto Export after scrape
        logging.info("Starting automatic data export...")
        export_dir = os.path.join(BASE_DIR, 'exports')
        run_export(db, export_dir) # Stock
        run_export(db, export_dir, since_timestamp=start_time) # Incremental

    elif args.command == 'export':
        output_dir = args.output_dir if os.path.isabs(args.output_dir) else os.path.join(BASE_DIR, args.output_dir)
        run_export(db, output_dir)

    elif args.command == 'stats':
        stats = db.get_statistics()
        print("\nDatabase Statistics:")
        print(f"Movies: {stats.get('movie_count', 0)}")
        print(f"TV Episodes: {stats.get('tv_episode_count', 0)}")
        print("\nMovies by Year (Top 10):")
        for year, count in stats.get('movies_by_year', []):
            print(f"  {year}: {count}")

if __name__ == "__main__":
    main()
