#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电视剧爬虫模块
爬取 Cuevana3 网站的电视剧数据
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class TVSeriesScraper:
    """电视剧爬虫类"""
    
    BASE_URL = "https://ww9.cuevana3.to"
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self, delay_range: tuple = (1, 3)):
        """
        初始化爬虫
        
        Args:
            delay_range: 请求延迟范围（秒）
        """
        self.delay_range = delay_range
        self.session = requests.Session()
    
    def _get_random_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    
    def _random_delay(self):
        """随机延迟"""
        time.sleep(random.uniform(*self.delay_range))
    
    def _fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """
        获取页面内容
        
        Args:
            url: 目标URL
            retries: 重试次数
            
        Returns:
            BeautifulSoup对象或None
        """
        for attempt in range(retries):
            try:
                response = self.session.get(
                    url,
                    headers=self._get_random_headers(),
                    timeout=30,
                    verify=False
                )
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except Exception as e:
                if attempt < retries - 1:
                    print(f"⚠️  请求失败（尝试 {attempt + 1}/{retries}），重试中...")
                    time.sleep(2)
                else:
                    print(f"❌ 请求失败 {url}: {e}")
                    return None
    
    def _extract_series_urls_from_list(self, soup: BeautifulSoup) -> List[str]:
        """
        从列表页提取电视剧URL
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            电视剧URL列表
        """
        urls = []
        
        # 查找所有电视剧链接
        links = soup.find_all('a', href=re.compile(r'/serie/[a-z0-9-]+'))
        
        for link in links:
            href = link.get('href')
            if href:
                # 只保留剧集主页链接，排除 Temporadas 等
                if href.count('/') == 2:  # /serie/slug 格式
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in urls:
                        urls.append(full_url)
        
        return urls
    
    def _extract_episode_urls_from_series_page(self, soup: BeautifulSoup) -> List[str]:
        """
        从电视剧主页提取所有剧集URL
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            剧集URL列表
        """
        urls = []
        
        # 查找所有剧集链接
        # 格式: /episodio/slug-{season}x{episode}
        links = soup.find_all('a', href=re.compile(r'/episodio/[a-z0-9-]+-\d+x\d+'))
        
        for link in links:
            href = link.get('href')
            if href:
                full_url = urljoin(self.BASE_URL, href)
                if full_url not in urls:
                    urls.append(full_url)
        
        return urls
    
    def _extract_episode_details(self, url: str) -> Optional[Dict]:
        """
        提取剧集详情
        
        Args:
            url: 剧集详情页URL
            
        Returns:
            剧集数据字典或None
        """
        soup = self._fetch_page(url)
        if not soup:
            return None
        
        try:
            episode_data = {'url': url}
            
            # 从URL提取季和集信息
            match = re.search(r'-(\d+)x(\d+)$', url)
            if match:
                episode_data['season'] = int(match.group(1))
                episode_data['episode'] = int(match.group(2))
            
            # 提取西语标题
            title_h1 = soup.find('h1', class_='Title')
            if title_h1:
                episode_data['title_spanish'] = title_h1.get_text(strip=True)
            
            # 提取原标题
            title_h2 = soup.find('h2', class_='SubTitle')
            if title_h2:
                original_title = title_h2.get_text(strip=True)
                # 移除 "Civil: " 前缀
                if original_title.startswith('Civil: '):
                    original_title = original_title[7:]
                episode_data['title_original'] = original_title
            
            # 提取元数据
            meta = soup.find('p', class_='meta')
            if meta:
                spans = meta.find_all('span')
                if len(spans) >= 3:
                    # 评分
                    rating_text = spans[0].get_text(strip=True)
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        episode_data['rating'] = float(rating_match.group(1))
                    
                    # 年份
                    year_text = spans[1].get_text(strip=True)
                    year_match = re.search(r'(\d{4})', year_text)
                    if year_match:
                        episode_data['year'] = int(year_match.group(1))
                    
                    # 清晰度
                    quality_text = spans[2].get_text(strip=True)
                    episode_data['quality'] = quality_text
            
            return episode_data
        
        except Exception as e:
            print(f"⚠️  提取剧集详情失败 {url}: {e}")
            return None
    
    def scrape_series_page(self, page: int = 1) -> List[str]:
        """
        爬取电视剧列表页，获取所有电视剧主页URL
        
        Args:
            page: 页码
            
        Returns:
            电视剧主页URL列表
        """
        if page == 1:
            url = f"{self.BASE_URL}/serie"
        else:
            url = f"{self.BASE_URL}/serie/page/{page}"
        
        print(f"\n📄 正在爬取电视剧列表第 {page} 页: {url}")
        
        soup = self._fetch_page(url)
        if not soup:
            return []
        
        series_urls = self._extract_series_urls_from_list(soup)
        print(f"   找到 {len(series_urls)} 个电视剧")
        
        return series_urls
    
    def scrape_all_series_list(self, max_pages: Optional[int] = None) -> List[str]:
        """
        爬取所有电视剧列表页
        
        Args:
            max_pages: 最大页数限制
            
        Returns:
            所有电视剧主页URL列表
        """
        all_series_urls = []
        page = 1
        
        print(f"\n{'='*60}")
        print(f"📺 开始爬取电视剧列表...")
        print(f"{'='*60}")
        
        while True:
            if max_pages and page > max_pages:
                break
            
            series_urls = self.scrape_series_page(page)
            
            if not series_urls:
                print(f"✅ 第 {page} 页没有更多电视剧，结束爬取")
                break
            
            all_series_urls.extend(series_urls)
            page += 1
            
            self._random_delay()
        
        print(f"\n✨ 电视剧列表爬取完成！共 {len(all_series_urls)} 部电视剧")
        return all_series_urls
    
    def scrape_series_episodes(self, series_url: str) -> List[Dict]:
        """
        爬取单部电视剧的所有剧集
        
        Args:
            series_url: 电视剧主页URL
            
        Returns:
            剧集数据列表
        """
        print(f"\n📺 正在爬取电视剧: {series_url}")
        
        soup = self._fetch_page(series_url)
        if not soup:
            return []
        
        # 获取所有剧集URL
        episode_urls = self._extract_episode_urls_from_series_page(soup)
        print(f"   找到 {len(episode_urls)} 个剧集")
        
        all_episodes = []
        
        for idx, episode_url in enumerate(episode_urls, 1):
            print(f"   [{idx}/{len(episode_urls)}] 正在爬取: {episode_url}")
            
            episode_data = self._extract_episode_details(episode_url)
            if episode_data:
                all_episodes.append(episode_data)
                season = episode_data.get('season', '?')
                episode = episode_data.get('episode', '?')
                title = episode_data.get('title_spanish', 'Unknown')
                print(f"      ✅ S{season}E{episode}: {title}")
            
            # 延迟
            self._random_delay()
        
        return all_episodes
    
    def scrape_all_episodes(
        self, 
        max_series: Optional[int] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict]:
        """
        爬取所有电视剧的所有剧集
        
        Args:
            max_series: 最大电视剧数量限制
            max_pages: 电视剧列表最大页数
            
        Returns:
            所有剧集数据列表
        """
        # 获取所有电视剧列表
        series_urls = self.scrape_all_series_list(max_pages=max_pages)
        
        if max_series:
            series_urls = series_urls[:max_series]
        
        all_episodes = []
        
        print(f"\n\n{'#'*60}")
        print(f"# 开始爬取 {len(series_urls)} 部电视剧的所有剧集")
        print(f"{'#'*60}")
        
        for idx, series_url in enumerate(series_urls, 1):
            print(f"\n\n{'='*60}")
            print(f"进度: {idx}/{len(series_urls)}")
            print(f"{'='*60}")
            
            episodes = self.scrape_series_episodes(series_url)
            all_episodes.extend(episodes)
            
            print(f"\n✅ 该剧共爬取 {len(episodes)} 个剧集")
            print(f"📊 累计: {len(all_episodes)} 个剧集")
            
            if idx < len(series_urls):
                print(f"\n⏳ 等待 {self.delay_range[1]} 秒后继续...")
                time.sleep(self.delay_range[1])
        
        print(f"\n\n{'='*60}")
        print(f"🎉 所有电视剧爬取完成！")
        print(f"📊 总计: {len(all_episodes)} 个剧集")
        print(f"{'='*60}")
        
        return all_episodes


if __name__ == "__main__":
    # 测试电视剧爬虫
    scraper = TVSeriesScraper(delay_range=(0.5, 1))
    
    # 测试爬取单部电视剧
    print("🧪 测试爬取单部电视剧的前3集...")
    test_url = "https://ww9.cuevana3.to/serie/teheran"
    
    soup = scraper._fetch_page(test_url)
    if soup:
        episode_urls = scraper._extract_episode_urls_from_series_page(soup)
        print(f"\n找到 {len(episode_urls)} 个剧集")
        
        # 只爬取前3集作为测试
        for url in episode_urls[:3]:
            episode_data = scraper._extract_episode_details(url)
            if episode_data:
                print(f"\n剧集数据:")
                for key, value in episode_data.items():
                    print(f"  {key}: {value}")
