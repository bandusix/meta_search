#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
97韩剧 - 电视剧爬虫模块
"""

import re
import sqlite3
import logging
import concurrent.futures
from .movie_spider import MovieSpider, BASE_URL
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class TVSpider(MovieSpider):
    """电视剧爬虫"""
    
    def _init_db(self):
        """初始化电视剧表"""
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
                    season INTEGER DEFAULT 1,
                    total_episodes INTEGER,
                    current_episode INTEGER,
                    rating REAL DEFAULT 0.0,
                    update_time TEXT DEFAULT '',
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    synopsis TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tv_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER NOT NULL,
                    episode_number INTEGER NOT NULL,
                    episode_title TEXT DEFAULT '',
                    play_url TEXT NOT NULL,
                    play_line_name TEXT DEFAULT '',
                    player_page_url TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vod_id, episode_number, play_line_name)
                );
                
                CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
                CREATE INDEX IF NOT EXISTS idx_tv_episodes_vod_id ON tv_episodes(vod_id);
            """)
    
    def parse_detail_page(self, soup):
        """解析详情页（电视剧专用）"""
        data = super().parse_detail_page(soup)
        
        episodes = []
        
        # 查找所有播放列表 (stui-content__playlist)
        # 页面可能包含多个播放线路
        playlists = soup.find_all('ul', class_='stui-content__playlist')
        
        # 查找对应的线路名称
        # 通常线路名称在 ul 前面的 h3 或者其他标签里，或者 stui-vodlist__head
        # 这里简化处理：尝试查找所有的线路容器
        
        # 97han结构通常是: 
        # <div class="stui-pannel__head bottom-line clearfix"> ... <h3 class="title">播放线路1</h3> ... </div>
        # <ul class="stui-content__playlist ..."> ... </ul>
        
        playlist_containers = soup.find_all('div', class_='stui-pannel__head')
        
        # 如果找不到标准的头部，尝试直接遍历所有 playlist
        if not playlists:
            return data
            
        for i, playlist in enumerate(playlists):
            # 尝试获取线路名称
            line_name = f"默认线路"
            
            # 尝试向上查找最近的 head
            parent = playlist.find_parent('div', class_='stui-pannel')
            if parent:
                head = parent.find('div', class_='stui-pannel__head')
                if head:
                    title_tag = head.find('h3', class_='title')
                    if title_tag:
                        line_name = title_tag.text.strip()
            
            # 如果是备用线路，可能没有明确的 title，用索引区分
            if line_name == "默认线路" and len(playlists) > 1:
                line_name = f"线路{i+1}"

            episode_links = playlist.find_all('a', href=re.compile(r'/Play/\d+-\d+-\d+\.html'))
            
            for link in episode_links:
                ep_text = link.text.strip()
                ep_href = link.get('href', '')
                full_play_url = urljoin(BASE_URL, ep_href)
                
                # 提取集数编号
                ep_match = re.search(r'第(\d+)期|第(\d+)集', ep_text)
                if ep_match:
                    ep_num = int(ep_match.group(1) or ep_match.group(2))
                else:
                    # 尝试从文本中直接提取数字
                    num_match = re.search(r'(\d+)', ep_text)
                    ep_num = int(num_match.group(1)) if num_match else 0
                
                episodes.append({
                    'episode_number': ep_num,
                    'episode_title': ep_text,
                    'play_url': full_play_url,     # 具体的m3u8或mp4地址 (需要二次解析，但这里先存播放页地址)
                    'play_line_name': line_name,   # 播放路线名称
                    'player_page_url': full_play_url # 网页播放器所在的页面 (即点击后的页面)
                })
        
        # 去重：同一线路同一集数去重
        unique_episodes = []
        seen = set()
        
        for ep in episodes:
            key = (ep['play_line_name'], ep['episode_number'])
            if key not in seen:
                seen.add(key)
                unique_episodes.append(ep)
        
        # 排序
        unique_episodes.sort(key=lambda x: (x['play_line_name'], x['episode_number']))
        
        data['episodes'] = unique_episodes
        
        # 计算总集数 (取集数最多的线路)
        if unique_episodes:
            max_eps = 0
            line_counts = {}
            for ep in unique_episodes:
                line = ep['play_line_name']
                line_counts[line] = line_counts.get(line, 0) + 1
            
            if line_counts:
                data['total_episodes'] = max(line_counts.values())
        
        return data
    
    def save_tv_series(self, conn, series, episodes):
        """保存电视剧及集数"""
        # 保存剧集信息
        conn.execute("""
            INSERT INTO tv_series (vod_id, title, original_title, category, type, region, year,
                                  language, director, actors, status, season, total_episodes, current_episode,
                                  rating, update_time, poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                season=excluded.season,
                total_episodes=excluded.total_episodes,
                current_episode=excluded.current_episode,
                rating=excluded.rating,
                update_time=excluded.update_time,
                poster_url=excluded.poster_url,
                synopsis=excluded.synopsis,
                updated_at=CURRENT_TIMESTAMP
        """, (
            series.get('vod_id'), series.get('title', ''),
            series.get('original_title'), series.get('category', ''),
            series.get('type', ''), series.get('region', ''),
            series.get('year', 0), series.get('language', ''),
            series.get('director', ''), series.get('actors', ''),
            series.get('status', ''), series.get('season', 1),
            series.get('total_episodes'), series.get('current_episode'),
            series.get('rating', 0.0), series.get('update_time', ''),
            series.get('poster_url', ''), series.get('detail_url', ''),
            series.get('synopsis', '')
        ))
        
        # 保存集数信息
        for ep in episodes:
            conn.execute("""
                INSERT INTO tv_episodes (vod_id, episode_number, episode_title, play_url, play_line_name, player_page_url)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(vod_id, episode_number, play_line_name) DO UPDATE SET
                    episode_title=excluded.episode_title,
                    play_url=excluded.play_url,
                    player_page_url=excluded.player_page_url
            """, (
                series.get('vod_id'), ep.get('episode_number', 0),
                ep.get('episode_title', ''), ep.get('play_url', ''),
                ep.get('play_line_name', ''), ep.get('player_page_url', '')
            ))
        
        conn.commit()

    def fetch_detail(self, series):
        """Worker function to fetch TV details"""
        try:
            # 详情页
            detail_resp = self.request(series['detail_url'])
            if detail_resp:
                detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                series.update(self.parse_detail_page(detail_soup))
                return series
        except Exception as e:
            logger.error(f"❌ 获取详情失败 [{series.get('vod_id')}]: {e}")
        return None
    
    def crawl(self, year_start=1945, year_end=2026, max_pages=None, max_episodes=None, start_page=1, max_workers=1, cid=2, category_name="电视剧"):
        """
        爬取电视剧及相关分类
        """
        
        page = start_page
        total_series = 0
        total_episodes = 0
        
        logger.info(f"🚀 开始爬取{category_name} (CID={cid})，使用 {max_workers} 个线程...")
        
        while True:
            if max_pages and page > start_page + max_pages - 1:
                break
            
            url = self.build_list_url(cid, page)
            logger.info(f"正在爬取第 {page} 页: {url}")
            
            response = self.request(url)
            
            if not response:
                break
            
            soup = BeautifulSoup(response.text, 'lxml')
            series_list, has_next = self.parse_list_page(soup)
            
            if not series_list:
                break
            
            # 使用线程池并发抓取详情页
            fetched_series = []
            if max_workers > 1:
                with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_series = {executor.submit(self.fetch_detail, series): series for series in series_list}
                    for future in concurrent.futures.as_completed(future_to_series):
                        series = future.result()
                        if series:
                            fetched_series.append(series)
            else:
                for series in series_list:
                    s = self.fetch_detail(series)
                    if s:
                        fetched_series.append(s)

            # 串行保存到数据库
            if fetched_series:
                with sqlite3.connect(self.db_path) as conn:
                    for series in fetched_series:
                        try:
                            # 过滤年份
                            if year_start <= series.get('year', 0) <= year_end:
                                series['category'] = category_name # 使用传入的分类名称
                                
                                # 应用集数限制
                                episodes = series.pop('episodes', [])
                                if max_episodes:
                                    episodes = episodes[:max_episodes]
                                
                                self.save_tv_series(conn, series, episodes)
                                
                                total_series += 1
                                total_episodes += len(episodes)
                                logger.info(f"✅ [{total_series}] {series['title']} ({len(episodes)}集)")
                        except Exception as e:
                            logger.error(f"❌ 保存失败: {e}")
            
            if not has_next:
                # 针对特定分类的尾页判断增强
                if cid == 3 and page < 111: # 综艺
                     page += 1
                     continue
                if cid == 4 and page < 238: # 动漫
                     page += 1
                     continue
                if cid == 30 and page < 319: # 短剧
                     page += 1
                     continue
                if cid == 36 and page < 177: # 伦理MV
                     page += 1
                     continue
                break
                
            page += 1
        
        logger.info(f"\n🎉 {category_name}爬取完成！共 {total_series} 部，{total_episodes} 集")
        return total_series, total_episodes
