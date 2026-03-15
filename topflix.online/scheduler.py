import schedule
import time
import subprocess
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)

def run_daily_crawl():
    logging.info("Starting daily incremental crawl...")
    try:
        # Run crawler with a limit (e.g., 500 items for daily check)
        # Assuming 500 items cover the new content on the first few pages
        # You can adjust the limit or modify spider_main.py to stop when hitting old dates
        result = subprocess.run(["python", "spider_main.py", "500", "10"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Daily crawl completed successfully.")
            logging.info(result.stdout)
        else:
            logging.error(f"Daily crawl failed with code {result.returncode}")
            logging.error(result.stderr)
            
    except Exception as e:
        logging.error(f"Error executing daily crawl: {e}")

def main():
    logging.info("Scheduler started. Waiting for scheduled time (02:00 AM)...")
    
    # Schedule the job every day at 02:00 AM
    schedule.every().day.at("02:00").do(run_daily_crawl)
    
    # Also run once immediately for verification (optional, remove in prod)
    # run_daily_crawl() 
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
