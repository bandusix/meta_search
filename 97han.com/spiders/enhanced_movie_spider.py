#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版电影爬虫 - 集成高级日志记录和自动优化
"""

import re
import time
import random
import logging
import sqlite3
import requests
import concurrent.futures
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# 导入增强组件
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_logger import logger as enhanced_logger
from utils.data_validator import DataValidator
from utils.auto_optimizer import AutoOptimizer

# 配置
BASE_URL = "http://www.97han.com"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
DEFAULT_DELAY = (3, 5)  # Slow requests: 3-5 seconds delay

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedMovieSpider:
    """增强版电影爬虫 - 支持详细日志记录和自动优化"""
    
    def __init__(self, db_path='spider.db', delay=DEFAULT_DELAY, spider_name='movie'):
        self.db_path = db_path
        self.delay = delay
        self.spider_name = spider_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': IPHONE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        })
        
        # 初始化增强组件
        self.validator = DataValidator(db_path)
        self.optimizer = AutoOptimizer()
        self.optimizer.register_callback('optimization_applied', self._on_optimization_applied)
        
        self._init_db()
        self._start_monitoring()
    
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    original_title TEXT,
                    category TEXT DEFAULT '',
                    type TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    language TEXT DEFAULT '',
                    director TEXT DEFAULT '',
                    actors TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    rating REAL DEFAULT 0.0,
                    update_time TEXT DEFAULT '',
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    synopsis TEXT DEFAULT '',
                    play_line_name TEXT DEFAULT '',
                    player_page_url TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
            """)
    
    def _start_monitoring(self):
        """启动监控"""
        self.optimizer.start_monitoring()
        print(f"🚀 [{self.spider_name}] 增强版爬虫已启动 - 慢速模式({self.delay[0]}-{self.delay[1]}s延迟)")
    
    def _on_optimization_applied(self, data):
        """优化应用回调"""
        print(f"📊 [{self.spider_name}] 优化参数已更新: {data}")
    
    def request(self, url, max_retries=3):
        """发送HTTP请求（增强版）"""
        full_url = url if url.startswith('http') else urljoin(BASE_URL, url)
        start_time = time.time()
        
        # 记录请求开始
        enhanced_logger.log_request_start(self.spider_name, full_url)
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(full_url, timeout=15)
                response.encoding = 'utf-8'
                elapsed_ms = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    # 记录成功响应
                    enhanced_logger.log_request_complete(
                        self.spider_name, full_url, response.status_code,
                        ['html_content'], None, 1, elapsed_ms
                    )
                    
                    # 添加性能数据到优化器
                    self.optimizer.add_performance_data(elapsed_ms/1000, False, False, 1)
                    
                    time.sleep(random.uniform(*self.delay))
                    return response
                    
                elif response.status_code == 404:
                    logger.warning(f"[{self.spider_name}] 页面不存在: {full_url}")
                    enhanced_logger.log_request_complete(
                        self.spider_name, full_url, response.status_code,
                        [], None, 0, elapsed_ms
                    )
                    return None
                    
                else:
                    logger.warning(f"[{self.spider_name}] HTTP {response.status_code}: {full_url}")
                    enhanced_logger.log_request_complete(
                        self.spider_name, full_url, response.status_code,
                        [], None, 0, elapsed_ms
                    )
                    
            except requests.exceptions.RequestException as e:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"[{self.spider_name}] 请求错误 ({attempt+1}/{max_retries}): {e}")
                enhanced_logger.log_error(self.spider_name, full_url, type(e).__name__, str(e))
                
                # 添加错误性能数据
                self.optimizer.add_performance_data(elapsed_ms/1000, True, False, 0)
            
            if attempt < max_retries - 1:
                backoff_time = random.uniform(3, 6) * (attempt + 1)  # 指数退避
                print(f"⏱️  [{self.spider_name}] 等待 {backoff_time:.1f}s 后重试...")
                time.sleep(backoff_time)
        
        return None
    
    def build_list_url(self, cid, page=1):
        """构造列表页URL"""
        if cid == 1: # 电影
            base_pattern = "show/1-{page}-----------.html"
            if page == 1:
                return f"{BASE_URL}/type/1.html"
            return urljoin(BASE_URL, base_pattern.format(page=page))
        
        elif cid == 2: # 电视剧
            if page == 1:
                return f"{BASE_URL}/type/2.html"
            return f"{BASE_URL}/type/2-{page}.html"
        
        elif cid == 3: # 综艺
            if page == 1:
                return f"{BASE_URL}/type/3.html"
            return f"{BASE_URL}/type/3-{page}.html"
        
        elif cid == 4: # 动漫
            if page == 1:
                return f"{BASE_URL}/type/4.html"
            return f"{BASE_URL}/type/4-{page}.html"
        
        elif cid == 30: # 短剧
            if page == 1:
                return f"{BASE_URL}/type/30.html"
            return f"{BASE_URL}/type/30-{page}.html"
        
        elif cid == 36: # 伦理MV
            if page == 1:
                return f"{BASE_URL}/type/36.html"
            return f"{BASE_URL}/type/36-{page}.html"
        
        else:
            return f"{BASE_URL}/type/{cid}.html"
    
    def parse_list_page(self, html):
        """解析列表页"""
        soup = BeautifulSoup(html, 'html.parser')
        movies = []
        
        # 查找视频列表
        video_items = soup.find_all('div', class_='stui-vodlist__box')
        
        for item in video_items:
            try:
                # 提取基本信息
                title_elem = item.find('a', class_='stui-vodlist__thumb')
                if not title_elem:
                    continue
                
                title = title_elem.get('title', '').strip()
                detail_url = title_elem.get('href', '')
                vod_id_match = re.search(r'(\d+)\.html', detail_url)
                vod_id = int(vod_id_match.group(1)) if vod_id_match else 0
                
                # 提取其他信息
                pic_elem = title_elem.find('img')
                poster_url = pic_elem.get('data-original', '') if pic_elem else ''
                
                # 提取年份和类型
                subtitle = item.find('span', class_='pic-text')
                year_text = subtitle.text if subtitle else ''
                year_match = re.search(r'(\d{4})', year_text)
                year = int(year_match.group(1)) if year_match else 0
                
                movie = {
                    'vod_id': vod_id,
                    'title': title,
                    'detail_url': detail_url,
                    'poster_url': poster_url,
                    'year': year,
                    'category': '电影'
                }
                
                movies.append(movie)
                
            except Exception as e:
                logger.error(f"[{self.spider_name}] 解析列表项失败: {e}")
                continue
        
        return movies
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        try:
            # 提取标题
            title_elem = soup.find('h1', class_='title')
            data['title'] = title_elem.text.strip() if title_elem else ''
            
            # 提取原始标题
            orig_title_elem = soup.find('span', class_='text-muted')
            data['original_title'] = orig_title_elem.text.strip() if orig_title_elem else None
            
            # 提取详细信息
            info_elem = soup.find('div', class_='stui-content__desc')
            if info_elem:
                info_text = info_elem.text.strip()
                
                # 提取导演
                director_match = re.search(r'导演：([^\n]+)', info_text)
                data['director'] = director_match.group(1).strip() if director_match else ''
                
                # 提取演员
                actors_match = re.search(r'主演：([^\n]+)', info_text)
                data['actors'] = actors_match.group(1).strip() if actors_match else ''
                
                # 提取类型
                type_match = re.search(r'类型：([^\n]+)', info_text)
                data['type'] = type_match.group(1).strip() if type_match else ''
                
                # 提取地区
                region_match = re.search(r'地区：([^\n]+)', info_text)
                data['region'] = region_match.group(1).strip() if region_match else ''
                
                # 提取年份
                year_match = re.search(r'年份：(\d{4})', info_text)
                data['year'] = int(year_match.group(1)) if year_match else 0
                
                # 提取语言
                lang_match = re.search(r'语言：([^\n]+)', info_text)
                data['language'] = lang_match.group(1).strip() if lang_match else ''
            
            # 提取评分
            rating_elem = soup.find('span', class_='score')
            if rating_elem:
                rating_text = rating_elem.text.strip()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                data['rating'] = float(rating_match.group(1)) if rating_match else 0.0
            
            # 提取简介
            synopsis_elem = soup.find('span', class_='detail-content')
            data['synopsis'] = synopsis_elem.text.strip() if synopsis_elem else ''
            
            # 提取播放线路信息
            data.update(self._extract_play_lines(soup))
            
        except Exception as e:
            logger.error(f"[{self.spider_name}] 解析详情页失败: {e}")
        
        return data
    
    def _extract_play_lines(self, soup):
        """提取播放线路信息"""
        play_lines = []
        
        # 查找播放列表
        playlists = soup.find_all('ul', class_='stui-content__playlist')
        
        for playlist in playlists:
            # 提取线路名称
            line_name = '默认线路'
            prev_elem = playlist.find_previous_sibling('h3')
            if prev_elem:
                line_name = prev_elem.text.strip()
            
            # 提取播放链接
            play_links = playlist.find_all('a')
            for link in play_links:
                play_url = link.get('href', '')
                if play_url:
                    play_lines.append({
                        'play_line_name': line_name,
                        'player_page_url': play_url,
                        'episode_title': link.text.strip()
                    })
        
        return {
            'play_lines': play_lines,
            'play_line_name': play_lines[0]['play_line_name'] if play_lines else '',
            'player_page_url': play_lines[0]['player_page_url'] if play_lines else ''
        }
    
    def save_movie(self, movie_data):
        """保存电影数据（增强版）"""
        try:
            # 数据验证
            is_valid, error_msg = self.validator.validate_movie_data(movie_data)
            if not is_valid:
                logger.warning(f"[{self.spider_name}] 数据验证失败: {error_msg}")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在
                cursor.execute("SELECT id FROM movies WHERE vod_id = ?", (movie_data['vod_id'],))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"[{self.spider_name}] 电影已存在，跳过: {movie_data['title']} (ID: {movie_data['vod_id']})")
                    enhanced_logger.log_request_complete(
                        self.spider_name, f"duplicate_check_{movie_data['vod_id']}", 200,
                        ['duplicate_check'], movie_data['vod_id'], 0, 0
                    )
                    return False
                
                # 插入数据
                cursor.execute("""
                    INSERT INTO movies (
                        vod_id, title, original_title, category, type, region, 
                        year, language, director, actors, status, rating,
                        update_time, poster_url, detail_url, synopsis,
                        play_line_name, player_page_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    movie_data['vod_id'],
                    movie_data['title'],
                    movie_data.get('original_title'),
                    movie_data.get('category', '电影'),
                    movie_data.get('type', ''),
                    movie_data.get('region', ''),
                    movie_data.get('year', 0),
                    movie_data.get('language', ''),
                    movie_data.get('director', ''),
                    movie_data.get('actors', ''),
                    movie_data.get('status', ''),
                    movie_data.get('rating', 0.0),
                    movie_data.get('update_time', ''),
                    movie_data.get('poster_url', ''),
                    movie_data.get('detail_url', ''),
                    movie_data.get('synopsis', ''),
                    movie_data.get('play_line_name', ''),
                    movie_data.get('player_page_url', '')
                ))
                
                saved_id = cursor.lastrowid
                
                # 记录详细保存信息
                saved_fields = list(movie_data.keys())
                enhanced_logger.log_request_complete(
                    self.spider_name, f"save_movie_{movie_data['vod_id']}", 200,
                    saved_fields, movie_data['vod_id'], 1, 0
                )
                
                logger.info(f"[{self.spider_name}] ✅ 保存成功: {movie_data['title']} (ID: {movie_data['vod_id']}, DB_ID: {saved_id})")
                return True
                
        except Exception as e:
            logger.error(f"[{self.spider_name}] 保存电影失败: {e}")
            enhanced_logger.log_error(self.spider_name, f"save_movie_{movie_data.get('vod_id', 'unknown')}", 
                                    type(e).__name__, str(e))
            return False
    
    def crawl_detail_page(self, movie):
        """爬取详情页（增强版）"""
        detail_url = movie['detail_url']
        start_time = time.time()
        
        enhanced_logger.log_request_start(self.spider_name, detail_url)
        
        response = self.request(detail_url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            detail_data = self.parse_detail_page(soup)
            
            # 合并数据
            movie_data = {**movie, **detail_data}
            
            # 记录解析完成
            elapsed_ms = (time.time() - start_time) * 1000
            enhanced_logger.log_request_complete(
                self.spider_name, detail_url, 200,
                list(detail_data.keys()), movie['vod_id'], 1, elapsed_ms
            )
            
            return movie_data
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            enhanced_logger.log_error(self.spider_name, detail_url, type(e).__name__, str(e))
            logger.error(f"[{self.spider_name}] 解析详情页失败 {detail_url}: {e}")
            return None
    
    def crawl_page(self, cid, page):
        """爬取单页（增强版）"""
        url = self.build_list_url(cid, page)
        print(f"\n📄 [{self.spider_name}] 正在爬取第 {page} 页: {url}")
        
        response = self.request(url)
        if not response:
            return 0
        
        try:
            movies = self.parse_list_page(response.text)
            print(f"📊 [{self.spider_name}] 第 {page} 页解析到 {len(movies)} 部电影")
            
            saved_count = 0
            for i, movie in enumerate(movies, 1):
                print(f"🎬 [{self.spider_name}] 正在处理第 {i}/{len(movies)} 部: {movie['title']}")
                
                # 爬取详情页
                movie_data = self.crawl_detail_page(movie)
                if movie_data:
                    # 保存数据
                    if self.save_movie(movie_data):
                        saved_count += 1
                
                # 显示进度
                if i % 5 == 0 or i == len(movies):
                    print(f"📈 [{self.spider_name}] 进度: {i}/{len(movies)} 完成, 已保存: {saved_count}")
            
            # 数据校验
            self._validate_page_data(page, saved_count)
            
            return saved_count
            
        except Exception as e:
            logger.error(f"[{self.spider_name}] 爬取第 {page} 页失败: {e}")
            return 0
    
    def _validate_page_data(self, page, saved_count):
        """验证页面数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM movies")
                total_count = cursor.fetchone()[0]
                
                enhanced_logger.log_validation(self.spider_name, True, total_count)
                print(f"✅ [{self.spider_name}] 第 {page} 页数据校验完成 - 总计: {total_count} 部电影")
                
        except Exception as e:
            logger.error(f"[{self.spider_name}] 数据校验失败: {e}")
            enhanced_logger.log_error(self.spider_name, f"validation_page_{page}", type(e).__name__, str(e))
    
    def crawl(self, year_start=1945, year_end=2026, max_pages=None, start_page=1, max_workers=1, cid=1):
        """主爬取函数（增强版）"""
        print(f"\n🎯 [{self.spider_name}] 开始爬取电影数据")
        print(f"📅 年份范围: {year_start}-{year_end}")
        print(f"📄 页码范围: {start_page}-{max_pages or '全部'}")
        print(f"🧵 并发数: {max_workers}")
        print(f"⏱️  延迟设置: {self.delay[0]}-{self.delay[1]} 秒")
        print("=" * 60)
        
        total_saved = 0
        page = start_page
        consecutive_empty = 0
        max_consecutive_empty = 5
        
        while True:
            if max_pages and page > max_pages:
                print(f"\n🏁 [{self.spider_name}] 达到最大页数限制: {max_pages}")
                break
            
            # 获取当前优化配置
            current_config = enhanced_logger.get_config()
            actual_workers = min(max_workers, current_config.get('concurrency', max_workers))
            
            saved_count = self.crawl_page(cid, page)
            total_saved += saved_count
            
            # 检查是否为空页
            if saved_count == 0:
                consecutive_empty += 1
                print(f"⚠️  [{self.spider_name}] 第 {page} 页无数据 (连续 {consecutive_empty} 次)")
                
                # 针对电影分类的特殊处理
                if cid == 1 and page < 1027 and consecutive_empty < max_consecutive_empty:
                    print(f"[{self.spider_name}] 电影分类继续尝试下一页...")
                    page += 1
                    continue
                elif consecutive_empty >= max_consecutive_empty:
                    print(f"\n🏁 [{self.spider_name}] 连续 {max_consecutive_empty} 页无数据，停止爬取")
                    break
            else:
                consecutive_empty = 0
            
            # 显示统计信息
            if page % 10 == 0:
                stats = enhanced_logger.get_stats()
                print(f"\n📊 [{self.spider_name}] 爬取统计:")
                print(f"   总请求: {stats['total_requests']}")
                print(f"   失败请求: {stats['failed_requests']}")
                print(f"   重复ID: {stats['duplicate_ids']}")
                print(f"   平均响应时间: {stats['avg_response_time']:.2f}s")
                print(f"   已保存: {total_saved} 部")
            
            page += 1
            
            # 每50页休息一会儿
            if page % 50 == 0:
                rest_time = random.uniform(10, 20)
                print(f"\n☕ [{self.spider_name}] 已爬取 {page-1} 页，休息 {rest_time:.1f} 秒...")
                time.sleep(rest_time)
        
        # 最终统计
        final_stats = enhanced_logger.get_stats()
        print(f"\n🎉 [{self.spider_name}] 爬取完成!")
        print(f"📈 总计保存: {total_saved} 部电影")
        print(f"📊 总请求: {final_stats['total_requests']} | 失败: {final_stats['failed_requests']} | 重复: {final_stats['duplicate_ids']}")
        print(f"⏱️  平均响应时间: {final_stats['avg_response_time']:.2f}s")
        
        # 数据完整性最终校验
        self._final_validation()
        
        return total_saved
    
    def _final_validation(self):
        """最终数据校验"""
        try:
            print(f"\n🔍 [{self.spider_name}] 正在进行最终数据校验...")
            
            # 检查数据库重复
            movie_duplicates = self.validator.check_database_duplicates('movies', 'vod_id')
            tv_duplicates = self.validator.check_database_duplicates('tv_series', 'vod_id')
            
            print(f"📋 数据校验结果:")
            print(f"   电影表: {movie_duplicates['total_records']} 条记录, {movie_duplicates['duplicate_ids']} 个重复ID")
            print(f"   电视剧表: {tv_duplicates['total_records']} 条记录, {tv_duplicates['duplicate_ids']} 个重复ID")
            
            # 验证统计
            validation_summary = self.validator.get_validation_summary()
            enhanced_logger.log_validation(
                self.spider_name, 
                movie_duplicates['duplicate_ids'] == 0 and tv_duplicates['duplicate_ids'] == 0,
                movie_duplicates['total_records'] + tv_duplicates['total_records']
            )
            
            print(f"✅ 校验完成 - 验证检查: {validation_summary['total_checks']} 次, 发现重复: {validation_summary['duplicates_found']} 个")
            
        except Exception as e:
            logger.error(f"[{self.spider_name}] 最终校验失败: {e}")
            enhanced_logger.log_error(self.spider_name, "final_validation", type(e).__name__, str(e))
    
    def close(self):
        """关闭爬虫"""
        print(f"\n🛑 [{self.spider_name}] 正在关闭爬虫...")
        self.optimizer.stop_monitoring()
        enhanced_logger.close()
        print(f"✅ [{self.spider_name}] 爬虫已关闭")