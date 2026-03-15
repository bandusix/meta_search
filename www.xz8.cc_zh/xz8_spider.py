import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import random
import re
import sqlite3
import pandas as pd
import os
from datetime import datetime

class MediaRepository:
    def __init__(self, db_path='xz8_media.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                play_url TEXT UNIQUE NOT NULL,
                detail_url TEXT,
                title TEXT NOT NULL,
                poster_url TEXT,
                year INTEGER,
                category TEXT,
                category_id INTEGER,
                genre TEXT,
                region TEXT,
                director TEXT,
                actors TEXT,
                status TEXT,
                quality TEXT,
                is_series BOOLEAN DEFAULT 0,
                episode_name TEXT,
                episode_num INTEGER,
                total_episodes INTEGER,
                source_name TEXT,
                source_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_play_url ON media_resources(play_url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_detail_url ON media_resources(detail_url)') # Added index for detail_url
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON media_resources(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON media_resources(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON media_resources(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_genre ON media_resources(genre)')
        
        conn.commit()
        conn.close()
    
    def is_detail_crawled(self, detail_url):
        """检查详情页是否已爬取"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT 1 FROM media_resources WHERE detail_url = ? LIMIT 1', (detail_url,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def insert_or_ignore(self, media_data):
        """插入数据，基于play_url自动去重"""
        conn = sqlite3.connect(self.db_path, timeout=30)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO media_resources (
                    play_url, detail_url, title, poster_url, year,
                    category, category_id, genre, region, director, actors,
                    status, quality, is_series, episode_name, episode_num,
                    total_episodes, source_name, source_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                media_data['play_url'],
                media_data.get('detail_url', ''),
                media_data['title'],
                media_data.get('poster_url', ''),
                media_data.get('year'),
                media_data.get('category'),
                media_data.get('category_id'),
                media_data.get('genre'),
                media_data.get('region'),
                media_data.get('director'),
                media_data.get('actors'),
                media_data.get('status'),
                media_data.get('quality'),
                media_data.get('is_series', False),
                media_data.get('episode_name'),
                media_data.get('episode_num'),
                media_data.get('total_episodes'),
                media_data.get('source_name'),
                media_data.get('source_id')
            ))
            
            conn.commit()
            return cursor.rowcount  # 返回插入行数（0表示已存在）
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0
        finally:
            conn.close()

import json

class XZ8Spider:
    """
    xz8.cc 多线程爬虫
    支持按年份、分类爬取，自动翻页，多线程并发
    支持断点续爬（记录每个分类的爬取页码）
    """
    
    BASE_URL = "https://www.xz8.cc"
    
    # 分类配置
    CATEGORIES = {
        'movie': {'id': 1, 'name': '电影', 'is_series': False},
        'tv': {'id': 2, 'name': '剧集', 'is_series': True},
        'variety': {'id': 3, 'name': '综艺', 'is_series': True},
        'anime': {'id': 4, 'name': '动漫', 'is_series': True},
    }
    
    def __init__(self, db_path='xz8_media.db', state_file='spider_state.json', max_workers=10, delay=(0.5, 1.5)):
        """
        初始化爬虫
        
        Args:
            db_path: 数据库路径
            state_file: 状态文件路径（用于记录爬取进度）
            max_workers: 最大线程数 (5-100)
            delay: 请求延迟范围 (min, max)秒
        """
        self.db = MediaRepository(db_path)
        self.state_file = state_file
        self.max_workers = max_workers
        self.delay = delay
        self.session = self._create_session()
        self.lock = threading.Lock()
        self.stats = {'processed': 0, 'inserted': 0, 'failed': 0, 'skipped': 0}
        self.state = self._load_state()
    
    def _load_state(self):
        """加载爬取状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_state(self):
        """保存爬取状态"""
        with self.lock:
            try:
                with open(self.state_file, 'w', encoding='utf-8') as f:
                    json.dump(self.state, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"Failed to save state: {e}")

    def _create_session(self):
        """创建请求会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            # 'Accept-Encoding': 'gzip, deflate, br', # Remove br if brotli is not installed
        })
        return session
    
    def fetch(self, url, retries=3):
        """发送请求并解析HTML（带延迟和重试）"""
        for i in range(retries):
            time.sleep(random.uniform(*self.delay))
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code != 200:
                    print(f"Fetch failed: {url}, status code: {response.status_code}")
                    continue
                response.encoding = 'utf-8'
                return BeautifulSoup(response.text, 'lxml')
            except Exception as e:
                print(f"Fetch error (attempt {i+1}): {url}, {e}")
                time.sleep(2)
        return None
    
    def crawl_category(self, category, max_pages=None, max_items=None):
        """
        爬取整个分类（不按年份筛选）
        支持断点续爬：自动从上次记录的页码开始
        """
        if category not in self.CATEGORIES:
            print(f"Error: Invalid category {category}")
            return

        cat_config = self.CATEGORIES[category]
        cat_id = cat_config['id']
        is_series = cat_config['is_series']
        
        # Determine start page from state
        start_page = self.state.get(category, 1)
        print(f"开始爬取 [{cat_config['name']}] 从第 {start_page} 页开始...")
        
        page = start_page
        while True:
            # Check manual limit if provided
            if max_pages and page >= start_page + max_pages:
                print(f"  Reached max pages limit for this run ({max_pages}). Stopping.")
                break
            
            # 正确的分页URL格式
            list_url = f"{self.BASE_URL}/vodshow/{cat_id}--------{page}---/"
            
            print(f"    Fetching list page {page}: {list_url}")
            items = self._parse_list_page(list_url)
            
            if not items:
                print(f"    No items found on page {page}. Stopping.")
                break
            
            # Filter items that are already crawled
            new_items = []
            for item in items:
                if self.db.is_detail_crawled(item['detail_url']):
                    self._update_stats(skipped=1)
                else:
                    new_items.append(item)
            
            if not new_items:
                print(f"    All {len(items)} items on page {page} already crawled. Moving to next page.")
                # Update state even if all skipped, to avoid rescanning this page next time
                self.state[category] = page + 1
                self._save_state()
                page += 1
                continue

            print(f"    Found {len(items)} items, {len(new_items)} new. Processing details...")
            
            # 多线程处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._process_detail, item, category, cat_id, is_series): item 
                    for item in new_items
                }
                
                for future in as_completed(futures):
                    item = futures[future]
                    try:
                        result = future.result()
                        if result:
                            print(f"      > Processed: {item['title']} (Added {result} playlists)")
                            self._update_stats(inserted=result)
                        else:
                            print(f"      ! Skipped/Empty: {item['title']}")
                    except Exception as e:
                        print(f"      X Error processing {item['title']}: {e}")
                        self._update_stats(failed=1)
            
            # Update state after finishing page
            self.state[category] = page + 1
            self._save_state()
            
            total_processed = self.stats['processed'] + self.stats['skipped']
            if max_items and total_processed >= max_items:
                print(f"  已达到最大数量限制: {max_items} (Processed: {self.stats['processed']}, Skipped: {self.stats['skipped']})")
                break
            
            page += 1
        
        print(f"爬取完成: {self.stats}")

    def crawl_all(self, max_pages_per_cat=None, max_items_per_cat=None):
        """
        爬取所有分类
        """
        for cat_key in self.CATEGORIES:
            self.crawl_category(cat_key, max_pages=max_pages_per_cat, max_items=max_items_per_cat)

    def _parse_list_page(self, url):
        """解析列表页，返回视频项列表"""
        soup = self.fetch(url)
        if not soup:
            return []
        
        items = []
        # Update: Use .module-items .module-item (a tag)
        elements = soup.select('.module-items .module-item')
        
        for item in elements:
            try:
                title = item.get('title', '')
                detail_href = item.get('href', '')
                if not detail_href:
                    continue
                
                detail_url = urljoin(self.BASE_URL, detail_href)
                
                # Poster
                poster_div = item.select_one('.module-item-pic img')
                poster_url = ''
                if poster_div:
                    poster_url = poster_div.get('data-original') or poster_div.get('src', '')
                    poster_url = urljoin(self.BASE_URL, poster_url)
                
                # Status
                status_div = item.select_one('.module-item-note')
                status = status_div.text.strip() if status_div else ''
                
                items.append({
                    'title': title,
                    'detail_url': detail_url,
                    'poster_url': poster_url,
                    'status': status,
                })
            except Exception as e:
                print(f"Error parsing item: {e}")
                continue
        
        return items
    
    def _process_detail(self, item, category, category_id, is_series):
        """
        处理详情页，提取所有播放详情页URL并保存
        """
        soup = self.fetch(item['detail_url'])
        if not soup:
            return 0
        
        # 提取元数据
        # .module-info-item usually contains text like "导演：XXX"
        # .module-info-tag-link a contains Year, Region, Genre
        
        year = None
        region = ''
        genre = ''
        
        tags = soup.select('.module-info-tag-link a')
        for tag in tags:
            text = tag.text.strip()
            if text.isdigit() and len(text) == 4:
                year = int(text)
            elif not region: # Assume first non-year is region
                region = text
            else:
                genre += text + ','
        genre = genre.strip(',')
        
        director = ''
        actors = ''
        remarks = ''
        
        # Parse module-info-items for Director and Actors
        for info_item in soup.select('.module-info-item'):
            text = info_item.text.strip()
            if '导演：' in text:
                director = text.replace('导演：', '').strip()
            elif '主演：' in text:
                actors = text.replace('主演：', '').strip()
            elif '备注：' in text:
                remarks = text.replace('备注：', '').strip()
        
        # Determine Status
        # Priority: Remarks > List Page Status
        final_status = remarks if remarks else item['status']
        
        # Determine Quality
        # Logic: 
        # 1. If status contains quality keywords (e.g. HD, BD), use it.
        # 2. For movies, if episode_name (link text) contains quality, use it.
        # 3. Otherwise leave empty.
        quality = ''
        quality_keywords = ['4K', '1080P', '720P', 'HD', 'BD', 'TC', 'TS', 'CAM', '高清', '蓝光', '正片', '抢先版']
        
        for kw in quality_keywords:
            if kw in final_status.upper():
                quality = final_status
                break
        
        info = {
            'title': item['title'],
            'detail_url': item['detail_url'],
            'poster_url': item['poster_url'],
            'year': year,
            'category': category,
            'category_id': category_id,
            'genre': genre,
            'region': region,
            'director': director,
            'actors': actors,
            'status': final_status,
            'quality': quality,
            'is_series': is_series,
        }
        
        # 提取播放详情页URL列表
        inserted_count = 0
        
        # Tabs: .module-tab-item
        # Playlists: .module-play-list
        
        tabs = soup.select('.module-tab-item')
        playlists = soup.select('.module-play-list')
        
        # If tabs exist, match with playlists
        # If no tabs but playlist exists (rare), handle it
        
        if not tabs and playlists:
             # Default source
             tabs = [{'text': '默认源'}] # Mock object
        
        for source_idx, playlist_div in enumerate(playlists):
            source_name = "默认源"
            if source_idx < len(tabs):
                # Check if tabs is a list of BeautifulSoup elements or mock dicts
                if isinstance(tabs[source_idx], dict):
                    source_name = tabs[source_idx]['text']
                else:
                    source_name = tabs[source_idx].text.strip() # .module-tab-item has data-dropdown-value attr too
            
            # Links inside playlist
            links = playlist_div.select('a')
            for ep_idx, ep_link in enumerate(links):
                episode_name = ep_link.text.strip()
                href = ep_link.get('href', '')
                if not href:
                    continue
                    
                play_url = urljoin(self.BASE_URL, href)
                
                # Check quality from episode name if not already set
                current_quality = info['quality']
                if not current_quality:
                    for kw in quality_keywords:
                        if kw in episode_name.upper():
                            current_quality = kw
                            break
                
                # 提取集数
                episode_num = self._extract_episode_num(episode_name)
                
                # 构建完整数据
                media_data = {
                    **info,
                    'play_url': play_url,
                    'episode_name': episode_name,
                    'episode_num': episode_num,
                    'quality': current_quality,
                    'source_name': source_name,
                    'source_id': source_idx + 1,
                }
                
                # 插入数据库（自动去重）
                inserted = self.db.insert_or_ignore(media_data)
                inserted_count += inserted
        
        with self.lock:
            self.stats['processed'] += 1
            
        return inserted_count
    
    def _extract_episode_num(self, episode_name):
        """提取集数编号"""
        match = re.search(r'第(\d+)集', episode_name)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)', episode_name)
        if match:
            return int(match.group(1))
        return None
    
    def _update_stats(self, inserted=0, failed=0, skipped=0):
        """更新统计信息"""
        with self.lock:
            self.stats['inserted'] += inserted
            self.stats['failed'] += failed
            self.stats['skipped'] += skipped

class DataExporter:
    def __init__(self, db_path='xz8_media.db', output_dir='output'):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_full(self, format='xlsx'):
        """
        全量导出所有数据
        """
        conn = sqlite3.connect(self.db_path)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"media_resources_full_{timestamp}.{format}"
        filepath = os.path.join(self.output_dir, filename)
        
        print("Reading data from database...")
        # 读取所有数据
        df = pd.read_sql_query('SELECT * FROM media_resources ORDER BY created_at DESC', conn)
        
        if df.empty:
            print("No data to export.")
            conn.close()
            return None

        print(f"Exporting {len(df)} records to {filepath}...")
        
        # 导出
        if format == 'xlsx':
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        conn.close()
        print(f"全量导出完成: {filepath}")
        return filepath
