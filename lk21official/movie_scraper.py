import os
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
import concurrent.futures
from typing import List, Dict, Optional
from urllib.parse import urljoin
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)


class LK21MovieScraper:
    """LK21 电影爬虫类"""
    
    BASE_URL = "https://tv8.lk21official.cc"
    # 修改代理API URL，筛选香港(HK)、新加坡(SG)、美国(US)的代理
    PROXY_LIST_URL = "https://proxy.webshare.io/api/v2/proxy/list/download/uhkhxborhjixfvjijsjickhkijtrodyqykuojfqa/-/any/username/direct/-/?plan_id=9877718&country_code_in=HK,SG,US"
    
    def __init__(self, delay_min=0.5, delay_max=1.5, max_workers=3):
        """
        初始化爬虫
        
        Args:
            delay_min: 最小延迟时间（秒）
            delay_max: 最大延迟时间（秒）
            max_workers: 最大并发线程数
        """
        self.session = requests.Session()
        
        # 优化连接池大小
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=max_workers + 10,
            pool_maxsize=max_workers + 10,
            max_retries=3
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_workers = max_workers
        self.ua = UserAgent(min_version=120.0) # Ensure modern browser versions
        self.proxies = []
        self._load_proxies()
        
        # 失败URL记录文件
        self.failed_urls_file = "failed_urls.txt"
        
    def _log_failed_url(self, url: str):
        """记录失败的URL"""
        try:
            with open(self.failed_urls_file, 'a', encoding='utf-8') as f:
                f.write(f"{url}\n")
        except Exception as e:
            logger.error(f"Failed to log url {url}: {e}")

    def _load_proxies(self):
        """加载代理列表"""
        try:
            logger.info("正在加载代理列表...")
            response = requests.get(self.PROXY_LIST_URL, timeout=30)
            if response.status_code == 200:
                # 假设格式为 IP:Port:Username:Password 或 IP:Port
                lines = response.text.strip().split('\n')
                for line in lines:
                    if not line.strip():
                        continue
                    parts = line.strip().split(':')
                    if len(parts) == 4:
                        ip, port, user, password = parts
                        proxy_url = f"http://{user}:{password}@{ip}:{port}"
                        self.proxies.append(proxy_url)
                    elif len(parts) == 2:
                        ip, port = parts
                        proxy_url = f"http://{ip}:{port}"
                        self.proxies.append(proxy_url)
                
                logger.info(f"成功加载 {len(self.proxies)} 个代理")
            else:
                logger.error(f"加载代理失败: Status {response.status_code}")
        except Exception as e:
            logger.error(f"加载代理出错: {e}")

    def _get_random_proxy(self) -> Optional[Dict[str, str]]:
        """获取随机代理"""
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {
            "http": proxy,
            "https": proxy
        }
    
    def _get_random_user_agent(self) -> str:
        """获取 Googlebot User-Agent (Desktop or Mobile)"""
        googlebots = [
            # Googlebot Desktop
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            # Googlebot Mobile
            'Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'
        ]
        return random.choice(googlebots)
    
    def _delay(self):
        """随机延迟"""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def _make_request(self, url: str, max_retries=5) -> Optional[requests.Response]:
        """
        发送 HTTP 请求，带重试机制和代理轮换
        
        Args:
            url: 目标URL
            max_retries: 最大重试次数
            
        Returns:
            Response 对象或 None
        """
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        for attempt in range(max_retries):
            proxy = self._get_random_proxy()
            headers = {
                'User-Agent': self._get_random_user_agent(),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            }
            
            try:
                # 每次请求使用新的 Session 或清除 cookies 以模拟新用户
                # 这里为了简单，我们每次请求使用新的代理和 headers
                response = self.session.get(
                    url, 
                    headers=headers, 
                    proxies=proxy, 
                    timeout=30,
                    verify=False # 忽略 SSL 证书错误，有些代理可能需要
                )
                response.encoding = 'utf-8'
                
                # 如果返回 403 Forbidden，可能是 WAF 拦截，视为失败重试
                if response.status_code == 403:
                    logger.warning(f"访问被拒绝 (403) [Attempt {attempt + 1}]: {url}")
                    continue
                
                if response.status_code == 404:
                     # 404 也可能是误报，尝试多试几次，如果 5 次都 404 才是真 404
                     # 但为了效率，这里我们还是记录并返回，交给 retry 逻辑处理
                     logger.warning(f"页面未找到 (404): {url}")
                     if attempt == max_retries - 1:
                        self._log_failed_url(url) # 记录失败URL以便重试
                     return None

                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"请求失败 (尝试 {attempt + 1}/{max_retries}) [Proxy: {proxy is not None}]: {url} - {str(e)[:100]}")
                if attempt < max_retries - 1:
                    time.sleep(2) # 失败后简短等待
                else:
                    logger.error(f"请求最终失败: {url}")
                    return None
    
    def _scrape_list_page(self, year: int, page: int) -> List[Dict]:
        """
        爬取电影列表页
        
        Args:
            year: 年份
            page: 页码
            
        Returns:
            电影列表
        """
        url = f"{self.BASE_URL}/year/{year}/page/{page}/"
        logger.info(f"正在爬取电影列表第 {page} 页: {url}")
        
        response = self._make_request(url)
        if not response:
            return []
        
        # 检查是否发生了重定向（例如页码超出范围重定向到了首页或第一页）
        # 注意：response.url 可能是最终的 URL
        # 优化判断：如果 URL 不包含 'year/{year}'，或者变成了首页，说明重定向了
        if response.url != url:
             # 如果重定向后的 URL 是首页 (https://tv8.lk21official.cc/) 
             # 或者不包含年份信息，说明该页码已经超出范围
             if response.url.rstrip('/') == self.BASE_URL.rstrip('/') or f"year/{year}" not in response.url:
                 logger.info(f"页面被重定向到首页或非年份页面，停止爬取: {url} -> {response.url}")
                 return []
             
             # 如果只是 http -> https 的重定向，或者是 url 规范化（末尾斜杠等），则继续
             # 但为了保险，我们可以检查页面内容是否真的包含该年份的电影
             
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有电影卡片
        movie_cards = soup.select('article[itemtype*="Movie"]')
        
        if not movie_cards:
            logger.info(f"第 {page} 页没有找到电影")
            return []
        
        movies = []
        year_mismatch_count = 0
        
        for card in movie_cards:
            try:
                # 提取详情页URL
                url_tag = card.select_one('a[itemprop="url"]')
                if not url_tag:
                    continue
                
                movie_url = urljoin(self.BASE_URL, url_tag.get('href', ''))
                
                # 提取标题
                title_tag = card.select_one('h3.poster-title[itemprop="name"]')
                title = title_tag.text.strip() if title_tag else ''
                
                # 提取年份
                year_tag = card.select_one('span.year[itemprop="datePublished"]')
                movie_year = year_tag.text.strip() if year_tag else str(year)
                
                # 检查年份是否匹配
                current_movie_year = int(movie_year) if movie_year.isdigit() else year
                if abs(current_movie_year - year) > 2:
                    year_mismatch_count += 1
                
                # 提取清晰度
                quality_tag = card.select_one('span.label')
                quality = quality_tag.text.strip() if quality_tag else ''
                
                # 提取时长
                duration_tag = card.select_one('span.duration[itemprop="duration"]')
                duration = duration_tag.text.strip() if duration_tag else ''
                
                # 提取图片URL
                img_tag = card.select_one('img[itemprop="image"]')
                image_url = img_tag.get('src', '') if img_tag else ''
                
                # 提取类型
                genre_tag = card.select_one('div.genre')
                genre = genre_tag.text.strip() if genre_tag else ''
                
                movies.append({
                    'title': title,
                    'year': current_movie_year,
                    'quality': quality,
                    'duration': duration,
                    'image_url': image_url,
                    'movie_url': movie_url,
                    'genre': genre,
                })
                
            except Exception as e:
                logger.error(f"解析电影卡片失败: {e}")
                continue
        
        # 如果大部分电影的年份都不匹配，说明可能是一个无效页面
        if len(movies) > 0 and (year_mismatch_count / len(movies)) > 0.5:
             logger.warning(f"第 {page} 页包含大量年份不匹配的电影 ({year_mismatch_count}/{len(movies)})，判定为无效页面")
             return []

        logger.info(f"   找到 {len(movies)} 部电影")
        return movies
    
    def _normalize_duration(self, duration: str) -> str:
        """
        标准化时长格式为 Xh Ym
        支持输入: "1h 22m", "01:40", "120 min", "1h", "45m"
        """
        if not duration or duration == 'N/A':
            return ""
            
        duration = duration.lower().strip()
        
        # 1. 处理 HH:MM 格式 (01:40)
        if ':' in duration and len(duration) <= 5:
            parts = duration.split(':')
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                hours = int(parts[0])
                minutes = int(parts[1])
                if hours > 0:
                    return f"{hours}h {minutes}m"
                else:
                    return f"{minutes}m"
                    
        # 2. 处理 "1h 22m" 或 "1h" 或 "45m" 格式
        if 'h' in duration or 'm' in duration:
            # 已经包含 h 或 m，尝试规范化空格
            # 移除多余空格，确保 h 和 m 之间有空格
            # 简单处理：如果已经是标准格式，直接返回
            # 这里可以加更复杂的正则，但通常直接返回即可，除非格式很乱
            return duration
            
        # 3. 处理纯数字或 "120 min"
        import re
        nums = re.findall(r'\d+', duration)
        if nums and 'min' in duration:
             total_min = int(nums[0])
             hours = total_min // 60
             minutes = total_min % 60
             if hours > 0:
                 return f"{hours}h {minutes}m"
             else:
                 return f"{minutes}m"
                 
        return duration

    def _determine_type(self, soup, detail) -> str:
        """确定电影类型 (Movie / TV Series)"""
        # 1. Check Genre/Category
        genre = detail.get('genre', '').lower()
        if any(k in genre for k in ['series', 'tv series', 'tv-series', '短剧', '电视剧']):
             return 'TV Series'
        
        # 2. Check Title
        title = detail.get('title', '').lower()
        if 'season' in title:
             return 'TV Series'
             
        # 3. Check specific elements (Episode list)
        if soup.select('.episode-list, #episodelist, .playlist, .myui-content__list'):
             return 'TV Series'
             
        return 'Movie'

    def scrape_movie_detail(self, movie_url: str) -> Dict:
        """
        爬取电影详情任务
        
        Args:
            movie_url: 电影详情页URL
            
        Returns:
            电影详情字典
        """
        # 预先检查 URL 是否合法
        if '/page/' in movie_url or '/year/' in movie_url:
            logger.warning(f"跳过非电影详情 URL: {movie_url}")
            return {}

        logger.info(f"正在爬取电影详情: {movie_url}")
        
        response = self._make_request(movie_url)
        if not response:
            return {}
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        detail = {}
        
        try:
            # 提取URL Title (HTML Title)
            if soup.title:
                raw_title = soup.title.string.strip()
                
                # 检查是否为首页或无效页面标题
                if "Nonton Film & Series Sub Indo Gratis di Layarkaca21 (LK21) Official" in raw_title:
                    logger.warning(f"页面重定向至首页或无效页面 (Title匹配): {movie_url}")
                    return {}

                # 移除 "Sub Indo di Lk21" 等后缀
                # 常见的后缀: "Sub Indo di Lk21", "Subtitle Indonesia", "LK21", "Nonton Film"
                # 扩展更多关键词
                remove_list = [
                    "Sub Indo di Lk21", "Sub Indo", "Subtitle Indonesia", 
                    "di Lk21", "LK21", "Layarkaca21", "Dunia21",
                    "Nonton Film", "Nonton Movie", "Nonton", "Streaming Movie", "Download Film",
                    "Film Bioskop", "Cinema 21", "XXI",
                    "Nonton Film & Series Sub Indo Gratis di Layarkaca21 (LK21) Official"
                ]
                
                clean_title = raw_title
                for text in remove_list:
                    # 使用大小写不敏感替换可能更安全，但这里先用 replace
                    clean_title = clean_title.replace(text, "")
                
                clean_title = clean_title.strip()
                # 移除可能产生的尾部连字符或竖线
                clean_title = clean_title.strip(" -|")
                detail['page_title'] = clean_title
            else:
                detail['page_title'] = ''
                
            # 提取 URL Slug (从 URL 中)
            path = urljoin(movie_url, '.').strip('/')
            detail['url_slug'] = movie_url.split('/')[-1] if movie_url else ''
            
            # 提取标题
            title_tag = soup.select_one('h1, [itemprop="name"]')
            detail['title'] = title_tag.text.strip() if title_tag else ''
            
            # 再次检查 title 是否包含非法关键词
            if "Nonton Film & Series" in detail['title']:
                 logger.warning(f"内容标题无效 (可能是首页): {detail['title']} - {movie_url}")
                 return {}

            # 提取原始标题
            # 这里的 original_title 可能在其他地方，需要检查页面结构
            # 暂时留空或尝试查找
            
            # 提取详细信息 (Info Tag)
            # <div class="info-tag"><span><strong><i class="fa-star"></i>4.3</strong></span><div class="broken-line"></div><span>WEBDL</span><div class="broken-line"></div><span>1080p</span><div class="broken-line"></div><span>1h 22m</span></div>
            info_tag = soup.select_one('.info-tag')
            if info_tag:
                # 评分
                rating_tag = info_tag.select_one('i.fa-star')
                if rating_tag and rating_tag.parent:
                     try:
                         detail['rating'] = float(rating_tag.parent.text.strip())
                     except:
                         pass
                
                # 提取 span 内容，排除评分
                spans = info_tag.find_all('span', recursive=False)
                info_texts = [span.text.strip() for span in spans if not span.find('i', class_='fa-star')]
                
                # 尝试解析 Quality, Resolution, Duration
                # 通常顺序不固定，需要根据内容判断
                for text in info_texts:
                    if any(q in text.upper() for q in ['WEBDL', 'BLURAY', 'HDTV', 'CAM', 'HDCAM']):
                        detail['quality'] = text
                    elif any(r in text for r in ['720p', '1080p', '480p', '4k']):
                        detail['resolution'] = text
                    elif 'h ' in text or 'm' in text or ':' in text: # 1h 22m, 2h 5m, 01:40
                        detail['duration'] = self._normalize_duration(text)
            
            # 提取标签列表 (Tag List) - 国家和类型
            # <div class="tag-list"><span class="tag"><a href="/country/usa">United States</a></span><span class="tag"><a href="/genre/horror">Horror</a></span></div>
            tag_list = soup.select('.tag-list .tag a')
            countries = []
            genres = []
            
            for tag in tag_list:
                href = tag.get('href', '')
                text = tag.text.strip()
                if '/country/' in href:
                    countries.append(text)
                elif '/genre/' in href:
                    genres.append(text)
            
            detail['country'] = ', '.join(countries)
            detail['genre'] = ', '.join(genres)
            
            # 提取描述
            desc_tag = soup.select_one('div[itemprop="description"], .entry-content p')
            detail['description'] = desc_tag.text.strip() if desc_tag else ''
            
            # 提取图片
            # 优先查找 myui-content__thumb 下的图片，或者 itemprop="image"
            img_tag = soup.select_one('.myui-content__thumb img, img[itemprop="image"]')
            if img_tag:
                # 优先使用 data-original (懒加载), 其次 src
                src = img_tag.get('data-original') or img_tag.get('src')
                if src and src.startswith('//'):
                    src = 'https:' + src
                detail['image_url'] = src if src else ''
            else:
                detail['image_url'] = ''
            
            # 确定类型
            detail['type'] = self._determine_type(soup, detail)

        except Exception as e:
            logger.error(f"Error parsing detail page {movie_url}: {e}")
            
        return detail
    
    def remove_duplicates(self):
        """去重失败URL文件"""
        if not os.path.exists(self.failed_urls_file):
            return
            
        try:
            with open(self.failed_urls_file, 'r', encoding='utf-8') as f:
                urls = [line.strip() for line in f if line.strip()]
            
            unique_urls = sorted(list(set(urls)))
            
            if len(urls) != len(unique_urls):
                logger.info(f"去重 failed_urls.txt: {len(urls)} -> {len(unique_urls)}")
                with open(self.failed_urls_file, 'w', encoding='utf-8') as f:
                    for url in unique_urls:
                        f.write(f"{url}\n")
        except Exception as e:
            logger.error(f"Failed to deduplicate failed urls: {e}")

    def retry_failed_urls(self) -> List[Dict]:
        """
        重试所有失败的 URL
        
        Returns:
            成功爬取的电影列表
        """
        if not os.path.exists(self.failed_urls_file):
            logger.info("没有失败的 URL 记录")
            return []
            
        with open(self.failed_urls_file, 'r', encoding='utf-8') as f:
            failed_urls = [line.strip() for line in f if line.strip()]
            
        if not failed_urls:
            return []
            
        logger.info(f"开始重试 {len(failed_urls)} 个失败的 URL...")
        
        # 备份并清空文件，防止重复处理
        bak_file = f"{self.failed_urls_file}.bak"
        if os.path.exists(bak_file):
            try:
                os.remove(bak_file)
            except Exception as e:
                logger.error(f"Failed to remove old backup file: {e}")
                
        try:
            os.rename(self.failed_urls_file, bak_file)
        except Exception as e:
            logger.error(f"Failed to rename failed urls file: {e}")
            # If rename fails, we should probably stop to avoid processing same urls and appending to same file
            return []
        
        all_movies = []
        
        # 并发重试
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {}
            for url in failed_urls:
                # 修复不完整的 URL
                if not url.startswith('http'):
                    # 尝试拼接 Base URL
                    # 有些 URL 可能是相对路径，或者只是 slug
                    if url.startswith('/'):
                         fixed_url = self.BASE_URL + url
                    else:
                         fixed_url = f"{self.BASE_URL}/{url}"
                    logger.info(f"修复不完整 URL: {url} -> {fixed_url}")
                    url = fixed_url
                
                future_to_url[executor.submit(self._scrape_detail_task, url)] = url
            
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    detail = future.result()
                    if detail:
                        # 补充缺失的基础信息 (从 URL 推断)
                        detail['movie_url'] = url
                        if not detail.get('year'):
                            # 尝试从 URL 提取年份: movie-title-2024
                            try:
                                year_part = url.split('-')[-1]
                                if year_part.isdigit() and len(year_part) == 4:
                                    detail['year'] = int(year_part)
                            except:
                                pass
                        all_movies.append(detail)
                        logger.info(f"重试成功: {url}")
                    else:
                        logger.warning(f"重试依然失败 (无数据): {url}")
                        self._log_failed_url(url) # 再次记录
                except Exception as e:
                    logger.error(f"重试出错 {url}: {e}")
                    self._log_failed_url(url) # 再次记录
                    
        logger.info(f"重试完成，成功找回 {len(all_movies)} 部电影")
        return all_movies

    def scrape_year(self, year: int, max_pages: Optional[int] = None, start_page: int = 1, on_progress=None, existing_urls=None) -> List[Dict]:
        """
        爬取指定年份的所有电影
        
        Args:
            year: 年份
            max_pages: 最大页数（None 表示爬取所有页面）
            start_page: 起始页码
            on_progress: 进度回调函数 func(year, page)
            existing_urls: 已存在电影 URL 集合 (set)，用于增量爬取判断
            
        Returns:
            电影列表（包含详细信息）
        """
        logger.info(f"============================================================")
        logger.info(f"开始爬取 {year} 年的电影 (从第 {start_page} 页开始, 线程数: {self.max_workers})")
        logger.info(f"============================================================")
        
        all_movies = []
        page = start_page
        consecutive_duplicates = 0
        MAX_DUPLICATES_TO_STOP = 20 # 连续遇到20个已存在电影则停止
        
        while True:
            if max_pages and page > max_pages:
                logger.info(f"已达到最大页数限制: {max_pages}")
                break
            
            # 爬取列表页
            movies_list = self._scrape_list_page(year, page)
            
            if not movies_list:
                logger.info(f"第 {page} 页没有数据或已被重定向，停止爬取该年份")
                break
            
            # 检查增量停止条件
            if existing_urls:
                new_movies_list = []
                for m in movies_list:
                    if m['movie_url'] in existing_urls:
                        consecutive_duplicates += 1
                        logger.debug(f"跳过已存在电影: {m['title']}")
                    else:
                        consecutive_duplicates = 0 # 重置计数器
                        new_movies_list.append(m)
                
                if consecutive_duplicates >= MAX_DUPLICATES_TO_STOP:
                    logger.info(f"连续遇到 {consecutive_duplicates} 个已存在电影，判定无需继续爬取该年份剩余部分")
                    break
                
                movies_list = new_movies_list
                if not movies_list:
                    logger.info(f"第 {page} 页所有电影均已存在，继续检查下一页...")
                    page += 1
                    self._delay()
                    continue
            
            # 并发爬取详情
            logger.info(f"正在爬取 {len(movies_list)} 部电影的详情...")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_movie = {
                    executor.submit(self._scrape_detail_task, movie['movie_url']): movie 
                    for movie in movies_list
                }
                
                for future in concurrent.futures.as_completed(future_to_movie):
                    movie_basic = future_to_movie[future]
                    try:
                        detail = future.result()
                        if detail:
                            # 合并信息
                            movie_basic.update(detail)
                            all_movies.append(movie_basic)
                    except Exception as e:
                        logger.error(f"Error scraping detail for {movie_basic['title']}: {e}")
            
            # 进度回调
            if on_progress:
                on_progress(year, page)
                
            page += 1
            self._delay()  # 列表页翻页延迟
        
        logger.info(f"✨ {year} 年共爬取 {len(all_movies)} 部电影")
        return all_movies

    def _scrape_detail_task(self, url: str) -> Dict:
        """线程任务：爬取详情并延迟"""
        self._delay()
        return self.scrape_movie_detail(url)
    
    def scrape_years(self, years: List[int], max_pages_per_year: Optional[int] = None) -> List[Dict]:
        """
        爬取多个年份的电影
        
        Args:
            years: 年份列表
            max_pages_per_year: 每个年份的最大页数
            
        Returns:
            所有电影列表
        """
        all_movies = []
        
        for year in years:
            movies = self.scrape_year(year, max_pages=max_pages_per_year)
            all_movies.extend(movies)
        
        logger.info(f"============================================================")
        logger.info(f"🎉 所有年份共爬取 {len(all_movies)} 部电影")
        logger.info(f"============================================================")
        
        return all_movies


# 使用示例
if __name__ == "__main__":
    scraper = LK21MovieScraper(delay_min=1, delay_max=3)
    
    # 爬取 2025 年的电影（仅前 2 页作为测试）
    movies = scraper.scrape_year(2025, max_pages=2)
    
    print(f"\n爬取到 {len(movies)} 部电影")
    if movies:
        print("\n第一部电影示例:")
        print(movies[0])
