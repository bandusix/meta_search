import concurrent.futures
import time
import argparse
import logging
import sys
import os
from pathlib import Path
from database import Database
from movie_scraper import LK21MovieScraper
from csv_exporter import CSVExporter
from utils import ProgressTracker

# 设置控制台输出编码为 UTF-8，解决 Windows 下的 UnicodeEncodeError
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lk21_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def scrape_movies(args):
    """爬取电影"""
    # 初始化数据库
    db = Database(args.db_path)
    
    # 初始化爬虫
    scraper = LK21MovieScraper(
        delay_min=args.delay_min, 
        delay_max=args.delay_max,
        max_workers=args.threads
    )
    
    # 初始化进度追踪器
    tracker = ProgressTracker()
    
    # 确定要爬取的年份列表
    if args.full_scan:
        # 完整扫描: 2026 -> 1917
        years = list(range(2026, 1916, -1))
    elif args.year:
        years = [args.year]
    elif args.year_range:
        start_year, end_year = args.year_range
        # 倒序：从最新年份开始
        years = list(range(end_year, start_year - 1, -1))
    elif args.years:
        # 倒序排序
        years = sorted(args.years, reverse=True)
    else:
        logger.error("请指定年份参数: --full-scan, --year, --year-range, 或 --years")
        return
    
    logger.info(f"将要爬取的年份: {years[:5]} ... (共 {len(years)} 年)")
    
    # 爬取电影
    for year in years:
        # 获取上次的进度
        start_page = 1
        if args.resume:
            last_page = tracker.get_last_page(year)
            if last_page > 0:
                start_page = last_page + 1  # 从下一页开始
                logger.info(f"🔁 恢复进度: {year} 年从第 {start_page} 页继续")
        
        # 定义进度回调
        def on_progress(y, p):
            tracker.save(y, p)
        
        # 完整扫描时，默认最大页数为 200（作为安全限制）
        # 如果用户手动指定了 --max-pages，则使用用户指定的数值
        
        current_max_pages = args.max_pages
        if current_max_pages is None:
             current_max_pages = 200

        movies = scraper.scrape_year(
            year, 
            max_pages=current_max_pages, 
            start_page=start_page,
            on_progress=on_progress
        )
        
        # 保存到数据库
        for movie in movies:
            db.insert_movie(movie)
            
        # 每次爬取完一年，自动导出数据
        if movies:
            try:
                exporter = CSVExporter(db_path=args.db_path, export_dir=args.export_dir)
                
                # 导出全量
                all_path = exporter.export_all_movies(fmt='excel')
                logger.info(f"📁 [自动导出] 全量数据已保存至: {all_path}")
                
                # 导出增量 (当天)
                inc_path = exporter.export_incremental_movies(days=1, fmt='excel')
                if inc_path:
                    logger.info(f"📁 [自动导出] 增量数据已保存至: {inc_path}")
                else:
                    logger.info("ℹ️ [自动导出] 今日无新增数据，跳过增量导出")
            except Exception as e:
                logger.error(f"❌ 自动导出失败: {e}", exc_info=True)
    
    logger.info("✅ 爬取完成！")


def export_movies(args):
    """导出电影"""
    exporter = CSVExporter(db_path=args.db_path, export_dir=args.export_dir)
    
    fmt = 'excel' if args.excel else 'csv'
    
    if args.all:
        filepath = exporter.export_all_movies(fmt=fmt)
    elif args.incremental:
        filepath = exporter.export_incremental_movies(days=args.days, fmt=fmt)
    elif args.year:
        filepath = exporter.export_by_year(args.year, fmt=fmt)
    else:
        logger.error("请指定导出类型: --all, --incremental, 或 --year")
        return
    
    logger.info(f"✅ 导出完成: {filepath}")


def show_stats(args):
    """显示统计信息"""
    db = Database(args.db_path)
    stats = db.get_statistics()
    
    print("\n============================================================")
    print("📊 数据库统计信息")
    print("============================================================")
    print(f"电影总数: {stats['total_movies']}")
    print(f"最早年份: {stats['min_year']}")
    print(f"最晚年份: {stats['max_year']}")
    print(f"最新更新: {stats['latest_update']}")
    print("\n按年份统计:")
    for year, count in stats['movies_by_year']:
        print(f"  {year}: {count} 部")
    print("============================================================\n")


