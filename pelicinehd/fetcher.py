import requests
import time
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from .config import USER_AGENTS, DELAY_RANGE, MAX_RETRIES, TIMEOUT, BASE_URL, PROXIES

class Fetcher:
    def __init__(self):
        self.session = requests.Session()
        self._setup_retries()
        self._update_headers()

    def _get_random_proxy(self):
        if not PROXIES:
            return None
        proxy = random.choice(PROXIES)
        return {
            "http": proxy,
            "https": proxy
        }

    def _setup_retries(self):
        retry_strategy = Retry(
            total=MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _update_headers(self):
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': BASE_URL,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8'
        })

    def get(self, url, params=None):
        self._delay()
        self._update_headers()
        proxies = self._get_random_proxy()
        try:
            response = self.session.get(url, params=params, timeout=TIMEOUT, proxies=proxies)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except requests.RequestException as e:
            logging.error(f"Request failed for {url}: {e}")
            return None

    def post(self, url, data=None, json=None):
        self._delay()
        self._update_headers()
        proxies = self._get_random_proxy()
        try:
            response = self.session.post(url, data=data, json=json, timeout=TIMEOUT, proxies=proxies)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response
        except requests.RequestException as e:
            logging.error(f"POST request failed for {url}: {e}")
            return None

    def _delay(self):
        time.sleep(random.uniform(*DELAY_RANGE))
