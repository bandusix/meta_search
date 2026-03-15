#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神马午夜电影网 - 电影爬虫模块
"""

import re
import time
import random
import logging
import sqlite3
import json
import requests
import concurrent.futures
from collections import Counter
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# 配置
BASE_URL = "http://movie.uishishuo11.com"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
DEFAULT_DELAY = (0.5, 1.5)  # 减少延迟以提高并发效率

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MovieSpider:
    """电影爬虫"""
    
    def __init__(self, db_path='spider.db', delay=DEFAULT_DELAY, max_workers=1):
        self.db_path = db_path
        self.delay = delay
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.mount('http://', requests.adapters.HTTPAdapter(
            pool_connections=100, 
            pool_maxsize=100,
            max_retries=10  # 增加最大重试次数
        ))
        self.session.headers.update({
            'User-Agent': IPHONE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        })
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS movies (
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
                    rating REAL DEFAULT 0.0,
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    synopsis TEXT DEFAULT '',
                    play_pages TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
                """
            )
            try:
                conn.execute("ALTER TABLE movies ADD COLUMN play_pages TEXT DEFAULT '[]'")
            except sqlite3.OperationalError:
                pass
    
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
                elif response.status_code in [502, 503]:
                    # 针对 502/503 的指数退避重试
                    wait_time = (attempt + 1) * 30  # 30s, 60s, 90s...
                    logger.warning(f"HTTP {response.status_code}: {full_url} - 暂停 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue # 强制重试，不进入下面的 sleep
                else:
                    logger.warning(f"HTTP {response.status_code}: {full_url}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"请求错误 ({attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5)) # 增加默认重试间隔
        
        return None
    
    def build_list_url(self, cid, page=1, year=None):
        """构造列表页URL"""
        # 修正：cid=1 (电影) 使用 vodshow 接口并按时间倒序 (Newest First)
        # cid=2 (电视剧) 继续使用 dongman 接口 (Verified Newest First)
        
        if cid in [1, 2]:
             # vodshow/{cid}--time------{page}---.html
             # 确保所有分类都按时间倒序
             return f"{BASE_URL}/vodshow/{cid}--time------{page}---.html"
             
        # 其他分类或默认情况
        return f"{BASE_URL}/dongman/{cid}-{page}.html"
    
    @staticmethod
    def extract_vod_id(url):
        """从URL中提取视频ID"""
        match = re.search(r'/(?:guankan|bofang)/(\d+)', url)
        return int(match.group(1)) if match else None
    
    def parse_list_page(self, soup):
        """解析列表页"""
        movies = []
        seen_ids = set()
        
        links = soup.find_all('a', href=re.compile(r'/guankan/\d+\.html'))
        
        for link in links:
            try:
                href = link.get('href', '')
                vod_id = self.extract_vod_id(href)
                
                if not vod_id or vod_id in seen_ids:
                    continue
                
                seen_ids.add(vod_id)
                detail_url = urljoin(BASE_URL, href)
                
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
                        elif any(k in text for k in ['正片', 'HD', '完结', '集']):
                            status = text
                
                title = link.text.strip()
                
                # 如果是短剧，跳过（留给 TVSpider 处理）
                # 注意：有些短剧可能分类在“短剧”下，这里简单通过标题或分类判断可能不够
                # 更好的方式是在 TVSpider 里处理短剧分类，而 MovieSpider 里排除
                # 但这里列表页可能看不出分类，需要进详情页
                # 所以我们先不下定论，等详情页解析后再决定是否保存
                
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
        # 尝试查找“下一页”按钮
        if soup.find('a', string='下一页') or soup.find('a', string='下页'):
            return movies, True
            
        # 兼容旧的 URL 模式检查
        has_next = bool(soup.find('a', href=re.compile(rf'/dongman/\d+-\d+\.html')))
        if has_next:
            return movies, True
            
        # 兼容 vodshow 模式
        if soup.find('a', href=re.compile(r'/vodshow/\d+.*?\d+.*?\.html')):
            return movies, True
            
        return movies, False
    
    def get_real_play_url(self, url):
        """获取真实播放地址"""
        try:
            resp = self.request(url)
            if resp:
                # 提取 player_aaaa 中的 url
                match = re.search(r'var player_aaaa={.*?"url":"(.*?)",', resp.text, re.DOTALL)
                if match:
                    return match.group(1).replace('\\/', '/')
        except Exception as e:
            logger.error(f"获取播放地址失败 {url}: {e}")
        return None

    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        # 标题
        title = soup.find('h1') or soup.find('h2')
        data['title'] = title.text.strip() if title else ''
        
        # 元数据容器
        info = soup.find('div', class_='myui-content__detail')
        if info:
            # 提取评分
            rating_text = info.find('span', string='评分：')
            if rating_text:
                rating_span = rating_text.find_next_sibling('span')
                if rating_span:
                    try:
                        data['rating'] = float(rating_span.text.strip())
                    except:
                        pass
            
            # 提取分类、地区、年份
            category_text = info.find('span', string='分类：')
            if category_text:
                parent = category_text.parent
                full_text = parent.get_text(strip=True)
                # 优化正则：年份允许非数字（如“未知”），后续再处理
                match = re.search(r'分类：(.+?)地区：(.+?)年份：(.*)', full_text)
                if match:
                    data['category'] = match.group(1).strip()
                    data['region'] = match.group(2).strip()
                    
                    year_str = match.group(3).strip()
                    # 尝试从年份字符串中提取数字，如果没有则默认为0
                    year_match = re.search(r'(\d+)', year_str)
                    data['year'] = int(year_match.group(1)) if year_match else 0
            
            # 提取更新状态
            update_text = info.find('span', string='更新：')
            if update_text:
                update_span = update_text.find_next_sibling('span')
                if update_span:
                    data['status'] = update_span.text.strip()
            
            # 提取导演
            director_text = info.find('span', string='导演：')
            if director_text:
                parent = director_text.parent
                match = re.search(r'导演：(.+)', parent.get_text(strip=True))
                if match:
                    data['director'] = match.group(1)
            
            # 提取主演
            actors_text = info.find('span', string='主演：')
            if actors_text:
                parent = actors_text.parent
                match = re.search(r'主演：(.+)', parent.get_text(strip=True))
                if match:
                    data['actors'] = match.group(1)
            
            # 提取简介
            desc_text = info.find('span', string='简介：')
            if desc_text:
                parent = desc_text.parent
                match = re.search(r'简介：(.+)', parent.get_text(strip=True))
                if match:
                    data['synopsis'] = match.group(1)[:500]
        
        # 海报图
        poster = soup.find('div', class_='myui-content__thumb')
        if poster:
            img = poster.find('img')
            if img:
                data['poster_url'] = img.get('data-original') or img.get('src', '')
        
        play_pages = []
        # 查找所有播放列表div (playlist1, playlist2...)
        playlists = soup.find_all('div', id=re.compile(r'playlist\d+'))
        
        # 查找对应的Tab名称
        tab_map = {}
        nav_tabs = soup.find('ul', class_='nav-tabs')
        if nav_tabs:
            for a in nav_tabs.find_all('a'):
                href = a.get('href', '').replace('#', '')
                tab_map[href] = a.text.strip()
        
        for pl in playlists:
            pl_id = pl.get('id')
            source_name = tab_map.get(pl_id, '未知源')
            
            # 排除广告tab (比如 "美女直播") - 通常广告tab的内容链接不同
            # 但这里我们主要看播放链接 /bofang/
            
            links = pl.find_all('a', href=re.compile(r'/bofang/'))
            for link in links:
                page_url = urljoin(BASE_URL, link.get('href'))
                title = link.text.strip()
                play_pages.append({
                    'source_name': source_name,
                    'title': title,
                    'page_url': page_url
                })
        data['play_pages'] = play_pages
        
        # 同时解析集数信息 (用于电视剧判定)
        data['episodes'] = self.parse_episodes(soup)

        return data
    
    def save_movie(self, conn, movie):
        """保存电影（Upsert）"""
        conn.execute(
            """
            INSERT INTO movies (vod_id, title, original_title, category, region, year,
                               director, actors, status, rating, poster_url, detail_url, synopsis, play_pages)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title,
                original_title=excluded.original_title,
                category=excluded.category,
                region=excluded.region,
                year=excluded.year,
                director=excluded.director,
                actors=excluded.actors,
                status=excluded.status,
                rating=excluded.rating,
                poster_url=excluded.poster_url,
                synopsis=excluded.synopsis,
                play_pages=excluded.play_pages,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                movie.get('vod_id'),
                movie.get('title', ''),
                movie.get('original_title'),
                movie.get('category', ''),
                movie.get('region', ''),
                movie.get('year', 0),
                movie.get('director', ''),
                movie.get('actors', ''),
                movie.get('status', ''),
                movie.get('rating', 0.0),
                movie.get('poster_url', ''),
                movie.get('detail_url', ''),
                movie.get('synopsis', ''),
                json.dumps(movie.get('play_pages', []), ensure_ascii=False)
            ),
        )
        conn.commit()

    def parse_episodes(self, soup):
        """解析集数信息"""
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
            # 过滤掉广告链接
            links = pl.find_all('a', href=re.compile(r'/bofang/'))
            for link in links:
                ep_text = link.text.strip()
                # 再次过滤可能的广告文本
                if '美女直播' in ep_text:
                    continue
                    
                ep_href = link.get('href', '')
                
                # 识别集数逻辑
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
        return unique_episodes

    def save_tv_from_movie_spider(self, conn, item):
        """将短剧保存到 tv 表"""
        # 使用 item 中的 episodes 字段，如果没有则尝试从 play_pages 转换
        # 如果是 MovieSpider 原生解析的，可能没有 episodes 字段，只有 play_pages
        # 所以我们需要确保在 save_item 调用前，item 已经有了 episodes 或者我们在这里解析
        # 更好的方式是：在 parse_detail_page 里统一解析 episodes
        
        episodes = item.get('episodes', [])
        if not episodes and item.get('play_pages'):
            # 兼容：如果只有 play_pages，转换一下
            for p in item['play_pages']:
                episodes.append({
                    'source_name': p.get('source_name', '未知'),
                    'episode_number': 0,
                    'episode_title': p.get('title', ''),
                    'page_url': p.get('page_url', '')
                })
            
        conn.execute(
            """
            INSERT INTO tv (vod_id, title, original_title, category, region, year,
                           director, actors, status, rating, poster_url, detail_url, synopsis, episodes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title,
                original_title=excluded.original_title,
                category=excluded.category,
                region=excluded.region,
                year=excluded.year,
                director=excluded.director,
                actors=excluded.actors,
                status=excluded.status,
                rating=excluded.rating,
                poster_url=excluded.poster_url,
                synopsis=excluded.synopsis,
                episodes=excluded.episodes,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                item.get('vod_id'),
                item.get('title', ''),
                item.get('original_title'),
                item.get('category', ''),
                item.get('region', ''),
                item.get('year', 0),
                item.get('director', ''),
                item.get('actors', ''),
                item.get('status', ''),
                item.get('rating', 0.0),
                item.get('poster_url', ''),
                item.get('detail_url', ''),
                item.get('synopsis', ''),
                json.dumps(episodes, ensure_ascii=False)
            ),
        )
        conn.commit()

    def save_item(self, conn, item):
        """通用保存方法 (智能分流)"""
        is_tv = False
        reason = ""
        
        # 规则 1: 分类ID检测
        # 注意：这里 item 没有 cid 字段，我们需要在 crawl 循环里注入，或者依靠分类名称
        # 如果分类是 "国产剧", "港台剧" 等，肯定是 TV
        # 简单起见，我们在 crawl 里会传入 cid，但 item 是字典，可以在 parse_list_page 里带上 cid
        # 或者我们依靠内容检测
        
        category = item.get('category', '')
        
        # 规则 2: 分类名称/标题检测
        if '剧' in category or '短剧' in item.get('title', ''):
            is_tv = True
            reason = f"分类/标题包含剧 ({category})"
            
        # 规则 3: 黑名单ID
        block_ids = {
            164966, 164965, 164960, 164967, 164963, 164959, 
            164964, 164958, 164961, 164962, 164956, 164957
        }
        if item.get('vod_id') in block_ids:
             is_tv = True
             reason = "黑名单ID"

        # 规则 4: 集数检测
        # 优先使用解析出的 episodes
        episodes = item.get('episodes', [])
        play_pages = item.get('play_pages', [])
        
        if not is_tv:
            # 如果有 episodes 且数量 > 2 (或者 play_pages 分组后 > 2)
            if episodes:
                # 简单判断：如果最大集数 > 2
                max_ep = 0
                for ep in episodes:
                    if ep.get('episode_number', 0) > max_ep:
                        max_ep = ep['episode_number']
                if max_ep > 2 or len(episodes) > 5: # 宽松一点，避免电影分成上下集被误判
                    is_tv = True
                    reason = f"集数 > 2 (Max: {max_ep})"
            elif play_pages:
                 source_counts = Counter(p.get('source_name') for p in play_pages)
                 if any(count > 2 for count in source_counts.values()):
                     is_tv = True
                     reason = f"播放源集数 > 2"

        if is_tv:
            logger.info(f"📺 归类为电视剧/短剧: {item['title']} ({reason})")
            self.save_tv_from_movie_spider(conn, item)
            return

        # 否则存为电影
        self.save_movie(conn, item)
        
    def check_exists(self, conn, vod_id):
        """检查视频是否已存在"""
        # 检查 movies 表
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM movies WHERE vod_id = ?", (vod_id,))
        if cursor.fetchone():
            return True
            
        # 检查 tv 表
        cursor.execute("SELECT 1 FROM tv WHERE vod_id = ?", (vod_id,))
        if cursor.fetchone():
            return True
            
        return False
    
    def fetch_and_parse_detail(self, movie):
        """
        在线程中执行：请求详情页并解析
        """
        try:
            detail_resp = self.request(movie['detail_url'])
            if detail_resp:
                detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                detail_data = self.parse_detail_page(detail_soup)
                movie.update(detail_data)
                return movie
            else:
                return None
        except Exception as e:
            logger.error(f"处理详情页失败 {movie.get('title')}: {e}")
            return None

    def load_progress(self, cid):
        """读取爬取进度"""
        try:
            with open(f'progress_movie_{cid}.txt', 'r') as f:
                page = int(f.read().strip())
                logger.info(f"🔄 恢复进度: 分类 {cid} 第 {page} 页")
                return page
        except FileNotFoundError:
            return 1

    def save_progress(self, cid, page):
        """保存爬取进度"""
        with open(f'progress_movie_{cid}.txt', 'w') as f:
            f.write(str(page))

    def crawl(self, year_start=1945, year_end=2026, max_pages=None, limit=None, cids=None, incremental=False):
        """
        爬取电影 (修正版：直接遍历分页，不按年份循环)
        cids: 要爬取的分类ID列表，如果不传则默认爬取 [1, 2] (电影和电视剧)
        incremental: 是否为增量模式 (遇旧即停)
        """
        total_count = 0
        
        # 线程池
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
        
        mode_str = "增量模式 (遇旧即停)" if incremental else "全量模式 (遍历所有分页)"
        logger.info(f"\n{'='*60}\n开始爬取 - {mode_str}\n{'='*60}")
        
        # 修正：遍历所有分类 ID
        # cid=1 使用新的 vodshow URL 确保是时间倒序
        # cid=2 也可以使用 vodshow
        
        if cids is None:
            cids = [1, 2]
        
        for cid in cids:
            logger.info(f"正在扫描分类 ID: {cid}")
            
            # 增量模式总是从第1页开始
            # 全量模式才读取进度
            if incremental:
                start_page = 1
            else:
                start_page = self.load_progress(cid)
                
            page = start_page
            empty_pages_count = 0
            consecutive_exists_count = 0 # 连续已存在计数
            STOP_THRESHOLD = 20 # 连续遇到20个已存在的就停止
            
            while True:
                if max_pages and page > max_pages:
                    break
                if limit and total_count >= limit:
                    break
                
                # 全量模式才保存进度，增量模式不需要保存中间进度
                if not incremental:
                    self.save_progress(cid, page)
                
                url = self.build_list_url(cid, page)
                
                response = self.request(url)
                if not response:
                    # 如果第一页就没响应，说明该分类可能不存在
                    if page == 1:
                        logger.info(f"分类 {cid} 不存在或无响应，跳过。")
                        break
                        
                    empty_pages_count += 1
                    if empty_pages_count > 3: # 连续3页没响应则停止该分类
                        break
                    page += 1
                    continue
                
                empty_pages_count = 0
                soup = BeautifulSoup(response.text, 'lxml')
                movies_list, has_next = self.parse_list_page(soup)
                
                if not movies_list:
                    # 页面存在但没解析出视频，可能是到底了
                    break
                
                # 增量模式：先检查本页有多少是已存在的
                # 列表是时间倒序的，如果发现已存在的，说明已经爬过了
                # 但为了保险，我们只有连续 N 个都是已存在的才停止
                
                # 预检查 (减少不必要的详情页请求)
                new_items = []
                with sqlite3.connect(self.db_path) as conn:
                    for m in movies_list:
                        if incremental and self.check_exists(conn, m['vod_id']):
                            consecutive_exists_count += 1
                            logger.debug(f"跳过已存在: {m['title']} (连续: {consecutive_exists_count})")
                        else:
                            consecutive_exists_count = 0 # 重置计数
                            new_items.append(m)
                
                if incremental and consecutive_exists_count >= STOP_THRESHOLD:
                    logger.info(f"🛑 分类 {cid} 已达到增量停止阈值 (连续 {STOP_THRESHOLD} 个已存在)，停止爬取。")
                    break
                
                if not new_items and incremental:
                    # 本页全是旧的，但还没触发阈值 (可能阈值设得大)
                    # 或者本页全是旧的，继续下一页看看
                    # 如果一整页都是旧的，基本上后面也都是旧的了 (因为是时间倒序)
                    logger.info(f"⚠️ 分类 {cid} 第 {page} 页全部已存在，停止爬取。")
                    break

                # 提交任务到线程池 (只处理新项目)
                items_to_process = new_items if incremental else movies_list
                future_to_movie = {executor.submit(self.fetch_and_parse_detail, m): m for m in items_to_process}
                
                with sqlite3.connect(self.db_path) as conn:
                    for future in concurrent.futures.as_completed(future_to_movie):
                        movie = future_to_movie[future]
                        try:
                            result = future.result()
                            if result:
                                # 过滤年份 (如果指定了范围)
                                movie_year = result.get('year', 0)
                                if (year_start <= movie_year <= year_end) or movie_year == 0:
                                    self.save_item(conn, result)
                                    total_count += 1
                                    if total_count % 10 == 0:
                                        logger.info(f"✅ 已保存 {total_count} 部 (最新: {result['title']})")
                                    
                                    if limit and total_count >= limit:
                                        for f in future_to_movie:
                                            f.cancel()
                                        break
                        except Exception as e:
                            logger.error(f"任务执行异常: {e}")

                if not has_next:
                    logger.info(f"分类 {cid} 未发现下一页，停止。")
                    break
                page += 1
            
            if limit and total_count >= limit:
                break
    
        executor.shutdown(wait=True)
        logger.info(f"\n🎉 爬取完成！共新增 {total_count} 部")
        return total_count
