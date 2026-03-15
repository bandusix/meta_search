# -*- coding: utf-8 -*-
'''
parsers/play_parser.py

Parses the HTML of a play page to extract rating and other metadata.
'''

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class PlayPageParser:
    '''Parses the play page HTML content.'''

    @staticmethod
    def parse(html_content):
        '''
        Extracts rating and metadata from the play page.

        Args:
            html_content (str): The HTML content of the play page.

        Returns:
            dict: A dictionary containing the extracted data.
        '''
        soup = BeautifulSoup(html_content, 'lxml')
        data = {}

        try:
            # --- Metadata Extraction (Category, Region, Year) ---
            # Corrected selector: p.text.text-overflow
            meta_p = soup.select_one('p.text.text-overflow')
            if meta_p:
                parts = [p.strip() for p in meta_p.text.split('/')]
                if len(parts) >= 3:
                    data['category'] = parts[0]
                    data['region'] = parts[1]
                    try:
                        data['year'] = int(parts[2])
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse year from metadata: {parts}")
                        data['year'] = None

            # --- Rating Extraction (Corrected Selectors) ---
            # Corrected selector: h4.ewave-star-text
            rating_text_el = soup.select_one('h4.ewave-star-text')
            if rating_text_el:
                data['rating_text'] = rating_text_el.text.strip()

            # Corrected selector: h4.ewave-star-num
            rating_num_el = soup.select_one('h4.ewave-star-num')
            if rating_num_el:
                try:
                    data['rating'] = float(rating_num_el.text.strip())
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse rating number: {rating_num_el.text.strip()}")
                    data['rating'] = 0.0
            
        except Exception as e:
            logger.error(f"Failed to parse play page: {e}", exc_info=True)

        return data
