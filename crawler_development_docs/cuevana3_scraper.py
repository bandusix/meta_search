#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cuevana3 电影爬虫
用于爬取 cuevana3.top 网站上指定年份范围的电影数据
支持从最新年份开始倒序爬取
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import argparse
from typing import List, Dict, Optional
import sys
from datetime import datetime


class Cuevana3Scraper:
    """Cuevana3 网站爬虫类"""
    
    # User-Agent 列表，用于随机选择
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    def __init__(self, delay_range: tuple = (1, 3)):
        """
        初始化爬虫
        
        Args:
            delay_range: 请求延迟范围（秒），默认 (1, 3)
        """
        self.delay_range = delay_range
        self.session = requests.Session()
        
    def _get_random_headers(self) -> Dict[str, str]:
        """获取随机 User-Agent 请求头"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def _random_delay(self):
        """随机延迟，模拟人类行为"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        获取页面内容
        
        Args:
            url: 目标 URL
            
        Returns:
            BeautifulSoup 对象，如果失败则返回 None
        """
        try:
            response = self.session.get(
                url,
                headers=self._get_random_headers(),
                timeout=30
            )
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {url}")
            print(f"   错误信息: {e}")
            return None
    
    def _extract_movies_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        从页面中提取电影数据
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            电影数据列表，每个元素包含 'Title' 和 'URL'
        """
        movies = []
        
        # 查找所有电影条目
        posts = soup.select('div[id^="post-"]')
        
        for post in posts:
            try:
                # 提取 URL
                link = post.select_one('a[href*="/pelicula/"]')
                if not link:
                    continue
                url = link.get('href', '').strip()
                
                # 提取标题
                title_div = post.select_one('div.Title')
                if not title_div:
                    continue
                
                # 复制标题元素以避免修改原始 DOM
                title_div_copy = title_div.__copy__()
                
                # 移除所有 span 标签（如 "PELÍCULA" 标签）
                for span in title_div_copy.find_all('span'):
                    span.decompose()
                
                title = title_div_copy.get_text(strip=True)
                
                # 验证数据有效性
                if url and title:
                    movies.append({
                        'Title': title,
                        'URL': url
                    })
            except Exception as e:
                print(f"⚠️  提取电影数据时出错: {e}")
                continue
        
        return movies
    
    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        获取总页数
        
        Args:
            soup: BeautifulSoup 对象
            
        Returns:
            总页数，如果无法确定则返回 1
        """
        try:
            # 查找分页导航中的最后一个页码链接
            pagination = soup.select('nav.pagination a.page-link')
            
            if not pagination:
                return 1
            
            # 获取所有页码
            page_numbers = []
            for link in pagination:
                text = link.get_text(strip=True)
                if text.isdigit():
                    page_numbers.append(int(text))
            
            return max(page_numbers) if page_numbers else 1
        except Exception as e:
            print(f"⚠️  获取总页数时出错: {e}")
            return 1
    
    def scrape_year(self, year: int) -> List[Dict[str, str]]:
        """
        爬取指定年份的电影数据
        
        Args:
            year: 目标年份
            
        Returns:
            该年份的所有电影数据列表
        """
        all_movies = []
        base_url = f"https://cuevana3.top/estreno/{year}/"
        
        print(f"\n{'='*60}")
        print(f"🎬 开始爬取 {year} 年的电影数据...")
        print(f"📍 基础 URL: {base_url}")
        print(f"{'='*60}")
        
        # 获取第一页以确定总页数
        print(f"\n📄 正在获取第 1 页...")
        soup = self._fetch_page(base_url)
        
        if not soup:
            print(f"❌ 无法获取 {year} 年的第一页，跳过该年份")
            return all_movies
        
        # 提取第一页的数据
        movies = self._extract_movies_from_page(soup)
        all_movies.extend(movies)
        print(f"   ✅ 提取到 {len(movies)} 部电影")
        
        # 获取总页数
        total_pages = self._get_total_pages(soup)
        print(f"\n📊 总页数: {total_pages}")
        
        # 遍历剩余页面
        for page_num in range(2, total_pages + 1):
            # 随机延迟
            self._random_delay()
            
            # 构建页面 URL
            page_url = f"{base_url}page/{page_num}/"
            print(f"\n📄 正在获取第 {page_num}/{total_pages} 页...")
            
            # 获取页面
            soup = self._fetch_page(page_url)
            
            if not soup:
                print(f"   ⚠️  跳过第 {page_num} 页")
                continue
            
            # 提取数据
            movies = self._extract_movies_from_page(soup)
            all_movies.extend(movies)
            print(f"   ✅ 提取到 {len(movies)} 部电影")
        
        print(f"\n✨ {year} 年爬取完成！共提取到 {len(all_movies)} 部电影")
        return all_movies
    
    def scrape_multiple_years(self, start_year: int, end_year: int, reverse: bool = True) -> List[Dict[str, str]]:
        """
        爬取多个年份的电影数据
        
        Args:
            start_year: 起始年份
            end_year: 结束年份
            reverse: 是否倒序爬取（从最新年份开始），默认 True
            
        Returns:
            所有年份的电影数据列表
        """
        all_movies = []
        
        # 生成年份列表
        years = list(range(start_year, end_year + 1))
        
        # 如果需要倒序，则反转列表（从最新年份开始）
        if reverse:
            years.reverse()
        
        print(f"\n🌟 开始爬取年份范围: {start_year} - {end_year}")
        print(f"📅 爬取顺序: {' → '.join(map(str, years))}")
        
        # 遍历所有年份
        for idx, year in enumerate(years, 1):
            print(f"\n\n{'#'*60}")
            print(f"# 进度: {idx}/{len(years)} | 当前年份: {year}")
            print(f"{'#'*60}")
            
            # 爬取该年份
            movies = self.scrape_year(year)
            
            # 添加年份信息到每条记录
            for movie in movies:
                movie['Year'] = year
            
            all_movies.extend(movies)
            
            # 如果不是最后一个年份，添加延迟
            if idx < len(years):
                print(f"\n⏳ 等待 {self.delay_range[1]} 秒后继续下一年份...")
                time.sleep(self.delay_range[1])
        
        print(f"\n\n{'='*60}")
        print(f"🎉 所有年份爬取完成！")
        print(f"📊 总计提取到 {len(all_movies)} 部电影")
        print(f"{'='*60}")
        
        return all_movies
    
    def save_to_csv(self, movies: List[Dict[str, str]], filename: str):
        """
        保存数据到 CSV 文件
        
        Args:
            movies: 电影数据列表
            filename: 输出文件名
        """
        try:
            if not movies:
                print("\n⚠️  没有数据可保存")
                return
            
            # 确定字段名（如果包含 Year 字段，则添加到列中）
            fieldnames = ['Title', 'URL']
            if movies and 'Year' in movies[0]:
                fieldnames = ['Year', 'Title', 'URL']
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(movies)
            
            print(f"\n💾 数据已保存到: {filename}")
            print(f"📝 文件包含 {len(movies)} 条记录")
        except Exception as e:
            print(f"\n❌ 保存 CSV 文件时出错: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Cuevana3 电影爬虫 - 爬取指定年份或年份范围的电影数据（支持倒序爬取）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 爬取单个年份
  python cuevana3_scraper.py 2024
  
  # 爬取年份范围（倒序：从2025到2020）
  python cuevana3_scraper.py 2020 2025
  
  # 爬取年份范围（正序：从2020到2025）
  python cuevana3_scraper.py 2020 2025 --no-reverse
  
  # 指定输出文件名
  python cuevana3_scraper.py 2024 -o movies_2024.csv
  
  # 自定义延迟时间
  python cuevana3_scraper.py 2024 --delay 2 4
        """
    )
    
    parser.add_argument(
        'start_year',
        type=int,
        help='起始年份（如果只提供一个年份，则只爬取该年份）'
    )
    
    parser.add_argument(
        'end_year',
        type=int,
        nargs='?',
        default=None,
        help='结束年份（可选，用于爬取年份范围）'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default=None,
        help='输出 CSV 文件名（默认：cuevana3_{year}.csv 或 cuevana3_{start}-{end}.csv）'
    )
    
    parser.add_argument(
        '--delay',
        type=float,
        nargs=2,
        default=[1, 3],
        metavar=('MIN', 'MAX'),
        help='请求延迟范围（秒），默认 1-3 秒'
    )
    
    parser.add_argument(
        '--no-reverse',
        action='store_true',
        help='不使用倒序爬取（默认从最新年份开始倒序爬取）'
    )
    
    args = parser.parse_args()
    
    # 确定是单年份还是年份范围
    if args.end_year is None:
        # 单年份模式
        single_year = args.start_year
        output_file = args.output or f"cuevana3_{single_year}.csv"
        
        print(f"\n{'='*60}")
        print(f"🎯 模式: 单年份爬取")
        print(f"📅 目标年份: {single_year}")
        print(f"💾 输出文件: {output_file}")
        print(f"⏱️  延迟范围: {args.delay[0]}-{args.delay[1]} 秒")
        print(f"{'='*60}")
        
        # 创建爬虫实例
        scraper = Cuevana3Scraper(delay_range=tuple(args.delay))
        
        # 执行爬取
        try:
            movies = scraper.scrape_year(single_year)
            
            if movies:
                scraper.save_to_csv(movies, output_file)
            else:
                print("\n⚠️  未提取到任何数据")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断爬取")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 发生未预期的错误: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        # 年份范围模式
        start_year = min(args.start_year, args.end_year)
        end_year = max(args.start_year, args.end_year)
        reverse = not args.no_reverse
        
        output_file = args.output or f"cuevana3_{start_year}-{end_year}.csv"
        
        print(f"\n{'='*60}")
        print(f"🎯 模式: 年份范围爬取")
        print(f"📅 年份范围: {start_year} - {end_year}")
        print(f"🔄 爬取顺序: {'倒序（从最新开始）' if reverse else '正序（从最旧开始）'}")
        print(f"💾 输出文件: {output_file}")
        print(f"⏱️  延迟范围: {args.delay[0]}-{args.delay[1]} 秒")
        print(f"{'='*60}")
        
        # 创建爬虫实例
        scraper = Cuevana3Scraper(delay_range=tuple(args.delay))
        
        # 执行爬取
        try:
            movies = scraper.scrape_multiple_years(start_year, end_year, reverse=reverse)
            
            if movies:
                scraper.save_to_csv(movies, output_file)
            else:
                print("\n⚠️  未提取到任何数据")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  用户中断爬取")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ 发生未预期的错误: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
