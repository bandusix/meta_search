#!/usr/bin/env python3
"""电视剧爬虫 - 支持季(Season)和集(Episode)两个维度"""

import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.base_spider import BaseSpider
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class TVSpider(BaseSpider):
    """电视剧爬虫
    
    支持维度：
    - 季(Season): 从标题解析（如"第二季"→2）
    - 集(Episode): 从播放列表解析（如"第01集"→1）
    - 播放源(Source): 支持多播放源（如云播、备用线路）
    """
    
    def _init_database(self):
        """初始化电视剧表"""
        self.logger.info("Initializing TV database tables...")
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tv_series (
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
                    total_episodes INTEGER,
                    current_episode INTEGER,
                    rating REAL DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    synopsis TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tv_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER NOT NULL,
                    season_number INTEGER DEFAULT 1,
                    episode_number INTEGER NOT NULL,
                    episode_title TEXT DEFAULT '',
                    play_url TEXT NOT NULL,
                    video_url TEXT DEFAULT '',
                    source_name TEXT DEFAULT '',
                    source_index INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vod_id, season_number, episode_number, source_index)
                );
                
                CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
                CREATE INDEX IF NOT EXISTS idx_tv_series_year ON tv_series(year);
                CREATE INDEX IF NOT EXISTS idx_tv_episodes_vod_id ON tv_episodes(vod_id);
            """)
    
    def parse_season_from_title(self, title):
        """从标题中解析季数
        
        Args:
            title: 剧集标题（如"乔治和曼迪的头婚生活第二季"）
        
        Returns:
            season_number: 季数（默认为1）
        """
        if not title:
            return 1
        
        # 中文格式：第X季
        season_match = re.search(r'第(\d+)季', title)
        if season_match:
            return int(season_match.group(1))
        
        # 英文格式：Season X
        season_match = re.search(r'[Ss]eason\s*(\d+)', title)
        if season_match:
            return int(season_match.group(1))
        
        # 简写格式：S1, S2...
        season_match = re.search(r'[Ss](\d+)\s*[Ee]\d+', title)
        if season_match:
            return int(season_match.group(1))
        
        return 1  # 默认第1季
    
    def parse_status(self, status_text):
        """解析状态文本，提取集数信息"""
        result = {'total_episodes': None, 'current_episode': None}
        
        if not status_text:
            return result
        
        # XX集全 / 全XX集
        full_match = re.search(r'(\d+)集全|全(\d+)集', status_text)
        if full_match:
            episodes = int(full_match.group(1) or full_match.group(2))
            result['total_episodes'] = episodes
            result['current_episode'] = episodes
            return result
        
        # 连载中 / 更新至XX集
        update_match = re.search(r'更新至[第]?(\d+)集', status_text)
        if update_match:
            result['current_episode'] = int(update_match.group(1))
        
        return result
    
    def parse_list_page(self, soup):
        """解析列表页"""
        tv_series = []
        
        for card in soup.select('li.hl-list-item'):
            try:
                link = card.select_one('a.hl-item-thumb')
                if not link:
                    continue
                
                href = link.get('href', '')
                detail_url = urljoin(self.base_url, href)
                vod_id = self.extract_vod_id(href)
                
                if not vod_id:
                    continue
                
                poster_url = link.get('data-original', '')
                title = link.get('title', '').strip()
                
                # 获取状态/清晰度
                status_el = card.select_one('.hl-pic-text .remarks') or card.select_one('.hl-pic-tag span')
                status = status_el.text.strip() if status_el else ''
                
                tv_series.append({
                    'vod_id': vod_id,
                    'title': title,
                    'poster_url': poster_url,
                    'detail_url': detail_url,
                    'status': status,
                })
            except Exception as e:
                self.logger.error(f"解析卡片失败: {e}")
        
        has_next = bool(soup.select_one('.hl-page-wrap a[href*="/page/"]'))
        return tv_series, has_next
    
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
                pass
        
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
        
        # 从标题中解析季数
        data['season_number'] = self.parse_season_from_title(data.get('title', ''))
        
        return data
    
    def parse_episodes(self, soup, vod_id, season_number=1):
        """解析剧集列表（支持多播放源）
        
        Args:
            soup: BeautifulSoup对象
            vod_id: 视频ID
            season_number: 季数（从标题解析得到）
        
        Returns:
            episodes: 剧集列表，包含季、集、播放源信息
        """
        episodes = []
        
        # 获取所有播放源
        source_tabs = soup.select('.hl-plays-from li')
        
        # 如果没有播放源标签，直接使用默认播放源
        if not source_tabs:
            source_tabs = [{'name': '云播', 'index': 1}]
        
        for source_idx, source_tab in enumerate(source_tabs, 1):
            # 获取播放源名称
            if isinstance(source_tab, dict): # Handle default case
                source_name = source_tab['name']
                source_index = source_tab['index']
            else:
                source_name_el = source_tab.select_one('span')
                source_name = source_name_el.text.strip() if source_name_el else f'播放源{source_idx}'
                
                # 获取播放源编号（从data-href中提取）
                data_href = source_tab.get('data-href', '')
                source_match = re.search(r'/play/\d+-(\d+)-\d+/', data_href)
                source_index = int(source_match.group(1)) if source_match else source_idx
            
            # 获取当前播放源的集数列表
            # 注意：美剧屋的集数列表是动态加载的，所有播放源共享同一个#hl-plays-list
            # 需要点击不同播放源来切换集数列表
            # 这里我们解析当前显示的集数列表
            playlist = soup.select('#hl-plays-list li a')
            
            for link in playlist:
                try:
                    href = link.get('href', '')
                    play_url = urljoin(self.base_url, href)
                    episode_title = link.text.strip()
                    
                    # 提取集数编号（支持"第01集"、"第1集"等格式）
                    episode_match = re.search(r'第(\d+)集', episode_title)
                    episode_number = int(episode_match.group(1)) if episode_match else 0
                    
                    # 从URL中提取source_index进行验证
                    url_match = re.search(r'/play/\d+-(\d+)-(\d+)/', href)
                    if url_match:
                        url_source_index = int(url_match.group(1))
                        url_episode = int(url_match.group(2))
                        # 如果URL中的episode与解析的一致，使用URL中的source_index
                        if url_episode == episode_number:
                            source_index = url_source_index
                    
                    episodes.append({
                        'vod_id': vod_id,
                        'season_number': season_number,  # 从标题解析的季数
                        'episode_number': episode_number,  # 从集数标题解析
                        'episode_title': episode_title,
                        'play_url': play_url,
                        'source_name': source_name,
                        'source_index': source_index,
                    })
                except Exception as e:
                    self.logger.error(f"解析剧集失败: {e}")
        
        return episodes
    
    def save_tv_series(self, conn, series):
        """保存电视剧主表"""
        conn.execute("""
            INSERT INTO tv_series (vod_id, title, original_title, category, genre, region, 
                                  year, language, director, actors, status, 
                                  total_episodes, current_episode, rating, rating_count,
                                  poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title, original_title=excluded.original_title,
                category=excluded.category, genre=excluded.genre,
                region=excluded.region, year=excluded.year,
                language=excluded.language, director=excluded.director,
                actors=excluded.actors, status=excluded.status,
                total_episodes=excluded.total_episodes, 
                current_episode=excluded.current_episode,
                rating=excluded.rating, rating_count=excluded.rating_count,
                poster_url=excluded.poster_url, synopsis=excluded.synopsis,
                updated_at=CURRENT_TIMESTAMP
        """, (
            series.get('vod_id'), series.get('title', ''),
            series.get('original_title', ''), series.get('category', ''),
            series.get('genre', ''), series.get('region', ''),
            series.get('year', 0), series.get('language', ''),
            series.get('director', ''), series.get('actors', ''),
            series.get('status', ''), series.get('total_episodes'),
            series.get('current_episode'), series.get('rating', 0.0),
            series.get('rating_count', 0), series.get('poster_url', ''),
            series.get('detail_url', ''), series.get('synopsis', '')
        ))
        conn.commit()
    
    def save_episodes(self, conn, episodes):
        """保存剧集"""
        for ep in episodes:
            conn.execute("""
                INSERT INTO tv_episodes (vod_id, season_number, episode_number, 
                                        episode_title, play_url, source_name, source_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vod_id, season_number, episode_number, source_index) DO UPDATE SET
                    episode_title=excluded.episode_title,
                    play_url=excluded.play_url,
                    source_name=excluded.source_name,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                ep['vod_id'], ep['season_number'], ep['episode_number'],
                ep['episode_title'], ep['play_url'], ep['source_name'], ep['source_index']
            ))
        conn.commit()
    
    def _process_detail(self, series, max_episodes):
        """线程工作函数：处理详情页"""
        try:
            detail_resp = self.request(series['detail_url'])
            if detail_resp:
                detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                series.update(self.parse_detail_page(detail_soup))
                
                # 获取季数（从标题解析）
                season_number = series.get('season_number', 1)
                
                # 解析剧集（传入季数）
                episodes = self.parse_episodes(detail_soup, series['vod_id'], season_number)
                
                # 限制集数
                if max_episodes and len(episodes) > max_episodes:
                    episodes = episodes[:max_episodes]
                
                return series, episodes
        except Exception as e:
            self.logger.error(f"❌ 详情页处理失败: {series.get('title', 'Unknown')} - {e}")
        return None, None

    def run(self, content_type='meiju', year_start=None, year_end=None, max_pages=None, max_episodes=None, max_items=None):
        """运行电视剧爬虫
        
        Args:
            content_type: 内容类型（默认meiju=美剧）
            year_start: 开始年份
            year_end: 结束年份
            max_pages: 每年份最大页数
            max_episodes: 每部剧最大集数限制
            max_items: 最大爬取剧集数（None=不限制）
        """
        config = self.config['crawl']['tv']
        content_type = content_type or config.get('content_type', 'meiju')
        year_start = year_start or config.get('year_start', 1945)
        year_end = year_end or config.get('year_end', 2026)
        max_episodes = max_episodes or config.get('max_episodes')
        
        max_workers = self.config['spider'].get('concurrent_requests', 1)
        self.logger.info(f"🚀 启动 {max_workers} 个线程进行爬取")

        # 构建年份列表（倒序）
        years = list(range(year_end, year_start - 1, -1))
        
        total_series = 0
        total_episodes = 0
        
        for year in years:
            if max_items and total_series >= max_items:
                break

            self.logger.info(f"\n{'='*60}\n开始爬取 {year} 年电视剧\n{'='*60}")
            
            page = 1
            year_series = 0
            
            while True:
                if max_pages and page > max_pages:
                    break
                if max_items and total_series >= max_items:
                    break
                
                url = self.build_list_url(content_type, page, year)
                response = self.request(url)
                
                if not response:
                    break
                
                soup = BeautifulSoup(response.text, 'lxml')
                series_list, has_next = self.parse_list_page(soup)
                
                if not series_list:
                    break
                
                # 并发处理详情页
                processed_results = []
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_series = {executor.submit(self._process_detail, s, max_episodes): s for s in series_list}
                    
                    for future in as_completed(future_to_series):
                        series_result, episodes_result = future.result()
                        if series_result:
                            processed_results.append((series_result, episodes_result))
                
                # 主线程写入数据库
                with sqlite3.connect(self.db_path) as conn:
                    for series, episodes in processed_results:
                        if max_items and total_series >= max_items:
                            break

                        try:
                            # 保存剧集
                            if episodes:
                                self.save_episodes(conn, episodes)
                                total_episodes += len(episodes)
                                series['total_episodes'] = len(episodes)
                            
                            # 保存电视剧主表
                            self.save_tv_series(conn, series)
                            total_series += 1
                            year_series += 1
                            
                            ep_info = f"({len(episodes)}集)" if series.get('total_episodes') else ""
                            self.logger.info(f"✅ [{total_series}] {series['title']} {ep_info} - {series.get('status', '')}")
                            
                        except Exception as e:
                            self.logger.error(f"❌ 保存失败: {series.get('title', 'Unknown')} - {e}")
                
                if not has_next:
                    break
                page += 1
            
            self.logger.info(f"{year}年共爬取 {year_series} 部电视剧")
        
        self.logger.info(f"\n🎉 电视剧爬取完成！共 {total_series} 部，{total_episodes} 集")
        return total_series, total_episodes
