import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_pagination():
    url = "https://www.1919ys.com/vsbstp/1-1.html"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    logger.info(f"Fetching {url}...")
    try:
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        soup = BeautifulSoup(response.text, 'lxml')
        
        # 1. Check for pagination container
        pagination = soup.select_one('.stui-page')
        if pagination:
            logger.info("Found pagination container (.stui-page):")
            # Print all links in pagination
            links = pagination.select('li a')
            for link in links:
                logger.info(f"  Link text: '{link.text.strip()}', href: '{link.get('href')}', title: '{link.get('title')}'")
        else:
            logger.warning("Pagination container (.stui-page) NOT found.")
            
        # 2. Check for "Next Page" specifically
        next_page = soup.select_one('.stui-page__item a[title="下一页"]')
        if next_page:
            logger.info(f"Found 'Next Page' button: {next_page}")
        else:
            logger.warning("'Next Page' button NOT found using selector: .stui-page__item a[title='下一页']")
            
        # 3. Check items count
        items = soup.select('.stui-vodlist__box')
        logger.info(f"Found {len(items)} items on page.")
        
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    # Suppress SSL warnings
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    debug_pagination()
