#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主爬虫协调器 - 统一管理和调度所有爬取任务
"""

import asyncio
import logging
import logging.handlers
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import lxml.html
from collections import deque
from urllib.parse import urljoin, urlparse

from database import DatabaseManager
from async_crawler import AsyncCrawler, ParserUtils, URLGenerator
from tv_parser import parse_tv_list as tv_parse_list, parse_tv_detail as tv_parse_detail

# 配置日志
@dataclass
class CrawlConfig:
    """爬取配置"""
    max_concurrent: int = 30
    delay_ms: int = 200
    batch_size: int = 50
    commit_batch_size: int = 200
    max_retries: int = 3
    timeout: int = 30
    
    # 分类配置
    categories = {
        'movie': {'start_page': 1, 'end_page': 1027, 'type': 'movie'},
        'tv': {'start_page': 1, 'end_page': 549, 'type': 'tv'},
        'variety': {'start_page': 1, 'end_page': 111, 'type': 'tv'},
        'anime': {'start_page': 1, 'end_page': 238, 'type': 'tv'},
        'short': {'start_page': 1, 'end_page': 319, 'type': 'tv'},
        'mv': {'start_page': 1, 'end_page': 177, 'type': 'tv'}
    }

class CrawlStats:
    """爬取统计"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.total_pages = 0
        self.success_pages = 0
        self.failed_pages = 0
        self.total_items = 0
        self.success_items = 0
        self.failed_items = 0
        self.retry_count = 0
        self.error_types = {}
    
    def get_summary(self) -> Dict:
        """获取统计摘要"""
        duration = (datetime.now() - self.start_time).total_seconds() / 3600  # 小时
        
        return {
            'duration_hours': round(duration, 2),
            'total_pages': self.total_pages,
            'success_pages': self.success_pages,
            'failed_pages': self.failed_pages,
            'page_success_rate': round(self.success_pages / max(self.total_pages, 1) * 100, 2),
            'total_items': self.total_items,
            'success_items': self.success_items,
            'failed_items': self.failed_items,
            'item_success_rate': round(self.success_items / max(self.total_items, 1) * 100, 2),
            'retry_count': self.retry_count,
            'error_types': self.error_types
        }

