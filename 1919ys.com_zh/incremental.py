import sys
import time
import logging
import concurrent.futures
from database import init_db
from spider import VS1919Spider
from exporter import export_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_spider_incremental(category_id, max_workers):
    """Run spider in incremental mode."""
    spider = None
    try:
        spider = VS1919Spider(max_workers=max_workers)
        # Incremental mode: stop after encountering 3 consecutive pages with NO new items
        spider.crawl_category(category_id, incremental=True)
    except Exception as e:
        logger.error(f"Incremental process for category {category_id} failed: {e}")
    finally:
        if spider:
            spider.close()

def main():
    # 1. Ensure DB exists
    init_db()
    
    # 2. Configuration for Incremental Update
    # Can use fewer threads for daily updates as volume is smaller
    threads_per_category = 20 
    
    categories = [
        VS1919Spider.CAT_MOVIE,
        VS1919Spider.CAT_TV,
        VS1919Spider.CAT_VARIETY,
        VS1919Spider.CAT_ANIME,
        VS1919Spider.CAT_DRAMA
    ]
    
    logger.info("Starting DAILY INCREMENTAL UPDATE...")
    
    with concurrent.futures.ProcessPoolExecutor(max_workers=len(categories)) as executor:
        futures = []
        for cat_id in categories:
            future = executor.submit(run_spider_incremental, cat_id, threads_per_category)
            futures.append(future)
            
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"An incremental process crashed: {e}")

    logger.info("Incremental update finished.")
    
    # Optional: Export only new data? Or full data?
    # Usually for production DB sync, you might want to export everything or handle DB sync differently.
    # For now, let's just log completion. The DB is updated.
    
if __name__ == "__main__":
    main()
