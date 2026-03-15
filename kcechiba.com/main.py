#!/usr/bin/env python3
"""主程序入口"""

import argparse
import sys
import yaml
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from spiders.movie_spider import MovieSpider
from spiders.tv_spider import TVSpider
from exporters.csv_exporter import CSVExporter

def load_config():
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    task_config = config.get('tasks', {})

    parser = argparse.ArgumentParser(description='策驰影院爬虫')
    parser.add_argument('--mode', choices=['movie', 'tv', 'all'], default='all',
                       help='爬取模式: movie=仅电影, tv=仅电视剧, all=全部')
    parser.add_argument('--task', choices=['init', 'daily', 'custom'], default='init',
                       help='任务类型: init=全量初始化, daily=每日增量(默认前20页), custom=自定义参数')
    parser.add_argument('--year-start', type=int, default=1945,
                       help='开始年份 (默认: 1945)')
    parser.add_argument('--year-end', type=int, default=2026,
                       help='结束年份 (默认: 2026)')
    parser.add_argument('--max-pages', type=int, default=None,
                       help='每年份最大页数 (自定义模式下有效)')
    parser.add_argument('--max-episodes', type=int, default=None,
                       help='每部剧最大集数限制 (默认: 不限制)')
    parser.add_argument('--max-items', type=int, default=None,
                       help='最大爬取数量 (默认: 不限制)')
    parser.add_argument('--start-page', type=int, default=1,
                       help='起始页码 (默认: 1)')
    parser.add_argument('--export', choices=['full', 'incremental', 'none'], default='none',
                       help='导出数据: full=全量, incremental=增量, none=不导出')
    
    args = parser.parse_args()
    
    # 根据任务类型设置参数
    max_pages = args.max_pages
    max_items = args.max_items
    
    if args.task == 'daily':
        daily_conf = task_config.get('daily', {})
        if max_pages is None:
            max_pages = daily_conf.get('max_pages', 20)
        if max_items is None:
            max_items = daily_conf.get('max_items')
        print(f"🔄 执行每日增量任务 (Max Pages: {max_pages})")
    elif args.task == 'init':
        init_conf = task_config.get('init', {})
        if max_pages is None:
            max_pages = init_conf.get('max_pages')
        if max_items is None:
            max_items = init_conf.get('max_items')
        print(f"🚀 执行全量初始化任务")
    
    print("="*60)
    print("🎬 策驰影院 (kcechiba.com) 爬虫系统")
    print("="*60)
    print(f"模式: {args.mode}")
    print(f"任务: {args.task}")
    print(f"年份范围: {args.year_start} - {args.year_end}")
    print(f"最大页数: {max_pages or '不限制'}")
    print(f"最大集数: {args.max_episodes or '不限制'}")
    print(f"最大数量: {max_items or '不限制'}")
    print(f"起始页码: {args.start_page}")
    print("="*60 + "\n")
    
    # 爬取电影
    if args.mode in ['movie', 'all']:
        print("\n" + "="*60)
        print("🎬 开始爬取电影")
        print("="*60 + "\n")
        
        movie_spider = MovieSpider()
        movie_count = movie_spider.run(
            year_start=args.year_start,
            year_end=args.year_end,
            max_pages=max_pages,
            max_items=max_items,
            start_page=args.start_page
        )
        
        print(f"\n✅ 电影爬取完成: {movie_count} 部")
    
    # 爬取电视剧
    if args.mode in ['tv', 'all']:
        print("\n" + "="*60)
        print("📺 开始爬取电视剧")
        print("="*60 + "\n")
        
        tv_spider = TVSpider()
        series_count, episodes_count = tv_spider.run(
            year_start=args.year_start,
            year_end=args.year_end,
            max_pages=max_pages,
            max_episodes=args.max_episodes,
            max_items=max_items,
            start_page=args.start_page
        )
        
        print(f"\n✅ 电视剧爬取完成: {series_count} 部, {episodes_count} 集")
    
    # 导出数据
    if args.export != 'none':
        print("\n" + "="*60)
        print("📊 开始导出数据")
        print("="*60 + "\n")
        
        exporter = CSVExporter()
        exporter.export_all(export_type=args.export)
    
    print("\n" + "="*60)
    print("🎉 所有任务完成!")
    print("="*60)

if __name__ == '__main__':
    main()
