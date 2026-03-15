import sys
import time
import logging
import concurrent.futures
from database import init_db
from spider import VS1919Spider
from exporter import export_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_spider_for_category(category_id, max_workers):
    """Entry point for a single process to crawl one category."""
    spider = None
    try:
        spider = VS1919Spider(max_workers=max_workers)
        spider.crawl_category(category_id)
    except Exception as e:
        logger.error(f"Process for category {category_id} failed: {e}")
    finally:
        if spider:
            spider.close()

def main():
    # 1. Initialize Database
    # We will keep the existing DB and append to it (init_db checks existence)
    init_db()
    
    # 2. Configuration - Forced Pagination Crawl
    # User requested to try fixing the issue with forced pagination.
    # Keep threads reasonable (5 per category) to be gentle but effective.
    threads_per_category = 5
    
    categories = [
        VS1919Spider.CAT_MOVIE,
        VS1919Spider.CAT_TV,
        VS1919Spider.CAT_VARIETY,
        VS1919Spider.CAT_ANIME,
        VS1919Spider.CAT_DRAMA
    ]
    
    logger.info(f"Starting FORCED PAGINATION CRAWL with {len(categories)} processes, {threads_per_category} threads each.")
    logger.info("This mode ignores 'Next Page' buttons and tries to increment page numbers until 3 consecutive empty pages.")
    logger.info("Press Ctrl+C to stop.")
    
    # 3. Parallel Execution using ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor(max_workers=len(categories)) as executor:
        futures = []
        for cat_id in categories:
            future = executor.submit(run_spider_for_category, cat_id, threads_per_category)
            futures.append(future)
            
        # Wait for all processes to complete
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"A category process crashed: {e}")

    logger.info("All categories finished.")
    
    # 4. Export Final Data
    logger.info("Exporting full data to CSV...")
    export_csv()

if __name__ == "__main__":
    main()
