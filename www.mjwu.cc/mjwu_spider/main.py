#!/usr/bin/env python3
"""主程序入口"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from spiders.movie_spider import MovieSpider
from spiders.tv_spider import TVSpider
from exporters.csv_exporter import CSVExporter

def main():
    parser = argparse.ArgumentParser(description='美剧屋爬虫')
    parser.add_argument('--mode', choices=['movie', 'tv', 'all'], default='all',
                       help='爬取模式: movie=仅电影, tv=仅电视剧, all=全部')
    parser.add_argument('--year-start', type=int, default=1945,
                       help='开始年份 (默认: 1945)')
    parser.add_argument('--year-end', type=int, default=2026,
                       help='结束年份 (默认: 2026)')
    parser.add_argument('--max-pages', type=int, default=None,
                       help='每年份最大页数 (默认: 不限制)')
    parser.add_argument('--max-episodes', type=int, default=None,
                       help='每部剧最大集数限制 (默认: 不限制)')
    parser.add_argument('--max-items', type=int, default=None,
                       help='最大爬取条数 (默认: 不限制)')
    parser.add_argument('--export', choices=['full', 'incremental', 'none'], default='none',
                       help='导出数据: full=全量, incremental=增量, none=不导出')
    parser.add_argument('--incremental', action='store_true',
                       help='启用增量爬取模式 (仅爬取当前年份)')
    
    args = parser.parse_args()
    
    # 增量模式逻辑优化
    if args.incremental:
        import datetime
        current_year = datetime.datetime.now().year
        print(f"🚀 启用增量爬取模式: 仅爬取 {current_year} 年数据")
        args.year_start = current_year
        args.year_end = current_year
        # 强制使用增量导出，除非用户明确指定了其他
        if args.export == 'none':
            args.export = 'incremental'

    print("="*60)
    print("🎬 美剧屋 (mjwu.cc) 爬虫系统")
    print("="*60)
    print(f"模式: {args.mode}")
    print(f"年份范围: {args.year_start} - {args.year_end}")
    print(f"最大页数: {args.max_pages or '不限制'}")
    print(f"最大集数: {args.max_episodes or '不限制'}")
    print(f"最大条数: {args.max_items or '不限制'}")
    print("="*60 + "\n")
    
    # 爬取电影
    if args.mode in ['movie', 'all']:
        print("\n" + "="*60)
        print("🎬 开始爬取电影")
        print("="*60 + "\n")
        
        movie_spider = MovieSpider()
        movie_count = movie_spider.run(
            content_type='dianying',
            year_start=args.year_start,
            year_end=args.year_end,
            max_pages=args.max_pages,
            max_items=args.max_items
        )
        
        print(f"\n✅ 电影爬取完成: {movie_count} 部")
    
    # 爬取电视剧
    if args.mode in ['tv', 'all']:
        print("\n" + "="*60)
        print("📺 开始爬取电视剧")
        print("="*60 + "\n")
        
        tv_spider = TVSpider()
        series_count, episodes_count = tv_spider.run(
            content_type='meiju',
            year_start=args.year_start,
            year_end=args.year_end,
            max_pages=args.max_pages,
            max_episodes=args.max_episodes,
            max_items=args.max_items
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
