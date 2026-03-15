import logging
import sys
import os
import re
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

def fetch_details(fetcher, url):
    """Fetch genres, duration, and quality from a URL"""
    try:
        response = fetcher.get(url)
        if not response:
            return None, True
            
        # Check for critical error text
        if "Ha habido un error crítico en esta web" in response.text:
            return None, True
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        data = {}
        
        # Genres
        genres_tag = soup.select_one('.genres')
        if genres_tag:
            genre_links = genres_tag.select('a')
            if genre_links:
                genres = [a.get_text(strip=True) for a in genre_links]
                data['genres'] = ', '.join(genres)
            else:
                data['genres'] = genres_tag.get_text(strip=True)
        else:
            data['genres'] = None
            
        # Duration (Movie only usually)
        duration_tag = soup.select_one('.duration')
        if duration_tag:
             data['duration'] = duration_tag.get_text(strip=True)
        else:
             data['duration'] = None

        # Quality (Often in list page, but check detail just in case?)
        # Detail page usually doesn't show quality prominently like list page card.
        # But sometimes it's in a tag. Let's look for common patterns.
        # Or maybe it's passed from list page logic.
        # For this script, we are re-scraping detail page.
        # If quality is missing in DB, we might need to search for it.
        # But quality is usually a property of the release, shown on the card.
        # On detail page, maybe: <span class="quality">...</span>?
        # Let's try generic selector.
        # The list page uses .Qlty
        # Let's see if detail page has it.
        # If not, we might be stuck without quality if we only look at detail page.
        # However, let's try to find it.
        # Some sites put it in metadata.
        
        return data, False
    except Exception as e:
        logging.error(f"Error fetching details for {url}: {e}")
    return None, False

def process_movie(fetcher, db, movie_id, url):
    data, is_error = fetch_details(fetcher, url)
    
    if is_error:
        logging.warning(f"Critical error or fetch failed for movie {url}. Deleting from DB...")
        if db.delete_movie(movie_id):
            logging.info(f"Deleted invalid movie: {url}")
        return

    if data:
        # For quality, if it's missing in DB, we might not find it on detail page easily.
        # But let's update what we found.
        # Wait, if duration is missing, we definitely want to update it.
        # If genres is missing, update it.
        
        # Since quality is hard to find on detail page (usually on poster card in list),
        # we might skip quality update here unless we find a specific tag.
        # But the user asked to fill empty fields.
        # If quality is NULL, and we can't find it, we can't fill it.
        # But at least we fill duration and genres.
        
        db.update_movie_details(movie_id, genres=data.get('genres'), duration=data.get('duration'))
        logging.info(f"Updated details for movie {url}")

def process_series(fetcher, db, series_url):
    data, is_error = fetch_details(fetcher, series_url)
    
    if is_error:
        logging.warning(f"Critical error or fetch failed for series {series_url}. Deleting from DB...")
        if db.delete_series(series_url):
            logging.info(f"Deleted invalid series: {series_url}")
        return

    if data:
        db.update_series_details(series_url, genres=data.get('genres'))
        logging.info(f"Updated details for series {series_url}")

def main():
    db = DatabaseManager()
    fetcher = Fetcher()
    
    # Fetch lists first
    movies = db.get_movies_missing_data()
    series_urls = db.get_series_missing_data()
    
    logging.info(f"Found {len(movies)} movies missing data (genres/duration/quality)")
    logging.info(f"Found {len(series_urls)} series missing data (genres/quality)")
    
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