#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版主程序 - 支持高级日志记录和自动优化
"""

import argparse
import sqlite3
import pandas as pd
from datetime import datetime
import sys
import os

# 导入增强版爬虫
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from spiders.enhanced_movie_spider import EnhancedMovieSpider
from spiders.enhanced_tv_spider import EnhancedTVSpider

def export_to_excel(db_path='spider.db', output_file=None):
    """导出数据到Excel文件"""
    if output_file is None:
        output_file = f"spider_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    try:
        with sqlite3.connect(db_path) as conn:
            # 读取电影数据
            movies_df = pd.read_sql_query("SELECT * FROM movies", conn)
            
            # 读取电视剧数据
            tv_series_df = pd.read_sql_query("SELECT * FROM tv_series", conn)
            
            # 读取剧集数据
            tv_episodes_df = pd.read_sql_query("SELECT * FROM tv_episodes", conn)
            
            # 写入Excel文件
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                movies_df.to_excel(writer, sheet_name='电影', index=False)
                tv_series_df.to_excel(writer, sheet_name='电视剧', index=False)
                tv_episodes_df.to_excel(writer, sheet_name='剧集', index=False)
            
            print(f"📊 数据导出完成: {output_file}")
            print(f"   电影: {len(movies_df)} 部")
            print(f"   电视剧: {len(tv_series_df)} 部")
            print(f"   剧集: {len(tv_episodes_df)} 集")
            
            return output_file
            
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return None

def show_statistics(db_path='spider.db'):
    """显示数据库统计信息"""
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # 电影统计
            cursor.execute("SELECT COUNT(*) FROM movies")
            movie_count = cursor.fetchone()[0]
            
            # 电视剧统计
            cursor.execute("SELECT COUNT(*) FROM tv_series")
            tv_count = cursor.fetchone()[0]
            
            # 剧集统计
            cursor.execute("SELECT COUNT(*) FROM tv_episodes")
            episode_count = cursor.fetchone()[0]
            
            # 播放线路统计
            cursor.execute("SELECT play_line_name, COUNT(*) as count FROM tv_episodes GROUP BY play_line_name ORDER BY count DESC")
            play_lines = cursor.fetchall()
            
            print("\n📈 数据库统计信息:")
            print(f"   电影: {movie_count} 部")
            print(f"   电视剧: {tv_count} 部")
            print(f"   剧集: {episode_count} 集")
            
            if play_lines:
                print(f"\n📺 播放线路统计:")
                for line_name, count in play_lines[:10]:  # 显示前10个
                    print(f"   {line_name}: {count} 集")
            
            return {
                'movies': movie_count,
                'tv_series': tv_count,
                'episodes': episode_count
            }
            
    except Exception as e:
        print(f"❌ 统计失败: {e}")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='增强版97韩剧爬虫程序')
    parser.add_argument('--spider', choices=['movie', 'tv'], default='movie',
                       help='选择爬虫类型 (movie: 电影, tv: 电视剧)')
    parser.add_argument('--year-start', type=int, default=1945, help='起始年份')
    parser.add_argument('--year-end', type=int, default=2026, help='结束年份')
    parser.add_argument('--start-page', type=int, default=1, help='起始页码')
    parser.add_argument('--max-pages', type=int, help='最大页数')
    parser.add_argument('--max-workers', type=int, default=1, help='并发数')
    parser.add_argument('--cid', type=int, default=1, help='分类ID')
    parser.add_argument('--category-name', type=str, help='分类名称')
    parser.add_argument('--delay', type=int, nargs=2, default=[3, 5], help='延迟范围 (秒)')
    parser.add_argument('--export-excel', action='store_true', help='导出到Excel')
    parser.add_argument('--show-stats', action='store_true', help='显示统计信息')
    parser.add_argument('--db-path', default='spider.db', help='数据库路径')
    
    args = parser.parse_args()
    
    print("🚀 增强版97韩剧爬虫启动!")
    print("=" * 60)
    
    # 显示统计信息
    if args.show_stats:
        show_statistics(args.db_path)
        return
    
    # 导出Excel
    if args.export_excel:
        export_to_excel(args.db_path)
        return
    
    # 启动爬虫
    try:
        if args.spider == 'movie':
            spider = EnhancedMovieSpider(
                db_path=args.db_path,
                delay=tuple(args.delay)
            )
            
            saved_count = spider.crawl(
                year_start=args.year_start,
                year_end=args.year_end,
                max_pages=args.max_pages,
                start_page=args.start_page,
                max_workers=args.max_workers,
                cid=args.cid
            )
            
        else:  # tv
            spider = EnhancedTVSpider(
                db_path=args.db_path,
                delay=tuple(args.delay)
            )
            
            saved_count = spider.crawl(
                year_start=args.year_start,
                year_end=args.year_end,
                max_pages=args.max_pages,
                start_page=args.start_page,
                max_workers=args.max_workers,
                cid=args.cid,
                category_name=args.category_name
            )
        
        print(f"\n🎉 爬取完成! 总计保存: {saved_count} 条记录")
        
        # 显示最终统计
        stats = show_statistics(args.db_path)
        
        # 自动导出
        if saved_count > 0:
            output_file = export_to_excel(args.db_path)
            if output_file:
                print(f"\n📊 数据已自动导出到: {output_file}")
        
        spider.close()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，正在安全关闭...")
        if 'spider' in locals():
            spider.close()
        print("✅ 已安全关闭")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()