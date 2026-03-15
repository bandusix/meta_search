import logging
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import BASE_URL, MAX_WORKERS

class MovieScraper:
    # Available years list as per guide
    AVAILABLE_YEARS = [
        1932, 1959, 1966, 1968, 1970, 1971, 1973, 1977, 1978, 1979,
        1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
        1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
        2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
        2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
        2020, 2021, 2022, 2023, 2024, 2025, 2026
    ]

    def __init__(self, fetcher, db, max_workers=MAX_WORKERS):
        self.fetcher = fetcher
        self.db = db
        self.max_workers = max_workers

    def scrape_year_range(self, start_year, end_year):
        """Scrape movies for a range of years (reverse order)"""
        years = [y for y in self.AVAILABLE_YEARS if start_year <= y <= end_year]
        years.sort(reverse=True)
        
        logging.info(f"Starting scrape for years: {years}")
        
        for year in years:
            self.scrape_year(year)

    def scrape_year(self, year, max_pages=None):
        """Scrape all movies for a specific year"""
        logging.info(f"Starting scrape for year {year}")
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                logging.info(f"Reached max pages {max_pages}")
                break
                
            url = f"{BASE_URL}/release/{year}/page/{page}/" if page > 1 else f"{BASE_URL}/release/{year}/"
            logging.info(f"Scanning Year {year} Page {page}: {url}")
            
            response = self.fetcher.get(url)
            if not response or response.status_code == 404:
                logging.info(f"Page {page} not found or error, stopping year {year}")
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try both selectors for robustness
            movies = soup.select('article.movies')
            if not movies:
                movies = soup.select('ul.post-lst > li.movies')
            
            if not movies:
                logging.info(f"No movies found on page {page}, stopping year {year}")
                break
                
            logging.info(f"Found {len(movies)} movies on page {page}")
            
            # Use ThreadPoolExecutor for concurrent processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self._process_movie, movie_node, year) for movie_node in movies]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logging.error(f"Error in movie processing thread: {e}")
            
            # Check for next page
            next_link = soup.select_one('a:-soup-contains("SIGUIENTE")')
            if not next_link:
                # Fallback check
                pagination = soup.select_one('.pagination')
                if not pagination or not pagination.find('a', href=re.compile(f'page/{page+1}')):
                    logging.info("No next page found")
                    break
            
            page += 1

    def _process_movie(self, node, default_year):
        """Extract basic info and visit detail page"""
        url_tag = node.select_one('a.lnk-blk')
        if not url_tag:
            return
        
        url = url_tag['href']
        
        # Check if it is a movie URL (not series)
        if '/movies/' not in url:
            return

        # Check DB
        if self.db.movie_exists(url):
            logging.info(f"Movie already exists: {url}")
            return

        # Extract List Page Info
        title_tag = node.select_one('.entry-title')
        title_spanish = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        rating_elem = node.select_one('.vote')
        rating_text = rating_elem.get_text(strip=True) if rating_elem else "0"
        rating = self._parse_rating(rating_text)

        quality_tag = node.select_one('.Qlty')
        quality = quality_tag.get_text(strip=True) if quality_tag else None
        
        # Extract Poster
        img_tag = node.select_one('img')
        poster_url = img_tag.get('src') if img_tag else None
        if poster_url and poster_url.startswith('//'):
            poster_url = 'https:' + poster_url

        # Extract Year (if available on card)
        year_tag = node.select_one('.year')
        year = int(year_tag.get_text(strip=True)) if year_tag else default_year

        # Fetch Detail Page for more info
        detail_data = self._scrape_detail(url)
        
        # Ensure we have essential data, otherwise skip or log warning
        # But we want to save partial data if possible, then fill later?
        # User requirement: "guarantee write two data and genre data can be crawled to enter the library"
        # This implies we should perhaps NOT save if these are missing?
        # Or try harder to find them.
        
        movie_data = {
            'title_spanish': title_spanish,
            'title_original': detail_data.get('title_original'),
            'year': detail_data.get('year', year), 
            'rating': rating,
            'quality': quality,
            'duration': detail_data.get('duration'),
            'url': url,
            'poster_url': poster_url,
            'genres': detail_data.get('genres')
        }
        
        if self.db.save_movie(movie_data):
            logging.info(f"Saved movie: {title_spanish} | URL: {url}")

    def _scrape_detail(self, url):
        """Extract detailed info from movie page"""
        data = {}
        try:
            response = self.fetcher.get(url)
            if not response:
                return data
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Year from detail (often more reliable)
            year_tag = soup.select_one('.entry-meta .year')
            if year_tag:
                try:
                    data['year'] = int(year_tag.get_text(strip=True))
                except:
                    pass
            
            # Duration
            # Often in <span class="duration"> or similar
            duration_tag = soup.select_one('.duration')
            if duration_tag:
                data['duration'] = duration_tag.get_text(strip=True)

            # Original Title
            # Look for specific markers
            # Example: <strong>Título original:</strong> ...
            # Or <div class="mvic-info"> ...
            target_elem = soup.find('strong', string=re.compile('Título original', re.I))
            if target_elem and target_elem.next_sibling:
                 data['title_original'] = target_elem.next_sibling.strip()
            
            # If not found, try other common patterns
            if 'title_original' not in data:
                # Sometimes it is just in a paragraph
                # Let's leave it as None if not found
                pass
            
            # Genres
            genres_tag = soup.select_one('.genres')
            if genres_tag:
                # Often contains links <a>Genre</a>
                genre_links = genres_tag.select('a')
                if genre_links:
                    genres = [a.get_text(strip=True) for a in genre_links]
                    data['genres'] = ', '.join(genres)
                else:
                    data['genres'] = genres_tag.get_text(strip=True)
            
        except Exception as e:
            logging.error(f"Error scraping detail {url}: {e}")
        
        return data

    def _parse_rating(self, rating_text):
        if not rating_text:
            return 0.0
        # "TMDB 4.5" -> 4.5
        match = re.search(r'(\d+(\.\d+)?)', rating_text)
        if match:
            return float(match.group(1))
        return 0.0
