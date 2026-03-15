#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步爬虫核心模块 - 基于aiohttp和asyncio
"""

import asyncio
import aiohttp
import logging
import random
import time
from typing import List, Dict, Optional, Callable
from datetime import datetime
from urllib.parse import urljoin, urlparse
import lxml.html
import json

logger = logging.getLogger(__name__)

IPHONE_UA_POOL = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.7 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/121.0.6167.62 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.109 Mobile/15E148 Safari/604.1",
]

ANDROID_CN_UA_POOL = [
    "Mozilla/5.0 (Linux; Android 14; 23127PN0CC Build/UKQ1.231003.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; 24031PN0DC Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; V2319A Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; V2309A Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; PGT-AN10 Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; ALN-AL00 Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; PHY110 Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; V2241A Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.230 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; M2012K11AC Build/UKQ1.231003.002) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
]

USER_AGENT_POOL = IPHONE_UA_POOL + ANDROID_CN_UA_POOL

class AsyncCrawler:
    """异步爬虫核心类"""
    
    def __init__(self, max_concurrent: int = 30, delay_ms: int = 200, timeout: int = 30):
        self.max_concurrent = max_concurrent
        self.delay_ms = delay_ms
        self.timeout = timeout
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.retry_config = {
            'max_retries': 3,
            'backoff_base': 1.0,
            'backoff_multiplier': 2.0
        }
        self._last_ua_family_by_host: Dict[str, str] = {}
    
    def _pick_user_agent(self, host: str, prefer_family: Optional[str] = None) -> str:
        if prefer_family == "iphone":
            ua = random.choice(IPHONE_UA_POOL)
            self._last_ua_family_by_host[host] = "iphone"
            return ua
        if prefer_family == "android":
            ua = random.choice(ANDROID_CN_UA_POOL)
            self._last_ua_family_by_host[host] = "android"
            return ua
        
        last = self._last_ua_family_by_host.get(host)
        if last == "iphone":
            ua = random.choice(ANDROID_CN_UA_POOL)
            self._last_ua_family_by_host[host] = "android"
            return ua
        if last == "android":
            ua = random.choice(IPHONE_UA_POOL)
            self._last_ua_family_by_host[host] = "iphone"
            return ua
        
        ua = random.choice(USER_AGENT_POOL)
        self._last_ua_family_by_host[host] = "android" if ua in ANDROID_CN_UA_POOL else "iphone"
        return ua

    def _merge_headers(self, base: Optional[Dict], url: str, prefer_family: Optional[str] = None) -> Dict:
        parsed = urlparse(url)
        host = parsed.netloc
        headers = dict(base or {})
        headers["User-Agent"] = self._pick_user_agent(host, prefer_family=prefer_family)
        headers.setdefault("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
        headers.setdefault("Accept-Language", "zh-CN,zh;q=0.9")
        headers.setdefault("Cache-Control", "no-cache")
        headers.setdefault("Pragma", "no-cache")
        headers.setdefault("Connection", "keep-alive")
        return headers
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(
            total=self.timeout,
            connect=10,
            sock_read=20
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self._merge_headers({}, "http://www.97han.com", prefer_family="iphone")
        )
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def fetch_with_retry(self, url: str, **kwargs) -> Optional[str]:
        """带重试机制的异步请求"""
        extra_delay_ms = int(kwargs.pop("extra_delay_ms", 0) or 0)
        prefer_family = kwargs.pop("prefer_family", None)
        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                async with self.semaphore:
                    # 限速延迟
                    jitter_ms = random.randint(0, 80)
                    await asyncio.sleep((self.delay_ms + extra_delay_ms + jitter_ms) / 1000)
                    
                    headers = self._merge_headers(kwargs.get("headers"), url, prefer_family=prefer_family)
                    kwargs["headers"] = headers
                    
                    async with self.session.get(url, **kwargs) as response:
                        if response.status == 200:
                            content = await response.text()
                            logger.info(f"✅ 成功获取: {url} (状态码: {response.status})")
                            return content
                        elif response.status == 403:
                            logger.warning(f"🚫 403错误: {url}, 尝试更换UA后重试 (尝试 {attempt + 1})")
                            if attempt < self.retry_config["max_retries"]:
                                backoff = self.retry_config["backoff_base"] * (self.retry_config["backoff_multiplier"] ** attempt)
                                await asyncio.sleep(backoff)
                                prefer_family = "android" if prefer_family == "iphone" else "iphone"
                                continue
                            return None
                        elif response.status == 429:
                            logger.warning(f"🧱 429限流: {url}, 退避重试 (尝试 {attempt + 1})")
                            if attempt < self.retry_config["max_retries"]:
                                backoff = self.retry_config["backoff_base"] * (self.retry_config["backoff_multiplier"] ** attempt)
                                await asyncio.sleep(backoff)
                                extra_delay_ms = max(extra_delay_ms, 300)
                                continue
                            return None
                        elif 500 <= response.status < 600:
                            logger.warning(f"⚠️  服务器错误: {url} (状态码: {response.status})")
                            if attempt < self.retry_config['max_retries']:
                                backoff = self.retry_config['backoff_base'] * (self.retry_config['backoff_multiplier'] ** attempt)
                                await asyncio.sleep(backoff)
                                continue
                            return None
                        elif response.status == 404:
                            logger.error(f"❌ 404不存在: {url}")
                            return None
                        else:
                            logger.error(f"❌ 请求失败: {url} (状态码: {response.status})")
                            return None
                            
            except asyncio.TimeoutError:
                logger.warning(f"⏰ 请求超时: {url} (尝试 {attempt + 1})")
                if attempt < self.retry_config['max_retries']:
                    backoff = self.retry_config['backoff_base'] * (self.retry_config['backoff_multiplier'] ** attempt)
                    await asyncio.sleep(backoff)
                    continue
            except Exception as e:
                logger.error(f"❌ 请求异常: {url} - {str(e)}")
                if attempt < self.retry_config['max_retries']:
                    backoff = self.retry_config['backoff_base'] * (self.retry_config['backoff_multiplier'] ** attempt)
                    await asyncio.sleep(backoff)
                    continue
        
        logger.error(f"❌ 所有重试失败: {url}")
        return None
    
    async def fetch_batch(self, urls: List[str], **kwargs) -> List[Optional[str]]:
        """批量异步请求"""
        if not urls:
            return []
        
        tasks = [self.fetch_with_retry(url, **kwargs) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results: List[Optional[str]] = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ 任务异常: {urls[i]} - {str(result)}")
                processed_results.append(None)
            else:
                processed_results.append(result)
        
        success_count = sum(1 for r in processed_results if r)
        if success_count == 0 and len(urls) > 0:
            logger.warning(f"🧯 批次全部失败，触发整批重试: {len(urls)} 个URL")
            await asyncio.sleep(2.0)
            retry_tasks = []
            for idx, url in enumerate(urls):
                prefer_family = "android" if (idx % 2 == 0) else "iphone"
                retry_tasks.append(
                    self.fetch_with_retry(
                        url,
                        extra_delay_ms=500,
                        prefer_family=prefer_family,
                        **kwargs,
                    )
                )
            retry_results = await asyncio.gather(*retry_tasks, return_exceptions=True)
            final_results: List[Optional[str]] = []
            for i, result in enumerate(retry_results):
                if isinstance(result, Exception):
                    logger.error(f"❌ 批次重试异常: {urls[i]} - {str(result)}")
                    final_results.append(None)
                else:
                    final_results.append(result)
            return final_results
        
        return processed_results

class ParserUtils:
    """解析工具类"""
    
    @staticmethod
    def parse_movie_list(html_content: str, base_url: str) -> List[Dict]:
        """解析电影列表页面"""
        try:
            doc = lxml.html.fromstring(html_content)
            movies = []
            
            # 根据97han网站结构解析电影列表
            movie_items = doc.xpath('//div[@class="movie-item"]//a[@class="movie-link"]')
            
            for item in movie_items:
                movie_url = item.get('href', '')
                if not movie_url:
                    continue
                
                movie_url = urljoin(base_url, movie_url)
                
                # 提取封面图
                cover_img = item.xpath('.//img[@class="cover"]/@src')
                cover = cover_img[0] if cover_img else ''
                
                # 提取标题
                title_elem = item.xpath('.//div[@class="title"]//text()')
                title = title_elem[0].strip() if title_elem else ''
                
                # 提取年份
                year_elem = item.xpath('.//span[@class="year"]//text()')
                year = int(year_elem[0].strip()) if year_elem and year_elem[0].strip().isdigit() else None
                
                movies.append({
                    'detail_url': movie_url,
                    'cover': cover,
                    'title': title,
                    'year': year
                })
            
            logger.info(f"📄 解析电影列表: 找到 {len(movies)} 部电影")
            return movies
            
        except Exception as e:
            logger.error(f"❌ 解析电影列表失败: {str(e)}")
            return []
    
    @staticmethod
    def parse_movie_detail(html_content: str, detail_url: str) -> Dict:
        """解析电影详情页面"""
        try:
            doc = lxml.html.fromstring(html_content)
            
            # 提取基本信息
            title = ParserUtils._extract_text(doc, '//h1[@class="title"]//text()')
            original_title = ParserUtils._extract_text(doc, '//div[@class="original-title"]//text()')
            year = ParserUtils._extract_number(doc, '//span[@class="year"]//text()')
            region = ParserUtils._extract_text(doc, '//span[@class="region"]//text()')
            genre = ParserUtils._extract_text(doc, '//span[@class="genre"]//text()')
            intro = ParserUtils._extract_text(doc, '//div[@class="synopsis"]//text()')
            
            # 提取播放线路
            play_lines = ParserUtils._extract_play_lines(doc, detail_url)
            
            return {
                'title': title,
                'original_title': original_title,
                'year': year,
                'region': region,
                'genre': genre,
                'intro': intro,
                'play_lines': play_lines
            }
            
        except Exception as e:
            logger.error(f"❌ 解析电影详情失败: {detail_url} - {str(e)}")
            return {}
    
    @staticmethod
    def _extract_play_lines(doc, detail_url: str) -> List[Dict]:
        """提取播放线路信息"""
        play_lines = []
        
        try:
            # 查找播放线路容器
            line_containers = doc.xpath('//div[@class="play-lines"]//div[@class="line-item"]')
            
            for container in line_containers:
                # 提取线路名称
                line_name = ParserUtils._extract_text(container, './/span[@class="line-name"]//text()')
                if not line_name:
                    continue
                
                # 提取播放链接
                play_links = container.xpath('.//a[@class="play-link"]')
                
                for link in play_links:
                    play_url = link.get('href', '')
                    episode_title = ParserUtils._extract_text(link, './/text()')
                    
                    if play_url:
                        play_lines.append({
                            'route_name': line_name,
                            'play_url': urljoin(detail_url, play_url),
                            'episode_title': episode_title.strip() if episode_title else ''
                        })
            
            logger.info(f"🎬 解析播放线路: 找到 {len(play_lines)} 个播放链接")
            return play_lines
            
        except Exception as e:
            logger.error(f"❌ 提取播放线路失败: {str(e)}")
            return []
    
    @staticmethod
    def _extract_text(doc, xpath: str) -> str:
        """提取文本内容"""
        try:
            elements = doc.xpath(xpath)
            return elements[0].strip() if elements else ''
        except:
            return ''
    
    @staticmethod
    def _extract_number(doc, xpath: str) -> Optional[int]:
        """提取数字内容"""
        try:
            text = ParserUtils._extract_text(doc, xpath)
            if text and text.isdigit():
                return int(text)
            return None
        except:
            return None

class URLGenerator:
    """URL生成器"""
    
    BASE_URL = "http://www.97han.com"
    
    @staticmethod
    def generate_movie_urls(start_page: int = 1, end_page: int = 1027) -> List[str]:
        """生成电影分页URL"""
        urls = []
        for page in range(start_page, end_page + 1):
            if page == 1:
                url = f"{URLGenerator.BASE_URL}/show/1-----------.html"
            else:
                url = f"{URLGenerator.BASE_URL}/show/1--------{page}---.html"
            urls.append(url)
        return urls
    
    @staticmethod
    def generate_tv_urls(category: str, start_page: int = 1, end_page: int = 1) -> List[str]:
        """生成电视剧分页URL"""
        category_map = {
            'tv': 2,      # 电视剧
            'variety': 3, # 综艺
            'anime': 4,   # 动漫
            'short': 30,  # 短剧
            'mv': 36      # 伦理MV
        }
        
        cid = category_map.get(category, 2)
        urls = []
        
        for page in range(start_page, end_page + 1):
            if page == 1:
                url = f"{URLGenerator.BASE_URL}/type/{cid}.html"
            else:
                url = f"{URLGenerator.BASE_URL}/type/{cid}-{page}.html"
            urls.append(url)
        
        return urls
