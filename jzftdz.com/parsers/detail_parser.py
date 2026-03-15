# -*- coding: utf-8 -*-
'''
parsers/detail_parser.py

Parses the HTML of a detail page to extract metadata, synopsis, and playlist info.
'''

import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DetailPageParser:
    '''Parses the detail page HTML content.'''

    @staticmethod
    def parse(html_content, base_url):
        '''
        Extracts all details from the page.

        Args:
            html_content (str): The HTML content of the detail page.
            base_url (str): The base URL of the website.

        Returns:
            dict: A dictionary containing all extracted details.
        '''
        from urllib.parse import urljoin
        soup = BeautifulSoup(html_content, 'lxml')
        details = {}

        try:
            # --- Basic Info Extraction ---
            info_section = soup.select_one('.info')
            if info_section:
                details['director'] = DetailPageParser._get_info_text(info_section, "导演")
                details['actors'] = DetailPageParser._get_info_text(info_section, "主演", join=True)

            # --- Synopsis Extraction ---
            synopsis_el = soup.select_one('.more-box p.pt-10.pb-10')
            if not synopsis_el:
                synopsis_el = soup.select_one('.more-box p')
            details['synopsis'] = synopsis_el.text.strip() if synopsis_el else ''

            # --- Poster URL Extraction ---
            poster_el = soup.select_one('.pic img')
            if poster_el:
                poster_url = poster_el.get('data-original') or poster_el.get('src')
                details['poster_url'] = urljoin(base_url, poster_url) if poster_url else ''

            # --- Playlist Extraction (Corrected Structure) ---
            sources = []
            source_tabs = soup.select('.playlist-tab li.ewave-tab')
            playlist_contents = soup.select('.ewave-playlist-content')

            for i, tab in enumerate(source_tabs):
                source_name = tab.text.strip()
                episodes = []
                # Ensure we don't go out of bounds
                if i < len(playlist_contents):
                    for link in playlist_contents[i].select('a'):
                        ep_url = link.get('href')
                        episodes.append({
                            'title': link.text.strip(),
                            'url': urljoin(base_url, ep_url) if ep_url else ''
                        })
                sources.append({'source_name': source_name, 'episodes': episodes})
            
            details['sources'] = sources
            # Use max() to find the source with the most episodes instead of summing all
            details['total_episodes'] = max((len(s.get('episodes', [])) for s in sources), default=0)

        except Exception as e:
            logger.error(f"Failed to parse detail page: {e}", exc_info=True)

        return details

    @staticmethod
    def _get_info_text(soup, label, join=False):
        '''Helper to extract text from the info section.'''
        try:
            span = soup.find('span', string=lambda t: t and label in t)
            if not span:
                return ''
            
            links = span.find_all_next('a', limit=10) # Limit to avoid grabbing unrelated links
            if join:
                return ', '.join(a.text.strip() for a in links if a.get('href','').startswith('/vodsearch'))
            else:
                link = span.find_next('a')
                return link.text.strip() if link else ''
        except Exception as e:
            logger.warning(f"Could not extract info for label '{label}': {e}")
            return ''
