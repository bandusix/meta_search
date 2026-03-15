#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本 - 验证爬虫系统各组件功能
"""

import asyncio
import sys
import os
import sqlite3
from datetime import datetime

# 添加模块路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from async_crawler import AsyncCrawler, ParserUtils, URLGenerator
from tv_parser import TVParserUtils

async def test_database():
    """测试数据库功能"""
    print("🧪 测试数据库功能...")
    
    db = DatabaseManager("test.db")
    
    # 测试数据插入
    test_movies = [
        {
            'category': 'movie',
            'title': '测试电影1',
            'cover': 'http://example.com/cover1.jpg',
            'year': 2023,
            'region': '中国',
            'genre': '动作',
            'intro': '测试简介',
            'detail_url': 'http://example.com/movie1',
            'route_name': '线路一',
            'play_url': 'http://example.com/play1'
        },
        {
            'category': 'movie',
            'title': '测试电影2',
            'cover': 'http://example.com/cover2.jpg',
            'year': 2024,
            'region': '美国',
            'genre': '科幻',
            'intro': '测试简介2',
            'detail_url': 'http://example.com/movie2',
            'route_name': '线路二',
            'play_url': 'http://example.com/play2'
        }
    ]
    
    inserted = db.batch_insert_movies(test_movies)
    print(f"✅ 插入测试数据: {inserted} 条记录")
    
    # 测试统计功能
    stats = db.get_statistics()
    print(f"📊 数据库统计: {stats}")
    
    # 清理测试数据库
    os.remove("test.db")
    print("✅ 数据库测试完成")

async def test_url_generator():
    """测试URL生成器"""
    print("🧪 测试URL生成器...")
    
    # 测试电影URL生成
    movie_urls = URLGenerator.generate_movie_urls(1, 5)
    print(f"🎬 生成电影URL: {len(movie_urls)} 个")
    for url in movie_urls[:3]:
        print(f"  - {url}")
    
    # 测试电视剧URL生成
    tv_urls = URLGenerator.generate_tv_urls('tv', 1, 3)
    print(f"📺 生成电视剧URL: {len(tv_urls)} 个")
    for url in tv_urls:
        print(f"  - {url}")
    
    print("✅ URL生成器测试完成")

async def test_parser():
    """测试解析器"""
    print("🧪 测试解析器...")
    
    # 创建测试HTML内容
    test_html = """
    <html>
    <body>
        <div class="movie-item">
            <a class="movie-link" href="/movie/123.html">
                <img class="cover" src="/cover/test.jpg">
                <div class="title">测试电影</div>
                <span class="year">2023</span>
            </a>
        </div>
    </body>
    </html>
    """
    
    # 测试电影列表解析
    movies = ParserUtils.parse_movie_list(test_html, "http://www.97han.com")
    print(f"🎬 解析电影列表: {len(movies)} 部电影")
    if movies:
        print(f"  - 标题: {movies[0]['title']}")
        print(f"  - 年份: {movies[0]['year']}")
        print(f"  - 详情URL: {movies[0]['detail_url']}")
    
    print("✅ 解析器测试完成")

async def test_crawler():
    """测试爬虫核心功能"""
    print("🧪 测试爬虫核心功能...")
    
    async with AsyncCrawler(max_concurrent=5, delay_ms=100, timeout=10) as crawler:
        # 测试简单URL（使用已知的稳定网站）
        test_urls = [
            "https://httpbin.org/status/200",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/user-agent"
        ]
        
        print(f"📡 测试批量请求: {len(test_urls)} 个URL")
        results = await crawler.fetch_batch(test_urls)
        
        success_count = sum(1 for r in results if r is not None)
        print(f"✅ 成功请求: {success_count}/{len(test_urls)}")
        
        if results[0]:
            print(f"📄 响应内容长度: {len(results[0])} 字符")
    
    print("✅ 爬虫核心测试完成")

def test_tv_parser():
    """测试电视剧解析器"""
    print("🧪 测试电视剧解析器...")
    
    # 创建测试HTML内容
    test_tv_html = """
    <html>
    <body>
        <div class="tv-item">
            <a class="tv-link" href="/tv/456.html">
                <img class="cover" src="/cover/tv_test.jpg">
                <div class="title">测试电视剧</div>
                <span class="year">2023</span>
                <span class="episodes">30集全</span>
            </a>
        </div>
    </body>
    </html>
    """
    
    # 测试电视剧列表解析
    series = TVParserUtils.parse_tv_list(test_tv_html, "http://www.97han.com")
    print(f"📺 解析电视剧列表: {len(series)} 部剧集")
    if series:
        print(f"  - 标题: {series[0]['title']}")
        print(f"  - 年份: {series[0]['year']}")
        print(f"  - 集数: {series[0]['total_episodes']}")
        print(f"  - vod_id: {series[0]['vod_id']}")
    
    print("✅ 电视剧解析器测试完成")

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("🚀 开始系统功能测试")
    print("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # 运行所有测试
        await test_database()
        print()
        
        test_tv_parser()
        print()
        
        await test_url_generator()
        print()
        
        await test_parser()
        print()
        
        await test_crawler()
        print()
        
        duration = (datetime.now() - start_time).total_seconds()
        
        print("=" * 60)
        print("✅ 所有测试完成!")
        print(f"⏱️  总耗时: {duration:.2f} 秒")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)