#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主程序入口"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from spiders.movie_spider import MovieSpider
from spiders.tv_spider import TVSpider
from exporters.csv_exporter import DataExporter


def main():
    parser = argparse.ArgumentParser(description='神马午夜电影网爬虫')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 电影爬虫
    movie_parser = subparsers.add_parser('movie', help='爬取电影')
    movie_parser.add_argument('--start-year', type=int, default=1945, help='开始年份')
    movie_parser.add_argument('--end-year', type=int, default=2026, help='结束年份')
    movie_parser.add_argument('--max-pages', type=int, help='每年份最大页数')
    movie_parser.add_argument('--limit', type=int, help='最大爬取数量')
    movie_parser.add_argument('--threads', type=int, default=1, help='线程数 (1-100)')
    movie_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 电视剧爬虫
    tv_parser = subparsers.add_parser('tv', help='爬取电视剧')
    tv_parser.add_argument('--start-year', type=int, help='开始年份')
    tv_parser.add_argument('--end-year', type=int, help='结束年份')
    tv_parser.add_argument('--max-pages', type=int, help='每年份最大页数')
    tv_parser.add_argument('--max-episodes', type=int, help='每部剧最大集数')
    tv_parser.add_argument('--limit', type=int, help='最大爬取数量')
    tv_parser.add_argument('--threads', type=int, default=1, help='线程数 (1-100)')
    tv_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 导出
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('--type', choices=['movies', 'tv', 'all'], 
                               default='all', help='导出类型')
    export_parser.add_argument('--export-type', choices=['full', 'incremental'],
                               default='full', help='导出方式')
    export_parser.add_argument('--format', choices=['csv', 'excel'],
                               default='csv', help='导出格式')
    export_parser.add_argument('--output', type=str, default='./exports', help='输出目录')
    export_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 统一爬取
    all_parser = subparsers.add_parser('all', help='统一爬取 (电影+电视剧)')
    all_parser.add_argument('--limit', type=int, help='最大爬取数量 (总计)')
    all_parser.add_argument('--threads', type=int, default=1, help='线程数 (1-100)')
    all_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 增量爬取
    inc_parser = subparsers.add_parser('incremental', help='增量爬取 (遇旧即停)')
    inc_parser.add_argument('--limit', type=int, help='最大爬取数量 (总计)')
    inc_parser.add_argument('--threads', type=int, default=1, help='线程数 (1-100)')
    inc_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')

    args = parser.parse_args()
    
    if args.command == 'movie':
        spider = MovieSpider(db_path=args.db, max_workers=args.threads)
        spider.crawl(
            year_start=args.start_year,
            year_end=args.end_year,
            max_pages=args.max_pages,
            limit=args.limit,
            cids=[1] # 仅爬取电影分类
        )
    
    elif args.command == 'tv':
        # 兼容旧命令，但推荐用 all
        # 实际上我们可以直接用 MovieSpider (因为现在它包含了 TV 逻辑)
        # 但为了保留 TVSpider 的特定参数支持（如 max_episodes），这里暂不改动 TVSpider
        # 或者我们可以让 TVSpider 继承新的 Unified Logic
        # 这里为了统一，我们让 tv 命令也使用 MovieSpider (Unified) 但只爬 cid=2
        spider = MovieSpider(db_path=args.db, max_workers=args.threads)
        spider.crawl(
            year_start=args.start_year,
            year_end=args.end_year,
            max_pages=args.max_pages,
            limit=args.limit,
            cids=[2] # 仅爬取电视剧分类
        )
        
    elif args.command == 'all':
        # 统一爬取 [1, 2]
        spider = MovieSpider(db_path=args.db, max_workers=args.threads)
        spider.crawl(limit=args.limit, cids=[1, 2])
        
    elif args.command == 'incremental':
        # 增量爬取 (遇旧即停)
        spider = MovieSpider(db_path=args.db, max_workers=args.threads)
        spider.crawl(limit=args.limit, cids=[1, 2], incremental=True)
    
    elif args.command == 'export':
        exporter = DataExporter(db_path=args.db, output_dir=args.output)
        
        if args.type in ['movies', 'all']:
            exporter.export_movies(args.export_type, args.format)
            
        if args.type in ['tv', 'all']:
            exporter.export_tv(args.export_type, args.format)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