def retry_failed(args):
    """重试失败的URL"""
    db = Database(args.db_path)
    scraper = LK21MovieScraper(
        delay_min=args.delay_min, 
        delay_max=args.delay_max,
        max_workers=args.threads
    )
    
    # 先去重
    scraper.remove_duplicates()
    
    movies = scraper.retry_failed_urls()
    
    if movies:
        for movie in movies:
            db.insert_movie(movie)
            
        try:
            exporter = CSVExporter(db_path=args.db_path, export_dir=args.export_dir)
            
            # 导出全量
            all_path = exporter.export_all_movies(fmt='excel')
            logger.info(f"📁 [自动导出] 全量数据已保存至: {all_path}")
            
            # 导出增量 (当天)
            inc_path = exporter.export_incremental_movies(days=1, fmt='excel')
            if inc_path:
                logger.info(f"📁 [自动导出] 增量数据已保存至: {inc_path}")
            else:
                logger.info("ℹ️ [自动导出] 今日无新增数据，跳过增量导出")
        except Exception as e:
            logger.error(f"❌ 自动导出失败: {e}", exc_info=True)
        
    logger.info("✅ 重试任务完成！")

def update_db(args):
    """更新现有数据库中的数据"""
    db = Database(args.db_path)
    scraper = LK21MovieScraper(
        delay_min=args.delay_min, 
        delay_max=args.delay_max,
        max_workers=args.threads
    )
    
    logger.info("正在读取数据库中所有 URL...")
    all_records = db.get_all_movie_urls()
    logger.info(f"数据库中共有 {len(all_records)} 条记录")
    
    valid_records = []
    invalid_count = 0
    
    # 过滤无效 URL，并且只处理未更新的记录（可选）
    # 这里我们假设所有记录都需要更新，或者根据某种标记
    # 如果要断点续传，可以记录已处理的ID
    
    # 读取已处理的ID
    processed_ids = set()
    progress_file = "update_progress.txt"
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            processed_ids = set(line.strip() for line in f if line.strip())
            
    logger.info(f"已处理 {len(processed_ids)} 条记录，跳过这些记录...")
    
    for record in all_records:
        url = record['movie_url']
        rec_id = str(record['id'])
        
        if rec_id in processed_ids:
            continue
            
        if not url.startswith('http'):
            logger.warning(f"发现无效 URL (ID: {record['id']}): {url} -> 将被删除")
            db.delete_movie(record['id'])
            invalid_count += 1
        else:
            valid_records.append(record)
            
    if invalid_count > 0:
        logger.info(f"已清理 {invalid_count} 条无效记录")
        
    logger.info(f"开始更新 {len(valid_records)} 条有效记录...")
    
    # 并发更新
    processed = 0
    total = len(valid_records)
    total_db_records = len(all_records)
    initial_processed_count = total_db_records - total
    
    # 打开进度文件准备追加
    progress_f = open(progress_file, 'a', encoding='utf-8')
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as executor:
        # 提交任务
        future_to_record = {
            executor.submit(scraper._scrape_detail_task, record['movie_url']): record 
            for record in valid_records
        }
        
        for future in concurrent.futures.as_completed(future_to_record):
            record = future_to_record[future]
            processed += 1
            if processed % 100 == 0:
                current_total_processed = initial_processed_count + processed
                logger.info(f"进度: {current_total_processed}/{total_db_records} ({(current_total_processed/total_db_records)*100:.1f}%)")
                # 强制刷新进度文件
                progress_f.flush()
                os.fsync(progress_f.fileno())
                
            try:
                detail = future.result()
                if detail:
                    # 补充 movie_url 确保能更新
                    detail['movie_url'] = record['movie_url']
                    db.insert_movie(detail)
                    # 记录成功ID
                    progress_f.write(f"{record['id']}\n")
                else:
                    logger.warning(f"更新失败 (无数据): {record['movie_url']}")
            except Exception as e:
                logger.error(f"更新出错 {record['movie_url']}: {e}")
    
    progress_f.close()
                
    # 导出
    try:
        exporter = CSVExporter(db_path=args.db_path, export_dir=args.export_dir)
        all_path = exporter.export_all_movies(fmt='excel')
        logger.info(f"📁 [自动导出] 全量数据已保存至: {all_path}")
    except Exception as e:
        logger.error(f"自动导出失败: {e}", exc_info=True)
        
    logger.info("✅ 数据库全量更新完成！")

