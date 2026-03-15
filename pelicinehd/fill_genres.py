import logging
import sys
import os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pelicinehd.database import DatabaseManager
from pelicinehd.fetcher import Fetcher
from pelicinehd.config import BASE_DIR, MAX_WORKERS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def fetch_genres(fetcher, url):
    """Fetch genres from a URL, returns (genres, is_error)"""
    try:
        response = fetcher.get(url)
        if not response:
            return None, False
            
        # Check for critical error text
        if "Ha habido un error crítico en esta web" in response.text:
            return None, True
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Genres
        genres_tag = soup.select_one('.genres')
        if genres_tag:
            genre_links = genres_tag.select('a')
            if genre_links:
                genres = [a.get_text(strip=True) for a in genre_links]
                return ', '.join(genres), False
            else:
                return genres_tag.get_text(strip=True), False
    except Exception as e:
        logging.error(f"Error fetching genres for {url}: {e}")
    return None, False

def process_movie(fetcher, db, movie_id, url):
    genres, is_error = fetch_genres(fetcher, url)
    
    if is_error:
        logging.warning(f"Critical error found for movie {url}. Deleting from DB...")
        if db.delete_movie(movie_id):
            logging.info(f"Deleted invalid movie: {url}")
        return

    if genres:
        if db.update_movie_genres(movie_id, genres):
            logging.info(f"Updated genres for movie {url}: {genres}")
        else:
            logging.error(f"Failed to update genres for movie {url}")
    else:
        logging.warning(f"No genres found for movie {url}")

def process_series(fetcher, db, series_url):
    genres, is_error = fetch_genres(fetcher, series_url)
    
    if is_error:
        logging.warning(f"Critical error found for series {series_url}. Deleting from DB...")
        if db.delete_series(series_url):
            logging.info(f"Deleted invalid series: {series_url}")
        return

    if genres:
        if db.update_series_genres(series_url, genres):
            logging.info(f"Updated genres for series {series_url}: {genres}")
        else:
            logging.error(f"Failed to update genres for series {series_url}")
    else:
        logging.warning(f"No genres found for series {series_url}")

def main():
    db = DatabaseManager()
    fetcher = Fetcher()
    
    # Fetch lists first
    movies = db.get_movies_missing_genres()
    series_urls = db.get_series_missing_genres()
    
    logging.info(f"Found {len(movies)} movies missing genres")
    logging.info(f"Found {len(series_urls)} series missing genres")
    
    # Use a single ThreadPoolExecutor for both to maximize throughput
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        
        # Submit Movie Tasks
        for m in movies:
            futures.append(executor.submit(process_movie, fetcher, db, m[0], m[1]))
            
        # Submit Series Tasks
        for s in series_urls:
            futures.append(executor.submit(process_series, fetcher, db, s[0]))
            
        # Wait for completion
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logging.error(f"Error in processing thread: {e}")

if __name__ == "__main__":
    main()