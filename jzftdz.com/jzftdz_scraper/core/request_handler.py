# -*- coding: utf-8 -*-
"""
core/request_handler.py

Manages HTTP requests with retries, random delays, and rotating user agents.
"""

import time
import random
import logging
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class RequestHandler:
    """Handles the sending of HTTP GET requests."""

    def __init__(self, base_url, delay_range, max_retries, timeout, user_agents):
        """
        Initializes the RequestHandler.

        Args:
            base_url (str): The base URL for relative links.
            delay_range (list): A list with two integers for min and max delay.
            max_retries (int): Maximum number of retries for a request.
            timeout (int): Request timeout in seconds.
            user_agents (list): A list of User-Agent strings to rotate.
        """
        self.base_url = base_url
        self.delay_range = tuple(delay_range)
        self.max_retries = max_retries
        self.timeout = timeout
        self.user_agents = user_agents
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
        })

    def _get_random_user_agent(self):
        """Returns a random User-Agent from the list."""
        return random.choice(self.user_agents)

    def get(self, url):
        """
        Performs a GET request with built-in error handling.

        Args:
            url (str): The URL to fetch.

        Returns:
            requests.Response or None: The response object on success, None on failure.
        """
        full_url = url if url.startswith('http') else urljoin(self.base_url, url)
        self.session.headers['User-Agent'] = self._get_random_user_agent()

        for attempt in range(self.max_retries):
            try:
                # Add a random delay before each request
                time.sleep(random.uniform(*self.delay_range))

                response = self.session.get(full_url, timeout=self.timeout)
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
                response.encoding = 'utf-8' # Set encoding to UTF-8
                logger.debug(f"Successfully fetched {full_url}")
                return response

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Page not found (404): {full_url}")
                    break  # Don't retry on 404
                logger.warning(f"HTTP Error {e.response.status_code} for {full_url} (Attempt {attempt + 1})")

            except requests.exceptions.Timeout:
                logger.warning(f"Request timed out for {full_url} (Attempt {attempt + 1})")

            except requests.exceptions.RequestException as e:
                logger.error(f"An unexpected request error occurred for {full_url}: {e}")

            # Wait before retrying
            if attempt < self.max_retries - 1:
                retry_delay = random.uniform(3, 6)
                logger.info(f"Waiting {retry_delay:.2f} seconds before retrying...")
                time.sleep(retry_delay)

        logger.error(f"Failed to fetch {full_url} after {self.max_retries} attempts.")
        return None
