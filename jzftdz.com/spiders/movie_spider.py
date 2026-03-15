"""
spiders/movie_spider.py

Spider implementation for crawling movies.
"""

import logging
from core.base_spider import BaseSpider

logger = logging.getLogger(__name__)

class MovieSpider(BaseSpider):
    """Spider to crawl movie data."""

    @property
    def spider_type(self):
        return 'movie'

    def should_crawl_category(self, category_name):
        """This spider handles categories related to movies."""
        return category_name in ['movie']

    def process_item(self, item):
        """Processes a single movie item found on a list page."""
        logger.debug(f"Processing movie item: {item['title']} (VOD ID: {item['vod_id']})")

        try:
            # 1. Fetch and parse the detail page
            detail_response = self.request_handler.get(item['detail_url'])
            if not detail_response:
                logger.error(f"Skipping item {item['vod_id']} due to detail page fetch failure.")
                return

            detail_data = self.detail_parser.parse(detail_response.text, self.config['spider']['base_url'])

            # Combine initial data with detail data
            full_data = {**item, **detail_data}

            # 2. Fetch rating and metadata from the play page (if enabled)
            if self.config['crawl']['fetch_rating'] and detail_data.get('sources'):
                sources = detail_data['sources']
                if sources and sources[0].get('episodes'):
                    # Get the first play URL to fetch metadata
                    first_play_url = sources[0]['episodes'][0]['url']
                    play_page_response = self.request_handler.get(first_play_url)
                    if play_page_response:
                        play_page_data = self.play_parser.parse(play_page_response.text)
                        full_data.update(play_page_data)
                    else:
                        logger.warning(f"Could not fetch play page for {item['vod_id']} to get rating.")
                else:
                    logger.warning(f"No episodes found for {item['vod_id']}, skipping rating fetch.")

            # 3. Save the combined data to the database
            self.db_manager.upsert_movie(full_data)
            logger.info(f"Successfully processed and saved movie: {full_data['title']}")

        except Exception as e:
            logger.error(f"An unexpected error occurred while processing movie {item['vod_id']}: {e}", exc_info=True)
