import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
import random
import logging
import urllib3
import concurrent.futures
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from database import get_connection

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VS1919Spider:
    BASE_URL = "https://www.1919ys.com"
    
    # Category IDs
    CAT_MOVIE = 1
    CAT_TV = 2
    CAT_VARIETY = 3
    CAT_ANIME = 4
    CAT_DRAMA = 34
    
    # Map ID to Category Name
    CAT_MAP = {
        1: 'movie',
        2: 'tv_series',
        3: 'variety_show',
        4: 'anime',
        34: 'short_drama'
    }
    
    def __init__(self, max_workers=60):
        self.session = requests.Session()
        
        # Configure robust retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(
            pool_connections=max_workers, 
            pool_maxsize=max_workers,
            max_retries=retry_strategy
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.session.verify = False
        self.conn = get_connection()
        self.max_workers = max_workers
        self.db_lock = threading.Lock()
        
    def close(self):
        self.conn.close()

    def crawl_category(self, category_id, incremental=False):
        """Crawl a specific category fully or incrementally."""
        cat_name = self.CAT_MAP.get(category_id, str(category_id))
        mode = "INCREMENTAL" if incremental else "FULL"
        logger.info(f"[{cat_name}] Starting {mode} crawl with {self.max_workers} threads...")
        
        count = 0
        new_items_count = 0
        page = 1
        consecutive_empty_pages = 0
        consecutive_errors = 0
        consecutive_no_new_items_pages = 0 # For incremental mode
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while True:
                list_url = f"{self.BASE_URL}/vsbstp/{category_id}-{page}.html"
                logger.info(f"[{cat_name}] Fetching list page {page}: {list_url}")
                
                try:
                    # Fetch list page
                    response = self.session.get(list_url, timeout=15)
                    if response.status_code != 200:
                        logger.error(f"[{cat_name}] Failed to fetch {list_url}: {response.status_code}")
                        consecutive_errors += 1
                        if consecutive_errors > 5:
                            logger.error(f"[{cat_name}] Too many consecutive errors. Stopping.")
                            break
                        time.sleep(5)
                        continue
                    
                    consecutive_errors = 0 # Reset error count
                    response.encoding = 'utf-8'
                    soup = BeautifulSoup(response.text, 'lxml')
                    
                    items = soup.select('.stui-vodlist__box')
                    if not items:
                        logger.warning(f"[{cat_name}] No items found on page {page}.")
                        consecutive_empty_pages += 1
                        if consecutive_empty_pages >= 3:
                            logger.info(f"[{cat_name}] 3 consecutive empty pages. Stopping.")
                            break
                        page += 1
                        continue
                        
                    consecutive_empty_pages = 0 # Reset empty page count
                    
                    # Submit detail tasks
                    futures = []
                    page_new_items = 0
                    
                    for item in items:
                        try:
                            thumb = item.select_one('.stui-vodlist__thumb')
                            detail_url = urljoin(self.BASE_URL, thumb['href'])
                            
                            # Incremental Check: If we already have this detail_url in DB, we might skip it?
                            # But wait, episodes might be updated (new episodes added).
                            # So we should probably check if the *number of episodes* changed or just re-crawl it.
                            # Re-crawling detail page is safer to get new episodes.
                            # Optimization: Check if 'update_time' or 'status' in DB matches? 
                            # The site list page doesn't show update time clearly in the box (only in detail).
                            # However, for efficiency, if we see a title we processed RECENTLY, maybe we stop?
                            # Standard incremental logic: if we encounter N items that haven't changed, we stop.
                            # But here, let's assume if we scan 3 pages and find NO new episodes/data, we stop.
                            
                            title = thumb['title']
                            poster_url = urljoin(self.BASE_URL, thumb['data-original'])
                            quality = item.select_one('.pic-text b').text if item.select_one('.pic-text b') else ''
                            genre = item.select_one('.pic-text1 b').text if item.select_one('.pic-text1 b') else ''
                            
                            future = executor.submit(self._fetch_detail_data, category_id, detail_url, title, poster_url, quality, genre)
                            futures.append(future)
                            
                        except Exception as e:
                            logger.error(f"[{cat_name}] Error submitting item: {e}")
                            continue
                    
                    # Process results
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            data = future.result()
                            if data:
                                with self.db_lock:
                                    saved_count = self._save_data(category_id, data)
                                    if saved_count > 0:
                                        page_new_items += saved_count
                                        new_items_count += saved_count
                                count += 1
                        except Exception as e:
                            logger.error(f"[{cat_name}] Error processing future: {e}")
                    
                    logger.info(f"[{cat_name}] Page {page} finished. Processed {len(futures)} items. New/Updated records: {page_new_items}")
                    
                    # Incremental Stop Condition
                    if incremental:
                        if page_new_items == 0:
                            consecutive_no_new_items_pages += 1
                            if consecutive_no_new_items_pages >= 3:
                                logger.info(f"[{cat_name}] Incremental scan finished: 3 consecutive pages with no updates.")
                                break
                        else:
                            consecutive_no_new_items_pages = 0
                    
                    # FORCED PAGINATION: Ignore "Next Page" button check
                    page += 1
                    
                except Exception as e:
                    logger.error(f"[{cat_name}] Error processing list page {page}: {e}")
                    consecutive_errors += 1
                    if consecutive_errors > 5:
                        break
                    time.sleep(5) # Cool down
                
        logger.info(f"[{cat_name}] Finished {mode} crawling. Total items scanned: {count}. New/Updated records: {new_items_count}")

    def _fetch_detail_data(self, category_id, detail_url, title, poster_url, quality, genre):
        """Fetch detail page and return data dict."""
        try:
            # Random delay to prevent overwhelming server if threads align
            time.sleep(random.uniform(0.1, 0.5))
            
            response = self.session.get(detail_url, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to fetch detail page {detail_url}")
                return None
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'lxml')
            
            info = self._extract_info(soup)
            info['title'] = title
            info['detail_url'] = detail_url
            info['poster_url'] = poster_url
            info['quality'] = quality
            info['genre'] = genre
            
            result = {'info': info}
            
            if category_id == self.CAT_MOVIE:
                play_url = self._extract_movie_play_url(soup)
                if play_url:
                    result['episodes'] = [{'episode_title': 'Full Movie', 'play_url': play_url}]
                else:
                    result['episodes'] = []
            else:
                result['episodes'] = self._extract_episode_play_urls(soup)
                
            return result
                
        except Exception as e:
            # logger.error(f"Error in _fetch_detail_data for {detail_url}: {e}")
            # Keep logs cleaner
            return None

    def _save_data(self, category_id, data):
        """Save flattened data to single table."""
        info = data['info']
        episodes = data['episodes']
        category_name = self.CAT_MAP.get(category_id, 'unknown')
        
        if not episodes:
            return 0

        cursor = self.conn.cursor()
        saved_count = 0
        
        for ep in episodes:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO media_resources (
                        category, title, episode_name, play_url, detail_url, poster_url,
                        year, quality, genre, region, director, actors, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    category_name,
                    info['title'],
                    ep['episode_title'],
                    ep['play_url'],
                    info['detail_url'],
                    info['poster_url'],
                    info['year'],
                    info['quality'],
                    info['genre'],
                    info['region'],
                    info['director'],
                    info['actors'],
                    info['status']
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Database error: {e}")
        
        self.conn.commit()
        return saved_count

    def _extract_info(self, soup):
        """Extract detailed info from detail page."""
        info_text = soup.select_one('.stui-content__detail .data.hidden-xs')
        info_str = info_text.text if info_text else ''
        
        year_match = re.search(r'年份：(\d{4})', info_str)
        region_match = re.search(r'地区：([^/]+)', info_str)
        
        director_elem = soup.find('p', class_='data', string=re.compile('导演'))
        actors_elem = soup.find('p', class_='data', string=re.compile('主演'))
        status_elem = soup.select_one('.data span[style*="red"]')
        
        return {
            'year': int(year_match.group(1)) if year_match else 0,
            'region': region_match.group(1).strip() if region_match else '',
            'director': director_elem.text.replace('导演：', '').strip() if director_elem else '',
            'actors': actors_elem.text.replace('主演：', '').strip() if actors_elem else '',
            'status': status_elem.text if status_elem else '',
        }

    def _extract_movie_play_url(self, soup):
        """Extract play URL for movie."""
        playlist = soup.select_one('.stui-content__playlist')
        if playlist:
            links = playlist.select('li a')
            for link in links:
                href = link['href']
                if '/vsbspy/' in href:
                    play_url = href
                    if not play_url.startswith('http'):
                        play_url = urljoin(self.BASE_URL, play_url)
                    return play_url
        return None

    def _extract_episode_play_urls(self, soup):
        """Extract all episode play URLs."""
        episodes = []
        source_tabs = soup.select('[data-toggle="tab"]')
        playlists = soup.select('.stui-content__playlist')
        
        for idx, playlist in enumerate(playlists):
            source_name = f"Source {idx+1}"
            if idx < len(source_tabs):
                source_name = source_tabs[idx].text.strip()
            
            episode_links = playlist.select('li a')
            
            for ep_link in episode_links:
                episode_title = ep_link.text.strip()
                play_url = ep_link['href']
                
                if '/vsbspy/' not in play_url:
                    continue
                
                if not play_url.startswith('http'):
                    play_url = urljoin(self.BASE_URL, play_url)
                
                full_title = f"{episode_title} [{source_name}]"
                
                episodes.append({
                    'episode_title': full_title,
                    'play_url': play_url
                })
        return episodes
