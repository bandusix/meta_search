#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cuevana3 爬虫主程序
支持电影和电视剧爬取，数据库存储，定时更新
"""

import argparse
import sys
import os
from datetime import datetime
from database import Database
from movie_scraper import MovieScraper
from tv_scraper import TVSeriesScraper
from config_manager import ConfigManager


def scrape_movies(args, config=None):
    """爬取电影"""
    if config is None:
        config = ConfigManager()
    
    db_path = config.get_database_path() if not args.database else args.database
    delay_range = config.get_delay_range() if args.delay_min == 1.0 else (args.delay_min, args.delay_max)
    
    db = Database(db_path)
    scraper = MovieScraper(delay_range=delay_range)
    
    if args.year_start and args.year_end:
        # 爬取年份范围
        movies = scraper.scrape_multiple_years(
            start_year=args.year_start,
            end_year=args.year_end,
            reverse=True,  # 从最新年份开始
            max_pages_per_year=args.max_pages
        )
    elif args.year_start:
        # 爬取单个年份
        movies = scraper.scrape_year(args.year_start, max_pages=args.max_pages)
    else:
        print("❌ 请指定年份参数 --year-start")
        return
    
    # 保存到数据库
    if movies:
        print(f"\n💾 正在保存到数据库...")
        success_count = db.bulk_insert_movies(movies)
        print(f"✅ 成功保存 {success_count}/{len(movies)} 部电影")
        
        # 显示统计信息
        stats = db.get_statistics()
        print(f"\n📊 数据库统计:")
        print(f"   电影总数: {stats['total_movies']}")
        print(f"   平均评分: {stats['avg_movie_rating']}")
    
    db.close()


def scrape_tv_series(args, config=None):
    """爬取电视剧"""
    if config is None:
        config = ConfigManager()
    
    db_path = config.get_database_path() if not args.database else args.database
    delay_range = config.get_delay_range() if args.delay_min == 1.0 else (args.delay_min, args.delay_max)
    
    db = Database(db_path)
    scraper = TVSeriesScraper(delay_range=delay_range)
    
    episodes = scraper.scrape_all_episodes(
        max_series=args.max_series,
        max_pages=args.max_pages
    )
    
    # 保存到数据库
    if episodes:
        print(f"\n💾 正在保存到数据库...")
        success_count = db.bulk_insert_tv_series(episodes)
        print(f"✅ 成功保存 {success_count}/{len(episodes)} 个剧集")
        
        # 显示统计信息
        stats = db.get_statistics()
        print(f"\n📊 数据库统计:")
        print(f"   剧集总数: {stats['total_tv_episodes']}")
        print(f"   独立剧集数: {stats['unique_tv_shows']}")
        print(f"   平均评分: {stats['avg_tv_rating']}")
    
    db.close()


def update_all(args, config=None):
    """更新所有数据（电影+电视剧）"""
    print(f"\n{'='*60}")
    print(f"🔄 开始更新所有数据")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    # 更新电影（最近2年）
    print(f"\n\n{'#'*60}")
    print(f"# 第1步: 更新电影数据")
    print(f"{'#'*60}")
    
    current_year = datetime.now().year
    args.year_start = current_year - 1
    args.year_end = current_year
    args.max_pages = 5  # 每个年份最多5页
    scrape_movies(args, config)
    
    # 更新电视剧（最近更新的剧集）
    print(f"\n\n{'#'*60}")
    print(f"# 第2步: 更新电视剧数据")
    print(f"{'#'*60}")
    
    args.max_series = 20  # 最多更新20部剧
    args.max_pages = 2  # 电视剧列表最多2页
    scrape_tv_series(args, config)
    
    print(f"\n\n{'='*60}")
    print(f"✅ 所有数据更新完成！")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")


def export_data(args, config=None):
    """导出数据到CSV"""
    if config is None:
        config = ConfigManager()
    
    db_path = config.get_database_path() if not args.database else args.database
    db = Database(db_path)
    
    # 确保导出目录存在
    export_dir = config.get_export_directory()
    if not os.path.exists(export_dir):
        os.makedirs(export_dir)
    
    if args.type == 'movies' or args.type == 'all':
        output_file = args.output or config.get_export_path('movies')
        db.export_to_csv('movies', output_file)
    
    if args.type == 'tv' or args.type == 'all':
        output_file = args.output or config.get_export_path('tv_series')
        db.export_to_csv('tv_series', output_file)
    
    db.close()


def show_stats(args, config=None):
    """显示数据库统计信息"""
    if config is None:
        config = ConfigManager()
    
    db_path = config.get_database_path() if not args.database else args.database
    db = Database(db_path)
    stats = db.get_statistics()
    
    print(f"\n{'='*60}")
    print(f"📊 数据库统计信息")
    print(f"{'='*60}")
    print(f"\n电影:")
    print(f"  总数: {stats['total_movies']}")
    print(f"  年份数: {stats['movie_years']}")
    print(f"  平均评分: {stats['avg_movie_rating']}")
    
    print(f"\n电视剧:")
    print(f"  剧集总数: {stats['total_tv_episodes']}")
    print(f"  独立剧集数: {stats['unique_tv_shows']}")
    print(f"  平均评分: {stats['avg_tv_rating']}")
    
    # 显示最新添加的内容
    print(f"\n最新添加的电影 (前5部):")
    latest_movies = db.get_latest_movies(5)
    for movie in latest_movies:
        print(f"  - {movie['title_spanish']} ({movie['year']}) - {movie['rating']}/10")
    
    print(f"\n最新添加的剧集 (前5集):")
    latest_tv = db.get_latest_tv_series(5)
    for episode in latest_tv:
        print(f"  - {episode['title_spanish']} S{episode['season']}E{episode['episode']} - {episode['rating']}/10")
    
    print(f"\n{'='*60}")
    
    db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Cuevana3 爬虫 - 爬取电影和电视剧数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 爬取2025年的电影
  python main.py movies --year-start 2025
  
  # 爬取2020-2025年的电影
  python main.py movies --year-start 2020 --year-end 2025
  
  # 爬取所有电视剧（限制20部）
  python main.py tv --max-series 20
  
  # 更新所有数据（推荐用于定时任务）
  python main.py update
  
  # 导出数据到CSV
  python main.py export --type all
  
  # 显示统计信息
  python main.py stats
        """
    )
    
    # 全局参数
    parser.add_argument('--database', '-db', default='cuevana3.db',
                        help='数据库文件路径 (默认: cuevana3.db)')
    parser.add_argument('--delay-min', type=float, default=1.0,
                        help='最小延迟时间（秒）(默认: 1.0)')
    parser.add_argument('--delay-max', type=float, default=3.0,
                        help='最大延迟时间（秒）(默认: 3.0)')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 电影爬取命令
    movies_parser = subparsers.add_parser('movies', help='爬取电影')
    movies_parser.add_argument('--year-start', type=int, required=True,
                               help='起始年份')
    movies_parser.add_argument('--year-end', type=int,
                               help='结束年份（可选，不指定则只爬取起始年份）')
    movies_parser.add_argument('--max-pages', type=int,
                               help='每个年份最大页数限制')
    
    # 电视剧爬取命令
    tv_parser = subparsers.add_parser('tv', help='爬取电视剧')
    tv_parser.add_argument('--max-series', type=int,
                           help='最大电视剧数量限制')
    tv_parser.add_argument('--max-pages', type=int,
                           help='电视剧列表最大页数')
    
    # 更新命令
    update_parser = subparsers.add_parser('update', help='更新所有数据（推荐用于定时任务）')
    
    # 导出命令
    export_parser = subparsers.add_parser('export', help='导出数据到CSV')
    export_parser.add_argument('--type', choices=['movies', 'tv', 'all'], 
                               default='all', help='导出类型')
    export_parser.add_argument('--output', '-o', help='输出文件名')
    
    # 统计命令
    stats_parser = subparsers.add_parser('stats', help='显示数据库统计信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 加载配置
    config = ConfigManager()
    
    # 执行对应命令
    if args.command == 'movies':
        scrape_movies(args, config)
    elif args.command == 'tv':
        scrape_tv_series(args, config)
    elif args.command == 'update':
        update_all(args, config)
    elif args.command == 'export':
        export_data(args, config)
    elif args.command == 'stats':
        show_stats(args, config)


if __name__ == "__main__":
    main()
