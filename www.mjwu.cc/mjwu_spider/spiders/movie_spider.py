#!/usr/bin/env python3
"""电影爬虫"""

import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.base_spider import BaseSpider
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class MovieSpider(BaseSpider):
    """电影爬虫"""
    
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
                CREATE INDEX IF NOT EXISTS idx_movies_category ON movies(category);
            """)
    
    def parse_list_page(self, soup):
        """解析列表页，返回电影列表和是否有下一页"""
        movies = []
        
        for card in soup.select('li.hl-list-item'):
            try:
                # 获取详情页链接
                link = card.select_one('a.hl-item-thumb')
                if not link:
                    continue
                
                href = link.get('href', '')
                detail_url = urljoin(self.base_url, href)
                vod_id = self.extract_vod_id(href)
                
                if not vod_id:
                    continue
                
                # 获取海报图
                poster_url = link.get('data-original', '')
                
                # 获取标题
                title = link.get('title', '').strip()
                
                # 获取状态/清晰度
                status_el = card.select_one('.hl-pic-text .remarks') or card.select_one('.hl-pic-tag span')
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
        
        # 检查是否有下一页
        has_next = bool(soup.select_one('.hl-page-wrap a[href*="/page/"]'))
        return movies, has_next
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        # 标题
        title_el = soup.select_one('.hl-data-list li:-soup-contains("片名") span') or \
                   soup.select_one('.hl-full-box li:-soup-contains("片名") span')
        if title_el:
            data['title'] = title_el.text.strip()
        
        # 评分
        score_el = soup.select_one('.hl-score-nums')
        if score_el:
            try:
                data['rating'] = float(score_el.text.strip())
            except:
                data['rating'] = 0.0
        
        # 评分次数
        rating_count_el = soup.select_one('.hl-score-data')
        if rating_count_el:
            match = re.search(r'(\d+)次评分', rating_count_el.text)
            if match:
                data['rating_count'] = int(match.group(1))
        
        # 解析信息列表
        info_items = soup.select('.hl-data-list li') or soup.select('.hl-full-box ul li')
        for li in info_items:
            text = li.text.strip()
            
            if '主演：' in text:
                actors_links = li.select('a')
                data['actors'] = ','.join(a.text.strip() for a in actors_links)
            
            elif '导演：' in text:
                director_links = li.select('a')
                data['director'] = ','.join(a.text.strip() for a in director_links)
            
            elif '类型：' in text:
                category_links = li.select('a')
                if category_links:
                    data['category'] = category_links[0].text.strip()
                    data['genre'] = ','.join(a.text.strip() for a in category_links)
            
            elif '地区：' in text:
                data['region'] = text.replace('地区：', '').strip()
            
            elif '年份：' in text:
                try:
                    # 尝试多种分隔符
                    year_str = text.replace('年份：', '').replace('年份:', '').strip()
                    data['year'] = int(year_str)
                except:
                    data['year'] = 0
        
        # 海报图
        poster_el = soup.select_one('.hl-item-thumb')
        if poster_el:
            data['poster_url'] = poster_el.get('data-original', '')
        
        # 简介
        synopsis_el = soup.select_one('li.blurb')
        if synopsis_el:
            data['synopsis'] = synopsis_el.text.replace('简介：', '').strip()[:500]
        
        # 播放链接（取第一集）
        play_link = soup.select_one('#hl-plays-list li a')
        if play_link:
            data['play_url'] = urljoin(self.base_url, play_link.get('href', ''))
        
        return data
    
    def save_movie(self, conn, movie):
        """保存电影（Upsert）"""
        conn.execute("""
            INSERT INTO movies (vod_id, title, original_title, category, genre, region, 
                               year, language, director, actors, status, rating, rating_count,
                               poster_url, detail_url, play_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title, original_title=excluded.original_title,
                category=excluded.category, genre=excluded.genre,
                region=excluded.region, year=excluded.year,
                language=excluded.language, director=excluded.director,
                actors=excluded.actors, status=excluded.status,
                rating=excluded.rating, rating_count=excluded.rating_count,
                poster_url=excluded.poster_url, play_url=excluded.play_url,
                synopsis=excluded.synopsis, updated_at=CURRENT_TIMESTAMP
        """, (
            movie.get('vod_id'), movie.get('title', ''),
            movie.get('original_title', ''), movie.get('category', ''),
            movie.get('genre', ''), movie.get('region', ''),
            movie.get('year', 0), movie.get('language', ''),
            movie.get('director', ''), movie.get('actors', ''),
            movie.get('status', ''), movie.get('rating', 0.0),
            movie.get('rating_count', 0), movie.get('poster_url', ''),
            movie.get('detail_url', ''), movie.get('play_url', ''),
            movie.get('synopsis', '')
        ))
        conn.commit()
    
    def _process_detail(self, movie):
        """线程工作函数：处理详情页"""
        try:
            detail_resp = self.request(movie['detail_url'])
            if detail_resp:
                detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                movie.update(self.parse_detail_page(detail_soup))
                return movie
        except Exception as e:
            self.logger.error(f"❌ 详情页处理失败: {movie.get('title', 'Unknown')} - {e}")
        return None

    def run(self, content_type='dianying', year_start=None, year_end=None, max_pages=None, max_items=None):
        """运行电影爬虫
        
        Args:
            content_type: 内容类型（默认dianying=电影）
            year_start: 开始年份（默认从配置读取）
            year_end: 结束年份（默认从配置读取）
            max_pages: 每年份最大页数（None=不限制）
            max_items: 最大爬取条数（None=不限制）
        """
        config = self.config['crawl']['movie']
        content_type = content_type or config.get('content_type', 'dianying')
        year_start = year_start or config.get('year_start', 1945)
        year_end = year_end or config.get('year_end', 2026)
        
        max_workers = self.config['spider'].get('concurrent_requests', 1)
        self.logger.info(f"🚀 启动 {max_workers} 个线程进行爬取")

        # 构建年份列表（倒序，从最新年份开始）
        years = list(range(year_end, year_start - 1, -1))
        
        total_count = 0
        
        for year in years:
            if max_items and total_count >= max_items:
                break

            self.logger.info(f"\n{'='*60}\n开始爬取 {year} 年电影\n{'='*60}")
            
            page = 1
            year_movies = 0
            
            while True:
                if max_pages and page > max_pages:
                    break
                if max_items and total_count >= max_items:
                    break
                
                url = self.build_list_url(content_type, page, year)
                response = self.request(url)
                
                if not response:
                    break
                
                soup = BeautifulSoup(response.text, 'lxml')
                movies, has_next = self.parse_list_page(soup)
                
                if not movies:
                    break
                
                # 并发处理详情页
                processed_movies = []
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_movie = {executor.submit(self._process_detail, m): m for m in movies}
                    
                    for future in as_completed(future_to_movie):
                        result = future.result()
                        if result:
                            processed_movies.append(result)
                
                # 主线程写入数据库
                with sqlite3.connect(self.db_path) as conn:
                    for movie in processed_movies:
                        if max_items and total_count >= max_items:
                            break

                        try:
                            self.save_movie(conn, movie)
                            total_count += 1
                            year_movies += 1
                            self.logger.info(f"✅ [{total_count}] {movie['title']} ({movie.get('year', 'N/A')}) - {movie.get('status', '')}")
                            
                        except Exception as e:
                            self.logger.error(f"❌ 保存失败: {movie.get('title', 'Unknown')} - {e}")
                
                if not has_next:
                    break
                page += 1
            
            self.logger.info(f"{year}年共爬取 {year_movies} 部电影")
        
        self.logger.info(f"\n🎉 电影爬取完成！共 {total_count} 部")
        return total_count
