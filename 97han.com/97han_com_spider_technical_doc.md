# 97韩剧 (www.97han.com) 爬虫系统技术文档

**版本**: v1.0  
**日期**: 2026-02-12  
**目标网站**: http://www.97han.com/  
**网站名称**: 97韩剧  
**CMS系统**: 苹果CMS V10 (推测)  
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

本项目旨在开发一个 Python 爬虫系统，用于从97韩剧网站爬取影视媒资数据。网站基于 **苹果CMS V10** 构建，使用 **stui** 模板，包含电影、电视剧、综艺、动漫等多种内容分类。

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
| 域名 | www.97han.com |
| 网站名称 | 97韩剧 |
| CMS系统 | 苹果CMS V10 (推测) |
| 模板 | stui |
| 编码 | UTF-8 |

### 2.2 内容分类体系

| 大类 | 分类ID (cid) | URL | 说明 |
|------|-------------|-----|------|
| 电影 | 1 | /type/1.html | 电影列表 |
| 电视剧 | 2 | /type/2.html | 电视剧列表 |
| 综艺 | 3 | /type/3.html | 综艺列表 |
| 动漫 | 4 | /type/4.html | 动漫列表 |
| 短剧大全 | 30 | /type/30.html | 短剧列表 |
| MV伦理 | 36 | /type/36.html | MV列表 |

### 2.3 电影子分类

| ID | 分类名称 | URL |
|----|---------|-----|
| 7 | 动作片 | /type/7.html |
| 8 | 喜剧片 | /type/8.html |
| 9 | 爱情片 | /type/9.html |
| 10 | 科幻片 | /type/10.html |
| 11 | 恐怖片 | /type/11.html |
| 12 | 剧情片 | /type/12.html |
| 13 | 犯罪片 | /type/13.html |
| 29 | 纪录片 | /type/29.html |

### 2.4 电视剧子分类

| ID | 分类名称 | URL |
|----|---------|-----|
| 14 | 国产剧 | /type/14.html |
| 15 | 港剧 | /type/15.html |
| 16 | 台湾剧 | /type/16.html |
| 17 | 韩剧 | /type/17.html |
| 18 | 日剧 | /type/18.html |
| 19 | 欧美剧 | /type/19.html |
| 20 | 海外剧 | /type/20.html |
| 31 | 泰剧 | /type/31.html |

---

## 3. URL路由体系

### 3.1 完整URL格式表

| 页面类型 | URL格式 | 示例 |
|---------|---------|------|
| 首页 | `/` | `http://www.97han.com/` |
| 列表页（分类） | `/type/{cid}.html` | `/type/1.html` |
| 列表页（分页） | `/type/{cid}-{page}.html` | `/type/1-2.html` |
| 影片详情页 | `/detail/{vod_id}.html` | `/detail/1435124.html` |
| 播放页（集数） | `/Play/{vod_id}-{source}-{episode}.html` | `/Play/1435130-1-1.html` |

**注意**: 播放页URL中的 `Play` 是大写P开头！

### 3.2 URL构造规则

```python
def build_list_url(cid, page=1):
    """构造列表页URL"""
    if page == 1:
        return f"http://www.97han.com/type/{cid}.html"
    else:
        return f"http://www.97han.com/type/{cid}-{page}.html"

def build_detail_url(vod_id):
    """构造详情页URL"""
    return f"http://www.97han.com/detail/{vod_id}.html"

def build_play_url(vod_id, source=1, episode=1):
    """构造播放页URL"""
    return f"http://www.97han.com/Play/{vod_id}-{source}-{episode}.html"
```

---

## 4. HTML结构与CSS选择器

### 4.1 推荐User-Agent

```python
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
```

**重要提示**: 该网站使用桌面UA会返回404，必须使用iPhone等移动端UA才能正常访问！

### 4.2 列表页结构

```html
<a href="/detail/1435124.html">女孩</a>
```

