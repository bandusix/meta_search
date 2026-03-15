import argparse
import sys
import os
from movie_scraper import MovieScraper
from tv_scraper import TVScraper
from database import Database
from exporter import Exporter

class DualLogger(object):
    """同时将输出写入终端和文件"""
    def __init__(self, filename, mode='a'):
        self.terminal = sys.stdout
        self.log = open(filename, mode, encoding='utf-8', buffering=1) # line buffering

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        # self.log.flush() # buffering=1 已经保证了行缓冲，通常不需要每次手动flush，除非非常实时

    def flush(self):
        self.terminal.flush()
        self.log.flush()

def main():
    # 设置双向日志记录 (仅在运行 task 时启用，避免干扰其他命令)
    if 'task' in sys.argv:
        sys.stdout = DualLogger('crawl.log')
        sys.stderr = sys.stdout

    parser = argparse.ArgumentParser(description='RepelisHD 爬虫系统')
    subparsers = parser.add_subparsers(dest='command')
    
    # task 子命令 (执行特定任务)
    task_parser = subparsers.add_parser('task', help='执行特定爬取任务')
    task_parser.add_argument('--movies', type=int, default=0, help='爬取电影数量')
    task_parser.add_argument('--tv', type=int, default=0, help='爬取电视剧数量')
    task_parser.add_argument('--delay-min', type=float, default=0.1, help='最小延迟(秒)')
    task_parser.add_argument('--delay-max', type=float, default=0.5, help='最大延迟(秒)')
    task_parser.add_argument('--threads', type=int, default=10, help='并发线程数 (1-50)')
    
    # export 子命令
    export_parser = subparsers.add_parser('export', help='导出数据到 Excel')
    export_parser.add_argument('--mode', choices=['full', 'incremental'], default='full', help='导出模式: full(存量) 或 incremental(增量)')
    export_parser.add_argument('--output-dir', default='./exports', help='导出目录')
    
    # movies 子命令
    movies_parser = subparsers.add_parser('movies', help='爬取电影')
    movies_parser.add_argument('--limit', type=int, default=2000, help='限制爬取数量')
    movies_parser.add_argument('--delay-min', type=float, default=1.0)
    movies_parser.add_argument('--delay-max', type=float, default=3.0)
    
    # tv 子命令
    tv_parser = subparsers.add_parser('tv', help='爬取电视剧')
    tv_parser.add_argument('--limit', type=int, default=2000, help='限制爬取电视剧数量')
    tv_parser.add_argument('--delay-min', type=float, default=1.0)
    tv_parser.add_argument('--delay-max', type=float, default=3.0)
    
    # stats 子命令
    subparsers.add_parser('stats', help='查看统计')
    
    args = parser.parse_args()
    
    # 如果没有参数，打印帮助
    if not args.command:
        parser.print_help()
        return

    db = Database('repelishd.db')
    
    if args.command == 'task':
        if args.movies > 0:
            print(f"开始爬取 {args.movies} 部电影...")
            existing_urls = db.get_existing_movie_urls()
            print(f"已存在 {len(existing_urls)} 部电影，将跳过详情页抓取")
            scraper = MovieScraper(args.delay_min, args.delay_max, max_workers=args.threads)
            movies = scraper.scrape_latest_movies(limit=args.movies, existing_urls=existing_urls)
            db.save_movies(movies)
            
        if args.tv > 0:
            print(f"开始爬取 {args.tv} 部电视剧...")
            existing_urls = db.get_existing_series_urls()
            print(f"已存在 {len(existing_urls)} 部电视剧，将跳过详情页抓取")
            scraper = TVScraper(args.delay_min, args.delay_max, max_workers=args.threads)
            episodes = scraper.scrape_latest_series(limit=args.tv, existing_urls=existing_urls)
            db.save_tv_episodes(episodes)
            
    elif args.command == 'export':
        exporter = Exporter(output_dir=args.output_dir)
        exporter.export(mode=args.mode)
            
    elif args.command == 'movies':
        scraper = MovieScraper(args.delay_min, args.delay_max)
        movies = scraper.scrape_latest_movies(limit=args.limit)
        db.save_movies(movies)
    
    elif args.command == 'tv':
        scraper = TVScraper(args.delay_min, args.delay_max)
        episodes = scraper.scrape_latest_series(limit=args.limit)
        db.save_tv_episodes(episodes)
        
    elif args.command == 'stats':
        movie_count = db.get_movie_count()
        tv_series_count = db.get_tv_series_count()
        episodes_count = len(db.get_all_tv_episodes())
        print(f"\n数据库统计:")
        print(f"  电影数量: {movie_count}")
        print(f"  电视剧数量: {tv_series_count}")
        print(f"  总剧集数: {episodes_count}")

if __name__ == '__main__':
    main()
