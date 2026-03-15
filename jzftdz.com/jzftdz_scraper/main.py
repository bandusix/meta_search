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
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
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

if __name__ == '__main__':
    main()
