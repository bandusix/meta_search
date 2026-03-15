#!/usr/bin/env python3
"""电影爬虫"""

import re
import sqlite3
from core.base_spider import BaseSpider
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class MovieSpider(BaseSpider):
    """电影爬虫"""
    
    # 电影分类ID映射
    # 新域名下: 电影=20
    MOVIE_CATEGORY_IDS = {20}
    
    def _init_database(self):
        """初始化电影表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    original_title TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    genre TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    language TEXT DEFAULT '',
                    director TEXT DEFAULT '',
                    actors TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    rating REAL DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    play_url TEXT DEFAULT '',
                    synopsis TEXT DEFAULT '',
                    duration TEXT DEFAULT '',
                    release_date TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
                CREATE INDEX IF NOT EXISTS idx_movies_category ON movies(category);
            """)
    
    def parse_list_page(self, soup):
        """解析列表页，返回电影列表和下一页URL"""
        movies = []
        
        # 适配 jbljc.com 的结构
        # 结构可能类似于: .module-item
        # 尝试查找包含详情页链接的卡片
        
        # 通用查找策略: 找包含 /voddetail/ 的链接
        # 避免找到导航栏链接
        
        # jbljc.com 可能是 mac cms 模板
        # 常见结构 .module-item, .list-item, .vod-item
        
        # 打印一下结构辅助调试 (仅首次)
        # print(soup.prettify()[:1000])
        
        # 尝试匹配常见的列表项
        items = soup.select('.module-item') or soup.select('.list-item') or soup.select('.vod-item') or soup.select('li.col-md-2')
        
        if not items:
            # 宽泛匹配: 查找所有指向详情页的图片链接
            links = soup.select('a[href*="/voddetail/"]')
            # 过滤掉非封面图链接 (通常封面图会有 img 子元素)
            items = [link.parent for link in links if link.find('img')]
            
        for item in items:
            try:
                # 获取链接
                link = item.find('a', href=re.compile(r'/voddetail/'))
                if not link:
                    link = item if item.name == 'a' else None
                
                if not link:
                    continue
                
                href = link.get('href', '')
                detail_url = urljoin(self.base_url, href)
                vod_id = self.extract_vod_id(href)
                
                if not vod_id:
                    continue
                
                # 获取标题
                title = link.get('title', '').strip()
                if not title:
                    # 尝试从下方文字获取
                    title_el = item.select_one('.module-poster-item-title') or item.select_one('.video-name')
                    if title_el:
                        title = title_el.text.strip()
                
                # 获取海报图
                img = link.select_one('img')
                poster_url = img.get('data-original', '') or img.get('src', '') if img else ''
                if poster_url.startswith('//'):
                    poster_url = 'https:' + poster_url
                
                # 获取状态/清晰度
                status_el = item.select_one('.module-item-note') or item.select_one('.video-serial')
                status = status_el.text.strip() if status_el else ''
                
                movies.append({
                    'vod_id': vod_id,
                    'title': title,
                    'poster_url': poster_url,
                    'detail_url': detail_url,
                    'status': status,
                })
            except Exception as e:
                self.logger.error(f"解析卡片失败: {e}")
        
        # 获取下一页链接
        next_url = None
        # 查找 text="下一页" 的链接
        next_page = soup.find('a', string=lambda text: text and ('下一页' in text or '>' in text))
        if next_page:
            href = next_page.get('href')
            if href and href != '#' and href != 'javascript:;':
                next_url = urljoin(self.base_url, href)
        
        return movies, next_url
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        # 标题
        title_el = soup.select_one('h1') or soup.select_one('.module-info-heading')
        if title_el:
            data['title'] = title_el.text.strip()
        
        # 提取信息
        # jbljc.com 可能的结构: .module-info-item
        
        # 尝试通用提取: 查找包含特定关键词的元素
        
        # 年份
        year_el = soup.find('a', href=re.compile(r'/date/|/year/'))
        if year_el and year_el.text.isdigit():
            data['year'] = int(year_el.text)
            
        # 地区
        region_el = soup.find('a', href=re.compile(r'/area/|/region/'))
        if region_el:
            data['region'] = region_el.text.strip()
            
        # 类型
        type_el = soup.find('a', href=re.compile(r'/vodtype/'))
        if type_el:
            data['category'] = type_el.text.strip()
            
        # 简介
        desc_el = soup.select_one('.module-info-introduction-content') or soup.select_one('.video-info-content')
        if desc_el:
            data['synopsis'] = desc_el.text.strip()[:500]
            
        # 播放链接
        play_link = soup.select_one('a[href*="/vodplay/"]')
        if play_link:
            data['play_url'] = urljoin(self.base_url, play_link.get('href', ''))
        
        return data
    
    def save_movie(self, conn, movie):
        """保存电影（Upsert）"""
        conn.execute("""
            INSERT INTO movies (vod_id, title, original_title, category, genre, region, 
                               year, language, director, actors, status, rating, rating_count,
                               poster_url, detail_url, play_url, synopsis, duration, release_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title, original_title=excluded.original_title,
                category=excluded.category, genre=excluded.genre,
                region=excluded.region, year=excluded.year,
                language=excluded.language, director=excluded.director,
                actors=excluded.actors, status=excluded.status,
                rating=excluded.rating, rating_count=excluded.rating_count,
                poster_url=excluded.poster_url, play_url=excluded.play_url,
                synopsis=excluded.synopsis, duration=excluded.duration,
                release_date=excluded.release_date, updated_at=CURRENT_TIMESTAMP
        """, (
            movie.get('vod_id'), movie.get('title', ''),
            movie.get('original_title', ''), movie.get('category', ''),
            movie.get('genre', ''), movie.get('region', ''),
            movie.get('year', 0), movie.get('language', ''),
            movie.get('director', ''), movie.get('actors', ''),
            movie.get('status', ''), movie.get('rating', 0.0),
            movie.get('rating_count', 0), movie.get('poster_url', ''),
            movie.get('detail_url', ''), movie.get('play_url', ''),
            movie.get('synopsis', ''), movie.get('duration', ''),
            movie.get('release_date', '')
        ))
        conn.commit()
    
    def run(self, category_id=20, year_start=None, year_end=None, max_pages=None, max_items=None, start_page=1):
        """运行电影爬虫"""
        config = self.config['crawl']['movie']
        category_id = category_id or config['category_id']
        # 确保使用新域名的正确分类ID (电影=20)
        if category_id == 1: 
            category_id = 20
            
        year_start = year_start or config.get('year_start', 1945)
        year_end = year_end or config.get('year_end', 2026)
        
        self.logger.info(f"\n{'='*60}\n开始爬取电影 (分类ID: {category_id})\n{'='*60}")
        
        page = start_page
        total_count = 0
        url = self.build_list_url(category_id, page) 
        
        while True:
            if max_pages and page > max_pages:
                break
            
            self.logger.info(f"正在爬取第 {page} 页: {url}")
            response = self.request(url)
            
            if not response:
                break
            
            soup = BeautifulSoup(response.text, 'lxml')
            movies, next_url = self.parse_list_page(soup)
            
            if not movies:
                self.logger.warning(f"页面无数据: {url}")
                break
            
            with sqlite3.connect(self.db_path) as conn:
                for movie in movies:
                    try:
                        # 详情页
                        detail_resp = self.request(movie['detail_url'])
                        if detail_resp:
                            detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                            detail_data = self.parse_detail_page(detail_soup)
                            movie.update(detail_data)
                        
                        self.save_movie(conn, movie)
                        total_count += 1
                        self.logger.info(f"✅ [{total_count}] {movie['title']} ({movie.get('year', 'N/A')}) - {movie.get('status', '')}")
                        
                        if max_items and total_count >= max_items:
                            self.logger.info(f"达到最大数量限制: {max_items}")
                            return total_count
                        
                    except Exception as e:
                        self.logger.error(f"❌ 处理失败: {movie.get('title', 'Unknown')} - {e}")
            
            if not next_url:
                self.logger.info("没有下一页")
                break
            
            page += 1
            url = next_url
            
            if max_items and total_count >= max_items:
                break
        
        self.logger.info(f"\n🎉 电影爬取完成！共 {total_count} 部")
        return total_count
