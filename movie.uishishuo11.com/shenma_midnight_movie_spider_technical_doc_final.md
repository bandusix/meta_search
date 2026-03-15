# 神马午夜电影网 (movie.uishishuo11.com) 爬虫系统技术文档

**版本**: v1.0  
**日期**: 2026-02-12  
**目标网站**: http://movie.uishishuo11.com/  
**网站名称**: 神马午夜电影网  
**CMS系统**: 苹果CMS (MacCMS) V10  
**文档类型**: 爬虫实现技术指南（仅调研，不执行爬虫）

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [网站结构分析](#2-网站结构分析)
3. [URL路由体系](#3-url路由体系)
4. [HTML结构与CSS选择器](#4-html结构与css选择器)
5. [数据库设计](#5-数据库设计)
6. [电影爬虫模块实现](#6-电影爬虫模块实现)
7. [电视剧爬虫模块实现](#7-电视剧爬虫模块实现)
8. [数据导出模块](#8-数据导出模块)
9. [主程序与命令行接口](#9-主程序与命令行接口)
10. [反爬虫策略](#10-反爬虫策略)

---

## 1. 项目概述

### 1.1 需求摘要

本项目旨在开发一个 Python 爬虫系统，用于从神马午夜电影网爬取影视媒资数据。网站基于 **苹果CMS V10** 构建，使用 **myui** 模板，包含电影、电视剧、综艺、动漫等多种内容分类。

### 1.2 功能需求

| 功能 | 描述 | 优先级 |
|------|------|--------|
| 电影数据爬取 | 按年份爬取所有电影（1945-2026） | P0 |
| 电视剧数据爬取 | 爬取所有电视剧及其集数列表 | P0 |
| 自动翻页 | 遍历所有分页 | P0 |
| 倒序爬取 | 从最新年份开始 | P0 |
| 数据库存储 | SQLite 双表存储 | P0 |
| CSV导出 | 增量和存量导出 | P0 |
| 自动去重 | 基于URL去重 | P0 |
| 增量更新 | 支持增量更新 | P0 |

### 1.3 技术栈

| 组件 | 选型 | 说明 |
|------|------|------|
| 语言 | Python 3.8+ | 主要开发语言 |
| HTTP客户端 | requests | 网络请求 |
| HTML解析 | BeautifulSoup4 + lxml | 页面解析 |
| 数据库 | SQLite3 | 轻量级本地存储 |
| 数据导出 | csv (标准库) | CSV格式输出 |

---

## 2. 网站结构分析

### 2.1 基本信息

| 属性 | 值 |
|------|-----|
| 域名 | movie.uishishuo11.com |
| 网站名称 | 神马午夜电影网 |
| CMS系统 | 苹果CMS (MacCMS) V10 |
| 模板 | myui |
| 编码 | UTF-8 |

### 2.2 内容分类体系

| 大类 | 分类ID (cid) | URL | 说明 |
|------|-------------|-----|------|
| 电影 | 1 | /dongman/1.html | 电影列表 |
| 电视剧 | 2 | /dongman/2.html | 电视剧列表 |
| 综艺 | 3 | /dongman/3.html | 综艺列表 |
| 动漫 | 4 | /dongman/4.html | 动漫列表 |

---

## 3. URL路由体系

### 3.1 完整URL格式表

| 页面类型 | URL格式 | 示例 |
|---------|---------|------|
| 首页 | `/` | `http://movie.uishishuo11.com/` |
| 列表页（分类） | `/dongman/{cid}.html` | `/dongman/1.html` |
| 列表页（分页） | `/dongman/{cid}-{page}.html` | `/dongman/1-2.html` |
| 影片详情页 | `/guankan/{vod_id}.html` | `/guankan/164883.html` |
| 播放页（集数） | `/bofang/{vod_id}-{source}-{episode}.html` | `/bofang/157410-1-1.html` |

### 3.2 URL构造规则

```python
def build_list_url(cid, page=1):
    """构造列表页URL"""
    if page == 1:
        return f"http://movie.uishishuo11.com/dongman/{cid}.html"
    else:
        return f"http://movie.uishishuo11.com/dongman/{cid}-{page}.html"

def build_detail_url(vod_id):
    """构造详情页URL"""
    return f"http://movie.uishishuo11.com/guankan/{vod_id}.html"

def build_play_url(vod_id, source=1, episode=1):
    """构造播放页URL"""
    return f"http://movie.uishishuo11.com/bofang/{vod_id}-{source}-{episode}.html"
```

---

## 4. HTML结构与CSS选择器

### 4.1 推荐User-Agent

```python
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
```

### 4.2 列表页结构

```html
<!-- 电影卡片 -->
<a href="/guankan/164883.html">
  <span>5.0分</span>
  <span>HD</span>
</a>
<a href="/guankan/164883.html">男孩2026</a>
```

**CSS选择器速查表（列表页）**:

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 详情页URL | `a[href*="guankan"]` | `.get('href')` |
| 评分 | `span` 包含"分" | `text.replace('分', '')` |
| 状态 | `span` 包含"正片/HD/完结"等 | `.text.strip()` |
| 标题 | 第二个`a`标签 | `.text.strip()` |

### 4.3 详情页结构

```html
<div class="myui-content__detail">
  <h1>男孩2026</h1>
  <p>
    <span>评分：</span><span>5.0</span><span>还行</span>
    <span>分类：</span><span>动作片</span>
    <span>地区：</span><span>韩国</span>
    <span>年份：</span><span>2026</span>
    <span>更新：</span><span>HD</span>
    <span>时间：</span><span>2026-02-14</span>
    <span>主演：</span><span>赵炳奎,柳仁秀...</span>
    <span>导演：</span><span>李尚德</span>
    <span>简介：</span><span>影片简介...</span>
  </p>
</div>
```

**CSS选择器速查表（详情页）**:

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 标题 | `h1` 或 `h2` | `.text.strip()` |
| 评分 | `.myui-content__detail span` 包含"评分" | 下一个兄弟元素 |
| 分类 | 同上 | 正则提取 |
| 地区 | 同上 | 正则提取 |
| 年份 | 同上 | 正则提取数字 |
| 状态 | `span` 包含"更新" | 下一个兄弟元素 |
| 导演 | `span` 包含"导演" | 父元素文本 |
| 主演 | `span` 包含"主演" | 父元素文本 |
| 简介 | `span` 包含"简介" | 父元素文本 |

### 4.4 播放列表结构（电视剧集数）

```html
<li>
  <a class="btn btn-default" href="/bofang/157410-1-1.html">第01集</a>
</li>
```

**CSS选择器速查表（播放列表）**:

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 集数链接 | `li a[href*="bofang"]` | `.get('href')` |
| 集数标题 | 同上 | `.text.strip()` |
| 集数编号 | 同上 | 正则提取数字 |

### 4.5 电影 vs 电视剧区分方法

**方法1：通过分类ID区分**（推荐）

```python
MOVIE_CID = 1
TV_CID = 2
```

**方法2：通过状态文本区分**

```python
status = soup.select_one('.status').text.strip()
# 电影状态: "正片", "HD", "预告片"
# 电视剧状态: "第XX集", "更新至XX集", "全XX集", "已完结"
is_tv_series = any(kw in status for kw in ['集', '完结', '更新'])
```

---

## 5. 数据库设计

### 5.1 电影表 (movies)

```sql
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vod_id INTEGER UNIQUE NOT NULL,          -- 视频ID
    title TEXT NOT NULL,                      -- 标题
    original_title TEXT,                      -- 原标题
    category TEXT DEFAULT '',                 -- 分类
    region TEXT DEFAULT '',                   -- 地区
    year INTEGER DEFAULT 0,                  -- 年份
    director TEXT DEFAULT '',                -- 导演
    actors TEXT DEFAULT '',                  -- 主演
    status TEXT DEFAULT '',                  -- 状态
    rating REAL DEFAULT 0.0,                 -- 评分
    poster_url TEXT DEFAULT '',              -- 海报图URL
    detail_url TEXT NOT NULL,                -- 详情页URL
    synopsis TEXT DEFAULT '',                -- 简介
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
CREATE INDEX IF NOT EXISTS idx_movies_created_at ON movies(created_at);
```

### 5.2 电视剧主表 (tv_series)

```sql
CREATE TABLE IF NOT EXISTS tv_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vod_id INTEGER UNIQUE NOT NULL,          -- 视频ID
    title TEXT NOT NULL,                      -- 剧名
    original_title TEXT,                      -- 原标题
    category TEXT DEFAULT '',                 -- 分类
    region TEXT DEFAULT '',                   -- 地区
    year INTEGER DEFAULT 0,                  -- 年份
    director TEXT DEFAULT '',                -- 导演
    actors TEXT DEFAULT '',                  -- 主演
    status TEXT DEFAULT '',                  -- 状态
    season INTEGER DEFAULT 1,                -- 季数
    total_episodes INTEGER,                  -- 总集数
    current_episode INTEGER,                 -- 当前更新到的集数
    rating REAL DEFAULT 0.0,                 -- 评分
    poster_url TEXT DEFAULT '',              -- 海报图URL
    detail_url TEXT NOT NULL,                -- 详情页URL
    synopsis TEXT DEFAULT '',                -- 简介
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
CREATE INDEX IF NOT EXISTS idx_tv_series_year ON tv_series(year);
CREATE INDEX IF NOT EXISTS idx_tv_series_created_at ON tv_series(created_at);
```

### 5.3 电视剧集数表 (tv_episodes)

```sql
CREATE TABLE IF NOT EXISTS tv_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vod_id INTEGER NOT NULL,                 -- 关联tv_series.vod_id
    episode_number INTEGER NOT NULL,         -- 集数编号
    episode_title TEXT DEFAULT '',           -- 集数标题
    play_url TEXT NOT NULL,                  -- 播放页URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vod_id, episode_number)           -- 去重
);

CREATE INDEX IF NOT EXISTS idx_tv_episodes_vod_id ON tv_episodes(vod_id);
```

### 5.4 导出日志表 (export_logs)

```sql
CREATE TABLE IF NOT EXISTS export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    export_type TEXT NOT NULL,               -- 'full' 或 'incremental'
    filepath TEXT NOT NULL,
    row_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. 电影爬虫模块实现

```python
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
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# 配置
BASE_URL = "http://movie.uishishuo11.com"
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
DEFAULT_DELAY = (1, 3)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MovieSpider:
    """电影爬虫"""
    
    def __init__(self, db_path='spider.db', delay=DEFAULT_DELAY):
        self.db_path = db_path
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': IPHONE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        })
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
            """)
    
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
                else:
                    logger.warning(f"HTTP {response.status_code}: {full_url}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"请求错误 ({attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def build_list_url(self, cid, page=1):
        """构造列表页URL"""
        if page == 1:
            return f"{BASE_URL}/dongman/{cid}.html"
        else:
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
        has_next = bool(soup.find('a', href=re.compile(rf'/dongman/1-\d+\.html')))
        
        return movies, has_next
    
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
                match = re.search(r'分类：(.+?)地区：(.+?)年份：(\d+)', full_text)
                if match:
                    data['category'] = match.group(1)
                    data['region'] = match.group(2)
                    data['year'] = int(match.group(3))
            
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
        poster = soup.find('img', class_='img-responsive')
        if poster:
            data['poster_url'] = poster.get('data-original') or poster.get('src', '')
        
        return data
    
    def save_movie(self, conn, movie):
        """保存电影（Upsert）"""
        conn.execute("""
            INSERT INTO movies (vod_id, title, original_title, category, region, year,
                               director, actors, status, rating, poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                updated_at=CURRENT_TIMESTAMP
        """, (
            movie.get('vod_id'), movie.get('title', ''),
            movie.get('original_title'), movie.get('category', ''),
            movie.get('region', ''), movie.get('year', 0),
            movie.get('director', ''), movie.get('actors', ''),
            movie.get('status', ''), movie.get('rating', 0.0),
            movie.get('poster_url', ''), movie.get('detail_url', ''),
            movie.get('synopsis', '')
        ))
        conn.commit()
    
    def crawl(self, year_start=1945, year_end=2026, max_pages=None):
        """
        爬取电影
        
        参数:
            year_start: 开始年份
            year_end: 结束年份
            max_pages: 每年份最大页数
        """
        # 倒序遍历年份
        years = list(range(year_end, year_start - 1, -1))
        total_count = 0
        
        for year in years:
            logger.info(f"\n{'='*60}\n开始爬取 {year} 年电影\n{'='*60}")
            
            page = 1
            while True:
                if max_pages and page > max_pages:
                    break
                
                url = self.build_list_url(1, page)
                response = self.request(url)
                
                if not response:
                    break
                
                soup = BeautifulSoup(response.text, 'lxml')
                movies, has_next = self.parse_list_page(soup)
                
                if not movies:
                    break
                
                with sqlite3.connect(self.db_path) as conn:
                    for movie in movies:
                        try:
                            # 详情页
                            detail_resp = self.request(movie['detail_url'])
                            if detail_resp:
                                detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                                movie.update(self.parse_detail_page(detail_soup))
                            
                            # 过滤年份（如果按年份爬取）
                            if movie.get('year') == year or year == 0:
                                self.save_movie(conn, movie)
                                total_count += 1
                                logger.info(f"✅ [{total_count}] {movie['title']}")
                            
                        except Exception as e:
                            logger.error(f"❌ 处理失败: {e}")
                
                if not has_next:
                    break
                page += 1
        
        logger.info(f"\n🎉 电影爬取完成！共 {total_count} 部")
        return total_count
```

---

## 7. 电视剧爬虫模块实现

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
神马午夜电影网 - 电视剧爬虫模块
"""

import re
import sqlite3
from movie_spider import MovieSpider
from bs4 import BeautifulSoup
from urllib.parse import urljoin


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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tv_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER NOT NULL,
                    episode_number INTEGER NOT NULL,
                    episode_title TEXT DEFAULT '',
                    play_url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vod_id, episode_number)
                );
                
                CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
                CREATE INDEX IF NOT EXISTS idx_tv_episodes_vod_id ON tv_episodes(vod_id);
            """)
    
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
        """解析详情页（电视剧专用）"""
        data = super().parse_detail_page(soup)
        
        # 提取播放列表（集数）
        episodes = []
        episode_links = soup.find_all('a', href=re.compile(r'/bofang/\d+-\d+-\d+\.html'))
        
        for link in episode_links:
            ep_text = link.text.strip()
            ep_href = link.get('href', '')
            
            # 提取集数编号
            ep_match = re.search(r'第(\d+)集', ep_text)
            ep_num = int(ep_match.group(1)) if ep_match else 0
            
            episodes.append({
                'episode_number': ep_num,
                'episode_title': ep_text,
                'play_url': urljoin(BASE_URL, ep_href)
            })
        
        # 去重并按集数排序
        seen = set()
        unique_episodes = []
        for ep in episodes:
            if ep['episode_number'] not in seen:
                seen.add(ep['episode_number'])
                unique_episodes.append(ep)
        
        unique_episodes.sort(key=lambda x: x['episode_number'])
        data['episodes'] = unique_episodes
        
        # 解析状态
        status_info = self.parse_status(data.get('status', ''))
        data.update(status_info)
        
        return data
    
    def save_tv_series(self, conn, series, episodes):
        """保存电视剧及集数"""
        # 保存剧集信息
        conn.execute("""
            INSERT INTO tv_series (vod_id, title, original_title, category, region, year,
                                  director, actors, status, season, total_episodes, current_episode,
                                  rating, poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                updated_at=CURRENT_TIMESTAMP
        """, (
            series.get('vod_id'), series.get('title', ''),
            series.get('original_title'), series.get('category', ''),
            series.get('region', ''), series.get('year', 0),
            series.get('director', ''), series.get('actors', ''),
            series.get('status', ''), series.get('season', 1),
            series.get('total_episodes'), series.get('current_episode'),
            series.get('rating', 0.0), series.get('poster_url', ''),
            series.get('detail_url', ''), series.get('synopsis', '')
        ))
        
        # 保存集数信息
        for ep in episodes:
            conn.execute("""
                INSERT INTO tv_episodes (vod_id, episode_number, episode_title, play_url)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(vod_id, episode_number) DO UPDATE SET
                    episode_title=excluded.episode_title,
                    play_url=excluded.play_url
            """, (
                series.get('vod_id'), ep.get('episode_number', 0),
                ep.get('episode_title', ''), ep.get('play_url', '')
            ))
        
        conn.commit()
    
    def crawl(self, year_start=None, year_end=None, max_pages=None, max_episodes=None):
        """
        爬取电视剧
        
        参数:
            year_start: 开始年份
            year_end: 结束年份
            max_pages: 每年份最大页数
            max_episodes: 每部剧最大集数限制
        """
        years = []
        if year_start and year_end:
            years = list(range(year_end, year_start - 1, -1))
        
        total_series = 0
        total_episodes = 0
        
        for year in years or ['']:
            year_str = f" {year}年" if year else ""
            logger.info(f"\n{'='*60}\n开始爬取{year_str}电视剧\n{'='*60}")
            
            page = 1
            while True:
                if max_pages and page > max_pages:
                    break
                
                url = self.build_list_url(2, page)
                response = self.request(url)
                
                if not response:
                    break
                
                soup = BeautifulSoup(response.text, 'lxml')
                series_list, has_next = self.parse_list_page(soup)
                
                if not series_list:
                    break
                
                with sqlite3.connect(self.db_path) as conn:
                    for series in series_list:
                        try:
                            # 详情页
                            detail_resp = self.request(series['detail_url'])
                            if detail_resp:
                                detail_soup = BeautifulSoup(detail_resp.text, 'lxml')
                                series.update(self.parse_detail_page(detail_soup))
                            
                            # 应用集数限制
                            episodes = series.pop('episodes', [])
                            if max_episodes:
                                episodes = episodes[:max_episodes]
                            
                            self.save_tv_series(conn, series, episodes)
                            
                            total_series += 1
                            total_episodes += len(episodes)
                            logger.info(f"✅ [{total_series}] {series['title']} ({len(episodes)}集)")
                            
                        except Exception as e:
                            logger.error(f"❌ 处理失败: {e}")
                
                if not has_next:
                    break
                page += 1
        
        logger.info(f"\n🎉 电视剧爬取完成！共 {total_series} 部剧，{total_episodes} 集")
        return total_series, total_episodes
```

---

## 8. 数据导出模块

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV导出器
"""

import csv
import os
import sqlite3
from datetime import datetime
from pathlib import Path


class CSVExporter:
    """CSV导出器"""
    
    def __init__(self, db_path='spider.db', output_dir='./exports'):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_movies(self, export_type='full'):
        """导出电影"""
        return self._export_table('movies', export_type)
    
    def export_tv_series(self, export_type='full'):
        """导出电视剧"""
        return self._export_table('tv_series', export_type)
    
    def export_tv_episodes(self, export_type='full'):
        """导出电视剧集数"""
        return self._export_table('tv_episodes', export_type)
    
    def _export_table(self, table_name, export_type='full'):
        """导出指定表"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{table_name}_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with sqlite3.connect(self.db_path) as conn:
            # 构建查询
            if export_type == 'incremental':
                last_time = self._get_last_export_time(conn, table_name)
                query = f"SELECT * FROM {table_name} WHERE created_at > ?"
                params = (last_time,)
            else:
                query = f"SELECT * FROM {table_name}"
                params = ()
            
            # 执行导出
            cursor = conn.execute(query, params)
            headers = [d[0] for d in cursor.description]
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                row_count = 0
                for row in cursor:
                    writer.writerow(row)
                    row_count += 1
            
            # 记录日志
            self._record_export_log(conn, table_name, export_type, filepath, row_count)
        
        print(f"导出完成: {filepath} ({row_count}条记录)")
        return filepath, row_count
    
    def _get_last_export_time(self, conn, table_name):
        """获取上次导出时间"""
        cursor = conn.execute("""
            SELECT created_at FROM export_logs 
            WHERE table_name = ? AND status = 'success'
            ORDER BY created_at DESC LIMIT 1
        """, (table_name,))
        result = cursor.fetchone()
        return result[0] if result else '1970-01-01 00:00:00'
    
    def _record_export_log(self, conn, table_name, export_type, filepath, row_count):
        """记录导出日志"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS export_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                export_type TEXT NOT NULL,
                filepath TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO export_logs (table_name, export_type, filepath, row_count)
            VALUES (?, ?, ?, ?)
        """, (table_name, export_type, str(filepath), row_count))
        conn.commit()
    
    def export_all(self):
        """导出所有数据"""
        results = {}
        results['movies'] = self.export_movies('full')
        results['tv_series'] = self.export_tv_series('full')
        results['tv_episodes'] = self.export_tv_episodes('full')
        return results
```

---

## 9. 主程序与命令行接口

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""主程序入口"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from spiders.movie_spider import MovieSpider
from spiders.tv_spider import TVSpider
from exporters.csv_exporter import CSVExporter


def main():
    parser = argparse.ArgumentParser(description='神马午夜电影网爬虫')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 电影爬虫
    movie_parser = subparsers.add_parser('movie', help='爬取电影')
    movie_parser.add_argument('--start-year', type=int, default=1945, help='开始年份')
    movie_parser.add_argument('--end-year', type=int, default=2026, help='结束年份')
    movie_parser.add_argument('--max-pages', type=int, help='每年份最大页数')
    movie_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 电视剧爬虫
    tv_parser = subparsers.add_parser('tv', help='爬取电视剧')
    tv_parser.add_argument('--start-year', type=int, help='开始年份')
    tv_parser.add_argument('--end-year', type=int, help='结束年份')
    tv_parser.add_argument('--max-pages', type=int, help='每年份最大页数')
    tv_parser.add_argument('--max-episodes', type=int, help='每部剧最大集数')
    tv_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 导出
    export_parser = subparsers.add_parser('export', help='导出数据')
    export_parser.add_argument('--type', choices=['movies', 'tv', 'tv_episodes', 'all'], 
                               default='all', help='导出类型')
    export_parser.add_argument('--export-type', choices=['full', 'incremental'],
                               default='full', help='导出方式')
    export_parser.add_argument('--output', type=str, default='./exports', help='输出目录')
    export_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    args = parser.parse_args()
    
    if args.command == 'movie':
        spider = MovieSpider(db_path=args.db)
        spider.crawl(
            year_start=args.start_year,
            year_end=args.end_year,
            max_pages=args.max_pages
        )
    
    elif args.command == 'tv':
        spider = TVSpider(db_path=args.db)
        spider.crawl(
            year_start=args.start_year,
            year_end=args.end_year,
            max_pages=args.max_pages,
            max_episodes=args.max_episodes
        )
    
    elif args.command == 'export':
        exporter = CSVExporter(db_path=args.db, output_dir=args.output)
        
        if args.type in ['movies', 'all']:
            exporter.export_movies(args.export_type)
        
        if args.type in ['tv', 'all']:
            exporter.export_tv_series(args.export_type)
        
        if args.type in ['tv_episodes', 'all']:
            exporter.export_tv_episodes(args.export_type)
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
```

### 使用示例

```bash
# 爬取电影（1945-2026，倒序）
python main.py movie

# 爬取2020-2025年电影
python main.py movie --start-year 2020 --end-year 2025

# 爬取所有电视剧
python main.py tv

# 爬取电视剧，每部剧最多10集
python main.py tv --max-episodes 10

# 导出所有数据（全量）
python main.py export

# 导出电影（增量）
python main.py export --type movies --export-type incremental
```

---

## 10. 反爬虫策略

| 策略 | 实现方式 |
|------|----------|
| User-Agent | 使用iPhone移动端UA |
| 随机延迟 | 每次请求间隔 1-3 秒随机 |
| 重试机制 | 失败时指数退避重试（最多3次） |
| 超时设置 | 15秒请求超时 |
| 连接复用 | 使用Session保持连接 |

---

**文档版本**: v1.0  
**最后更新**: 2026-02-12
