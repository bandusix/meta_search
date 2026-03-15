import requests
from bs4 import BeautifulSoup
import time
import random
import re
from db_manager import DBManager
from exporters import Exporter
import sys
import logging
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
BASE_URL = "https://topflix.online"
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 16; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]
MAX_RETRIES = 3
TARGET_COUNT = 500
MAX_WORKERS = 10 # Default workers

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)

class TopFlixCrawler:
    def __init__(self, workers=MAX_WORKERS):
        self.db = DBManager()
        self.session = requests.Session()
        self.workers = workers
        
    def get_random_header(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": BASE_URL
        }

    def fetch_url(self, url):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                response = self.session.get(url, headers=self.get_random_header(), timeout=20)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    logging.warning(f"404 Not Found: {url}")
                    return None
                else:
                    logging.warning(f"Status {response.status_code}: {url}")
            except Exception as e:
                logging.error(f"Error fetching {url}: {e}")
            
            retries += 1
            time.sleep(random.uniform(1, 3))
        return None

    def parse_list_item(self, item):
        try:
            title_elem = item.select_one('.poster__title span')
            title = title_elem.text.strip() if title_elem else "Unknown"
            
            link_elem = item.select_one('.poster__title a')
            if not link_elem:
                link_elem = item.select_one('a')
            detail_url = link_elem['href'] if link_elem else ""
            
            year_tag = item.select_one('.bslide__meta span:first-child')
            year = 0
            if year_tag and year_tag.text.strip().isdigit():
                year = int(year_tag.text.strip())
            
            rating_tag = item.select_one('.rating.roundnum')
            rating = float(rating_tag.text.strip()) if rating_tag else 0.0
            
            img_tag = item.select_one('.poster__img img')
            poster = img_tag['src'] if img_tag else ""
            if poster and '?' in poster:
                poster = poster.split('?')[0]

            return {
                "title": title,
                "detail_url": detail_url,
                "year": year,
                "rating": rating,
                "poster_url": poster
            }
        except Exception as e:
            logging.error(f"Error parsing item: {e}")
            return None

    def process_movie_item(self, item_data):
        # Fetch details for Quality and Player URL
        # To avoid blocking too much, we sleep a bit less or random
        time.sleep(random.uniform(0.5, 1.5))
        
        detail_html = self.fetch_url(item_data['detail_url'])
        item_data['quality'] = "HD" # Default to HD
        item_data['player_url'] = item_data['detail_url'] # Default
        
        if detail_html:
            d_soup = BeautifulSoup(detail_html, 'html.parser')
            # Try to find quality in text
            page_text = d_soup.get_text()
            if "4K" in page_text:
                item_data['quality'] = "4K"
            elif "1080p" in page_text:
                item_data['quality'] = "1080p"
            elif "720p" in page_text:
                item_data['quality'] = "720p"
            
            # Also check for specific tags if any
            q_tag = d_soup.select_one('.quality')
            if q_tag:
                item_data['quality'] = q_tag.text.strip()

        # Upsert / Update
        if self.db.movie_exists(item_data['detail_url']):
            logging.info(f"Updating existing movie: {item_data['title']}")
            self.db.connect()
            try:
                self.db.cursor.execute("UPDATE movies SET quality=?, player_url=? WHERE detail_url=?", 
                                     (item_data['quality'], item_data['player_url'], item_data['detail_url']))
                self.db.conn.commit()
            finally:
                self.db.close()
        else:
            self.db.save_movie(item_data)
            logging.info(f"Saved Movie: {item_data['title']}")

    def crawl_movies(self, limit=TARGET_COUNT):
        logging.info(f"--- Starting Movie Crawl (Limit: {limit}) ---")
        page = 1
        count = 0
        empty_pages = 0
        
        while count < limit:
            url = f"{BASE_URL}/filmes/page/{page}/"
            logging.info(f"Fetching Movies Page {page}...")
            html = self.fetch_url(url)
            
            if not html:
                empty_pages += 1
                if empty_pages >= 3:
                    logging.info("Max empty pages reached. Stopping.")
                    break
                page += 1
                continue
            
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select('.poster.grid-item')
            
            if not items:
                empty_pages += 1
                if empty_pages >= 3:
                    logging.info("No items found for 3 consecutive pages. Stopping.")
                    break
            else:
                empty_pages = 0
            
            # Process items in parallel for this page
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = []
                for item in items:
                    if count >= limit:
                        break
                    data = self.parse_list_item(item)
                    if not data:
                        continue
                    
                    futures.append(executor.submit(self.process_movie_item, data))
                    count += 1
                
                # Wait for page items to finish
                for f in futures:
                    f.result()
                
            page += 1
            time.sleep(random.uniform(1, 3))

    def process_tv_item(self, item_data):
        # Check existence
        show_id = self.db.tv_show_exists(item_data['detail_url'])
        if not show_id:
            show_id = self.db.save_tv_show(item_data)
            logging.info(f"Saved Show: {item_data['title']}")
        else:
            logging.info(f"Show exists: {item_data['title']}")
        
        # Fetch Detail Page
        time.sleep(random.uniform(0.5, 1.5))
        detail_html = self.fetch_url(item_data['detail_url'])
        if detail_html:
            d_soup = BeautifulSoup(detail_html, 'html.parser')
            episodes = d_soup.select('.seasoncontent-v2 .epi-link')
            
            if not episodes:
                 episodes = d_soup.select('.episodios li')
            
            saved_eps = 0
            for ep in episodes:
                ep_url = ep.get('href')
                ep_title = ep.select_one('.name').text.strip() if ep.select_one('.name') else ""
                ep_num_txt = ep.select_one('.numerando').text.strip() if ep.select_one('.numerando') else ""
                
                season_num = 0
                episode_num = 0
                
                match_s_e = re.search(r's(\d+)e(\d+)', ep_url, re.IGNORECASE)
                if match_s_e:
                    season_num = int(match_s_e.group(1))
                    episode_num = int(match_s_e.group(2))
                else:
                    match_x = re.search(r'(\d+)x(\d+)', ep_url, re.IGNORECASE)
                    if match_x:
                        season_num = int(match_x.group(1))
                        episode_num = int(match_x.group(2))
                
                if season_num == 0 and episode_num == 0 and '-' in ep_num_txt:
                    parts = ep_num_txt.split('-')
                    if len(parts) >= 2:
                        season_num = int(parts[0].strip()) if parts[0].strip().isdigit() else 0
                        episode_num = int(parts[1].strip()) if parts[1].strip().isdigit() else 0
                
                ep_data = {
                    "show_id": show_id,
                    "season_number": season_num,
                    "episode_number": episode_num,
                    "title": ep_title,
                    "detail_url": ep_url,
                    "player_url": ep_url
                }
                self.db.save_episode(ep_data)
                saved_eps += 1
            
            if saved_eps > 0:
                logging.info(f"  > Saved {saved_eps} episodes for {item_data['title']}")

    def crawl_tv_series(self, limit=TARGET_COUNT):
        logging.info(f"--- Starting TV Series Crawl (Limit: {limit}) ---")
        page = 1
        count = 0
        empty_pages = 0
        
        while count < limit:
            url = f"{BASE_URL}/series/page/{page}/"
            logging.info(f"Fetching Series Page {page}...")
            html = self.fetch_url(url)
            
            if not html:
                empty_pages += 1
                if empty_pages >= 3:
                    break
                page += 1
                continue
                
            soup = BeautifulSoup(html, 'html.parser')
            items = soup.select('.poster.grid-item')
            
            if not items:
                empty_pages += 1
                if empty_pages >= 3:
                    break
            else:
                empty_pages = 0
            
            with ThreadPoolExecutor(max_workers=self.workers) as executor:
                futures = []
                for item in items:
                    if count >= limit:
                        break
                    data = self.parse_list_item(item)
                    if not data:
                        continue
                    
                    futures.append(executor.submit(self.process_tv_item, data))
                    count += 1
                
                for f in futures:
                    f.result()

            page += 1
            time.sleep(random.uniform(1, 3))

    def run(self, limit=TARGET_COUNT):
        # 1. Crawl Movies
        self.crawl_movies(limit)
        
        # 2. Crawl TV Series
        self.crawl_tv_series(limit)
        
        # 3. Export
        try:
            exporter = Exporter()
            exporter.export_data()
        except Exception as e:
            logging.error(f"Export failed: {e}")

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else TARGET_COUNT
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else MAX_WORKERS
    
    crawler = TopFlixCrawler(workers=workers)
    crawler.run(limit)
