#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电影爬虫模块
爬取 Cuevana3 网站的电影数据
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


class MovieScraper:
    """电影爬虫类"""
    
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
                    verify=False  # 禁用SSL验证
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
    
    def _extract_movie_urls_from_list(self, soup: BeautifulSoup) -> List[str]:
        """
        从列表页提取电影URL
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            电影URL列表
        """
        urls = []
        
        # 查找所有电影卡片
        # 通常在 div[id^="post-"] 或 article 中
        movie_items = soup.find_all('div', id=re.compile(r'^post-'))
        
        if not movie_items:
            # 备用方案：查找所有包含电影链接的 a 标签
            movie_items = soup.find_all('article') or soup.find_all('div', class_=re.compile(r'movie|item|post'))
        
        for item in movie_items:
            link = item.find('a', href=True)
            if link:
                href = link.get('href')
                # 电影链接格式: /数字/slug
                if href and re.match(r'/\d+/[a-z0-9-]+$', href) and '/episodio/' not in href:
                    full_url = urljoin(self.BASE_URL, href)
                    if full_url not in urls:
                        urls.append(full_url)
        
        return urls
    
    def _extract_movie_details(self, url: str) -> Optional[Dict]:
        """
        提取电影详情
        
        Args:
            url: 电影详情页URL
            
        Returns:
            电影数据字典或None
        """
        soup = self._fetch_page(url)
        if not soup:
            return None
        
        try:
            movie_data = {'url': url}
            
            # 提取西语标题
            title_h1 = soup.find('h1', class_='Title')
            if title_h1:
                movie_data['title_spanish'] = title_h1.get_text(strip=True)
            
            # 提取原标题
            title_h2 = soup.find('h2', class_='SubTitle')
            if title_h2:
                original_title = title_h2.get_text(strip=True)
                # 移除 "Civil: " 前缀
                if original_title.startswith('Civil: '):
                    original_title = original_title[7:]
                movie_data['title_original'] = original_title
            
            # 提取元数据
            meta = soup.find('p', class_='meta')
            if meta:
                spans = meta.find_all('span')
                if len(spans) >= 3:
                    # 评分
                    rating_text = spans[0].get_text(strip=True)
                    rating_match = re.search(r'([\d.]+)', rating_text)
                    if rating_match:
                        movie_data['rating'] = float(rating_match.group(1))
                    
                    # 年份
                    year_text = spans[1].get_text(strip=True)
                    year_match = re.search(r'(\d{4})', year_text)
                    if year_match:
                        movie_data['year'] = int(year_match.group(1))
                    
                    # 清晰度
                    quality_text = spans[2].get_text(strip=True)
                    movie_data['quality'] = quality_text
            
            return movie_data
        
        except Exception as e:
            print(f"⚠️  提取电影详情失败 {url}: {e}")
            return None
    
    def scrape_year(self, year: int, max_pages: Optional[int] = None) -> List[Dict]:
        """
        爬取指定年份的电影
        
        Args:
            year: 年份
            max_pages: 最大页数限制（None表示爬取所有页）
            
        Returns:
            电影数据列表
        """
        all_movies = []
        page = 1
        
        print(f"\n{'='*60}")
        print(f"🎬 开始爬取 {year} 年的电影...")
        print(f"{'='*60}")
        
        while True:
            if max_pages and page > max_pages:
                break
            
            # 构建 URL - 使用正确的格式
            if page == 1:
                url = f"{self.BASE_URL}/year/{year}"
            else:
                url = f"{self.BASE_URL}/year/{year}/page/{page}"
            
            print(f"\n📄 正在爬取第 {page} 页: {url}")
            
            soup = self._fetch_page(url)
            if not soup:
                print(f"⚠️  跳过第 {page} 页")
                break
            
            # 提取电影URL
            movie_urls = self._extract_movie_urls_from_list(soup)
            
            if not movie_urls:
                print(f"✅ 第 {page} 页没有更多电影，结束爬取")
                break
            
            print(f"   找到 {len(movie_urls)} 个电影链接")
            
            # 爬取每部电影的详情
            for idx, movie_url in enumerate(movie_urls, 1):
                print(f"   [{idx}/{len(movie_urls)}] 正在爬取: {movie_url}")
                
                movie_data = self._extract_movie_details(movie_url)
                if movie_data:
                    all_movies.append(movie_data)
                    print(f"      ✅ {movie_data.get('title_spanish', 'Unknown')}")
                
                # 延迟
                self._random_delay()
            
            page += 1
            
            # 检查是否有下一页
            pagination = soup.find('nav', class_='pagination')
            if not pagination:
                break
            
            next_link = pagination.find('a', class_='next')
            if not next_link:
                break
        
        print(f"\n✨ {year} 年爬取完成！共 {len(all_movies)} 部电影")
        return all_movies
    
    def scrape_multiple_years(
        self, 
        start_year: int, 
        end_year: int, 
        reverse: bool = True,
        max_pages_per_year: Optional[int] = None
    ) -> List[Dict]:
        """
        爬取多个年份的电影
        
        Args:
            start_year: 起始年份
            end_year: 结束年份
            reverse: 是否倒序（从最新年份开始）
            max_pages_per_year: 每个年份的最大页数
            
        Returns:
            所有电影数据列表
        """
        all_movies = []
        
        years = list(range(start_year, end_year + 1))
        if reverse:
            years.reverse()
        
        print(f"\n🌟 开始爬取年份范围: {start_year} - {end_year}")
        print(f"📅 爬取顺序: {' → '.join(map(str, years))}")
        
        for idx, year in enumerate(years, 1):
            print(f"\n\n{'#'*60}")
            print(f"# 进度: {idx}/{len(years)} | 当前年份: {year}")
            print(f"{'#'*60}")
            
            movies = self.scrape_year(year, max_pages=max_pages_per_year)
            all_movies.extend(movies)
            
            if idx < len(years):
                print(f"\n⏳ 等待 {self.delay_range[1]} 秒后继续...")
                time.sleep(self.delay_range[1])
        
        print(f"\n\n{'='*60}")
        print(f"🎉 所有年份爬取完成！")
        print(f"📊 总计: {len(all_movies)} 部电影")
        print(f"{'='*60}")
        
        return all_movies


if __name__ == "__main__":
    # 测试电影爬虫
    scraper = MovieScraper(delay_range=(0.5, 1))
    
    # 测试爬取单个年份（只爬取第1页）
    print("🧪 测试爬取 2025 年第1页...")
    movies = scraper.scrape_year(2025, max_pages=1)
    
    print(f"\n📊 爬取结果:")
    print(f"   总数: {len(movies)}")
    
    if movies:
        print(f"\n📝 示例数据（前3条）:")
        for movie in movies[:3]:
            print(f"\n   标题: {movie.get('title_spanish')}")
            print(f"   原标题: {movie.get('title_original')}")
            print(f"   年份: {movie.get('year')}")
            print(f"   评分: {movie.get('rating')}")
            print(f"   清晰度: {movie.get('quality')}")
            print(f"   URL: {movie.get('url')}")
