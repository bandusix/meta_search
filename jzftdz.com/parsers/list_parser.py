# -*- coding: utf-8 -*-
"""
parsers/list_parser.py

Parses the HTML of a list page to extract movie/series cards and pagination info.
"""

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Define content type IDs for robust classification
MOVIE_CIDS = {1, 6, 7, 8, 9, 10, 11, 12, 24, 44, 45}
TV_CIDS = {2, 13, 14, 15, 16, 20, 21, 22, 23}

class ListPageParser:
    """Parses the list page HTML content."""

    @staticmethod
    def parse(html_content, category_id, base_url):
        """
        Extracts all item cards and the URL for the next page.

        Args:
            html_content (str): The HTML content of the list page.
            category_id (int): The category ID of the current page.
            base_url (str): The base URL of the website.

        Returns:
            tuple: A tuple containing:
                - list: A list of dictionaries, where each dict represents an item.
                - str or None: The URL of the next page, or None if it's the last page.
        """
        from urllib.parse import urljoin
        soup = BeautifulSoup(html_content, 'lxml')
        cards = []

        # Corrected selector based on verification
        item_elements = soup.select('ul.row > li.col-xs-4')

        for item in item_elements:
            try:
                link_tag = item.select_one('a[href*="voddetail"]')
                if not link_tag:
                    continue

                detail_url_raw = link_tag.get('href')
                detail_url = urljoin(base_url, detail_url_raw)
                title = link_tag.get('title', '').strip()

                img_wrapper = item.select_one('.img-wrapper')
                poster_url = img_wrapper.get('data-original') if img_wrapper else ''
                if poster_url:
                    poster_url = urljoin(base_url, poster_url)

                status_tag = item.select_one('.item-status')
                status_text = status_tag.text.strip() if status_tag else ''

                # Robustly determine content type
                content_type = 'movie' # Default assumption
                if category_id in TV_CIDS:
                    content_type = 'tv'
                elif category_id in MOVIE_CIDS:
                    # Correction logic: if it's in a movie category but looks like a series
                    if any(kw in status_text for kw in ['集', '更新', '完结']):
                        content_type = 'tv'
                        logger.info(f"Corrected content type to 'tv' for '{title}' based on status: '{status_text}'")

                cards.append({
                    'vod_id': ListPageParser._extract_vod_id(detail_url_raw),
                    'title': title,
                    'detail_url': detail_url,
                    'poster_url': poster_url,
                    'status_text': status_text,
                    'content_type': content_type
                })

            except Exception as e:
                logger.error(f"Failed to parse an item card: {e}", exc_info=True)

        # Corrected selector for the 'next page' link
        next_page_tag = soup.select_one('ul.ewave-page a:-soup-contains("下一页")')
        next_page_url = urljoin(base_url, next_page_tag.get('href')) if next_page_tag else None

        logger.info(f"Parsed {len(cards)} items from the list page.")
        return cards, next_page_url

    @staticmethod
    def _extract_vod_id(url):
        """Extracts the video ID from a URL."""
        if not url:
            return None
        try:
            # e.g., /voddetail/95508.html -> 95508
            return int(url.split('/')[-1].split('.')[0])
        except (ValueError, IndexError):
            logger.warning(f"Could not extract vod_id from URL: {url}")
            return None