**CSS选择器速查表（列表页）**:

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 详情页URL | `a[href*="/detail/"]` | `.get('href')` |
| 标题 | 同上 | `.text.strip()` |
| 评分 | 父元素中的span | 正则提取 |
| 状态 | 父元素中的span | `.text.strip()` |

### 4.3 详情页结构

```html
<div class="stui-content__detail">
  <h1>女孩</h1>
  <span>2.0</span>
  <span>类型：剧情</span>
  <span>地区：中国台湾中国大陆</span>
  <span>年份：2025</span>
  <span>语言：汉语普通话闽南</span>
  <span>主演：邱泽汤毓绮白小樱...</span>
  <span>导演：舒淇</span>
  <span>更新：2026-02-14 01:02:34</span>
</div>
<div class="stui-content__desc">
  1988年，基隆港烟尘蔽日，林小丽（白小樱 饰）在迷惘中长大...
</div>
```

**CSS选择器速查表（详情页）**:

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 标题 | `h1` 或 `h2` | `.text.strip()` |
| 评分 | `.stui-content__detail span` (数字) | `float(.text)` |
| 类型 | 包含"类型："的span | 正则提取 |
| 地区 | 包含"地区："的span | 正则提取 |
| 年份 | 包含"年份："的span | `int(.text)` |
| 语言 | 包含"语言："的span | 正则提取 |
| 主演 | 包含"主演："的span | 正则提取 |
| 导演 | 包含"导演："的span | 正则提取 |
| 更新时间 | 包含"更新："的span | 正则提取 |
| 简介 | `.stui-content__desc` | `.text.strip()` |

### 4.4 播放列表结构（电视剧集数）

```html
<div class="playlist">
  <ul class="stui-content__playlist clearfix">
    <li>
      <a href="/Play/1435130-1-4.html">第04期</a>
    </li>
    <li>
      <a href="/Play/1435130-1-3.html">第03期</a>
    </li>
    ...
  </ul>
</div>
```

**CSS选择器速查表（播放列表）**:

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 集数链接 | `ul.stui-content__playlist li a` | `.get('href')` |
| 集数标题 | 同上 | `.text.strip()` |
| 集数编号 | 同上 | 正则提取数字 |

### 4.5 电影 vs 电视剧区分方法

**方法1：通过分类ID区分**（推荐）

```python
MOVIE_CIDS = {1, 7, 8, 9, 10, 11, 12, 13, 29}  # 电影相关
TV_CIDS = {2, 14, 15, 16, 17, 18, 19, 20, 31}   # 电视剧相关
```

**方法2：通过集数数量区分**

