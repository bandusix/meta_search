"""
spiders/tv_spider.py

Spider implementation for crawling TV series.
"""

import logging
from core.base_spider import BaseSpider

logger = logging.getLogger(__name__)

class TVSpider(BaseSpider):
    """Spider to crawl TV series data."""

    @property
    def spider_type(self):
        return 'tv'

    def should_crawl_category(self, category_name):
        """This spider handles categories related to TV series."""
        return category_name in ['tv', 'variety', 'anime', 'short_drama']

    def process_item(self, item):
        """Processes a single TV series item found on a list page."""
        logger.debug(f"Processing TV series item: {item['title']} (VOD ID: {item['vod_id']})")

        try:
            # 1. Fetch and parse the detail page
            detail_response = self.request_handler.get(item['detail_url'])
            if not detail_response:
                logger.error(f"Skipping item {item['vod_id']} due to detail page fetch failure.")
                return

            detail_data = self.detail_parser.parse(detail_response.text)

            # Combine initial data with detail data
            full_data = {**item, **detail_data}

            # 2. Fetch rating and metadata from the play page (if enabled)
            if self.config['crawl']['fetch_rating'] and detail_data.get('sources'):
                # Get the first play URL to fetch metadata
                first_play_url = detail_data['sources'][0]['episodes'][0]['url']
                play_page_response = self.request_handler.get(first_play_url)
                if play_page_response:
                    play_page_data = self.play_parser.parse(play_page_response.text)
                    full_data.update(play_page_data)
                else:
                    logger.warning(f"Could not fetch play page for {item['vod_id']} to get rating.")

            # 3. Save the combined data to the database
            self.db_manager.upsert_tv_series(full_data)
            logger.info(f"Successfully processed and saved TV series: {full_data['title']}")

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing TV series {item['vod_id']}: {e}", exc_info=True)