class OptimizedCrawler:
    """优化版爬虫主类"""
    
    def __init__(self, config: CrawlConfig = None):
        self.config = config or CrawlConfig()
        self.db = DatabaseManager("optimized_crawler.db")
        self.stats = CrawlStats()
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志系统"""
        # 创建logs目录
        os.makedirs("logs", exist_ok=True)
        
        # 根日志器配置
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器（每日滚动，保留7天）
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename="logs/crawler.log",
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 错误日志处理器
        error_handler = logging.handlers.TimedRotatingFileHandler(
            filename="logs/crawler_error.log",
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("🚀 优化版爬虫日志系统初始化完成")
    
    async def crawl_category(self, category: str, start_page: int, end_page: int, content_type: str):
        """爬取单个分类"""
        self.logger.info(f"🎯 开始爬取分类: {category} (页码: {start_page}-{end_page})")
        
        # 生成URL列表
        if content_type == 'movie':
            urls = URLGenerator.generate_movie_urls(start_page, end_page)
        else:
            urls = URLGenerator.generate_tv_urls(category, start_page, end_page)
        
        # 分批处理
        total_batches = (len(urls) + self.config.batch_size - 1) // self.config.batch_size
        
        async with AsyncCrawler(
            max_concurrent=self.config.max_concurrent,
            delay_ms=self.config.delay_ms,
            timeout=self.config.timeout
        ) as crawler:
            
            failed_page_urls: List[str] = []
            for batch_idx in range(total_batches):
                start_idx = batch_idx * self.config.batch_size
                end_idx = min(start_idx + self.config.batch_size, len(urls))
                batch_urls = urls[start_idx:end_idx]
                
                self.logger.info(f"📦 处理批次 {batch_idx + 1}/{total_batches} (URL数: {len(batch_urls)})")
                
                # 批量获取页面内容
                contents = await crawler.fetch_batch(batch_urls)
                
                # 解析和处理内容
                all_items = []
                for url, content in zip(batch_urls, contents):
                    self.stats.total_pages += 1
                    
                    if content is None:
                        self.stats.failed_pages += 1
                        failed_page_urls.append(url)
                        self.logger.warning(f"❌ 页面获取失败: {url}")
                        continue
                    
                    self.stats.success_pages += 1
                    
                    # 解析列表页面
                    if content_type == 'movie':
                        items = ParserUtils.parse_movie_list(content, url)
                    else:
                        items = tv_parse_list(content, url)
                    
                    self.stats.total_items += len(items)
                    all_items.extend(items)
                    
                    self.logger.info(f"✅ 解析成功: {url} - 找到 {len(items)} 个项目")
                
                # 批量处理详情页
                if all_items:
                    await self._process_detail_pages(crawler, all_items, category, content_type)
                
                # 更新数据库元数据
                self.db.update_metadata(
                    category=category,
                    total_pages=end_page - start_page + 1,
                    current_page=end_idx,
                    items_found=self.stats.total_items,
                    status='running'
                )
                
                self.logger.info(f"📊 批次 {batch_idx + 1} 完成 - 累计处理: {self.stats.total_items} 个项目")
            
            if failed_page_urls:
                self.logger.warning(f"🔁 分类 {category} 累计失败页面 {len(failed_page_urls)}，开始重试")
                recovered = await self._retry_failed_pages(crawler, failed_page_urls, category, content_type)
                self.logger.info(f"🔁 分类 {category} 重试完成，恢复成功 {recovered} 页")
        
        # 标记完成
        self.db.update_metadata(
            category=category,
            total_pages=end_page - start_page + 1,
            current_page=end_page,
            items_found=self.stats.total_items,
            status='completed'
        )
        
        self.logger.info(f"✅ 分类 {category} 爬取完成")

    async def _retry_failed_pages(self, crawler: AsyncCrawler, failed_urls: List[str], category: str, content_type: str) -> int:
        remaining = list(dict.fromkeys(failed_urls))
        recovered_total = 0
        max_rounds = 3
        chunk_size = min(self.config.batch_size, 30)
        
        for round_idx in range(max_rounds):
            if not remaining:
                break
            
            self.logger.warning(f"🔁 失败页重试轮次 {round_idx + 1}/{max_rounds}，待重试 {len(remaining)} 页")
            next_remaining: List[str] = []
            
            for offset in range(0, len(remaining), chunk_size):
                chunk = remaining[offset:offset + chunk_size]
                tasks = []
                for i, url in enumerate(chunk):
                    prefer_family = "android" if ((i + round_idx) % 2 == 0) else "iphone"
                    tasks.append(
                        crawler.fetch_with_retry(
                            url,
                            extra_delay_ms=500 + round_idx * 300,
                            prefer_family=prefer_family,
                        )
                    )
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for url, content in zip(chunk, results):
                    if isinstance(content, Exception) or content is None:
                        next_remaining.append(url)
                        continue
                    
                    recovered_total += 1
                    if self.stats.failed_pages > 0:
                        self.stats.failed_pages -= 1
                    self.stats.success_pages += 1
                    
                    if content_type == "movie":
                        items = ParserUtils.parse_movie_list(content, url)
                    else:
                        items = tv_parse_list(content, url)
                    
                    self.stats.total_items += len(items)
                    if items:
                        await self._process_detail_pages(crawler, items, category=category, content_type=content_type)
            
            self.stats.retry_count += len(remaining)
            remaining = next_remaining
        
        if remaining:
            self.logger.warning(f"🔁 失败页重试结束，仍失败 {len(remaining)} 页")
        
        return recovered_total
    
    async def _process_detail_pages(self, crawler: AsyncCrawler, items: List[Dict], category: str, content_type: str):
        """批量处理详情页"""
        self.logger.info(f"🔍 开始处理 {len(items)} 个详情页")
        
        # 获取详情页URL
        detail_urls = [item['detail_url'] for item in items if item.get('detail_url')]
        
        # 批量获取详情页内容
        detail_contents = await crawler.fetch_batch(detail_urls)
        
        # 解析详情页并提取播放线路
        all_movies = []
        all_episodes = []
        
        for item, content in zip(items, detail_contents):
            if content is None:
                self.stats.failed_items += 1
                continue
            
            try:
                # 解析详情页
                if content_type == 'movie':
                    detail_info = ParserUtils.parse_movie_detail(content, item['detail_url'])
                else:
                    detail_info = tv_parse_detail(content, item['detail_url'])
                
                if content_type == 'movie':
                    # 处理电影数据
                    for play_line in detail_info.get('play_lines', []):
                        movie_data = {
                            'category': category,
                            'title': detail_info.get('title', item.get('title', '')),
                            'cover': item.get('cover', ''),
                            'year': detail_info.get('year'),
                            'region': detail_info.get('region', ''),
                            'genre': detail_info.get('genre', ''),
                            'intro': detail_info.get('intro', ''),
                            'detail_url': item['detail_url'],
                            'route_name': play_line['route_name'],
                            'play_url': play_line['play_url']
                        }
                        all_movies.append(movie_data)
                
                else:
                    # 处理电视剧数据
                    series_data = {
                        'category': category,
                        'title': detail_info.get('title', item.get('title', '')),
                        'cover': item.get('cover', ''),
                        'year': detail_info.get('year'),
                        'region': detail_info.get('region', ''),
                        'genre': detail_info.get('genre', ''),
                        'intro': detail_info.get('intro', ''),
                        'detail_url': item['detail_url'],
                        'total_episodes': len(detail_info.get('play_lines', []))
                    }
                    
                    # 处理剧集数据
                    for play_line in detail_info.get('play_lines', []):
                        episode_data = {
                            'vod_id': item.get('vod_id', 0),
                            'episode_number': play_line.get('episode_number', 1),
                            'episode_title': play_line.get('episode_title', ''),
                            'route_name': play_line['route_name'],
                            'play_url': play_line['play_url']
                        }
                        all_episodes.append(episode_data)
                
                self.stats.success_items += 1
                
            except Exception as e:
                self.stats.failed_items += 1
                self.logger.error(f"❌ 解析详情页失败: {item['detail_url']} - {str(e)}")
        
        # 批量插入数据库
        if all_movies:
            inserted = self.db.batch_insert_movies(all_movies)
            self.logger.info(f"💾 批量插入电影数据: {inserted} 条记录")
        
        if all_episodes:
            inserted = self.db.batch_insert_episodes(all_episodes)
            self.logger.info(f"💾 批量插入剧集数据: {inserted} 条记录")
    
    async def crawl_all_categories(self):
        """爬取所有分类"""
        self.logger.info("🚀 开始全站爬取任务")
        
        # 创建任务列表
        tasks = []
        for category, config in self.config.categories.items():
            task = self.crawl_category(
                category=category,
                start_page=config['start_page'],
                end_page=config['end_page'],
                content_type=config['type']
            )
            tasks.append(task)
        
        # 并发执行所有任务
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 输出最终统计
        summary = self.stats.get_summary()
        self.logger.info("📊 爬取任务完成统计:")
        self.logger.info(f"⏱️  总耗时: {summary['duration_hours']} 小时")
        self.logger.info(f"📄 总页面数: {summary['total_pages']}")
        self.logger.info(f"✅ 成功页面: {summary['success_pages']} ({summary['page_success_rate']}%)")
        self.logger.info(f"📦 总项目数: {summary['total_items']}")
        self.logger.info(f"✅ 成功项目: {summary['success_items']} ({summary['item_success_rate']}%)")
        self.logger.info(f"🔄 重试次数: {summary['retry_count']}")
        
        # 数据库统计
        db_stats = self.db.get_statistics()
        self.logger.info("💾 数据库统计:")
        self.logger.info(f"🎬 电影总数: {db_stats.get('movies', 0)}")
        self.logger.info(f"📺 剧集总数: {db_stats.get('episodes', 0)}")
        
        # 清理数据库
        self.db.vacuum()
        
        return summary
    
    def get_progress(self) -> Dict:
        """获取当前进度"""
        return {
            'stats': self.stats.get_summary(),
            'database': self.db.get_statistics()
        }

    async def crawl_site_wide(self, strategy: str = "bfs", max_pages: int = 100000):
        base = "http://www.97han.com"
        seeds = [
            f"{base}/",
            f"{base}/show/1-----------.html",
            f"{base}/type/2.html",
            f"{base}/type/3.html",
            f"{base}/type/4.html",
            f"{base}/type/30.html",
            f"{base}/type/36.html",
        ]
        visited = set()
        q = deque(seeds) if strategy == "bfs" else list(seeds)
        domain = urlparse(base).netloc
        async with AsyncCrawler(
            max_concurrent=self.config.max_concurrent,
            delay_ms=self.config.delay_ms,
            timeout=self.config.timeout
        ) as crawler:
            processed_pages = 0
            while q and processed_pages < max_pages:
                batch = []
                while q and len(batch) < self.config.batch_size:
                    u = q.popleft() if strategy == "bfs" else q.pop()
                    if u in visited:
                        continue
                    if urlparse(u).netloc != domain:
                        continue
                    visited.add(u)
                    batch.append(u)
                if not batch:
                    break
                contents = await crawler.fetch_batch(batch)
                items_to_process: List[Dict] = []
                for url, content in zip(batch, contents):
                    processed_pages += 1
                    self.stats.total_pages += 1
                    if not content:
                        self.stats.failed_pages += 1
                        continue
                    self.stats.success_pages += 1
                    try:
                        doc = lxml.html.fromstring(content)
                        links = [urljoin(url, h) for h in doc.xpath('//a/@href') if h]
                        for link in links:
                            if link in visited:
                                continue
                            parsed = urlparse(link)
                            if parsed.netloc != domain:
                                continue
                            if any(link.endswith(ext) for ext in [".jpg", ".png", ".gif", ".css", ".js", ".ico"]):
                                continue
                            if len(q) < max_pages:
                                if strategy == "bfs":
                                    q.append(link)
                                else:
                                    q.append(link)
                        movie_items = ParserUtils.parse_movie_list(content, url)
                        tv_items = tv_parse_list(content, url)
                        if movie_items or tv_items:
                            items_to_process.extend(movie_items)
                            items_to_process.extend(tv_items)
                        else:
                            md = ParserUtils.parse_movie_detail(content, url)
                            td = tv_parse_detail(content, url)
                            if md.get("play_lines"):
                                for pl in md.get("play_lines", []):
                                    items_to_process.append({
                                        'detail_url': url,
                                        'title': md.get('title', ''),
                                        'cover': '',
                                        'year': md.get('year'),
                                        'list_detect': 'movie',
                                        'direct_detail': True
                                    })
                            elif td.get("play_lines"):
                                items_to_process.append({
                                    'detail_url': url,
                                    'title': td.get('title', ''),
                                    'cover': '',
                                    'year': td.get('year'),
                                    'list_detect': 'tv',
                                    'direct_detail': True
                                })
                    except Exception as e:
                        self.stats.failed_pages += 1
                        continue
                if items_to_process:
                    await self._process_detail_pages(crawler, items_to_process, category="site", content_type="mixed")
        return self.stats.get_summary()

# 全局实例
crawler_instance = None

def get_crawler() -> OptimizedCrawler:
    """获取爬虫实例"""
    global crawler_instance
    if crawler_instance is None:
        crawler_instance = OptimizedCrawler()
    return crawler_instance

async def main():
    """主入口函数"""
    crawler = get_crawler()
    
    try:
        mode = os.getenv("FULL_SITE_CRAWL", "").strip().lower()
        if mode in ("1", "true", "yes", "on", "bfs", "dfs"):
            strategy = "dfs" if mode == "dfs" else "bfs"
            summary = await crawler.crawl_site_wide(strategy=strategy)
        else:
            summary = await crawler.crawl_all_categories()
        
        print("\n" + "="*60)
        print("🎉 全站爬取任务完成!")
        print("="*60)
        print(f"⏱️  总耗时: {summary['duration_hours']} 小时")
        print(f"📄 总页面数: {summary['total_pages']}")
        print(f"✅ 成功页面: {summary['success_pages']} ({summary['page_success_rate']}%)")
        print(f"📦 总项目数: {summary['total_items']}")
        print(f"✅ 成功项目: {summary['success_items']} ({summary['item_success_rate']}%)")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断任务")
    except Exception as e:
        print(f"\n❌ 任务执行失败: {str(e)}")
        logging.error(f"任务执行失败: {str(e)}", exc_info=True)

if __name__ == "__main__":
    # 运行爬虫
    asyncio.run(main())