def cleanup_db(args):
    """清理和规范化数据库"""
    db = Database(args.db_path)
    conn = db._get_connection()
    cursor = conn.cursor()
    
    logger.info("开始清理数据库...")
    
    # 1. 删除特定ID
    bad_ids = [244584, 244583, 244582, 244581, 244580, 244550]
    cursor.execute(f"DELETE FROM movies WHERE id IN ({','.join(map(str, bad_ids))})")
    logger.info(f"已删除 {cursor.rowcount} 条指定的问题记录")
    
    # 2. 删除无效 URL
    cursor.execute("DELETE FROM movies WHERE movie_url LIKE '%/page/%' OR movie_url LIKE '%/year/%'")
    logger.info(f"已删除 {cursor.rowcount} 条无效URL记录 (listing page)")
    
    # 3. 删除首页标题记录
    cursor.execute("DELETE FROM movies WHERE title LIKE '%Nonton Film & Series Sub Indo Gratis di Layarkaca21%'")
    logger.info(f"已删除 {cursor.rowcount} 条首页标题记录")
    
    # 4. 规范化时长、清理标题和确定类型
    logger.info("正在规范化时长、清理标题和确定类型...")
    cursor.execute("SELECT id, title, page_title, duration, genre FROM movies")
    all_movies = cursor.fetchall()
    
    scraper = LK21MovieScraper()
    
    update_count = 0
    remove_list = [
        "Sub Indo di Lk21", "Sub Indo", "Subtitle Indonesia", 
        "di Lk21", "LK21", "Layarkaca21", "Dunia21",
        "Nonton Film", "Nonton Movie", "Nonton", "Streaming Movie", "Download Film",
        "Film Bioskop", "Cinema 21", "XXI",
        "Nonton Film & Series Sub Indo Gratis di Layarkaca21 (LK21) Official"
    ]
    
    for row in all_movies:
        mid = row['id']
        duration = row['duration']
        page_title = row['page_title']
        
        needs_update = False
        new_duration = duration
        new_page_title = page_title
        
        # 规范化时长
        if duration:
            norm_duration = scraper._normalize_duration(duration)
            if norm_duration != duration:
                new_duration = norm_duration
                needs_update = True
                
        # 清理标题
        if page_title:
            cleaned = page_title
            for text in remove_list:
                cleaned = cleaned.replace(text, "")
            cleaned = cleaned.strip(" -|")
            
            if cleaned != page_title:
                new_page_title = cleaned
                needs_update = True
        
        # Determine Type
        movie_type = 'Movie'
        genre = row['genre']
        if genre:
            g_lower = genre.lower()
            if any(k in g_lower for k in ['series', 'tv series', 'tv-series', '短剧', '电视剧']):
                movie_type = 'TV Series'
        
        if 'season' in row['title'].lower():
            movie_type = 'TV Series'

        # Always update type (backfill)
        needs_update = True
        
        if needs_update:
            cursor.execute(
                "UPDATE movies SET duration = ?, page_title = ?, type = ? WHERE id = ?",
                (new_duration, new_page_title, movie_type, mid)
            )
            update_count += 1
            if update_count % 1000 == 0:
                logger.info(f"已更新 {update_count} 条记录...")
                conn.commit()
                
    conn.commit()
    logger.info(f"✅ 清理完成，共更新 {update_count} 条记录")
    conn.close()

def run_daily_update(args):
    """执行每日增量更新"""
    from datetime import datetime
    
    current_year = datetime.now().year
    years_to_scan = [current_year, current_year - 1] # 扫描今年和去年，以防跨年数据
    
    logger.info(f"🚀 开始每日增量爬取任务: 扫描 {years_to_scan} 年的数据")
    
    db = Database(args.db_path)
    
    # 获取所有已存在的 URL，用于快速去重
    existing_records = db.get_all_movie_urls()
    existing_urls = set(r['movie_url'] for r in existing_records)
    logger.info(f"当前数据库已有 {len(existing_urls)} 部电影，将跳过已存在的记录")
    
    scraper = LK21MovieScraper(max_workers=args.threads)
    
    for year in years_to_scan:
        logger.info(f"正在检查 {year} 年的新电影...")
        # 传递 existing_urls 给 scraper，scraper 内部会判断连续重复则停止
        movies = scraper.scrape_year(year, existing_urls=existing_urls)
        
        if movies:
            logger.info(f"发现 {len(movies)} 部新电影，正在入库...")
            count = 0
            for m in movies:
                if db.insert_movie(m):
                    count += 1
            logger.info(f"✅ {year} 年新增入库 {count} 部电影")
        else:
            logger.info(f"{year} 年没有发现新电影")
            
    logger.info("🎉 每日增量任务完成")