```python
episode_links = soup.select('ul.stui-content__playlist li a')
is_movie = len(episode_links) <= 1
is_tv_series = len(episode_links) > 1
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
    type TEXT DEFAULT '',                     -- 类型
    region TEXT DEFAULT '',                   -- 地区
    year INTEGER DEFAULT 0,                  -- 年份
    language TEXT DEFAULT '',                -- 语言
    director TEXT DEFAULT '',                -- 导演
    actors TEXT DEFAULT '',                  -- 主演
    status TEXT DEFAULT '',                  -- 状态
    rating REAL DEFAULT 0.0,                 -- 评分
    update_time TEXT DEFAULT '',             -- 更新时间
    poster_url TEXT DEFAULT '',              -- 海报图URL
    detail_url TEXT NOT NULL,                -- 详情页URL
    synopsis TEXT DEFAULT '',                -- 简介
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
CREATE INDEX IF NOT EXISTS idx_movies_category ON movies(category);
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
    type TEXT DEFAULT '',                     -- 类型
    region TEXT DEFAULT '',                   -- 地区
    year INTEGER DEFAULT 0,                  -- 年份
    language TEXT DEFAULT '',                -- 语言
    director TEXT DEFAULT '',                -- 导演
    actors TEXT DEFAULT '',                  -- 主演
    status TEXT DEFAULT '',                  -- 状态
    season INTEGER DEFAULT 1,                -- 季数
    total_episodes INTEGER,                  -- 总集数
    current_episode INTEGER,                 -- 当前更新到的集数
    rating REAL DEFAULT 0.0,                 -- 评分
    update_time TEXT DEFAULT '',             -- 更新时间
    poster_url TEXT DEFAULT '',              -- 海报图URL
    detail_url TEXT NOT NULL,                -- 详情页URL
    synopsis TEXT DEFAULT '',                -- 简介
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
CREATE INDEX IF NOT EXISTS idx_tv_series_year ON tv_series(year);
CREATE INDEX IF NOT EXISTS idx_tv_series_category ON tv_series(category);
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
CREATE INDEX IF NOT EXISTS idx_tv_episodes_play_url ON tv_episodes(play_url);
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

### 5.5 Upsert操作（去重与增量更新）

```python
def upsert_movie(conn, movie_data):
    """插入或更新电影数据"""
    conn.execute("""
        INSERT INTO movies (vod_id, title, original_title, category, type, region, year,
                           language, director, actors, status, rating, update_time,
                           poster_url, detail_url, synopsis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(vod_id) DO UPDATE SET
            title = excluded.title,
            original_title = excluded.original_title,
            category = excluded.category,
            type = excluded.type,
            region = excluded.region,
            year = excluded.year,
            language = excluded.language,
            director = excluded.director,
            actors = excluded.actors,
            status = excluded.status,
            rating = excluded.rating,
            update_time = excluded.update_time,
            poster_url = excluded.poster_url,
            synopsis = excluded.synopsis,
            updated_at = CURRENT_TIMESTAMP
    """, tuple(movie_data.values()))
    conn.commit()
