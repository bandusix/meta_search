#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
97韩剧 - 电影爬虫模块
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

# 配置
BASE_URL = "http://www.97han.com"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
DEFAULT_DELAY = (3, 5)  # Slow requests: 3-5 seconds delay

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MovieSpider:
    """电影爬虫"""
    
    def __init__(self, db_path='spider.db', delay=DEFAULT_DELAY):
        self.db_path = db_path
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': IPHONE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        })
        self._init_db()
    
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
            """)
    
    def request(self, url, max_retries=3):
        """发送HTTP请求"""
        full_url = url if url.startswith('http') else urljoin(BASE_URL, url)
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(full_url, timeout=15)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    time.sleep(random.uniform(*self.delay))
                    return response
                elif response.status_code == 404:
                    logger.warning(f"页面不存在: {full_url}")
                    return None
                else:
                    logger.warning(f"HTTP {response.status_code}: {full_url}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"请求错误 ({attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3, 6))
        
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
            if page == 1:
                return f"{BASE_URL}/type/{cid}.html"
            return f"{BASE_URL}/type/{cid}-{page}.html"
    
    @staticmethod
    def extract_vod_id(url):
        """从URL中提取视频ID"""
        match = re.search(r'/(?:detail|Play|html)/(\d+)', url)
        return int(match.group(1)) if match else None
    
    def parse_list_page(self, soup):
        """解析列表页"""
        movies = []
        seen_ids = set()
        
        # Match /detail/ OR /html/ links
        links = soup.find_all('a', href=re.compile(r'/(?:detail|html)/\d+\.html'))
        
        for link in links:
            try:
                href = link.get('href', '')
                vod_id = self.extract_vod_id(href)
                
                if not vod_id or vod_id in seen_ids:
                    continue
                
                seen_ids.add(vod_id)
                detail_url = urljoin(BASE_URL, href)
                
                title = link.text.strip()
                
                # 提取评分和状态
                parent = link.find_parent()
                rating = 0.0
                status = ""
                
                if parent:
                    spans = parent.find_all('span')
                    for span in spans:
                        text = span.text.strip()
                        if '分' in text:
                            try:
                                rating = float(text.replace('分', ''))
                            except:
                                pass
                        elif any(k in text for k in ['HD', '完结', '集', '更新', '正片', '高清']):
                            status = text
                
                movies.append({
                    'vod_id': vod_id,
                    'title': title,
                    'rating': rating,
                    'status': status,
                    'detail_url': detail_url,
                })
                
            except Exception as e:
                logger.error(f"解析卡片失败: {e}")
        
        # 检查是否有下一页
        has_next = bool(soup.find('a', string='下一页'))
        
        return movies, has_next
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        # 标题 - 优先查找带有title类的h1，或者stui-content__detail下的h1
        title = soup.find('h1', class_='title')
        if not title:
            detail_div = soup.find('div', class_='stui-content__detail')
            if detail_div:
                title = detail_div.find('h1')
        
        # 如果还是没找到，尝试查找非logo的h1
        if not title:
            for h in soup.find_all('h1'):
                classes = h.get('class', [])
                if 'logo' not in classes and 'mlogo' not in classes:
                    title = h
                    break
                    
        data['title'] = title.text.strip() if title else ''
        
        # 获取所有文本内容
        content = soup.get_text()
        
        # 提取评分
        rating_match = re.search(r'(\d+\.?\d*)分', content)
        if rating_match:
            try:
                data['rating'] = float(rating_match.group(1))
            except:
                pass
        
        # 提取类型
        type_match = re.search(r'类型[：:]([^\n]+)', content)
        if type_match:
            data['type'] = type_match.group(1).strip()
        
        # 提取地区
        region_match = re.search(r'地区[：:]([^\n]+)', content)
        if region_match:
            data['region'] = region_match.group(1).strip()
        
        # 提取年份
        year_match = re.search(r'年份[：:](\d{4})', content)
        if year_match:
            data['year'] = int(year_match.group(1))
        
        # 提取语言
        language_match = re.search(r'语言[：:]([^\n]+)', content)
        if language_match:
            data['language'] = language_match.group(1).strip()
        
        # 提取导演
        director_match = re.search(r'导演[：:]([^\n]+)', content)
        if director_match:
            data['director'] = director_match.group(1).strip()
        
        # 提取主演
        actors_match = re.search(r'主演[：:]([^\n]+)', content)
        if actors_match:
            data['actors'] = actors_match.group(1).strip()
        
        # 提取更新时间
        update_match = re.search(r'更新[：:]([^\n]+)', content)
        if update_match:
            data['update_time'] = update_match.group(1).strip()
        
        # 提取简介
        desc = soup.find('div', class_='stui-content__desc')
        if desc:
            data['synopsis'] = desc.text.strip()[:500]
            
        return data
    
    def save_movie(self, conn, movie):
        """保存电影（Upsert）"""
        conn.execute("""
            INSERT INTO movies (vod_id, title, original_title, category, type, region, year,
                               language, director, actors, status, rating, update_time,
                               poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title,
                original_title=excluded.original_title,
                category=excluded.category,
                type=excluded.type,
                region=excluded.region,
                year=excluded.year,
                language=excluded.language,
                director=excluded.director,
                actors=excluded.actors,
                status=excluded.status,
                rating=excluded.rating,
                update_time=excluded.update_time,
                poster_url=excluded.poster_url,
                synopsis=excluded.synopsis,
                updated_at=CURRENT_TIMESTAMP
        """, (
            movie.get('vod_id'), movie.get('title', ''),
            movie.get('original_title'), movie.get('category', ''),
            movie.get('type', ''), movie.get('region', ''),
            movie.get('year', 0), movie.get('language', ''),
            movie.get('director', ''), movie.get('actors', ''),
            movie.get('status', ''), movie.get('rating', 0.0),
            movie.get('update_time', ''), movie.get('poster_url', ''),
            movie.get('detail_url', ''), movie.get('synopsis', '')
        ))
        conn.commit()

    def fetch_detail(self, movie):
        """Worker function to fetch movie details"""
        try:
            # 详情页
            detail_resp = self.request(movie['detail_url'])
            if detail_resp:
                detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                movie.update(self.parse_detail_page(detail_soup))
                return movie
        except Exception as e:
            logger.error(f"❌ 获取详情失败 [{movie.get('vod_id')}]: {e}")
        return None
    
    def crawl(self, year_start=1945, year_end=2026, max_pages=None, start_page=1, max_workers=1, cid=1):
        """
        爬取电影
        
        参数:
            year_start: 开始年份
            year_end: 结束年份
            max_pages: 最大页数
            start_page: 起始页码
            max_workers: 线程数
            cid: 分类ID
        """
        
        page = start_page
        total_count = 0
        
        logger.info(f"🚀 开始爬取分类[{cid}]，使用 {max_workers} 个线程...")
        
        while True:
            if max_pages and page > start_page + max_pages - 1:
                break
            
            url = self.build_list_url(cid, page)
            logger.info(f"正在爬取第 {page} 页: {url}")
            
            response = self.request(url)
            
            if not response:
                # 针对电影分类的特殊处理：如果404，可能是因为到了尾页，但也可能只是中间页缺失
                # 用户提示电影有1027页，所以我们不应该轻易break，除非连续多次404
                if cid == 1 and page < 1027:
                     logger.warning(f"页面 {url} 返回 404，尝试下一页...")
                     page += 1
                     continue
                break
            
            soup = BeautifulSoup(response.text, 'lxml')
            movies, has_next = self.parse_list_page(soup)
            
            if not movies:
                if cid == 1 and page < 1027: # 同上，针对电影分类的容错
                    logger.warning(f"页面 {url} 解析无数据，尝试下一页...")
                    page += 1
                    continue
                break
            
            # 使用线程池并发抓取详情页
            fetched_movies = []
            if max_workers > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_movie = {executor.submit(self.fetch_detail, movie): movie for movie in movies}
                    for future in concurrent.futures.as_completed(future_to_movie):
                        movie = future.result()
                        if movie:
                            fetched_movies.append(movie)
            else:
                for movie in movies:
                    m = self.fetch_detail(movie)
                    if m:
                        fetched_movies.append(m)

            # 串行保存到数据库
            if fetched_movies:
                with sqlite3.connect(self.db_path) as conn:
                    for movie in fetched_movies:
                        try:
                            # 过滤年份
                            if year_start <= movie.get('year', 0) <= year_end:
                                movie['category'] = '电影'
                                self.save_movie(conn, movie)
                                total_count += 1
                                logger.info(f"✅ [{total_count}] {movie['title']} ({movie.get('year', 'N/A')})")
                        except Exception as e:
                            logger.error(f"❌ 保存失败: {e}")
            
            if not has_next and not (cid == 1 and page < 1027): # 电影分页可能没有下一页按钮
                break
            page += 1
        
        logger.info(f"\n🎉 爬取完成！共 {total_count} 部")
        return total_count
