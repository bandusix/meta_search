import sys
import logging
from xz8_spider import XZ8Spider, DataExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("spider.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_round_1():
    """
    Round 1: Basic functionality test.
    Crawl a small amount of data (e.g., Movie, 2026, max 10 items) to verify the pipeline.
    """
    print("=== Starting Round 1: Basic Functionality Test ===")
    
    # Initialize spider with fewer workers for debugging
    spider = XZ8Spider(db_path='xz8_media_test.db', max_workers=2, delay=(1, 2))
    
    # Crawl movies from 2026, limit to 10 items
    print("Crawling Movies 2026 (Max 10 items)...")
    spider.crawl_by_year('movie', start_year=2026, end_year=2025, max_items=10)
    
    # Check stats
    print(f"Round 1 Stats: {spider.stats}")
    
    # Export data to check content
    exporter = DataExporter(db_path='xz8_media_test.db', output_dir='output_round_1')
    exporter.export_full(format='xlsx')
    
    print("=== Round 1 Completed ===")

def run_round_2():
    """
    Round 2: Improved crawling logic.
    Use crawl_category to test list parsing and detail parsing on real data.
    Limit to 1 page (approx 72 items).
    """
    print("=== Starting Round 2: Category Crawling Test ===")
    
    # Initialize spider
    spider = XZ8Spider(db_path='xz8_media_round2.db', max_workers=5, delay=(0.5, 1.0))
    
    # Crawl 'movie' category, max 1 page
    print("Crawling Category 'movie' (Max 1 page)...")
    spider.crawl_category('movie', max_pages=1)
    
    # Check stats
    print(f"Round 2 Stats: {spider.stats}")
    
    # Export data
    exporter = DataExporter(db_path='xz8_media_round2.db', output_dir='output_round_2')
    filepath = exporter.export_full(format='xlsx')
    
    print(f"=== Round 2 Completed. Exported to {filepath} ===")

def run_round_3():
    """
    Round 3: Final Optimization.
    Crawl all categories (Movie, TV, Variety, Anime), limit to 1 page each.
    This will produce a comprehensive dataset for review.
    """
    print("=== Starting Round 3: Full Site Crawl (Sample) ===")
    
    # Initialize spider
    spider = XZ8Spider(db_path='xz8_media_final.db', max_workers=10, delay=(0.5, 1.0))
    
    # Crawl all categories, max 1 page each
    print("Crawling all categories (Max 1 page per category)...")
    spider.crawl_all(max_pages_per_cat=1)
    
    # Check stats
    print(f"Round 3 Stats: {spider.stats}")
    
    # Export data
    exporter = DataExporter(db_path='xz8_media_final.db', output_dir='output_final')
    filepath = exporter.export_full(format='xlsx')
    
    print(f"=== Round 3 Completed. Exported to {filepath} ===")

def run_round_4():
    """
    Round 4: Quality & Status Logic Verification.
    Crawl 'tv' category (Max 1 page) to verify the fix for quality/status fields.
    """
    print("=== Starting Round 4: Quality/Status Verification ===")
    
    # Initialize spider with a NEW database to ensure clean data
    spider = XZ8Spider(db_path='xz8_media_round4_v2.db', max_workers=5, delay=(0.5, 1.0))
    
    # Crawl 'tv' category, max 1 page (TV usually has the issue mentioned by user)
    print("Crawling Category 'tv' (Max 1 page)...")
    spider.crawl_category('tv', max_pages=1)

    # Crawl 'movie' category, max 1 page (To verify quality extraction)
    print("Crawling Category 'movie' (Max 1 page)...")
    spider.crawl_category('movie', max_pages=1)
    
    # Check stats
    print(f"Round 4 Stats: {spider.stats}")
    
    # Export data
    exporter = DataExporter(db_path='xz8_media_round4_v2.db', output_dir='output_round_4')
    filepath = exporter.export_full(format='xlsx')
    
    print(f"=== Round 4 Completed. Exported to {filepath} ===")
    
    # Verify data content
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect('xz8_media_round4_v2.db')
    df = pd.read_sql_query("SELECT title, category, status, quality FROM media_resources WHERE quality != '' LIMIT 10", conn)
    print("\nSample Data with Quality:")
    print(df)

    df_empty = pd.read_sql_query("SELECT title, category, status, quality FROM media_resources WHERE quality == '' LIMIT 10", conn)
    print("\nSample Data with Empty Quality:")
    print(df_empty)
    conn.close()

def run_round_5():
    """
    Round 5: Pilot Crawl (100 items per category).
    - Verifies checkpoint system (resumable crawl).
    - Verifies deduplication (skips existing detail pages).
    - Crawls approx 100 items (2 pages) per category.
    """
    print("=== Starting Round 5: Pilot Crawl (100 items per category) ===")
    
    # Initialize spider with persistent state file
    # We use a new DB for this pilot to simulate a fresh start
    spider = XZ8Spider(db_path='xz8_media_pilot.db', state_file='spider_pilot_state.json', max_workers=10, delay=(0.5, 1.0))
    
    # Crawl all categories, limit to 100 items (approx 2 pages) per category
    # max_pages_per_cat=2 should give us roughly 144 items if per page is 72
    print("Crawling all categories (Max 100 items per category)...")
    spider.crawl_all(max_pages_per_cat=None, max_items_per_cat=100)
    
    # Check stats
    print(f"Round 5 Stats: {spider.stats}")
    
    # Export data
    exporter = DataExporter(db_path='xz8_media_pilot.db', output_dir='output_pilot')
    filepath = exporter.export_full(format='xlsx')
    
    print(f"=== Round 5 Completed. Exported to {filepath} ===")

def run_full_crawl(limit_pages=None):
    """
    Full Crawl Mode.
    - Uses persistent state 'spider_full_state.json'.
    - Uses 'xz8_media_full.db'.
    - Crawls ALL pages if limit_pages is None.
    """
    print(f"=== Starting Full Crawl (Limit: {limit_pages if limit_pages else 'Unlimited'} pages/cat) ===")
    
    # Initialize spider
    # Speed up: max_workers=20, reduced delay
    spider = XZ8Spider(db_path='xz8_media_full.db', state_file='spider_full_state.json', max_workers=20, delay=(0.1, 0.4))
    
    # Crawl all categories
    spider.crawl_all(max_pages_per_cat=limit_pages)
    
    # Check stats
    print(f"Full Crawl Stats: {spider.stats}")
    
    # Export data
    exporter = DataExporter(db_path='xz8_media_full.db', output_dir='output_full')
    filepath = exporter.export_full(format='xlsx')
    
    print(f"=== Full Crawl Batch Completed. Exported to {filepath} ===")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == 'round1':
            run_round_1()
        elif sys.argv[1] == 'round2':
            run_round_2()
        elif sys.argv[1] == 'round3':
            run_round_3()
        elif sys.argv[1] == 'round4':
            run_round_4()
        elif sys.argv[1] == 'round5':
            run_round_5()
        elif sys.argv[1] == 'full':
            # Default to 5 pages per category for stability check in this environment
            # User can change this to None for true full crawl
            limit = 5 
            if len(sys.argv) > 2:
                try:
                    limit = int(sys.argv[2])
                    if limit == 0: limit = None # 0 means unlimited
                except:
                    pass
            run_full_crawl(limit_pages=limit)
    else:
        # Default run: 200 pages per batch for faster full crawl
        run_full_crawl(limit_pages=200)
