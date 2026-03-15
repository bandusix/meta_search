#!/usr/bin/env python3
"""电视剧爬虫"""

import re
import json
import sqlite3
from core.base_spider import BaseSpider
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class TVSpider(BaseSpider):
    """电视剧爬虫"""
    
    # 电视剧分类ID映射
    # 新域名下: 电视剧=28
    TV_CATEGORY_IDS = {28}
    
    def _init_database(self):
        """初始化电视剧表"""
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
                    duration TEXT DEFAULT '',
                    release_date TEXT DEFAULT '',
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
                    UNIQUE(vod_id, season_number, episode_number, source_index)
                );
                
                CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
                CREATE INDEX IF NOT EXISTS idx_tv_series_year ON tv_series(year);
                CREATE INDEX IF NOT EXISTS idx_tv_episodes_vod_id ON tv_episodes(vod_id);
            """)
    
    def parse_status(self, status_text):
        """解析状态文本，提取集数信息"""
        result = {'total_episodes': None, 'current_episode': None}
        
        if not status_text:
            return result
        
        # 全XX集 / 第XX集完结
        full_match = re.search(r'[全第](\d+)集[完结]?', status_text)
        if full_match:
            result['total_episodes'] = int(full_match.group(1))
            result['current_episode'] = result['total_episodes']
            return result
        
        # 已完结
        if '完结' in status_text or '已完结' in status_text:
            result['total_episodes'] = result.get('current_episode')
        
        # 连载中 / 更新至XX集
        update_match = re.search(r'更新至[第]?(\d+)集', status_text)
        if update_match:
            result['current_episode'] = int(update_match.group(1))
        
        return result
    
    def parse_list_page(self, soup):
        """解析列表页"""
        tv_series = []
        
        # 适配 jbljc.com 的结构
        # 尝试匹配常见的列表项
        items = soup.select('.module-item') or soup.select('.list-item') or soup.select('.vod-item') or soup.select('li.col-md-2')
        
        if not items:
            links = soup.select('a[href*="/voddetail/"]')
            items = [link.parent for link in links if link.find('img')]
            
        for item in items:
            try:
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
                
                title = link.get('title', '').strip()
                if not title:
                    title_el = item.select_one('.module-poster-item-title') or item.select_one('.video-name')
                    if title_el:
                        title = title_el.text.strip()
                
                img = link.select_one('img')
                poster_url = img.get('data-original', '') or img.get('src', '') if img else ''
                if poster_url.startswith('//'):
                    poster_url = 'https:' + poster_url
                
                status_el = item.select_one('.module-item-note') or item.select_one('.video-serial')
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
        
        next_url = None
        next_page = soup.find('a', string=lambda text: text and ('下一页' in text or '>' in text))
        if next_page:
            href = next_page.get('href')
            if href and href != '#' and href != 'javascript:;':
                next_url = urljoin(self.base_url, href)
        
        return tv_series, next_url
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        title_el = soup.select_one('h1') or soup.select_one('.module-info-heading')
        if title_el:
            data['title'] = title_el.text.strip()
        
        # 提取信息
        year_el = soup.find('a', href=re.compile(r'/date/|/year/'))
        if year_el and year_el.text.isdigit():
            data['year'] = int(year_el.text)
            
        region_el = soup.find('a', href=re.compile(r'/area/|/region/'))
        if region_el:
            data['region'] = region_el.text.strip()
            
        type_el = soup.find('a', href=re.compile(r'/vodtype/'))
        if type_el:
            data['category'] = type_el.text.strip()
            
        # 状态
        # 尝试查找包含状态信息的元素
        # jbljc 可能在 .module-info-item 中
        
        desc_el = soup.select_one('.module-info-introduction-content') or soup.select_one('.video-info-content')
        if desc_el:
            data['synopsis'] = desc_el.text.strip()[:500]
        
        return data
    
    def parse_episodes(self, soup, vod_id):
        """解析剧集列表"""
        episodes = []
        
        # 策略1: 查找 ul.stui-content__playlist (jbljc.com)
        playlists = soup.select('ul.stui-content__playlist')
        
        if playlists:
            for idx, playlist in enumerate(playlists):
                source_name = f"线路{idx+1}"
                source_index = idx + 1
                links = playlist.select('a')
                for link in links:
                    self._parse_single_episode(link, vod_id, source_name, source_index, episodes)
        else:
            # 策略2: 通用查找
            # 获取所有集数链接
            playlist = soup.select('.module-play-list-content a') or soup.select('.playlist a')
            for link in playlist:
                self._parse_single_episode(link, vod_id, "默认线路", 1, episodes)
                
        return episodes

    def _parse_single_episode(self, link, vod_id, source_name, source_index, episodes):
        try:
            href = link.get('href', '')
            play_url = urljoin(self.base_url, href)
            episode_title = link.text.strip()
            
            # 提取集数编号
            episode_match = re.search(r'第(\d+)集', episode_title)
            if episode_match:
                episode_number = int(episode_match.group(1))
            elif episode_title.isdigit():
                episode_number = int(episode_title)
            else:
                # 尝试从 URL 提取
                url_match = re.search(r'-(\d+)\.html', href)
                episode_number = int(url_match.group(1)) if url_match else 0
            
            episodes.append({
                'vod_id': vod_id,
                'episode_number': episode_number,
                'episode_title': episode_title,
                'play_url': play_url,
                'source_name': source_name,
                'source_index': source_index,
                'season_number': 1,
            })
        except Exception as e:
            self.logger.error(f"解析单集失败: {e}")

    def parse_play_page(self, html):
        """解析播放页，提取真实播放地址"""
        script_pattern = r'var player_aaaa=(\{.*?\});'
        match = re.search(script_pattern, html, re.DOTALL)
        if match:
            try:
                player_data = json.loads(match.group(1))
                return player_data.get('url')
            except:
                pass
        return None

    def save_tv_series(self, conn, series):
        """保存电视剧主表"""
        conn.execute("""
            INSERT INTO tv_series (vod_id, title, original_title, category, genre, region, 
                                  year, language, director, actors, status, 
                                  total_episodes, current_episode, rating, rating_count,
                                  poster_url, detail_url, synopsis, duration, release_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                duration=excluded.duration, release_date=excluded.release_date,
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
            series.get('detail_url', ''), series.get('synopsis', ''),
            series.get('duration', ''), series.get('release_date', '')
        ))
        conn.commit()
    
    def save_episodes(self, conn, episodes):
        """保存剧集"""
        for ep in episodes:
            conn.execute("""
                INSERT INTO tv_episodes (vod_id, season_number, episode_number, 
                                        episode_title, play_url, video_url, source_name, source_index)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vod_id, season_number, episode_number, source_index) DO UPDATE SET
                    episode_title=excluded.episode_title,
                    play_url=excluded.play_url,
                    video_url=excluded.video_url,
                    source_name=excluded.source_name,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                ep['vod_id'], ep['season_number'], ep['episode_number'],
                ep['episode_title'], ep['play_url'], ep.get('video_url', ''), ep['source_name'], ep['source_index']
            ))
        conn.commit()
    
    def run(self, category_id=28, year_start=None, year_end=None, max_pages=None, max_episodes=None, max_items=None, start_page=1):
        """运行电视剧爬虫"""
        config = self.config['crawl']['tv']
        category_id = category_id or config['category_id']
        # 确保使用新域名的正确分类ID (电视剧=28)
        if category_id == 2:
            category_id = 28
            
        year_start = year_start or config.get('year_start', 1945)
        year_end = year_end or config.get('year_end', 2026)
        max_episodes = max_episodes or config.get('max_episodes')
        
        self.logger.info(f"\n{'='*60}\n开始爬取电视剧 (分类ID: {category_id})\n{'='*60}")
        
        page = start_page
        total_series = 0
        total_episodes = 0
        url = self.build_list_url(category_id, page)
        
        while True:
            if max_pages and page > max_pages:
                break
            
            self.logger.info(f"正在爬取第 {page} 页: {url}")
            response = self.request(url)
            
            if not response:
                break
            
            soup = BeautifulSoup(response.text, 'lxml')
            series_list, next_url = self.parse_list_page(soup)
            
            if not series_list:
                self.logger.warning(f"页面无数据: {url}")
                break
            
            with sqlite3.connect(self.db_path) as conn:
                for series in series_list:
                    try:
                        # 1. 详情页
                        detail_resp = self.request(series['detail_url'])
                        if detail_resp:
                            detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                            series.update(self.parse_detail_page(detail_soup))
                            
                            # 解析剧集
                            episodes = self.parse_episodes(detail_soup, series['vod_id'])
                            
                            # 限制集数
                            if max_episodes and len(episodes) > max_episodes:
                                episodes = episodes[:max_episodes]
                            
                            # 保存剧集
                            if episodes:
                                self.save_episodes(conn, episodes)
                                total_episodes += len(episodes)
                                series['total_episodes'] = len(episodes)
                        
                        # 保存电视剧主表
                        self.save_tv_series(conn, series)
                        total_series += 1
                        
                        ep_info = f"({len(episodes)}集)" if series.get('total_episodes') else ""
                        self.logger.info(f"✅ [{total_series}] {series['title']} {ep_info} - {series.get('status', '')}")
                        
                        if max_items and total_series >= max_items:
                            self.logger.info(f"达到最大数量限制: {max_items}")
                            return total_series, total_episodes
                        
                    except Exception as e:
                        self.logger.error(f"❌ 处理失败: {series.get('title', 'Unknown')} - {e}")
            
            if not next_url:
                self.logger.info("没有下一页")
                break
            
            page += 1
            url = next_url
            
            if max_items and total_series >= max_items:
                break
        
        self.logger.info(f"\n🎉 电视剧爬取完成！共 {total_series} 部，{total_episodes} 集")
        return total_series, total_episodes
