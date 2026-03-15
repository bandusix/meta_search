_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE_CODE__", text="# -*- coding: utf-8 -*-
"'''
core/base_spider.py

Provides the abstract base class for all spiders, defining the main crawl loop
and orchestration logic.
"'''

import logging
from abc import ABC, abstractmethod

from core.request_handler import RequestHandler
from core.database import DatabaseManager
from parsers.list_parser import ListPageParser
from parsers.detail_parser import DetailPageParser
from parsers.play_parser import PlayPageParser
from utils.url_builder import build_list_url

logger = logging.getLogger(__name__)

class BaseSpider(ABC):
    "'''Abstract base class for spiders."'''

    def __init__(self, config):
        "'''Initializes the spider with configuration."'''
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

    def run(self):
        "'''Main entry point to start the crawling process."'''
        self.db_manager.connect()
        self.db_manager.create_tables()

        start_year = self.config['crawl']['year_start']
        end_year = self.config['crawl']['year_end']

        # Crawl in reverse chronological order for fresher content first
        for year in range(end_year, start_year - 1, -1):
            for category_name, category_ids in self.config['crawl']['categories'].items():
                if not self.should_crawl_category(category_name):
                    continue
                
                for cid in category_ids:
                    logger.info(f"--- Starting crawl for category '{category_name}' (ID: {cid}), Year: {year} ---")
                    self.crawl_category_by_year(cid, year)
        
        self.db_manager.close()
        logger.info("Spider run finished.")

    def crawl_category_by_year(self, category_id, year):
        "'''Crawls all pages for a given category and year."'''
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

            items, next_page_url = self.list_parser.parse(response.text, category_id)
            if not items:
                logger.info("No items found on page. Assuming end of category for this year.")
                self.db_manager.update_crawl_progress(task_key, category_id, year, current_page, 'completed')
                break

            for item in items:
                # Filter items based on spider type (movie/tv)
                if item['content_type'] == self.spider_type:
                    self.process_item(item)

            self.db_manager.update_crawl_progress(task_key, category_id, year, current_page, 'completed')

            if not next_page_url:
                logger.info(f"No 'next page' link found. Finished crawling year {year} for category {category_id}.")
                break

            current_page += 1

    def _get_start_page(self, task_key_prefix):
        "'''Determines the starting page based on saved progress."'''
        # A simple implementation: check the last completed page for this prefix
        # A more robust solution would query the DB for the max page number with 'completed' status.
        # For now, we start from 1, assuming we want to re-check for updates.
        # To implement true resume, this logic needs to be more sophisticated.
        return 1

    @property
    @abstractmethod
    def spider_type(self):
        "'''Should return 'movie' or 'tv'."'''
        pass

    @abstractmethod
    def should_crawl_category(self, category_name):
        "'''Determines if this spider should handle a given category name."'''
        pass

    @abstractmethod
    def process_item(self, item):
        "'''Abstract method to process a single item (movie or TV series)."'''
        pass
