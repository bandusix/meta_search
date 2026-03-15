#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扩展解析功能 - 电视剧、综艺、动漫等列表解析
"""

from typing import List, Dict
import lxml.html
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)

class TVParserUtils:
    """电视剧相关解析工具"""
    
    @staticmethod
    def parse_tv_list(html_content: str, base_url: str) -> List[Dict]:
        """解析电视剧/综艺/动漫列表页面"""
        try:
            doc = lxml.html.fromstring(html_content)
            series = []
            
            # 根据97han网站结构解析电视剧列表
            series_items = doc.xpath('//div[@class="tv-item"]//a[@class="tv-link"]')
            
            for item in series_items:
                series_url = item.get('href', '')
                if not series_url:
                    continue
                
                series_url = urljoin(base_url, series_url)
                
                # 提取封面图
                cover_img = item.xpath('.//img[@class="cover"]/@src')
                cover = cover_img[0] if cover_img else ''
                
                # 提取标题
                title_elem = item.xpath('.//div[@class="title"]//text()')
                title = title_elem[0].strip() if title_elem else ''
                
                # 提取年份
                year_elem = item.xpath('.//span[@class="year"]//text()')
                year = int(year_elem[0].strip()) if year_elem and year_elem[0].strip().isdigit() else None
                
                # 提取集数信息
                episodes_elem = item.xpath('.//span[@class="episodes"]//text()')
                total_episodes = 0
                if episodes_elem:
                    # 提取数字（如"30集全"中的30）
                    import re
                    match = re.search(r'(\d+)', episodes_elem[0])
                    if match:
                        total_episodes = int(match.group(1))
                
                # 提取vod_id（从URL中提取）
                vod_id = 0
                import re
                match = re.search(r'/(\d+)\.html', series_url)
                if match:
                    vod_id = int(match.group(1))
                
                series.append({
                    'detail_url': series_url,
                    'cover': cover,
                    'title': title,
                    'year': year,
                    'total_episodes': total_episodes,
                    'vod_id': vod_id
                })
            
            logger.info(f"📺 解析电视剧列表: 找到 {len(series)} 部剧集")
            return series
            
        except Exception as e:
            logger.error(f"❌ 解析电视剧列表失败: {str(e)}")
            return []
    
    @staticmethod
    def parse_tv_detail(html_content: str, detail_url: str) -> Dict:
        """解析电视剧详情页面"""
        try:
            doc = lxml.html.fromstring(html_content)
            
            # 提取基本信息
            title = TVParserUtils._extract_text(doc, '//h1[@class="title"]//text()')
            original_title = TVParserUtils._extract_text(doc, '//div[@class="original-title"]//text()')
            year = TVParserUtils._extract_number(doc, '//span[@class="year"]//text()')
            region = TVParserUtils._extract_text(doc, '//span[@class="region"]//text()')
            genre = TVParserUtils._extract_text(doc, '//span[@class="genre"]//text()')
            intro = TVParserUtils._extract_text(doc, '//div[@class="synopsis"]//text()')
            
            # 提取播放线路和剧集信息
            play_lines = TVParserUtils._extract_tv_play_lines(doc, detail_url)
            
            return {
                'title': title,
                'original_title': original_title,
                'year': year,
                'region': region,
                'genre': genre,
                'intro': intro,
                'play_lines': play_lines,
                'total_episodes': len(play_lines)
            }
            
        except Exception as e:
            logger.error(f"❌ 解析电视剧详情失败: {detail_url} - {str(e)}")
            return {}
    
    @staticmethod
    def _extract_tv_play_lines(doc, detail_url: str) -> List[Dict]:
        """提取电视剧播放线路和剧集信息"""
        play_lines = []
        
        try:
            # 查找播放线路容器
            line_containers = doc.xpath('//div[@class="tv-play-lines"]//div[@class="line-item"]')
            
            for container in line_containers:
                # 提取线路名称
                line_name = TVParserUtils._extract_text(container, './/span[@class="line-name"]//text()')
                if not line_name:
                    continue
                
                # 提取剧集列表
                episode_links = container.xpath('.//div[@class="episode-list"]//a[@class="episode-link"]')
                
                for i, link in enumerate(episode_links, 1):
                    play_url = link.get('href', '')
                    episode_title = TVParserUtils._extract_text(link, './/text()')
                    
                    if play_url:
                        play_lines.append({
                            'route_name': line_name,
                            'play_url': urljoin(detail_url, play_url),
                            'episode_title': episode_title.strip() if episode_title else f'第{i}集',
                            'episode_number': i
                        })
            
            logger.info(f"📺 解析电视剧播放线路: 找到 {len(play_lines)} 个剧集链接")
            return play_lines
            
        except Exception as e:
            logger.error(f"❌ 提取电视剧播放线路失败: {str(e)}")
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
    def _extract_number(doc, xpath: str) -> int:
        """提取数字内容"""
        try:
            text = TVParserUtils._extract_text(doc, xpath)
            if text and text.isdigit():
                return int(text)
            return 0
        except:
            return 0

# 将TV解析器添加到主解析模块中
def parse_tv_list(html_content: str, base_url: str) -> List[Dict]:
    """解析电视剧列表（兼容接口）"""
    return TVParserUtils.parse_tv_list(html_content, base_url)

def parse_tv_detail(html_content: str, detail_url: str) -> Dict:
    """解析电视剧详情（兼容接口）"""
    return TVParserUtils.parse_tv_detail(html_content, detail_url)