```

---

## 6. 电影爬虫模块实现

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
97韩剧 - 电影爬虫模块
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
BASE_URL = "http://www.97han.com"
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
                    type TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    language TEXT DEFAULT '',
                    director TEXT DEFAULT '',
                    actors TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    rating REAL DEFAULT 0.0,
                    update_time TEXT DEFAULT '',
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
            return f"{BASE_URL}/type/{cid}.html"
        else:
            return f"{BASE_URL}/type/{cid}-{page}.html"
    
    @staticmethod
    def extract_vod_id(url):
        """从URL中提取视频ID"""
        match = re.search(r'/(?:detail|Play)/(\d+)', url)
        return int(match.group(1)) if match else None
    
    def parse_list_page(self, soup):
        """解析列表页"""
        movies = []
        seen_ids = set()
        
        links = soup.find_all('a', href=re.compile(r'/detail/\d+\.html'))
        
        for link in links:
            try:
                href = link.get('href', '')
                vod_id = self.extract_vod_id(href)
                
                if not vod_id or vod_id in seen_ids:
                    continue
                
                seen_ids.add(vod_id)
                detail_url = urljoin(BASE_URL, href)
                
                title = link.text.strip()
                
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
                        elif any(k in text for k in ['HD', '完结', '集', '更新', '正片', '高清']):
                            status = text
                
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
        has_next = bool(soup.find('a', string='下一页'))
        
        return movies, has_next
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        # 标题
        title = soup.find('h1') or soup.find('h2')
        data['title'] = title.text.strip() if title else ''
        
        # 获取所有文本内容
        content = soup.get_text()
        
        # 提取评分
        rating_match = re.search(r'(\d+\.?\d*)分', content)
        if rating_match:
            try:
                data['rating'] = float(rating_match.group(1))
            except:
                pass
        
        # 提取类型
        type_match = re.search(r'类型[：:]([^\n]+)', content)
        if type_match:
            data['type'] = type_match.group(1).strip()
        
        # 提取地区
        region_match = re.search(r'地区[：:]([^\n]+)', content)
        if region_match:
            data['region'] = region_match.group(1).strip()
        
        # 提取年份
        year_match = re.search(r'年份[：:](\d{4})', content)
        if year_match:
            data['year'] = int(year_match.group(1))
        
        # 提取语言
        language_match = re.search(r'语言[：:]([^\n]+)', content)
        if language_match:
            data['language'] = language_match.group(1).strip()
        
        # 提取导演
        director_match = re.search(r'导演[：:]([^\n]+)', content)
        if director_match:
            data['director'] = director_match.group(1).strip()
        
        # 提取主演
        actors_match = re.search(r'主演[：:]([^\n]+)', content)
        if actors_match:
            data['actors'] = actors_match.group(1).strip()
        
        # 提取更新时间
        update_match = re.search(r'更新[：:]([^\n]+)', content)
        if update_match:
            data['update_time'] = update_match.group(1).strip()
        
        # 提取简介
        desc = soup.find('div', class_='stui-content__desc')
        if desc:
            data['synopsis'] = desc.text.strip()[:500]
        
        return data
    
    def save_movie(self, conn, movie):
        """保存电影（Upsert）"""
        conn.execute("""
            INSERT INTO movies (vod_id, title, original_title, category, type, region, year,
                               language, director, actors, status, rating, update_time,
                               poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title,
                original_title=excluded.original_title,
                category=excluded.category,
                type=excluded.type,
                region=excluded.region,
                year=excluded.year,
                language=excluded.language,
                director=excluded.director,
                actors=excluded.actors,
                status=excluded.status,
                rating=excluded.rating,
                update_time=excluded.update_time,
                poster_url=excluded.poster_url,
                synopsis=excluded.synopsis,
                updated_at=CURRENT_TIMESTAMP
        """, (
            movie.get('vod_id'), movie.get('title', ''),
            movie.get('original_title'), movie.get('category', ''),
            movie.get('type', ''), movie.get('region', ''),
            movie.get('year', 0), movie.get('language', ''),
            movie.get('director', ''), movie.get('actors', ''),
            movie.get('status', ''), movie.get('rating', 0.0),
            movie.get('update_time', ''), movie.get('poster_url', ''),
            movie.get('detail_url', ''), movie.get('synopsis', '')
        ))
        conn.commit()
    
    def crawl(self, year_start=1945, year_end=2026, max_pages=None):
        """
        爬取电影
        
        参数:
            year_start: 开始年份
            year_end: 结束年份
            max_pages: 最大页数
        """
        cid = 1  # 电影
        
        page = 1
        total_count = 0
        
        while True:
            if max_pages and page > max_pages:
                break
            
            url = self.build_list_url(cid, page)
            logger.info(f"正在爬取第 {page} 页: {url}")
            
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
                        
                        # 过滤年份
                        if year_start <= movie.get('year', 0) <= year_end:
                            movie['category'] = '电影'
                            self.save_movie(conn, movie)
                            total_count += 1
                            logger.info(f"✅ [{total_count}] {movie['title']} ({movie.get('year', 'N/A')})")
                        
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
97韩剧 - 电视剧爬虫模块
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
                    type TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    language TEXT DEFAULT '',
                    director TEXT DEFAULT '',
                    actors TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    season INTEGER DEFAULT 1,
                    total_episodes INTEGER,
                    current_episode INTEGER,
                    rating REAL DEFAULT 0.0,
                    update_time TEXT DEFAULT '',
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
    
    def parse_detail_page(self, soup):
        """解析详情页（电视剧专用）"""
        data = super().parse_detail_page(soup)
        
        # 提取播放列表（集数）
        episodes = []
        playlist = soup.find('ul', class_='stui-content__playlist')
        
        if playlist:
            episode_links = playlist.find_all('a', href=re.compile(r'/Play/\d+-\d+-\d+\.html'))
            
            for link in episode_links:
                ep_text = link.text.strip()
                ep_href = link.get('href', '')
                
                # 提取集数编号
                ep_match = re.search(r'第(\d+)期|第(\d+)集', ep_text)
                ep_num = int(ep_match.group(1) or ep_match.group(2)) if ep_match else 0
                
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
        
        # 计算总集数
        if unique_episodes:
            data['total_episodes'] = len(unique_episodes)
        
        return data
    
    def save_tv_series(self, conn, series, episodes):
        """保存电视剧及集数"""
        # 保存剧集信息
        conn.execute("""
            INSERT INTO tv_series (vod_id, title, original_title, category, type, region, year,
                                  language, director, actors, status, season, total_episodes, current_episode,
                                  rating, update_time, poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title,
                original_title=excluded.original_title,
                category=excluded.category,
                type=excluded.type,
                region=excluded.region,
                year=excluded.year,
                language=excluded.language,
                director=excluded.director,
                actors=excluded.actors,
                status=excluded.status,
                season=excluded.season,
                total_episodes=excluded.total_episodes,
                current_episode=excluded.current_episode,
                rating=excluded.rating,
                update_time=excluded.update_time,
                poster_url=excluded.poster_url,
                synopsis=excluded.synopsis,
                updated_at=CURRENT_TIMESTAMP
        """, (
            series.get('vod_id'), series.get('title', ''),
            series.get('original_title'), series.get('category', ''),
            series.get('type', ''), series.get('region', ''),
            series.get('year', 0), series.get('language', ''),
            series.get('director', ''), series.get('actors', ''),
            series.get('status', ''), series.get('season', 1),
            series.get('total_episodes'), series.get('current_episode'),
            series.get('rating', 0.0), series.get('update_time', ''),
            series.get('poster_url', ''), series.get('detail_url', ''),
            series.get('synopsis', '')
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
    
    def crawl(self, year_start=1945, year_end=2026, max_pages=None, max_episodes=None):
        """
        爬取电视剧
        
        参数:
            year_start: 开始年份
            year_end: 结束年份
            max_pages: 最大页数
            max_episodes: 每部剧最大集数限制
        """
        cid = 2  # 电视剧
        
        page = 1
        total_series = 0
        total_episodes = 0
        
        while True:
            if max_pages and page > max_pages:
                break
            
            url = self.build_list_url(cid, page)
            logger.info(f"正在爬取第 {page} 页: {url}")
            
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
                        
                        # 过滤年份
                        if year_start <= series.get('year', 0) <= year_end:
                            series['category'] = '电视剧'
                            
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
    parser = argparse.ArgumentParser(description='97韩剧爬虫')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 电影爬虫
    movie_parser = subparsers.add_parser('movie', help='爬取电影')
    movie_parser.add_argument('--start-year', type=int, default=1945, help='开始年份')
    movie_parser.add_argument('--end-year', type=int, default=2026, help='结束年份')
    movie_parser.add_argument('--max-pages', type=int, help='最大页数')
    movie_parser.add_argument('--db', type=str, default='spider.db', help='数据库路径')
    
    # 电视剧爬虫
    tv_parser = subparsers.add_parser('tv', help='爬取电视剧')
    tv_parser.add_argument('--start-year', type=int, default=1945, help='开始年份')
    tv_parser.add_argument('--end-year', type=int, default=2026, help='结束年份')
    tv_parser.add_argument('--max-pages', type=int, help='最大页数')
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
# 爬取电影（1945-2026）
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
| **User-Agent** | 必须使用iPhone移动端UA，桌面UA会返回404 |
| 随机延迟 | 每次请求间隔 1-3 秒随机 |
| 重试机制 | 失败时指数退避重试（最多3次） |
| 超时设置 | 15秒请求超时 |
| 连接复用 | 使用Session保持连接 |

---

## ⚠️ 重要提示

**该网站必须使用iPhone等移动端User-Agent才能访问！**

使用桌面UA（如Chrome、Firefox）会返回 **404 Not Found** 错误。

**推荐UA**:
```python
IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
```

---

**文档版本**: v1.0  
**最后更新**: 2026-02-12
