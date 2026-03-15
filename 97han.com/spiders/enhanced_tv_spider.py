#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版电视剧爬虫 - 集成高级日志记录和自动优化
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

class EnhancedTVSpider:
    """增强版电视剧爬虫 - 支持详细日志记录和自动优化"""
    
    def __init__(self, db_path='spider.db', delay=DEFAULT_DELAY, spider_name='tv'):
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
                CREATE TABLE IF NOT EXISTS tv_series (
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
                CREATE TABLE IF NOT EXISTS tv_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id INTEGER NOT NULL,
                    episode_number INTEGER DEFAULT 0,
                    title TEXT DEFAULT '',
                    play_line_name TEXT DEFAULT '',
                    player_page_url TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (series_id) REFERENCES tv_series (id),
                    UNIQUE(series_id, episode_number, play_line_name)
                );
                CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
                CREATE INDEX IF NOT EXISTS idx_tv_episodes_series_id ON tv_episodes(series_id);
                CREATE INDEX IF NOT EXISTS idx_tv_episodes_series_episode ON tv_episodes(series_id, episode_number);
            """)
    
    def _start_monitoring(self):
        """启动监控"""
        self.optimizer.start_monitoring()
        print(f"🚀 [{self.spider_name}] 增强版电视剧爬虫已启动 - 慢速模式({self.delay[0]}-{self.delay[1]}s延迟)")
    
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
        if cid == 2: # 电视剧
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
        series = []
        
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
                
                series = {
                    'vod_id': vod_id,
                    'title': title,
                    'detail_url': detail_url,
                    'poster_url': poster_url,
                    'year': year,
                    'category': '电视剧'
                }
                
                series.append(series)
                
            except Exception as e:
                logger.error(f"[{self.spider_name}] 解析列表项失败: {e}")
                continue
        
        return series
    
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
            
            # 提取播放线路和剧集信息
            episodes_data = self._extract_episodes(soup)
            data.update(episodes_data)
            
        except Exception as e:
            logger.error(f"[{self.spider_name}] 解析详情页失败: {e}")
        
        return data
    
    def _extract_episodes(self, soup):
        """提取剧集和播放线路信息"""
        episodes = []
        play_lines = []
        
        # 查找播放列表
        playlists = soup.find_all('ul', class_='stui-content__playlist')
        
        for playlist in playlists:
            # 提取线路名称
            line_name = '默认线路'
            prev_elem = playlist.find_previous_sibling('h3')
            if prev_elem:
                line_name = prev_elem.text.strip()
            
            play_lines.append(line_name)
            
            # 提取剧集链接
            episode_links = playlist.find_all('a')
            for link in episode_links:
                episode_url = link.get('href', '')
                episode_title = link.text.strip()
                
                # 提取集数
                episode_match = re.search(r'(\d+)', episode_title)
                episode_number = int(episode_match.group(1)) if episode_match else 0
                
                episodes.append({
                    'episode_number': episode_number,
                    'title': episode_title,
                    'play_line_name': line_name,
                    'player_page_url': episode_url
                })
        
        return {
            'episodes': episodes,
            'play_lines': play_lines,
            'play_line_name': play_lines[0] if play_lines else '',
            'player_page_url': episodes[0]['player_page_url'] if episodes else ''
        }
    
    def save_series(self, series_data):
        """保存电视剧数据（增强版）"""
        try:
            # 数据验证
            is_valid, error_msg = self.validator.validate_tv_data(series_data)
            if not is_valid:
                logger.warning(f"[{self.spider_name}] 数据验证失败: {error_msg}")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在
                cursor.execute("SELECT id FROM tv_series WHERE vod_id = ?", (series_data['vod_id'],))
                existing = cursor.fetchone()
                
                if existing:
                    logger.info(f"[{self.spider_name}] 电视剧已存在，跳过: {series_data['title']} (ID: {series_data['vod_id']})")
                    enhanced_logger.log_request_complete(
                        self.spider_name, f"duplicate_check_{series_data['vod_id']}", 200,
                        ['duplicate_check'], series_data['vod_id'], 0, 0
                    )
                    return False
                
                # 插入电视剧基本信息
                cursor.execute("""
                    INSERT INTO tv_series (
                        vod_id, title, original_title, category, type, region, 
                        year, language, director, actors, status, rating,
                        update_time, poster_url, detail_url, synopsis,
                        play_line_name, player_page_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    series_data['vod_id'],
                    series_data['title'],
                    series_data.get('original_title'),
                    series_data.get('category', '电视剧'),
                    series_data.get('type', ''),
                    series_data.get('region', ''),
                    series_data.get('year', 0),
                    series_data.get('language', ''),
                    series_data.get('director', ''),
                    series_data.get('actors', ''),
                    series_data.get('status', ''),
                    series_data.get('rating', 0.0),
                    series_data.get('update_time', ''),
                    series_data.get('poster_url', ''),
                    series_data.get('detail_url', ''),
                    series_data.get('synopsis', ''),
                    series_data.get('play_line_name', ''),
                    series_data.get('player_page_url', '')
                ))
                
                series_id = cursor.lastrowid
                
                # 保存剧集信息
                episodes = series_data.get('episodes', [])
                saved_episodes = 0
                
                for episode in episodes:
                    try:
                        cursor.execute("""
                            INSERT OR IGNORE INTO tv_episodes 
                            (series_id, episode_number, title, play_line_name, player_page_url)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            series_id,
                            episode['episode_number'],
                            episode['title'],
                            episode['play_line_name'],
                            episode['player_page_url']
                        ))
                        
                        if cursor.rowcount > 0:
                            saved_episodes += 1
                            
                    except Exception as e:
                        logger.warning(f"[{self.spider_name}] 保存剧集失败: {e}")
                
                # 记录详细保存信息
                saved_fields = list(series_data.keys())
                enhanced_logger.log_request_complete(
                    self.spider_name, f"save_series_{series_data['vod_id']}", 200,
                    saved_fields, series_data['vod_id'], saved_episodes, 0
                )
                
                logger.info(f"[{self.spider_name}] ✅ 保存成功: {series_data['title']} (ID: {series_data['vod_id']}, DB_ID: {series_id}, 剧集: {saved_episodes})")
                return True
                
        except Exception as e:
            logger.error(f"[{self.spider_name}] 保存电视剧失败: {e}")
            enhanced_logger.log_error(self.spider_name, f"save_series_{series_data.get('vod_id', 'unknown')}", 
                                    type(e).__name__, str(e))
            return False
    
    def crawl_detail_page(self, series):
        """爬取详情页（增强版）"""
        detail_url = series['detail_url']
        start_time = time.time()
        
        enhanced_logger.log_request_start(self.spider_name, detail_url)
        
        response = self.request(detail_url)
        if not response:
            return None
        
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            detail_data = self.parse_detail_page(soup)
            
            # 合并数据
            series_data = {**series, **detail_data}
            
            # 记录解析完成
            elapsed_ms = (time.time() - start_time) * 1000
            enhanced_logger.log_request_complete(
                self.spider_name, detail_url, 200,
                list(detail_data.keys()), series['vod_id'], len(detail_data.get('episodes', [])), elapsed_ms
            )
            
            return series_data
            
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
            series_list = self.parse_list_page(response.text)
            print(f"📊 [{self.spider_name}] 第 {page} 页解析到 {len(series_list)} 部电视剧")
            
            saved_count = 0
            for i, series in enumerate(series_list, 1):
                print(f"📺 [{self.spider_name}] 正在处理第 {i}/{len(series_list)} 部: {series['title']}")
                
                # 爬取详情页
                series_data = self.crawl_detail_page(series)
                if series_data:
                    # 保存数据
                    if self.save_series(series_data):
                        saved_count += 1
                
                # 显示进度
                if i % 5 == 0 or i == len(series_list):
                    print(f"📈 [{self.spider_name}] 进度: {i}/{len(series_list)} 完成, 已保存: {saved_count}")
            
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
                cursor.execute("SELECT COUNT(*) FROM tv_series")
                total_count = cursor.fetchone()[0]
                
                enhanced_logger.log_validation(self.spider_name, True, total_count)
                print(f"✅ [{self.spider_name}] 第 {page} 页数据校验完成 - 总计: {total_count} 部电视剧")
                
        except Exception as e:
            logger.error(f"[{self.spider_name}] 数据校验失败: {e}")
            enhanced_logger.log_error(self.spider_name, f"validation_page_{page}", type(e).__name__, str(e))
    
    def crawl(self, year_start=1945, year_end=2026, max_pages=None, start_page=1, max_workers=1, cid=2, category_name=None):
        """主爬取函数（增强版）"""
        # 根据分类ID确定分类名称
        if category_name is None:
            category_names = {
                2: '电视剧',
                3: '综艺',
                4: '动漫',
                30: '短剧',
                36: '伦理MV'
            }
            category_name = category_names.get(cid, '电视剧')
        
        print(f"\n🎯 [{self.spider_name}] 开始爬取{category_name}数据")
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
                
                if consecutive_empty >= max_consecutive_empty:
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
        print(f"📈 总计保存: {total_saved} 部{category_name}")
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