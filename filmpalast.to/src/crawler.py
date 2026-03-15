import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin
from datetime import datetime
import re
from fake_useragent import UserAgent

import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.database import DatabaseManager

class FilmPalastCrawler:
    """Filmpalast.to 爬虫主类"""

    def __init__(self, config: Dict):
        self.base_url = config['crawler']['base_url']
        self.config = config
        self.session = requests.Session()
        self.db_manager = DatabaseManager(config['database']['path'])
        self.ua = UserAgent()
        self.setup_session()
        
        # 队列用于多线程写入
        self.db_queue = queue.Queue()
        self.running = False
        
        # 日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config['logging']['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # 缓存已存在的项目，用于去重
        self.logger.info("正在加载已存在的数据以进行去重...")
        self.existing_movie_urls, self.existing_episode_keys = self.db_manager.get_existing_items()
        self.logger.info(f"已加载 {len(self.existing_movie_urls)} 部电影和 {len(self.existing_episode_keys)} 集剧集")

    def setup_session(self):
        """设置会话配置"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def get_random_user_agent(self):
        """获取随机User-Agent"""
        return self.ua.random

    def request_with_retry(self, url: str, max_retries: int = 3) -> requests.Response:
        """带重试的请求函数"""
        for attempt in range(max_retries):
            try:
                # 随机延时
                if attempt > 0:
                    time.sleep(random.uniform(2.0, 5.0) * attempt)
                
                headers = {'User-Agent': self.get_random_user_agent()}
                response = self.session.get(
                    url,
                    timeout=self.config['crawler'].get('timeout', 30),
                    headers=headers
                )
                
                if response.status_code == 200:
                    return response
                
                self.logger.warning(f"请求返回状态码 {response.status_code}: {url}")
                
            except Exception as e:
                self.logger.warning(f"请求失败 (尝试 {attempt+1}/{max_retries}): {e}")
                
            time.sleep(1)

        raise Exception(f"请求失败，URL: {url}")

    def check_page_valid(self, page_num: int) -> bool:
        """检查页面是否包含有效数据"""
        url = f"{self.base_url}/page/{page_num}"
        try:
            response = self.request_with_retry(url)
            
            # 1. 检查是否有列表项
            if 'class="liste' not in response.text:
                return False
                
            soup = BeautifulSoup(response.text, 'lxml')
            articles = soup.find_all('article', class_='liste')
            
            if not articles:
                return False
                
            # 2. 关键检查：Filmpalast 超出页数时会返回第1页或最后一页的内容
            # 我们检查分页导航中的 "active" 类是否对应当前请求的页码
            # 或者检查 URL 是否被重定向（requests 默认会自动重定向，但 url 属性会变）
            # 注意：Filmpalast 可能做的是内部重写而不是 HTTP 重定向
            
            # 方法 A: 检查分页器中的当前页
            active_page = soup.find('a', class_='active')
            if active_page:
                try:
                    current_active = int(active_page.get_text(strip=True))
                    if current_active != page_num:
                        self.logger.info(f"请求第 {page_num} 页，但页面显示当前为第 {current_active} 页 - 视为无效")
                        return False
                except ValueError:
                    pass
            
            return True
            
        except:
            return False

    def probe_max_pages(self) -> int:
        """二分法探测实际最大页数（自适应上限）"""
        low = 1
        high = 5000 # 初始猜测
        
        self.logger.info("正在探测最大页数...")
        
        # 1. 寻找上限 (如果5000页还有效，继续往上找)
        while self.check_page_valid(high):
            self.logger.info(f"页数上限 {high} 有效，继续扩展探测范围...")
            low = high
            high += 5000 # 步进 5000
            
        self.logger.info(f"锁定页数范围: {low} - {high}")
        
        # 2. 二分查找精确边界
        last_valid = low
        while low <= high:
            mid = (low + high) // 2
            if self.check_page_valid(mid):
                last_valid = mid
                low = mid + 1
            else:
                high = mid - 1
                
        self.logger.info(f"探测到的实际最大页数: {last_valid}")
        return last_valid

    def detect_max_pages(self) -> int:
        """检测最大页数"""
        try:
            # 直接使用增强版探测，因为它更可靠
            return self.probe_max_pages()
        except Exception as e:
            self.logger.error(f"检测最大页数失败: {e}")
            return 3000 # Fallback

    def extract_items_from_page(self, page: int) -> List[Dict]:
        """从页面提取所有条目（电影和剧集）"""
        url = f"{self.base_url}/page/{page}"
        self.logger.info(f"正在爬取页面: {url}")
        
        try:
            response = self.request_with_retry(url)
            
            # Debug: Save HTML to file
            if page == 1:
                with open(f"logs/page_{page}.html", "w", encoding="utf-8") as f:
                    f.write(response.text)
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            items = []
            articles = soup.find_all('article', class_='liste')
            
            for article in articles:
                item_data = self.parse_article(article)
                if item_data:
                    items.append(item_data)
            
            return items
        except Exception as e:
            self.logger.error(f"提取页面 {page} 数据失败: {e}")
            return []

    def parse_article(self, article) -> Optional[Dict]:
        """解析单个文章块"""
        try:
            title_elem = article.find('h2').find('a')
            title = title_elem.get_text(strip=True)
            url_path = title_elem['href']
            # 根据用户要求，在所有URL后添加 #video_player
            full_url = urljoin(self.base_url, url_path)
            if not full_url.endswith("#video_player"):
                full_url += "#video_player"
            
            img_elem = article.find('img')
            poster_url = urljoin(self.base_url, img_elem['src']) if img_elem else None
            
            # 提取评分
            rating = 0.0
            stars = article.find_all('img', class_='raStars')
            if stars:
                on_stars = sum(1 for star in stars if 'star_on.png' in star.get('src', ''))
                rating = float(on_stars)

            # 提取IMDb
            text_content = article.get_text()
            imdb_rating = 0.0
            imdb_match = re.search(r'Imdb:\s*([\d.]+)/10', text_content)
            if imdb_match:
                imdb_rating = float(imdb_match.group(1))

            # 提取Release Title
            release_elem = article.find('span', class_='releaseTitleHome')
            release_title = release_elem.get_text(strip=True).replace('Release: ', '') if release_elem else ''

            # 提取年份
            year = self.extract_year(release_title, text_content)

            # 提取Quality
            quality = self.extract_quality(release_title)

            # 提取Views/Votes
            views = 0
            votes = 0
            views_match = re.search(r'Views:\s*<strong>([\d,.]+)</strong>', text_content)
            if views_match:
                views = int(views_match.group(1).replace(',', '').replace('.', ''))
            
            votes_match = re.search(r'Votes:\s*<strong>([\d,.]+)</strong>', text_content)
            if votes_match:
                votes = int(votes_match.group(1).replace(',', '').replace('.', ''))

            return {
                'title': title,
                'url': full_url,
                'poster_url': poster_url,
                'year': year,
                'rating': rating,
                'imdb_rating': imdb_rating,
                'quality': quality,
                'release_title': release_title,
                'views': views,
                'votes': votes
            }
        except Exception as e:
            self.logger.warning(f"解析文章失败: {e}")
            return None

    def extract_year(self, release_title: str, text_content: str) -> Optional[int]:
        """提取年份"""
        # 1. Try from release title (e.g., Movie.Title.2023.1080p)
        if release_title:
            match = re.search(r'\.(\d{4})\.', release_title)
            if match:
                return int(match.group(1))
        
        # 2. Try from text content "Jahr: 2023"
        match = re.search(r'Jahr:\s*<b>(\d{4})</b>', text_content)
        if match:
            return int(match.group(1))
            
        # 3. Fallback
        match = re.search(r'\b(19\d{2}|20\d{2})\b', text_content)
        if match:
            return int(match.group(1))
            
        return None

    def extract_quality(self, release_title: str) -> str:
        """提取清晰度"""
        release_lower = release_title.lower()
        if '2160p' in release_lower or '4k' in release_lower: return '2160p'
        if '1080p' in release_lower: return '1080p'
        if '720p' in release_lower: return '720p'
        if '480p' in release_lower: return '480p'
        if 'web-dl' in release_lower or 'webrip' in release_lower: return 'WEB-DL'
        if 'bluray' in release_lower: return 'BluRay'
        if 'hdtv' in release_lower: return 'HDTV'
        return 'Unknown'

    def is_tv_episode_url(self, url: str) -> bool:
        """检测URL是否为电视剧集"""
        patterns = [
            r'-s\d+e\d+',
            r'-\d+x\d+',
            r'-season-\d+-episode-\d+',
            r'/season/\d+/episode/\d+'
        ]
        for pattern in patterns:
            if re.search(pattern, url):
                return True
        return False

    def extract_season_episode(self, url: str) -> Tuple[int, int]:
        """从URL提取季和集"""
        patterns = [
            (r'-s(\d+)e(\d+)', 1, 2),
            (r'-(\d+)x(\d+)', 1, 2),
            (r'-season-(\d+)-episode-(\d+)', 1, 2)
        ]
        
        for pattern, g1, g2 in patterns:
            match = re.search(pattern, url)
            if match:
                return int(match.group(g1)), int(match.group(g2))
        
        return 1, 1 # Default

    def extract_series_title(self, url: str) -> str:
        """提取剧集系列标题"""
        # Get the slug part
        slug = url.split('/')[-1]
        # Remove episode info
        slug = re.sub(r'-s\d+e\d+.*', '', slug)
        slug = re.sub(r'-\d+x\d+.*', '', slug)
        slug = re.sub(r'-season-\d+.*', '', slug)
        
        return slug.replace('-', ' ').title()

    def db_writer(self):
        """数据库写入线程"""
        while self.running or not self.db_queue.empty():
            try:
                # 获取队列数据，超时1秒
                item = self.db_queue.get(timeout=1)
                
                # 写入数据库
                if self.is_tv_episode_url(item['url']):
                    season, episode = self.extract_season_episode(item['url'])
                    series_title = self.extract_series_title(item['url'])
                    
                    episode_data = item.copy()
                    episode_data['series_title'] = series_title
                    episode_data['episode_title'] = item['title']
                    episode_data['season'] = season
                    episode_data['episode'] = episode
                    
                    self.db_manager.save_episode(episode_data)
                else:
                    self.db_manager.save_movie(item)
                    
                self.db_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"数据库写入错误: {e}")

    def crawl_page(self, page: int):
        """爬取单个页面（线程安全）"""
        try:
            items = self.extract_items_from_page(page)
            if items:
                new_items_count = 0
                for item in items:
                    # 检查是否重复
                    is_duplicate = False
                    if self.is_tv_episode_url(item['url']):
                        season, episode = self.extract_season_episode(item['url'])
                        series_title = self.extract_series_title(item['url'])
                        if (series_title, season, episode) in self.existing_episode_keys:
                            is_duplicate = True
                    else:
                        if item['url'] in self.existing_movie_urls:
                            is_duplicate = True
                            
                    if not is_duplicate:
                        self.db_queue.put(item)
                        new_items_count += 1
                        
                return new_items_count
            return 0
        except Exception as e:
            self.logger.error(f"页面 {page} 处理失败: {e}")
            return 0

    def crawl_incremental(self, max_pages: int = 50, max_workers: int = 10):
        """
        增量爬取
        :param max_pages: 爬取的页数范围（从第1页开始），默认50页，通常足够覆盖一天的更新
        :param max_workers: 线程数
        """
        self.logger.info(f"开始增量爬取，范围: 前 {max_pages} 页，线程数: {max_workers}")
        
        # 启动数据库写入线程
        self.running = True
        writer_thread = threading.Thread(target=self.db_writer)
        writer_thread.daemon = True
        writer_thread.start()
        
        total_new_items = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务
            future_to_page = {
                executor.submit(self.crawl_page, page): page 
                for page in range(1, max_pages + 1)
            }
            
            # 处理结果
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    count = future.result()
                    total_new_items += count
                    if count > 0:
                        self.logger.info(f"第 {page} 页发现 {count} 条新数据")
                except Exception as e:
                    self.logger.error(f"页面 {page} 增量爬取异常: {e}")
        
        # 等待写入完成
        self.logger.info("增量爬取完成，等待数据写入...")
        self.running = False
        writer_thread.join()
        
        self.logger.info(f"增量更新结束，共新增数据: {total_new_items} 条")

    def crawl_full_site(self, max_workers: int = 10):
        """全站爬取"""
        self.logger.info(f"开始全站爬取，使用线程数: {max_workers}")
        
        # 1. 检测最大页数
        max_page = self.detect_max_pages()
        self.logger.info(f"全站总页数: {max_page}")
        
        # 2. 启动数据库写入线程
        self.running = True
        writer_thread = threading.Thread(target=self.db_writer)
        writer_thread.daemon = True
        writer_thread.start()
        
        # 3. 使用线程池并发爬取
        total_items = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_page = {
                executor.submit(self.crawl_page, page): page 
                for page in range(1, max_page + 1)
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_page):
                page = future_to_page[future]
                try:
                    count = future.result()
                    total_items += count
                    if page % 10 == 0:
                        self.logger.info(f"已处理完第 {page} 页，累计获取 {total_items} 条数据")
                except Exception as e:
                    self.logger.error(f"页面 {page} 任务异常: {e}")
        
        # 4. 等待所有数据写入完成
        self.logger.info("所有页面爬取完成，等待数据写入...")
        self.running = False
        writer_thread.join()
        
        self.logger.info(f"全站爬取结束，总计获取数据: {total_items} 条")

    def crawl_content(self, target_movies: int = 100, target_episodes: int = 100):
        """爬取内容，直到满足目标数量"""
        self.logger.info(f"开始爬取，目标：电影 {target_movies} 部，剧集 {target_episodes} 集")
        
        movies_count = 0
        episodes_count = 0
        
        max_page = self.detect_max_pages()
        
        for page in range(1, max_page + 1):
            if movies_count >= target_movies and episodes_count >= target_episodes:
                self.logger.info("已达到所有目标数量，停止爬取")
                break
                
            self.logger.info(f"正在处理第 {page} 页... (当前进度: 电影 {movies_count}/{target_movies}, 剧集 {episodes_count}/{target_episodes})")
            
            items = self.extract_items_from_page(page)
            if not items:
                self.logger.info(f"第 {page} 页没有数据，停止爬取")
                break
                
            for item in items:
                # 检查是否为电视剧
                if self.is_tv_episode_url(item['url']):
                    if episodes_count < target_episodes:
                        season, episode = self.extract_season_episode(item['url'])
                        series_title = self.extract_series_title(item['url'])
                        
                        episode_data = item.copy()
                        episode_data['series_title'] = series_title
                        episode_data['episode_title'] = item['title']
                        episode_data['season'] = season
                        episode_data['episode'] = episode
                        
                        if self.db_manager.save_episode(episode_data):
                            episodes_count += 1
                else:
                    # 认为是电影
                    if movies_count < target_movies:
                        if self.db_manager.save_movie(item):
                            movies_count += 1
            
            # 稍微休息一下
            time.sleep(random.uniform(1.0, 2.0))

        self.logger.info(f"爬取结束。总计：电影 {movies_count} 部，剧集 {episodes_count} 集")
        return movies_count, episodes_count