def main():
    parser = argparse.ArgumentParser(description="LK21 电影爬虫系统")
    # 通用参数
    parser.add_argument('--db-path', default='lk21.db', help='数据库路径 (默认: lk21.db)')
    parser.add_argument('--export-dir', default='exports', help='导出目录 (默认: exports)')
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # scrape 子命令
    scrape_parser = subparsers.add_parser('scrape', help='爬取电影')
    scrape_parser.add_argument('--full-scan', action='store_true', help='完整扫描所有年份 (1917-2026)')
    scrape_parser.add_argument('--year', type=int, help='爬取指定年份')
    scrape_parser.add_argument('--year-range', nargs=2, type=int, metavar=('START', 'END'), help='爬取年份范围')
    scrape_parser.add_argument('--years', nargs='+', type=int, help='爬取指定年份列表')
    scrape_parser.add_argument('--delay-min', type=float, default=0.5, help='最小延迟时间（秒）')
    scrape_parser.add_argument('--delay-max', type=float, default=1.5, help='最大延迟时间（秒）')
    scrape_parser.add_argument('--threads', type=int, default=10, help='并发线程数 (默认: 10)')
    scrape_parser.add_argument('--resume', action='store_true', help='从上次中断处继续')
    scrape_parser.add_argument('--max-pages', type=int, help='每年最大爬取页数 (默认无限制)')
    
    # export 子命令
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('--all', action='store_true', help='导出所有电影')
    export_parser.add_argument('--incremental', action='store_true', help='导出增量电影')
    export_parser.add_argument('--days', type=int, default=1, help='增量导出的天数')
    export_parser.add_argument('--year', type=int, help='导出指定年份')
    export_parser.add_argument('--export-dir', default='exports', help='导出目录')
    export_parser.add_argument('--excel', action='store_true', help='导出为 Excel 格式 (.xlsx)')
    
    # stats 子命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    
    # retry 子命令
    retry_parser = subparsers.add_parser('retry', help='重试失败的URL')
    retry_parser.add_argument('--delay-min', type=float, default=1.0, help='最小延迟时间（秒）')
    retry_parser.add_argument('--delay-max', type=float, default=3.0, help='最大延迟时间（秒）')
    retry_parser.add_argument('--threads', type=int, default=3, help='并发线程数 (默认: 3)')
    
    # update 子命令
    update_parser = subparsers.add_parser('update', help='更新数据库中现有记录')
    update_parser.add_argument('--delay-min', type=float, default=0.5, help='最小延迟时间（秒）')
    update_parser.add_argument('--delay-max', type=float, default=1.5, help='最大延迟时间（秒）')
    update_parser.add_argument('--threads', type=int, default=20, help='并发线程数 (默认: 20)')
    
    # cleanup 子命令
    cleanup_parser = subparsers.add_parser('cleanup', help='清理和规范化数据库')
    
    # daily 子命令
    daily_parser = subparsers.add_parser('daily', help='每日增量爬取')
    daily_parser.add_argument('--threads', type=int, default=5, help='并发线程数 (默认: 5)')

    args = parser.parse_args()
    
    if args.command == 'scrape':
        if not hasattr(args, 'export_dir'):
            args.export_dir = 'exports'
        scrape_movies(args)
    elif args.command == 'export':
        if not hasattr(args, 'export_dir'):
            args.export_dir = 'exports'
        export_movies(args)
    elif args.command == 'stats':
        show_stats(args)
    elif args.command == 'retry':
        if not hasattr(args, 'export_dir'):
            args.export_dir = 'exports'
        retry_failed(args)
    elif args.command == 'update':
        if not hasattr(args, 'export_dir'):
            args.export_dir = 'exports'
        update_db(args)
    elif args.command == 'cleanup':
        cleanup_db(args)
    elif args.command == 'daily':
        run_daily_update(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
