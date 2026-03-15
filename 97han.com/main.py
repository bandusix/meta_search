#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主程序入口"""

import argparse
import sys
import os
from pathlib import Path

# Ensure the current directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from spiders.movie_spider import MovieSpider
from spiders.tv_spider import TVSpider
from exporters.csv_exporter import CSVExporter
from exporters.excel_exporter import ExcelExporter


def main():
    parser = argparse.ArgumentParser(description='97韩剧爬虫')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 电影爬虫
    movie_parser = subparsers.add_parser('movie', help='爬取电影')
    movie_parser.add_argument('--start-year', type=int, default=1945, help='开始年份')
    movie_parser.add_argument('--end-year', type=int, default=2026, help='结束年份')
    movie_parser.add_argument('--start-page', type=int, default=1, help='起始页码')
    movie_parser.add_argument('--max-pages', type=int, help='最大页数')
    movie_parser.add_argument('--threads', type=int, default=1, help='线程数')
    movie_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 电视剧爬虫
    tv_parser = subparsers.add_parser('tv', help='爬取电视剧')
    tv_parser.add_argument('--cid', type=int, default=2, help='分类ID (2=电视剧, 3=综艺, 4=动漫, 30=短剧, 36=伦理MV)')
    tv_parser.add_argument('--category-name', type=str, default='电视剧', help='分类名称')
    tv_parser.add_argument('--start-year', type=int, default=1945, help='开始年份')
    tv_parser.add_argument('--end-year', type=int, default=2026, help='结束年份')
    tv_parser.add_argument('--start-page', type=int, default=1, help='起始页码')
    tv_parser.add_argument('--max-pages', type=int, help='最大页数')
    tv_parser.add_argument('--max-episodes', type=int, help='每部剧最大集数')
    tv_parser.add_argument('--threads', type=int, default=1, help='线程数')
    tv_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 导出
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('--type', choices=['movies', 'tv', 'tv_episodes', 'all'], 
                               default='all', help='导出类型')
    export_parser.add_argument('--export-type', choices=['full', 'incremental'],
                               default='full', help='导出方式')
    export_parser.add_argument('--format', choices=['csv', 'excel'],
                               default='csv', help='导出格式 (csv/excel)')
    export_parser.add_argument('--output', type=str, default='./exports', help='输出目录')
    export_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    args = parser.parse_args()
    
    if args.command == 'movie':
        spider = MovieSpider(db_path=args.db)
        spider.crawl(
            year_start=args.start_year,
            year_end=args.end_year,
            max_pages=args.max_pages,
            start_page=args.start_page,
            max_workers=args.threads
        )
    
    elif args.command == 'tv':
        spider = TVSpider(db_path=args.db)
        spider.crawl(
            year_start=args.start_year,
            year_end=args.end_year,
            max_pages=args.max_pages,
            max_episodes=args.max_episodes,
            start_page=args.start_page,
            max_workers=args.threads,
            cid=args.cid,
            category_name=args.category_name
        )
    
    elif args.command == 'export':
        if args.format == 'excel':
            exporter = ExcelExporter(db_path=args.db, output_dir=args.output)
        else:
            exporter = CSVExporter(db_path=args.db, output_dir=args.output)
        
        if args.type in ['movies', 'all']:
            exporter.export_movies(args.export_type)
        
        if args.type in ['tv', 'all']:
            exporter.export_tv_series(args.export_type)
        
        if args.type in ['tv_episodes', 'all']:
            exporter.export_tv_episodes(args.export_type)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
