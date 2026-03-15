# -*- coding: utf-8 -*-
'''
core/base_spider.py

Provides the abstract base class for all spiders, defining the main crawl loop
and orchestration logic.
'''

import logging
import time
import psutil
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.request_handler import RequestHandler
from core.database import DatabaseManager
from parsers.list_parser import ListPageParser
from parsers.detail_parser import DetailPageParser
from parsers.play_parser import PlayPageParser
from utils.url_builder import build_list_url

logger = logging.getLogger(__name__)

class BaseSpider(ABC):
    '''Abstract base class for spiders.'''

    def __init__(self, config):
        '''Initializes the spider with configuration.'''
        self.config = config
        self.request_handler = RequestHandler(
            base_url=config['spider']['base_url'],
            delay_range=config['spider']['delay_range'],
            max_retries=config['spider']['max_retries'],
            timeout=config['spider']['timeout'],
            user_agents=config['spider']['user_agents']
        )
        self.db_manager = DatabaseManager(config['database']['path'])
        self.list_parser = ListPageParser()
        self.detail_parser = DetailPageParser()
        self.play_parser = PlayPageParser()
        self.items_crawled = 0
        self.max_items = config['crawl'].get('max_items')
        
        # Concurrency settings
        self.concurrency = config['spider'].get('concurrency', 20)
        self.dynamic_config = config['spider'].get('dynamic_concurrency', {})
        self.dynamic_enabled = self.dynamic_config.get('enabled', False)
        if self.dynamic_enabled:
            self.target_cpu = self.dynamic_config.get('target_cpu_percent', 30)
            self.min_threads = self.dynamic_config.get('min_threads', 5)
            self.max_threads = self.dynamic_config.get('max_threads', 100)
            self.check_interval = self.dynamic_config.get('check_interval', 5)
            self.last_check_time = 0

    def adjust_concurrency(self):
        """Adjusts the number of threads based on CPU usage."""
        if not self.dynamic_enabled:
            return

        current_time = time.time()
        if current_time - self.last_check_time < self.check_interval:
            return

        self.last_check_time = current_time
        cpu_percent = psutil.cpu_percent(interval=None) # Non-blocking check
        
        # Simple adjustment logic
        if cpu_percent < self.target_cpu - 5: # CPU is low, increase threads
            if self.concurrency < self.max_threads:
                self.concurrency = min(self.concurrency + 2, self.max_threads)
                logger.info(f"CPU usage {cpu_percent}% < Target {self.target_cpu}%. Increasing threads to {self.concurrency}")
        elif cpu_percent > self.target_cpu + 5: # CPU is high, decrease threads
            if self.concurrency > self.min_threads:
                self.concurrency = max(self.concurrency - 2, self.min_threads)
                logger.info(f"CPU usage {cpu_percent}% > Target {self.target_cpu}%. Decreasing threads to {self.concurrency}")

    def process_item_wrapper(self, item):
        """Wrapper for process_item to handle exceptions and logging."""
        try:
            self.process_item(item)
            return True
        except Exception as e:
            logger.error(f"Error processing item {item.get('title', 'Unknown')} (VOD ID: {item.get('vod_id')}): {e}", exc_info=True)
            return False

    def run(self):
        '''Main entry point to start the crawling process.'''
        self.db_manager.connect()
        self.db_manager.create_tables()

        # Check for incremental mode flag (set via main.py or config)
        if self.config.get('incremental_mode', False):
            self.run_incremental()
            return

        start_year = self.config['crawl']['year_start']
        end_year = self.config['crawl']['year_end']
        
        logger.info(f"Starting spider with concurrency: {self.concurrency}")
        if self.max_items:
            logger.info(f"Max items limit set to: {self.max_items}")

        # Crawl in reverse chronological order for fresher content first
        try:
            for year in range(end_year, start_year - 1, -1):
                if self.max_items and self.items_crawled >= self.max_items:
                    break
                for category_name, category_ids in self.config['crawl']['categories'].items():
                    if not self.should_crawl_category(category_name):
                        continue
                    
                    if self.max_items and self.items_crawled >= self.max_items:
                        break

                    for cid in category_ids:
                        if self.max_items and self.items_crawled >= self.max_items:
                            break
                        logger.info(f"--- Starting crawl for category '{category_name}' (ID: {cid}), Year: {year} ---")
                        self.crawl_category_by_year(cid, year)
        finally:
            self.db_manager.close()
            logger.info(f"Spider run finished. Total items crawled: {self.items_crawled}")

    def run_incremental(self):
        """
        Runs the spider in incremental mode.
        Crawls each category from page 1 (no year filter) until N consecutive pages contain only existing items.
        """
        logger.info(f"Starting INCREMENTAL update with concurrency: {self.concurrency}")
        
        try:
            for category_name, category_ids in self.config['crawl']['categories'].items():
                if not self.should_crawl_category(category_name):
                    continue
                
                for cid in category_ids:
                    logger.info(f"--- Starting INCREMENTAL crawl for category '{category_name}' (ID: {cid}) ---")
                    self.crawl_category_incremental(cid)
        finally:
            self.db_manager.close()
            logger.info(f"Incremental run finished. Total items crawled: {self.items_crawled}")

    def crawl_category_incremental(self, category_id):
        """Crawls a category incrementally until existing items are found consistently."""
        current_page = 1
        consecutive_existing_pages = 0
        stop_threshold = 3  # Stop after 3 pages where all items exist
        
        while True:
            # Construct URL without year
            url = build_list_url(self.config['spider']['base_url'], category_id, current_page, year=None)
            logger.info(f"Crawling incremental page {current_page} for category {category_id}: {url}")
            
            response = self.request_handler.get(url)
            if not response:
                logger.error(f"Failed to fetch page {url}. Skipping category.")
                break

            items, next_page_url = self.list_parser.parse(response.text, category_id, self.config['spider']['base_url'])
            if not items:
                logger.info("No items found on page. End of category.")
                break

            # Check how many items already exist
            existing_count = 0
            for item in items:
                if self.db_manager.exists(item['vod_id']):
                    existing_count += 1
            
            logger.info(f"Page {current_page}: {existing_count}/{len(items)} items already exist.")
            
            # If all items exist, increment counter
            if existing_count == len(items):
                consecutive_existing_pages += 1
                logger.info(f"All items on page {current_page} exist. Consecutive existing pages: {consecutive_existing_pages}")
            else:
                consecutive_existing_pages = 0 # Reset if we find even one new item
            
            # Stop condition
            if consecutive_existing_pages >= stop_threshold:
                logger.info(f"Reached stop threshold ({stop_threshold} pages of existing items). Stopping category {category_id}.")
                break

            # Process items concurrently (even if they exist, to check for updates like new episodes)
            self.adjust_concurrency()
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                futures = []
                for item in items:
                    if self.max_items and self.items_crawled >= self.max_items:
                        logger.info(f"Reached max items limit ({self.max_items}). Stopping.")
                        return # Stop everything

                    if item['content_type'] == self.spider_type:
                        futures.append(executor.submit(self.process_item_wrapper, item))
                        self.items_crawled += 1
                
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error in concurrent processing: {e}")

            if not next_page_url:
                break
            
            current_page += 1

    def crawl_category_by_year(self, category_id, year):
        '''Crawls all pages for a given category and year.'''
        task_key_prefix = f"{self.spider_type}_{category_id}_{year}"
        current_page = self._get_start_page(task_key_prefix)
        max_pages = self.config['crawl']['max_pages_per_year']

        while True:
            if max_pages is not None and current_page > max_pages:
                logger.info(f"Reached max pages ({max_pages}) for {year}. Moving to next task.")
                break

            task_key = f"{task_key_prefix}_{current_page}"
            self.db_manager.update_crawl_progress(task_key, category_id, year, current_page, 'running')

            url = build_list_url(self.config['spider']['base_url'], category_id, current_page, year)
            logger.info(f"Crawling page {current_page} for year {year}: {url}")
            
            response = self.request_handler.get(url)
            if not response:
                self.db_manager.update_crawl_progress(task_key, category_id, year, current_page, 'failed')
                break # Stop this category-year if a page fails

            items, next_page_url = self.list_parser.parse(response.text, category_id, self.config['spider']['base_url'])
            if not items:
                logger.info("No items found on page. Assuming end of category for this year.")
                self.db_manager.update_crawl_progress(task_key, category_id, year, current_page, 'completed')
                break

            # Process items concurrently
            # Note: ThreadPoolExecutor doesn't support dynamic resizing of max_workers easily in Python < 3.9
            # However, we can control how many tasks we submit or re-create the executor for each batch (page).
            # Re-creating per page is safer for dynamic adjustment.
            
            self.adjust_concurrency() # Check and adjust before processing a page
            
            with ThreadPoolExecutor(max_workers=self.concurrency) as executor:
                futures = []
                for item in items:
                    if self.max_items and self.items_crawled >= self.max_items:
                        logger.info(f"Reached max items limit ({self.max_items}). Stopping.")
                        break

                    # Filter items based on spider type (movie/tv)
                    if item['content_type'] == self.spider_type:
                        futures.append(executor.submit(self.process_item_wrapper, item))
                        self.items_crawled += 1
                
                # Wait for all tasks to complete
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        # Result is handled in wrapper
                    except Exception as e:
                        logger.error(f"Error in concurrent processing: {e}")

            self.db_manager.update_crawl_progress(task_key, category_id, year, current_page, 'completed')

            if self.max_items and self.items_crawled >= self.max_items:
                break

            if not next_page_url:
                logger.info(f"No 'next page' link found. Finished crawling year {year} for category {category_id}.")
                break

            current_page += 1

    def _get_start_page(self, task_key_prefix):
        '''Determines the starting page based on saved progress.'''
        # Extract category_id and year from task_key_prefix (e.g., "movie_6_2026")
        try:
            parts = task_key_prefix.split('_')
            category_id = int(parts[1])
            year = int(parts[2])
            
            last_completed_page = self.db_manager.get_max_completed_page(category_id, year)
            if last_completed_page > 0:
                start_page = last_completed_page + 1
                logger.info(f"Resuming crawl for Category {category_id}, Year {year} from page {start_page}")
                return start_page
        except (IndexError, ValueError) as e:
            logger.warning(f"Failed to parse task key prefix '{task_key_prefix}' for resumption: {e}")
        
        return 1

    @property
    @abstractmethod
    def spider_type(self):
        '''Should return 'movie' or 'tv'.'''
        pass

    @abstractmethod
    def should_crawl_category(self, category_name):
        '''Determines if this spider should handle a given category name.'''
        pass

    @abstractmethod
    def process_item(self, item):
        '''Abstract method to process a single item (movie or TV series).'''
        pass
