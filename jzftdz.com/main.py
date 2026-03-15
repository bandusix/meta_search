#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py

Main entry point for the jzftdz.com scraper application.
"""

import sys
import argparse
import yaml
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import setup_logger
from spiders.movie_spider import MovieSpider
from spiders.tv_spider import TVSpider
from core.database import DatabaseManager
from exporters.excel_exporter import ExcelExporter

def load_config(config_path='config/settings.yaml'):
    """Loads the YAML configuration file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    """Main function to run the scraper."""
    parser = argparse.ArgumentParser(description='jzftdz.com Scraper')
    parser.add_argument(
        '--type',
        choices=['movie', 'tv', 'all'],
        default='all',
        help='Type of content to scrape: movie, tv, or all (default: all)'
    )
    parser.add_argument(
        '--config',
        default='config/settings.yaml',
        help='Path to the configuration file (default: config/settings.yaml)'
    )
    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Run in incremental update mode (crawl latest items only)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set incremental mode in config
    if args.incremental:
        config['incremental_mode'] = True
        print("Running in INCREMENTAL UPDATE mode.")
    
    # Setup logger
    setup_logger(config)
    
    # Run the appropriate spider(s)
    if args.type in ['movie', 'all']:
        print("Starting Movie Spider...")
        movie_spider = MovieSpider(config)
        movie_spider.run()
    
    if args.type in ['tv', 'all']:
        print("Starting TV Spider...")
        tv_spider = TVSpider(config)
        tv_spider.run()
    
    print("Scraping completed successfully!")

    # --- Export Data ---
    print("Starting data export...")
    try:
        db_manager = DatabaseManager(config['database']['path'])
        db_manager.connect()
        exporter = ExcelExporter(db_manager, config['export']['output_dir'])

        # 1. Incremental Export
        print("Exporting incremental data...")
        inc_file = exporter.export(export_type='incremental')
        if inc_file:
            print(f"Incremental export saved to: {inc_file}")
        else:
            print("No incremental data to export.")

        # 2. Full (Stock) Export
        print("Exporting full stock data...")
        full_file = exporter.export(export_type='full')
        if full_file:
            print(f"Full export saved to: {full_file}")
        else:
            print("No data found for full export.")

        db_manager.close()
        print("Data export completed.")

    except Exception as e:
        print(f"Error during export: {e}")

if __name__ == '__main__':
    main()
