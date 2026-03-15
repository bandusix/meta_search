#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神马午夜电影网 - 电视剧爬虫模块
"""

import re
import sqlite3
import json
import logging
import concurrent.futures
from .movie_spider import MovieSpider, BASE_URL
from bs4 import BeautifulSoup
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class TVSpider(MovieSpider):
    """电视剧爬虫"""
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS tv (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    original_title TEXT,
                    category TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    director TEXT DEFAULT '',
                    actors TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    season INTEGER DEFAULT 1,
                    total_episodes INTEGER,
                    current_episode INTEGER,
                    rating REAL DEFAULT 0.0,
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    synopsis TEXT DEFAULT '',
                    episodes TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_tv_vod_id ON tv(vod_id);
                """
            )
            try:
                conn.execute("ALTER TABLE tv ADD COLUMN episodes TEXT DEFAULT '[]'")
            except sqlite3.OperationalError:
                pass
    
    def parse_status(self, status_text):
        """解析状态文本"""
        result = {'total_episodes': None, 'current_episode': None}
        
        if not status_text:
            return result
        
        # 全XX集 / 第XX集完结
        full_match = re.search(r'(?:全|第)(\d+)集(?:完结)?', status_text)
        if full_match:
            result['total_episodes'] = int(full_match.group(1))
            result['current_episode'] = result['total_episodes']
            return result
        
        # 更新至第XX集
        update_match = re.search(r'更新至第?(\d+)集', status_text)
        if update_match:
            result['current_episode'] = int(update_match.group(1))
        
        return result
    
    def parse_detail_page(self, soup):
        data = super().parse_detail_page(soup)

        # 海报图
        poster = soup.find('div', class_='myui-content__thumb')
        if poster:
            img = poster.find('img')
            if img:
                data['poster_url'] = img.get('data-original') or img.get('src', '')

        episodes = []
        tab_map = {}
        nav_tabs = soup.find('ul', class_='nav-tabs')
        if nav_tabs:
            for a in nav_tabs.find_all('a'):
                href = a.get('href', '').replace('#', '')
                tab_map[href] = a.text.strip()

        playlists = soup.find_all('div', id=re.compile(r'playlist\d+'))
        for pl in playlists:
            pl_id = pl.get('id')
            source_name = tab_map.get(pl_id, '未知源')
            # 过滤掉广告链接（例如 href="/6225.html" 或 title="💞美女直播💞"）
            links = pl.find_all('a', href=re.compile(r'/bofang/'))
            for link in links:
                ep_text = link.text.strip()
                # 再次过滤可能的广告文本
                if '美女直播' in ep_text:
                    continue
                    
                ep_href = link.get('href', '')
                
                # 识别集数逻辑优化：
                # 1. 优先匹配 "全集" "完结" 等合并集关键字，给予特殊集数 (如 9999) 以便排序
                # 2. 其次匹配数字 "第X集" 或 "X"
                # 3. 默认为 0
                
                ep_num = 0
                if '全集' in ep_text or '完结' in ep_text or '合集' in ep_text:
                    ep_num = 9999
                else:
                    ep_match = re.search(r'(?:第(\d+)集)|(\d+)', ep_text)
                    if ep_match:
                        ep_num = int(next(g for g in ep_match.groups() if g))
                
                episodes.append({
                    'source_name': source_name,
                    'episode_number': ep_num,
                    'episode_title': ep_text,
                    'page_url': urljoin(BASE_URL, ep_href)
                })

        seen = set()
        unique_episodes = []
        for ep in episodes:
            key = (ep['source_name'], ep['episode_number'])
            if key not in seen:
                seen.add(key)
                unique_episodes.append(ep)
        unique_episodes.sort(key=lambda x: (x['source_name'], x['episode_number']))
        data['episodes'] = unique_episodes

        status_info = self.parse_status(data.get('status', ''))
        data.update(status_info)
        return data
    
    def save_tv_series(self, conn, series, episodes):
        conn.execute(
            """
            INSERT INTO tv (vod_id, title, original_title, category, region, year,
                            director, actors, status, season, total_episodes, current_episode,
                            rating, poster_url, detail_url, synopsis, episodes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title,
                original_title=excluded.original_title,
                category=excluded.category,
                region=excluded.region,
                year=excluded.year,
                director=excluded.director,
                actors=excluded.actors,
                status=excluded.status,
                season=excluded.season,
                total_episodes=excluded.total_episodes,
                current_episode=excluded.current_episode,
                rating=excluded.rating,
                poster_url=excluded.poster_url,
                synopsis=excluded.synopsis,
                episodes=excluded.episodes,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                series.get('vod_id'),
                series.get('title', ''),
                series.get('original_title'),
                series.get('category', ''),
                series.get('region', ''),
                series.get('year', 0),
                series.get('director', ''),
                series.get('actors', ''),
                series.get('status', ''),
                series.get('season', 1),
                series.get('total_episodes'),
                series.get('current_episode'),
                series.get('rating', 0.0),
                series.get('poster_url', ''),
                series.get('detail_url', ''),
                series.get('synopsis', ''),
                json.dumps(episodes, ensure_ascii=False),
            ),
        )
        conn.commit()

    def save_item(self, conn, item):
        """Override save_item to handle episodes inside item if needed, 
           but in crawl loop we handle separation.
           This method might not be called if we use specific save logic in crawl.
        """
        episodes = item.pop('episodes', [])
        self.save_tv_series(conn, item, episodes)
    
    def load_progress(self, cid):
        """读取爬取进度"""
        try:
            with open(f'progress_tv_{cid}.txt', 'r') as f:
                page = int(f.read().strip())
                logger.info(f"🔄 恢复进度: 分类 {cid} 第 {page} 页")
                return page
        except FileNotFoundError:
            return 1

    def save_progress(self, cid, page):
        """保存爬取进度"""
        with open(f'progress_tv_{cid}.txt', 'w') as f:
            f.write(str(page))

    def crawl(self, year_start=None, year_end=None, max_pages=None, max_episodes=None, limit=None):
        """
        爬取电视剧 (修正版：直接遍历分页)
        """
        # 移除年份循环，因为 build_list_url 并不支持年份参数，且列表是按时间混合排序的
        
        total_series = 0
        total_episodes = 0
        
        # 线程池
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        
        logger.info(f"\n{'='*60}\n开始全量爬取电视剧 (遍历所有分页)\n{'='*60}")
        
        # TV 分类通常是 2
        # 根据分析，dongman/2-1.html 已经是时间倒序（最新在前面）
        cids = [2] # 只爬取电视剧大类
        
        for cid in cids:
            logger.info(f"正在扫描分类 ID: {cid}")
            # 读取进度
            start_page = self.load_progress(cid)
            page = start_page
            empty_pages_count = 0
            
            while True:
                if max_pages and page > max_pages:
                    break
                if limit and total_series >= limit:
                    break
                
                # 保存进度
                self.save_progress(cid, page)
                
                url = self.build_list_url(cid, page)
                # logger.info(f"正在爬取分类 {cid} 第 {page} 页: {url}")
                
                response = self.request(url)
                
                if not response:
                    if page == 1:
                        logger.info(f"分类 {cid} 不存在或无响应，跳过。")
                        break
                    
                    empty_pages_count += 1
                    if empty_pages_count > 3: 
                        break
                    page += 1
                    continue
                
                empty_pages_count = 0
                soup = BeautifulSoup(response.text, 'lxml')
                series_list, has_next = self.parse_list_page(soup)
                
                if not series_list:
                    break
                
                # 提交任务
                future_to_series = {executor.submit(self.fetch_and_parse_detail, s): s for s in series_list}
                
                with sqlite3.connect(self.db_path) as conn:
                    for future in concurrent.futures.as_completed(future_to_series):
                        series = future_to_series[future]
                        try:
                            result = future.result()
                            if result:
                                # 年份过滤 (如果提供了)
                                if year_start and year_end:
                                    s_year = result.get('year', 0)
                                    if not (year_start <= s_year <= year_end) and s_year != 0:
                                        continue

                                # 应用集数限制
                                episodes = result.pop('episodes', [])
                                if max_episodes:
                                    episodes = episodes[:max_episodes]
                                
                                self.save_tv_series(conn, result, episodes)
                                
                                total_series += 1
                                total_episodes += len(episodes)
                                if total_series % 50 == 0:
                                    logger.info(f"✅ 已保存 {total_series} 部剧 (最新: {result['title']})")

                                if limit and total_series >= limit:
                                    for f in future_to_series:
                                        f.cancel()
                                    break
                                
                        except Exception as e:
                            logger.error(f"❌ 处理失败: {e}")
                
                if not has_next:
                    logger.info(f"分类 {cid} 未发现下一页，停止。")
                    break
                page += 1
            
            if limit and total_series >= limit:
                break
        
        executor.shutdown(wait=True)
        logger.info(f"\n🎉 电视剧爬取完成！共 {total_series} 部剧，{total_episodes} 集")
        return total_series, total_episodes
