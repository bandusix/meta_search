import logging
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from .config import BASE_URL, MAX_WORKERS

class TVScraper:
    def __init__(self, fetcher, db, max_workers=MAX_WORKERS):
        self.fetcher = fetcher
        self.db = db
        self.max_workers = max_workers

    def scrape_all(self, max_pages=None, max_series=None):
        """Scrape all TV series"""
        page = 1
        total_series = 0
        
        while True:
            if max_pages and page > max_pages:
                logging.info(f"Reached max pages {max_pages}")
                break
                
            url = f"{BASE_URL}/series/page/{page}/" if page > 1 else f"{BASE_URL}/series/"
            logging.info(f"Scanning TV Series Page {page}: {url}")
            
            response = self.fetcher.get(url)
            if not response or response.status_code == 404:
                break
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Selector for series in list
            series_list = soup.select('article.movies')
            if not series_list:
                series_list = soup.select('ul.post-lst > li.series')
            
            if not series_list:
                break
                
            # Use ThreadPoolExecutor for concurrent processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(self._process_series, series_node) for series_node in series_list]
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result: # If we need to count processed series
                             total_series += 1
                    except Exception as e:
                        logging.error(f"Error processing series thread: {e}")
            
            if max_series and total_series >= max_series:
                 logging.info(f"Reached max series limit (approx): {total_series}")
                 return

            # Pagination check
            next_link = soup.select_one('a:-soup-contains("SIGUIENTE")')
            if not next_link:
                # Fallback check
                pagination = soup.select_one('.pagination')
                if not pagination or not pagination.find('a', href=re.compile(f'page/{page+1}')):
                    break
            
            page += 1

    def _process_series(self, node):
        url_tag = node.select_one('a.lnk-blk')
        if not url_tag:
            return False
        
        url = url_tag['href']
        if '/series/' not in url:
            return False

        logging.info(f"Processing Series: {url}")
        
        # Extract Series Info from List
        title_tag = node.select_one('.entry-title')
        title_spanish = title_tag.get_text(strip=True) if title_tag else "Unknown"
        
        rating_elem = node.select_one('.vote')
        rating_text = rating_elem.get_text(strip=True) if rating_elem else "0"
        rating = self._parse_rating(rating_text)
        
        year_elem = node.select_one('.year')
        year = int(year_elem.get_text(strip=True)) if year_elem else 0
        
        img_elem = node.select_one('img')
        poster_url = img_elem.get('src') if img_elem else None
        if poster_url and poster_url.startswith('//'):
            poster_url = 'https:' + poster_url

        series_data = {
            'title_spanish': title_spanish,
            'rating': rating,
            'year': year,
            'url': url,
            'poster_url': poster_url
        }
        
        # We always scrape detail because episodes are there
        self._scrape_series_detail(series_data)
        return True

    def _scrape_series_detail(self, series_data):
        url = series_data['url']
        response = self.fetcher.get(url)
        if not response:
            return
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Update Series Info if needed (e.g. Original Title)
        # Assuming original title might be found similar to movies
        series_data['title_original'] = None
        target_elem = soup.find('strong', string=re.compile('Título original', re.I))
        if target_elem and target_elem.next_sibling:
             series_data['title_original'] = target_elem.next_sibling.strip()

        # Genres
        genres_tag = soup.select_one('.genres')
        if genres_tag:
             genre_links = genres_tag.select('a')
             if genre_links:
                 genres = [a.get_text(strip=True) for a in genre_links]
                 series_data['genres'] = ', '.join(genres)
             else:
                 series_data['genres'] = genres_tag.get_text(strip=True)
        else:
            series_data['genres'] = None

        # Find seasons
        season_links = soup.select('.choose-season .sub-menu li a')
        
        # Extract Post ID for AJAX
        post_id = None
        if season_links:
            post_id = season_links[0].get('data-post')
        
        # Process Season 1 (Default loaded)
        self._parse_episodes(soup, series_data, 1)
        
        # Process other seasons if exist
        if season_links and len(season_links) > 1:
            for link in season_links:
                season_num = int(link.get('data-season'))
                if season_num == 1:
                    continue # Already done
                
                logging.info(f"Fetching Season {season_num} for {series_data['title_spanish']}")
                self._fetch_and_parse_season(post_id, season_num, series_data)

    def _fetch_and_parse_season(self, post_id, season_num, series_data):
        """AJAX fetch for other seasons"""
        ajax_url = f"{BASE_URL}/wp-admin/admin-ajax.php"
        data = {
            'action': 'action_select_season',
            'season': season_num,
            'post': post_id
        }
        
        response = self.fetcher.post(ajax_url, data=data)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            self._parse_episodes(soup, series_data, season_num)

    def _parse_episodes(self, soup, series_data, season_num):
        episodes = soup.select('li article.episodes')
        if not episodes:
            episodes = soup.select('article.episodes')

        for ep in episodes:
            try:
                # URL
                url_tag = ep.select_one('a.lnk-blk')
                if not url_tag: continue
                url = url_tag['href']
                
                if self.db.episode_exists(url):
                    continue

                # Title: 1x1 or Spartacus... 1x1
                ep_title = ep.select_one('h2.entry-title').get_text(strip=True)
                
                # Extract episode number
                num_tag = ep.select_one('span.num-epi')
                episode_num = 0
                if num_tag:
                    num_text = num_tag.get_text(strip=True)
                    parts = num_text.split('x')
                    if len(parts) == 2:
                        episode_num = int(parts[1])
                
                # Save
                ep_data = {
                    'series_title_spanish': series_data['title_spanish'],
                    'series_title_original': series_data.get('title_original'),
                    'year': series_data['year'],
                    'rating': series_data['rating'],
                    'quality': 'HD', # Default or extract if available
                    'season': season_num,
                    'episode': episode_num,
                    'episode_title': ep_title,
                    'url': url,
                    'series_url': series_data['url'],
                    'poster_url': series_data.get('poster_url'),
                    'genres': series_data.get('genres')
                }
                
                if self.db.save_episode(ep_data):
                    logging.info(f"Saved Episode: {ep_title} | URL: {url}")
                    
            except Exception as e:
                logging.error(f"Error parsing episode: {e}")

    def _parse_rating(self, rating_text):
        if not rating_text:
            return 0.0
        match = re.search(r'(\d+(\.\d+)?)', rating_text)
        if match:
            return float(match.group(1))
        return 0.0
