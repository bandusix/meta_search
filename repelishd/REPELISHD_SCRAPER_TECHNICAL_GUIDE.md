# RepelisHD (repelishd.city) 爬虫系统技术实现文档

**版本**: v1.0
**日期**: 2026-02-08
**目标网站**: https://repelishd.city

---

## 目录

1. [项目概述](#1-项目概述)
2. [网站结构分析](#2-网站结构分析)
3. [URL 路由体系](#3-url-路由体系)
4. [HTML 结构与 CSS 选择器](#4-html-结构与-css-选择器)
5. [数据库设计](#5-数据库设计)
6. [电影爬虫模块实现](#6-电影爬虫模块实现)
7. [电视剧爬虫模块实现](#7-电视剧爬虫模块实现)
8. [主程序与命令行接口](#8-主程序与命令行接口)
9. [反爬虫策略](#9-反爬虫策略)
10. [数据导出模块](#10-数据导出模块)
11. [定时任务与增量更新](#11-定时任务与增量更新)
12. [常见问题与解决方案](#12-常见问题与解决方案)

---

## 1. 项目概述

### 1.1 项目目标

开发一套完整的 Python 爬虫系统，用于从 repelishd.city 网站爬取电影和电视剧数据，支持按年份爬取、自动翻页、增量更新，并将数据存储到 SQLite 数据库和导出为 CSV 格式。

### 1.2 功能需求

#### 电影数据爬取

- 按年份爬取（支持 1932-2026 及未来年份）
- 年份范围爬取，倒序优先（从最新年份开始）
- 自动翻页，爬取所有电影
- 提取字段：西语标题、原标题、图片URL、年份、评分、清晰度、详情页URL

#### 电视剧数据爬取

- 爬取所有电视剧列表
- 自动提取所有季和集
- 支持限制爬取数量
- 提取字段：西语标题、原标题、图片URL、年份、评分、清晰度、季数、集数、剧集详情页URL

#### 数据存储与导出

- SQLite 数据库，两个独立表（movies、tv_episodes）
- 自动去重（基于URL）
- 支持增量更新
- 导出为 CSV 格式，文件名包含时间戳

### 1.3 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| 编程语言 | Python 3.7+ | 主要开发语言 |
| HTTP 请求 | requests / httpx | 网页请求 |
| HTML 解析 | BeautifulSoup4 + lxml | 页面解析 |
| 数据库 | SQLite3 | 轻量级本地存储 |
| 数据导出 | csv (标准库) | CSV 格式导出 |
| 正则表达式 | re (标准库) | 数据清洗与模式匹配 |

---

## 2. 网站结构分析

### 2.1 网站基本信息

| 属性 | 值 |
|------|-----|
| 域名 | repelishd.city |
| 协议 | HTTPS |
| 语言 | 西班牙语 (es-MX) |
| 模板引擎 | DLE (DataLife Engine) |
| 编码 | UTF-8 |
| Cloudflare 保护 | 是 |

### 2.2 内容分类

| 类型 | 列表页路径 | 详情页路径 | 总页数 |
|------|-----------|-----------|--------|
| 电影 | `/pelicula/page/{page}/` | `/ver-pelicula/{id}-{slug}-online-espanol.html` | ~775页 |
| 电视剧 | `/series/page/{page}/` | `/ver-pelicula/{id}-{slug}-online-espanol.html` | ~107页 |
| 按年份 | `/xfsearch/year/{year}/page/{page}/` | 同上 | 因年份而异 |

### 2.3 关键发现

1. **电影和电视剧共用相同的卡片结构**：均使用 `article.item.movies` 作为容器
2. **电影和电视剧共用相同的详情页URL前缀**：均为 `/ver-pelicula/`
3. **区分方式**：通过 `.quality` 标签内容区分——电影显示 `HD`，电视剧显示 `s{season}-e{episode}` 格式
4. **按年份搜索页面混合了电影和电视剧**：需要在爬取时进行过滤

---

## 3. URL 路由体系

### 3.1 电影相关 URL

| 用途 | URL 格式 | 示例 |
|------|---------|------|
| 电影总列表（第1页） | `https://repelishd.city/pelicula/` | - |
| 电影总列表（分页） | `https://repelishd.city/pelicula/page/{page}/` | `/pelicula/page/775/` |
| 按年份搜索（第1页） | `https://repelishd.city/xfsearch/year/{year}` | `/xfsearch/year/2001` |
| 按年份搜索（分页） | `https://repelishd.city/xfsearch/year/{year}/page/{page}/` | `/xfsearch/year/2001/page/2/` |
| 电影详情页 | `https://repelishd.city/ver-pelicula/{id}-{slug}-online-espanol.html` | `/ver-pelicula/38-dont-fuck-in-the-woods-2-online-espanol.html` |

### 3.2 电视剧相关 URL

| 用途 | URL 格式 | 示例 |
|------|---------|------|
| 电视剧列表（第1页） | `https://repelishd.city/series/` | - |
| 电视剧列表（分页） | `https://repelishd.city/series/page/{page}/` | `/series/page/9/` |
| 电视剧详情页 | `https://repelishd.city/ver-pelicula/{id}-{slug}-online-espanol.html` | `/ver-pelicula/13303-tracker-online-espanol.html` |

### 3.3 分页 URL 规则

- 第1页：不带 `/page/` 后缀
- 第2页及以后：`/page/{page}/`
- 分页从 1 开始计数
- 按年份搜索的分页格式：`/xfsearch/year/{year}/page/{page}/`

---

## 4. HTML 结构与 CSS 选择器

### 4.1 列表页卡片结构

电影和电视剧在列表页使用**完全相同的卡片结构**：

```html
<article class="item movies">
    <div class="poster">
        <!-- 海报图片 -->
        <img src="/uploads/mini/cuimage/{hash1}/{hash2}.jpg" alt="电影标题">
        <!-- 评分 -->
        <div class="rating"><span class="icon-star2"></span>3.5</div>
        <!-- 清晰度/季集信息 -->
        <div class="mepo">
            <span class="quality">HD</span>              <!-- 电影 -->
            <span class="quality" style="background-color: #2944D5;">s3-e9</span>  <!-- 电视剧 -->
        </div>
        <!-- 详情页链接 -->
        <a href="https://repelishd.city/ver-pelicula/{id}-{slug}-online-espanol.html">
            <div class="see play1"></div>
        </a>
        <!-- 音频语言标签 -->
        <div class="audio">
            <div class="latino"></div>       <!-- 拉丁语配音 -->
            <div class="castellano"></div>   <!-- 卡斯蒂利亚语配音 -->
            <div class="subtitulado"></div>  <!-- 字幕 -->
        </div>
    </div>
    <div class="data">
        <h3><a href="https://repelishd.city/ver-pelicula/{id}-{slug}-online-espanol.html">电影标题</a></h3>
        <span>2022</span>  <!-- 年份 -->
    </div>
</article>
```

### 4.2 列表页 CSS 选择器速查表

| 数据字段 | CSS 选择器 | 提取方式 | 示例值 |
|---------|-----------|---------|--------|
| 卡片容器 | `article.item.movies` | 遍历 | - |
| 西语标题 | `article .data h3 a` | `.text` | `"Jason X"` |
| 详情页URL | `article .data h3 a` | `['href']` | `"https://repelishd.city/ver-pelicula/..."` |
| 备选URL | `article .poster > a` | `['href']` | 同上 |
| 评分 | `article .rating` | `.text` (去除icon) | `"3.5"` |
| 清晰度/季集 | `article .quality` | `.text` | `"HD"` 或 `"s3-e9"` |
| 年份 | `article .data span` | `.text` | `"2022"` |
| 海报URL | `article .poster img` | `['src']` | `"/uploads/mini/cuimage/..."` |
| 音频-拉丁 | `article .audio .latino` | 存在性检查 | - |
| 音频-卡斯蒂利亚 | `article .audio .castellano` | 存在性检查 | - |
| 音频-字幕 | `article .audio .subtitulado` | 存在性检查 | - |

### 4.3 区分电影与电视剧

```python
def is_tv_series(article):
    """通过 .quality 标签内容判断是否为电视剧"""
    quality = article.select_one('.quality')
    if quality:
        text = quality.get_text(strip=True)
        # 电视剧格式: s{数字}-e{数字}
        return bool(re.match(r's\d+-e\d+', text))
    return False
```

### 4.4 详情页结构

#### 4.4.1 头部区域 (.sheader)

```html
<div class="sheader">
    <div class="poster">
        <img itemprop="image" src="/uploads/mini/cuimage/{hash1}/{hash2}.jpg" 
             alt="标题 online HD español repelishd" 
             title="标题 online repelishd">
    </div>
    <div class="data">
        <h1>标题 online HD</h1>                     <!-- 电影 -->
        <h1>ver serie 标题 online</h1>               <!-- 电视剧 -->
        <div class="extra">
            <span>2024</span>                         <!-- 年份 -->
            <span class="country">Estados Unidos</span>  <!-- 国家 -->
            <span itemprop="duration" class="runtime">81 Min.</span>  <!-- 时长 -->
            <span>Terror</span>                       <!-- 类型（电影） -->
            <span>Series   Drama   Crimen</span>      <!-- 类型（电视剧，包含"Series"关键词） -->
            <span>HD/latino, sub</span>               <!-- 清晰度/音频 -->
        </div>
        <div class="starstruck-ptype">
            <!-- 评分系统 -->
            <span class="dt_rating_vgs">6.8</span>   <!-- 站内评分 -->
        </div>
        <div class="wp-content">
            <!-- 电影/电视剧简介 -->
        </div>
    </div>
</div>
```

#### 4.4.2 原标题区域

```html
<div class="custom_fields">
    <b class="variante">Título original</b>
    <span class="valor">Original Title Here</span>
</div>
```

#### 4.4.3 IMDb/TMDb 评分区域

页面底部文本区域包含：
- **Título original**: 原标题
- **IMDb Rating**: IMDb 评分和投票数
- **TMDb Rating**: TMDb 评分

### 4.5 详情页 CSS 选择器速查表

| 数据字段 | CSS 选择器 | 提取方式 | 示例值 |
|---------|-----------|---------|--------|
| 标题(含后缀) | `.sheader .data h1` | `.text` | `"Don't Fuck in the Woods 2 online HD"` |
| 年份 | `.sheader .extra span:first-child` | `.text` | `"2022"` |
| 国家 | `.sheader .extra .country` | `.text` | `"Estados Unidos"` |
| 时长 | `.sheader .extra .runtime` | `.text` | `"81 Min."` |
| 类型 | `.sheader .extra span` (第4个) | `.text` | `"Terror"` |
| 清晰度 | `.sheader .extra span` (最后一个) | `.text` | `"HD/latino, sub"` |
| 站内评分 | `.dt_rating_vgs` | `.text` | `"6.8"` |
| 海报URL | `.sheader .poster img` | `['src']` | `"/uploads/mini/cuimage/..."` |
| 原标题 | `.custom_fields .valor` | `.text` | `"Original Title"` |

### 4.6 电视剧季集结构

#### 4.6.1 季选择器

```html
<div class="tab-pane fade active show" id="season-1">
    <ul>
        <li class="active">
            <a href="#" id="serie-1_1" data-num="1x1" data-title="Episode 1" 
               data-link="https://supervideo.cc/embed-xxx.html">1</a>
            <div class="mirrors">
                <a href="#" data-m="sup" data-link="https://supervideo.cc/embed-xxx.html">
                    Supervideo
                </a>
                <a href="#" data-m="dropload" data-link="https://dropload.tv/embed-xxx.html">
                    Dropload
                </a>
            </div>
        </li>
        <!-- 更多剧集... -->
    </ul>
</div>
<div class="tab-pane fade" id="season-2">
    <!-- Season 2 剧集 -->
</div>
```

#### 4.6.2 季集 CSS 选择器

| 数据字段 | CSS 选择器 | 提取方式 | 示例值 |
|---------|-----------|---------|--------|
| 季容器 | `div[id^="season-"]` | 遍历 | `id="season-1"` |
| 季数 | `div[id^="season-"]` | 从 id 解析 | `1` |
| 剧集链接 | `a[id^="serie-"]` | 遍历 | `id="serie-1_1"` |
| 季x集编号 | `a[id^="serie-"]` | `['data-num']` | `"1x1"` |
| 剧集标题 | `a[id^="serie-"]` | `['data-title']` | `"Episode 1"` |
| 播放链接 | `a[id^="serie-"]` | `['data-link']` | `"https://supervideo.cc/..."` |

#### 4.6.3 从 id 解析季集号

```python
import re

def parse_episode_id(episode_id):
    """从 serie-X_Y 格式解析季数和集数"""
    match = re.match(r'serie-(\d+)_(\d+)', episode_id)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

# 示例
# parse_episode_id("serie-1_1")  → (1, 1)
# parse_episode_id("serie-2_13") → (2, 13)
```

#### 4.6.4 从 data-num 解析季集号

```python
def parse_data_num(data_num):
    """从 1x1 格式解析季数和集数"""
    match = re.match(r'(\d+)x(\d+)', data_num)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None

# 示例
# parse_data_num("1x1")  → (1, 1)
# parse_data_num("3x9")  → (3, 9)
```

### 4.7 分页结构

```html
<div class="pagination">
    <!-- 上一页（第1页时为span，否则为a） -->
    <span><i id="prevpagination" class="fas fa-caret-left"></i></span>
    <!-- 或 -->
    <a href="/pelicula/page/774/"><i id="prevpagination" class="fas fa-caret-left"></i></a>
    
    <!-- 页码 -->
    <span>1</span>                          <!-- 当前页（span标签） -->
    <a href="/pelicula/page/2/">2</a>       <!-- 其他页（a标签） -->
    <span class="nav_ext">...</span>        <!-- 省略号 -->
    <a href="/pelicula/page/775/">775</a>   <!-- 最后一页 -->
    
    <!-- 下一页（最后一页时无此元素） -->
    <a href="/pelicula/page/2/"><i id="nextpagination" class="fas fa-caret-right"></i></a>
</div>
```

#### 分页检测逻辑

```python
def has_next_page(soup):
    """检查是否有下一页"""
    pagination = soup.select_one('.pagination')
    if not pagination:
        return False
    next_btn = pagination.select_one('#nextpagination')
    return next_btn is not None

def get_max_page(soup):
    """获取最大页码"""
    pagination = soup.select_one('.pagination')
    if not pagination:
        return 1
    page_links = pagination.select('a[href*="/page/"]')
    max_page = 1
    for link in page_links:
        href = link.get('href', '')
        match = re.search(r'/page/(\d+)/', href)
        if match:
            page_num = int(match.group(1))
            max_page = max(max_page, page_num)
    return max_page
```

---

## 5. 数据库设计

### 5.1 数据库文件

- 文件名: `repelishd.db`
- 引擎: SQLite3

### 5.2 电影表 (movies)

```sql
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title_spanish TEXT NOT NULL,        -- 西语标题
    title_original TEXT,                -- 原标题
    year INTEGER,                       -- 年份
    rating REAL,                        -- 评分
    quality TEXT,                       -- 清晰度 (HD, CAM等)
    image_url TEXT,                     -- 海报图片URL
    detail_url TEXT UNIQUE NOT NULL,    -- 详情页URL (唯一约束，用于去重)
    country TEXT,                       -- 国家
    duration TEXT,                      -- 时长
    genre TEXT,                         -- 类型
    audio TEXT,                         -- 音频语言
    imdb_rating REAL,                   -- IMDb评分
    tmdb_rating REAL,                   -- TMDb评分
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
CREATE INDEX IF NOT EXISTS idx_movies_rating ON movies(rating);
CREATE UNIQUE INDEX IF NOT EXISTS idx_movies_url ON movies(detail_url);
```

### 5.3 电视剧剧集表 (tv_episodes)

```sql
CREATE TABLE IF NOT EXISTS tv_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_title_spanish TEXT NOT NULL,  -- 电视剧西语标题
    series_title_original TEXT,          -- 电视剧原标题
    year INTEGER,                        -- 年份
    rating REAL,                         -- 评分
    quality TEXT,                        -- 清晰度
    image_url TEXT,                      -- 海报图片URL
    series_url TEXT NOT NULL,            -- 电视剧详情页URL
    season INTEGER NOT NULL,             -- 季数
    episode INTEGER NOT NULL,            -- 集数
    episode_title TEXT,                  -- 剧集标题
    episode_data_num TEXT,               -- 季集编号 (如 "1x1")
    country TEXT,                        -- 国家
    duration TEXT,                       -- 时长
    genre TEXT,                          -- 类型
    audio TEXT,                          -- 音频语言
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(series_url, season, episode)  -- 联合唯一约束
);

CREATE INDEX IF NOT EXISTS idx_tv_series_url ON tv_episodes(series_url);
CREATE INDEX IF NOT EXISTS idx_tv_season ON tv_episodes(season);
CREATE INDEX IF NOT EXISTS idx_tv_year ON tv_episodes(year);
```

### 5.4 去重与增量更新策略

```python
def upsert_movie(conn, movie_data):
    """插入或更新电影记录"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO movies (title_spanish, title_original, year, rating, quality, 
                           image_url, detail_url, country, duration, genre, audio,
                           imdb_rating, tmdb_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(detail_url) DO UPDATE SET
            title_spanish = excluded.title_spanish,
            title_original = excluded.title_original,
            rating = excluded.rating,
            quality = excluded.quality,
            image_url = excluded.image_url,
            updated_at = CURRENT_TIMESTAMP
    ''', (movie_data['title_spanish'], movie_data['title_original'], 
          movie_data['year'], movie_data['rating'], movie_data['quality'],
          movie_data['image_url'], movie_data['detail_url'],
          movie_data['country'], movie_data['duration'], movie_data['genre'],
          movie_data['audio'], movie_data['imdb_rating'], movie_data['tmdb_rating']))
    conn.commit()
```

---

## 6. 电影爬虫模块实现

### 6.1 模块架构

```
movie_scraper.py
├── class MovieScraper
│   ├── __init__(self, db_path, delay_range)
│   ├── _get_session(self) -> requests.Session
│   ├── _fetch_page(self, url) -> BeautifulSoup
│   ├── _parse_movie_card(self, article) -> dict
│   ├── _parse_movie_detail(self, url) -> dict
│   ├── _has_next_page(self, soup) -> bool
│   ├── scrape_by_year(self, year, max_pages) -> list
│   ├── scrape_year_range(self, start_year, end_year, max_pages) -> list
│   └── scrape_all_movies(self, max_pages) -> list
```

### 6.2 核心代码实现

#### 6.2.1 基础请求类

```python
import requests
import random
import time
import re
from bs4 import BeautifulSoup

class BaseScraper:
    """基础爬虫类"""
    
    BASE_URL = "https://repelishd.city"
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self, delay_min=1, delay_max=3):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = self._create_session()
    
    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': self.BASE_URL,
        })
        session.verify = False  # 某些环境下可能需要
        return session
    
    def _random_delay(self):
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _rotate_user_agent(self):
        self.session.headers['User-Agent'] = random.choice(self.USER_AGENTS)
    
    def _fetch_page(self, url, max_retries=3):
        for attempt in range(max_retries):
            try:
                self._rotate_user_agent()
                response = self.session.get(url, timeout=30)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                elif response.status_code == 404:
                    print(f"  ⚠️ 页面不存在 (404): {url}")
                    return None
                else:
                    print(f"  ⚠️ HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⚠️ 请求超时 (尝试 {attempt+1}/{max_retries}): {url}")
            except requests.exceptions.ConnectionError:
                print(f"  ⚠️ 连接错误 (尝试 {attempt+1}/{max_retries}): {url}")
            except Exception as e:
                print(f"  ⚠️ 请求异常 (尝试 {attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 5
                print(f"  ⏳ 等待 {wait} 秒后重试...")
                time.sleep(wait)
        
        return None
```

#### 6.2.2 电影列表解析

```python
class MovieScraper(BaseScraper):
    """电影爬虫"""
    
    def _parse_movie_card(self, article):
        """解析电影卡片，提取基本信息"""
        try:
            # 检查是否为电视剧（跳过）
            quality_el = article.select_one('.quality')
            quality_text = quality_el.get_text(strip=True) if quality_el else ''
            if re.match(r's\d+-e\d+', quality_text):
                return None  # 这是电视剧，跳过
            
            # 标题和URL
            title_el = article.select_one('.data h3 a')
            if not title_el:
                return None
            
            title = title_el.get_text(strip=True)
            detail_url = title_el.get('href', '')
            if not detail_url.startswith('http'):
                detail_url = self.BASE_URL + detail_url
            
            # 评分
            rating_el = article.select_one('.rating')
            rating_text = rating_el.get_text(strip=True) if rating_el else ''
            try:
                rating = float(rating_text) if rating_text else None
            except ValueError:
                rating = None
            
            # 清晰度
            quality = quality_text if quality_text else None
            
            # 年份
            year_el = article.select_one('.data span')
            year_text = year_el.get_text(strip=True) if year_el else ''
            try:
                year = int(year_text) if year_text else None
            except ValueError:
                year = None
            
            # 海报URL
            img_el = article.select_one('.poster img')
            image_url = img_el.get('src', '') if img_el else ''
            if image_url and not image_url.startswith('http'):
                image_url = self.BASE_URL + image_url
            
            # 音频语言
            audio_langs = []
            if article.select_one('.audio .latino'):
                audio_langs.append('Latino')
            if article.select_one('.audio .castellano'):
                audio_langs.append('Castellano')
            if article.select_one('.audio .subtitulado'):
                audio_langs.append('Subtitulado')
            audio = ', '.join(audio_langs) if audio_langs else None
            
            return {
                'title_spanish': title,
                'year': year,
                'rating': rating,
                'quality': quality,
                'image_url': image_url,
                'detail_url': detail_url,
                'audio': audio,
            }
            
        except Exception as e:
            print(f"  ⚠️ 解析卡片失败: {e}")
            return None
    
    def _parse_movie_detail(self, url):
        """访问详情页，提取额外信息"""
        soup = self._fetch_page(url)
        if not soup:
            return {}
        
        detail = {}
        
        try:
            # 原标题
            custom_fields = soup.select_one('.custom_fields')
            if custom_fields:
                valor = custom_fields.select_one('.valor')
                if valor:
                    detail['title_original'] = valor.get_text(strip=True)
            
            # 国家
            country_el = soup.select_one('.sheader .extra .country')
            if country_el:
                detail['country'] = country_el.get_text(strip=True)
            
            # 时长
            runtime_el = soup.select_one('.sheader .extra .runtime')
            if runtime_el:
                detail['duration'] = runtime_el.get_text(strip=True)
            
            # 类型
            extra = soup.select_one('.sheader .extra')
            if extra:
                spans = extra.select('span')
                if len(spans) >= 4:
                    genre = spans[3].get_text(strip=True)
                    if genre and 'HD' not in genre and '/' not in genre:
                        detail['genre'] = genre
            
            # 清晰度（从详情页获取更准确的信息）
            if extra:
                spans = extra.select('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if 'HD' in text or 'CAM' in text:
                        detail['quality'] = text
                        break
            
            # 站内评分
            rating_el = soup.select_one('.dt_rating_vgs')
            if rating_el:
                try:
                    detail['rating'] = float(rating_el.get_text(strip=True))
                except ValueError:
                    pass
            
            # 海报（高清版）
            poster_el = soup.select_one('.sheader .poster img')
            if poster_el:
                src = poster_el.get('src', '')
                if src and not src.startswith('http'):
                    src = self.BASE_URL + src
                detail['image_url'] = src
            
        except Exception as e:
            print(f"  ⚠️ 解析详情页失败: {e}")
        
        return detail
    
    def scrape_by_year(self, year, max_pages=None, fetch_details=True):
        """按年份爬取电影"""
        movies = []
        page = 1
        
        print(f"\n{'='*60}")
        print(f"🎬 开始爬取 {year} 年电影...")
        print(f"{'='*60}")
        
        while True:
            if max_pages and page > max_pages:
                break
            
            # 构建URL
            if page == 1:
                url = f"{self.BASE_URL}/xfsearch/year/{year}"
            else:
                url = f"{self.BASE_URL}/xfsearch/year/{year}/page/{page}/"
            
            print(f"\n📄 正在爬取第 {page} 页: {url}")
            
            soup = self._fetch_page(url)
            if not soup:
                print(f"  ❌ 获取页面失败，停止爬取")
                break
            
            # 解析所有卡片
            articles = soup.select('article.item.movies')
            if not articles:
                # 尝试备选选择器
                articles = soup.select('article.item')
            
            if not articles:
                print(f"  ✅ 没有更多内容，结束爬取")
                break
            
            page_movies = []
            for article in articles:
                movie = self._parse_movie_card(article)
                if movie:  # None 表示是电视剧，已跳过
                    page_movies.append(movie)
            
            print(f"  找到 {len(page_movies)} 部电影 (过滤掉 {len(articles) - len(page_movies)} 部电视剧)")
            
            # 可选：访问详情页获取更多信息
            if fetch_details:
                for i, movie in enumerate(page_movies):
                    print(f"  📖 获取详情 ({i+1}/{len(page_movies)}): {movie['title_spanish']}")
                    detail = self._parse_movie_detail(movie['detail_url'])
                    movie.update(detail)
                    self._random_delay()
            
            movies.extend(page_movies)
            
            # 检查是否有下一页
            pagination = soup.select_one('.pagination')
            if not pagination or not pagination.select_one('#nextpagination'):
                print(f"  ✅ 已到最后一页")
                break
            
            page += 1
            self._random_delay()
        
        print(f"\n✨ {year} 年电影爬取完成！共 {len(movies)} 部电影")
        return movies
    
    def scrape_year_range(self, start_year, end_year, max_pages_per_year=None, fetch_details=True):
        """按年份范围爬取，倒序优先"""
        all_movies = []
        years = sorted(range(start_year, end_year + 1), reverse=True)
        
        print(f"\n{'#'*60}")
        print(f"# 开始爬取 {start_year}-{end_year} 年电影（倒序）")
        print(f"# 年份顺序: {' → '.join(map(str, years))}")
        print(f"{'#'*60}")
        
        for year in years:
            movies = self.scrape_by_year(year, max_pages_per_year, fetch_details)
            all_movies.extend(movies)
        
        print(f"\n🎉 所有年份爬取完成！总计 {len(all_movies)} 部电影")
        return all_movies
```

### 6.3 标题清洗

电影详情页的 `<h1>` 标签包含后缀（如 "online HD"），需要清洗：

```python
def clean_title(raw_title):
    """清洗标题，去除 'online HD' 等后缀"""
    # 去除常见后缀
    suffixes = [
        ' online HD', ' online', ' Online HD', ' Online',
        ' en Español', ' en español', ' Español', ' español',
    ]
    title = raw_title
    for suffix in suffixes:
        if title.endswith(suffix):
            title = title[:-len(suffix)]
    
    # 去除 "ver serie " 前缀（电视剧）
    if title.lower().startswith('ver serie '):
        title = title[len('ver serie '):]
    
    return title.strip()
```

---

## 7. 电视剧爬虫模块实现

### 7.1 模块架构

```
tv_scraper.py
├── class TVScraper(BaseScraper)
│   ├── __init__(self, db_path, delay_range)
│   ├── _parse_series_card(self, article) -> dict
│   ├── _parse_series_detail(self, url) -> dict
│   ├── _parse_episodes(self, soup) -> list
│   ├── scrape_series_list(self, max_pages) -> list
│   └── scrape_all_series(self, max_pages, max_series) -> list
```

### 7.2 核心代码实现

#### 7.2.1 电视剧列表爬取

```python
class TVScraper(BaseScraper):
    """电视剧爬虫"""
    
    def _parse_series_card(self, article):
        """解析电视剧卡片"""
        try:
            # 检查是否为电视剧
            quality_el = article.select_one('.quality')
            quality_text = quality_el.get_text(strip=True) if quality_el else ''
            
            if not re.match(r's\d+-e\d+', quality_text):
                return None  # 这是电影，跳过
            
            # 解析季集信息 (如 "s3-e9")
            se_match = re.match(r's(\d+)-e(\d+)', quality_text)
            latest_season = int(se_match.group(1)) if se_match else None
            latest_episode = int(se_match.group(2)) if se_match else None
            
            # 标题和URL
            title_el = article.select_one('.data h3 a')
            if not title_el:
                return None
            
            title = title_el.get_text(strip=True)
            detail_url = title_el.get('href', '')
            if not detail_url.startswith('http'):
                detail_url = self.BASE_URL + detail_url
            
            # 评分
            rating_el = article.select_one('.rating')
            rating_text = rating_el.get_text(strip=True) if rating_el else ''
            try:
                rating = float(rating_text) if rating_text else None
            except ValueError:
                rating = None
            
            # 年份
            year_el = article.select_one('.data span')
            year_text = year_el.get_text(strip=True) if year_el else ''
            try:
                year = int(year_text) if year_text else None
            except ValueError:
                year = None
            
            # 海报URL
            img_el = article.select_one('.poster img')
            image_url = img_el.get('src', '') if img_el else ''
            if image_url and not image_url.startswith('http'):
                image_url = self.BASE_URL + image_url
            
            # 音频
            audio_langs = []
            if article.select_one('.audio .latino'):
                audio_langs.append('Latino')
            if article.select_one('.audio .castellano'):
                audio_langs.append('Castellano')
            if article.select_one('.audio .subtitulado'):
                audio_langs.append('Subtitulado')
            
            return {
                'title_spanish': title,
                'year': year,
                'rating': rating,
                'latest_season': latest_season,
                'latest_episode': latest_episode,
                'image_url': image_url,
                'detail_url': detail_url,
                'audio': ', '.join(audio_langs) if audio_langs else None,
            }
            
        except Exception as e:
            print(f"  ⚠️ 解析电视剧卡片失败: {e}")
            return None
    
    def _parse_episodes(self, soup):
        """从详情页解析所有季集信息"""
        episodes = []
        
        # 获取所有季
        season_divs = soup.select('div[id^="season-"]')
        
        for season_div in season_divs:
            # 从 id 获取季数
            season_id = season_div.get('id', '')
            season_match = re.match(r'season-(\d+)', season_id)
            if not season_match:
                continue
            season_num = int(season_match.group(1))
            
            # 获取该季的所有剧集
            episode_links = season_div.select('a[id^="serie-"]')
            
            for ep_link in episode_links:
                ep_id = ep_link.get('id', '')
                data_num = ep_link.get('data-num', '')
                data_title = ep_link.get('data-title', '')
                
                # 从 id 解析集数
                ep_match = re.match(r'serie-\d+_(\d+)', ep_id)
                episode_num = int(ep_match.group(1)) if ep_match else None
                
                episodes.append({
                    'season': season_num,
                    'episode': episode_num,
                    'episode_title': data_title,
                    'episode_data_num': data_num,
                })
        
        return episodes
    
    def _parse_series_detail(self, url):
        """访问电视剧详情页，提取元数据和所有剧集"""
        soup = self._fetch_page(url)
        if not soup:
            return {}, []
        
        detail = {}
        
        try:
            # 原标题
            custom_fields = soup.select_one('.custom_fields')
            if custom_fields:
                valor = custom_fields.select_one('.valor')
                if valor:
                    detail['title_original'] = valor.get_text(strip=True)
            
            # 国家
            country_el = soup.select_one('.sheader .extra .country')
            if country_el:
                detail['country'] = country_el.get_text(strip=True)
            
            # 时长
            runtime_el = soup.select_one('.sheader .extra .runtime')
            if runtime_el:
                detail['duration'] = runtime_el.get_text(strip=True)
            
            # 类型
            extra = soup.select_one('.sheader .extra')
            if extra:
                spans = extra.select('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if 'Series' in text:
                        # 去除 "Series" 前缀，保留类型
                        genre = text.replace('Series', '').strip()
                        if genre:
                            detail['genre'] = genre
                        break
            
            # 清晰度
            if extra:
                spans = extra.select('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if 'HD' in text or '/' in text:
                        detail['quality'] = text
                        break
            
            # 评分
            rating_el = soup.select_one('.dt_rating_vgs')
            if rating_el:
                try:
                    detail['rating'] = float(rating_el.get_text(strip=True))
                except ValueError:
                    pass
            
            # 海报
            poster_el = soup.select_one('.sheader .poster img')
            if poster_el:
                src = poster_el.get('src', '')
                if src and not src.startswith('http'):
                    src = self.BASE_URL + src
                detail['image_url'] = src
            
        except Exception as e:
            print(f"  ⚠️ 解析电视剧详情失败: {e}")
        
        # 解析所有剧集
        episodes = self._parse_episodes(soup)
        
        return detail, episodes
    
    def scrape_series_list(self, max_pages=None):
        """爬取电视剧列表"""
        series_list = []
        page = 1
        
        print(f"\n{'='*60}")
        print(f"📺 开始爬取电视剧列表...")
        print(f"{'='*60}")
        
        while True:
            if max_pages and page > max_pages:
                break
            
            if page == 1:
                url = f"{self.BASE_URL}/series/"
            else:
                url = f"{self.BASE_URL}/series/page/{page}/"
            
            print(f"\n📄 正在爬取第 {page} 页: {url}")
            
            soup = self._fetch_page(url)
            if not soup:
                break
            
            articles = soup.select('article.item.movies')
            if not articles:
                articles = soup.select('article.item')
            
            if not articles:
                print(f"  ✅ 没有更多内容")
                break
            
            page_series = []
            for article in articles:
                series = self._parse_series_card(article)
                if series:
                    page_series.append(series)
            
            print(f"  找到 {len(page_series)} 部电视剧")
            series_list.extend(page_series)
            
            # 检查下一页
            pagination = soup.select_one('.pagination')
            if not pagination or not pagination.select_one('#nextpagination'):
                print(f"  ✅ 已到最后一页")
                break
            
            page += 1
            self._random_delay()
        
        print(f"\n✨ 电视剧列表爬取完成！共 {len(series_list)} 部电视剧")
        return series_list
    
    def scrape_all_series(self, max_pages=None, max_series=None):
        """爬取所有电视剧及其剧集"""
        # 第一步：获取电视剧列表
        series_list = self.scrape_series_list(max_pages)
        
        if max_series:
            series_list = series_list[:max_series]
        
        print(f"\n{'#'*60}")
        print(f"# 开始爬取 {len(series_list)} 部电视剧的所有剧集")
        print(f"{'#'*60}")
        
        all_episodes = []
        
        for i, series in enumerate(series_list):
            print(f"\n[{i+1}/{len(series_list)}] 📺 {series['title_spanish']}")
            
            detail, episodes = self._parse_series_detail(series['detail_url'])
            
            # 合并信息
            for ep in episodes:
                ep_data = {
                    'series_title_spanish': series['title_spanish'],
                    'series_title_original': detail.get('title_original', ''),
                    'year': series['year'],
                    'rating': detail.get('rating', series['rating']),
                    'quality': detail.get('quality', ''),
                    'image_url': detail.get('image_url', series['image_url']),
                    'series_url': series['detail_url'],
                    'season': ep['season'],
                    'episode': ep['episode'],
                    'episode_title': ep['episode_title'],
                    'episode_data_num': ep['episode_data_num'],
                    'country': detail.get('country', ''),
                    'duration': detail.get('duration', ''),
                    'genre': detail.get('genre', ''),
                    'audio': series.get('audio', ''),
                }
                all_episodes.append(ep_data)
            
            print(f"  ✅ 找到 {len(episodes)} 个剧集")
            self._random_delay()
        
        print(f"\n🎉 所有电视剧爬取完成！总计 {len(all_episodes)} 个剧集")
        return all_episodes
```

---

## 8. 主程序与命令行接口

### 8.1 命令行参数设计

```
usage: main.py [-h] {movies,tv,update,stats,export} ...

RepelisHD 爬虫系统

commands:
  movies    爬取电影数据
  tv        爬取电视剧数据
  update    更新所有数据
  stats     查看数据库统计
  export    导出数据到CSV

movies 参数:
  --year YEAR           爬取指定年份
  --start-year START    起始年份
  --end-year END        结束年份
  --max-pages N         每个年份最大页数
  --no-details          不访问详情页
  --delay-min FLOAT     最小延迟(秒)
  --delay-max FLOAT     最大延迟(秒)

tv 参数:
  --max-pages N         列表最大页数
  --max-series N        最大电视剧数量
  --delay-min FLOAT     最小延迟(秒)
  --delay-max FLOAT     最大延迟(秒)
```

### 8.2 主程序框架

```python
import argparse
import sys
from movie_scraper import MovieScraper
from tv_scraper import TVScraper
from database import Database

def main():
    parser = argparse.ArgumentParser(description='RepelisHD 爬虫系统')
    subparsers = parser.add_subparsers(dest='command')
    
    # movies 子命令
    movies_parser = subparsers.add_parser('movies', help='爬取电影')
    movies_parser.add_argument('--year', type=int, help='指定年份')
    movies_parser.add_argument('--start-year', type=int, help='起始年份')
    movies_parser.add_argument('--end-year', type=int, help='结束年份')
    movies_parser.add_argument('--max-pages', type=int, help='最大页数')
    movies_parser.add_argument('--no-details', action='store_true', help='不访问详情页')
    movies_parser.add_argument('--delay-min', type=float, default=1.0)
    movies_parser.add_argument('--delay-max', type=float, default=3.0)
    
    # tv 子命令
    tv_parser = subparsers.add_parser('tv', help='爬取电视剧')
    tv_parser.add_argument('--max-pages', type=int, help='最大页数')
    tv_parser.add_argument('--max-series', type=int, help='最大电视剧数')
    tv_parser.add_argument('--delay-min', type=float, default=1.0)
    tv_parser.add_argument('--delay-max', type=float, default=3.0)
    
    # update 子命令
    subparsers.add_parser('update', help='更新所有数据')
    
    # stats 子命令
    subparsers.add_parser('stats', help='查看统计')
    
    # export 子命令
    export_parser = subparsers.add_parser('export', help='导出CSV')
    export_parser.add_argument('--output-dir', default='./exports')
    
    args = parser.parse_args()
    
    db = Database('repelishd.db')
    
    if args.command == 'movies':
        scraper = MovieScraper(args.delay_min, args.delay_max)
        if args.year:
            movies = scraper.scrape_by_year(args.year, args.max_pages, not args.no_details)
        elif args.start_year and args.end_year:
            movies = scraper.scrape_year_range(args.start_year, args.end_year, 
                                                args.max_pages, not args.no_details)
        db.save_movies(movies)
    
    elif args.command == 'tv':
        scraper = TVScraper(args.delay_min, args.delay_max)
        episodes = scraper.scrape_all_series(args.max_pages, args.max_series)
        db.save_tv_episodes(episodes)
    
    # ... 其他命令

if __name__ == '__main__':
    main()
```

---

## 9. 反爬虫策略

### 9.1 已知防护措施

| 防护类型 | 说明 | 应对策略 |
|---------|------|---------|
| Cloudflare | 基础 DDoS 防护 | 使用 Session 保持 Cookie |
| 频率限制 | 过快请求可能被封 | 随机延迟 1-3 秒 |
| User-Agent 检测 | 可能检测爬虫 UA | 随机轮换 UA |
| 弹窗广告 | 页面有广告弹窗 | 不影响 HTML 解析 |

### 9.2 应对策略

```python
# 1. 随机 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
    # ... 更多 UA
]

# 2. 随机延迟
import random
time.sleep(random.uniform(1.0, 3.0))

# 3. Session 保持
session = requests.Session()
session.headers.update({
    'Accept-Language': 'es-MX,es;q=0.9',
    'Referer': 'https://repelishd.city',
})

# 4. 重试机制
for attempt in range(3):
    try:
        response = session.get(url, timeout=30)
        break
    except Exception:
        time.sleep((attempt + 1) * 5)

# 5. 编码处理
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')
```

### 9.3 Cloudflare 绕过注意事项

如果遇到 Cloudflare 挑战页面，可以考虑：

1. **使用 cloudscraper 库**：`pip install cloudscraper`
2. **使用 Selenium/Playwright**：模拟真实浏览器
3. **降低请求频率**：增加延迟到 3-5 秒

```python
# 使用 cloudscraper 替代 requests
import cloudscraper
scraper = cloudscraper.create_scraper()
response = scraper.get(url)
```

---

## 10. 数据导出模块

### 10.1 CSV 导出

```python
import csv
import os
from datetime import datetime

def export_movies_csv(db, output_dir='./exports'):
    """导出电影数据到CSV"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'repelishd_movies_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    
    movies = db.get_all_movies()
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Year', 'Title_Spanish', 'Title_Original', 'Rating', 
            'Quality', 'Image_URL', 'Detail_URL', 'Country', 
            'Duration', 'Genre', 'Audio', 'IMDb_Rating', 'TMDb_Rating'
        ])
        for movie in movies:
            writer.writerow([
                movie['year'], movie['title_spanish'], movie['title_original'],
                movie['rating'], movie['quality'], movie['image_url'],
                movie['detail_url'], movie['country'], movie['duration'],
                movie['genre'], movie['audio'], movie['imdb_rating'],
                movie['tmdb_rating']
            ])
    
    print(f"✅ 电影数据已导出: {filepath} ({len(movies)} 条记录)")
    return filepath

def export_tv_csv(db, output_dir='./exports'):
    """导出电视剧数据到CSV"""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'repelishd_tv_episodes_{timestamp}.csv'
    filepath = os.path.join(output_dir, filename)
    
    episodes = db.get_all_tv_episodes()
    
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Year', 'Series_Title_Spanish', 'Series_Title_Original',
            'Season', 'Episode', 'Episode_Title', 'Episode_DataNum',
            'Rating', 'Quality', 'Image_URL', 'Series_URL',
            'Country', 'Duration', 'Genre', 'Audio'
        ])
        for ep in episodes:
            writer.writerow([
                ep['year'], ep['series_title_spanish'], ep['series_title_original'],
                ep['season'], ep['episode'], ep['episode_title'],
                ep['episode_data_num'], ep['rating'], ep['quality'],
                ep['image_url'], ep['series_url'], ep['country'],
                ep['duration'], ep['genre'], ep['audio']
            ])
    
    print(f"✅ 电视剧数据已导出: {filepath} ({len(episodes)} 条记录)")
    return filepath
```

---

## 11. 定时任务与增量更新

### 11.1 增量更新策略

```python
def update_movies(db, scraper, recent_years=2):
    """增量更新电影数据"""
    current_year = datetime.now().year
    years = list(range(current_year - recent_years + 1, current_year + 2))  # 包含下一年
    years.sort(reverse=True)
    
    for year in years:
        movies = scraper.scrape_by_year(year, fetch_details=True)
        db.save_movies(movies)  # upsert 自动去重

def update_tv(db, scraper, max_pages=5):
    """增量更新电视剧数据"""
    episodes = scraper.scrape_all_series(max_pages=max_pages)
    db.save_tv_episodes(episodes)  # upsert 自动去重
```

### 11.2 Windows 定时任务

```batch
@echo off
:: RepelisHD 每日更新脚本
cd /d "%~dp0"
python main.py update >> logs\update_%date:~0,4%%date:~5,2%%date:~8,2%.log 2>&1
```

使用 Windows 任务计划程序设置每日执行。

### 11.3 Linux Crontab

```bash
# 每天凌晨3点执行更新
0 3 * * * cd /path/to/repelishd && python3 main.py update >> logs/update_$(date +\%Y\%m\%d).log 2>&1
```

---

## 12. 常见问题与解决方案

### 12.1 编码问题

**问题**: 西班牙语特殊字符（如 ñ, á, é）显示为乱码

**解决**: 
```python
response.encoding = 'utf-8'
soup = BeautifulSoup(response.text, 'html.parser')
```

### 12.2 Cloudflare 拦截

**问题**: 返回 403 或 Cloudflare 挑战页面

**解决**: 
```python
import cloudscraper
scraper = cloudscraper.create_scraper()
```

### 12.3 请求超时

**问题**: 网络不稳定导致超时

**解决**: 实现重试机制，每次增加等待时间

### 12.4 数据重复

**问题**: 多次运行导致数据重复

**解决**: 使用 `ON CONFLICT ... DO UPDATE` SQL 语句实现 upsert

### 12.5 按年份搜索混合电影和电视剧

**问题**: `/xfsearch/year/{year}` 页面同时包含电影和电视剧

**解决**: 通过 `.quality` 标签内容过滤，`HD` 为电影，`s\d+-e\d+` 为电视剧

### 12.6 Python 缓存问题

**问题**: 修改代码后运行仍使用旧版本

**解决**: 
```batch
rmdir /s /q __pycache__
del /s /q *.pyc
:: 或使用 -B 参数
python -B main.py ...
```

---

## 附录 A: 与 Cuevana3 爬虫的对比

| 特性 | Cuevana3 (ww9.cuevana3.to) | RepelisHD (repelishd.city) |
|------|---------------------------|---------------------------|
| 模板引擎 | WordPress | DLE (DataLife Engine) |
| 电影URL | `/pelicula/{slug}/` | `/ver-pelicula/{id}-{slug}-online-espanol.html` |
| 电视剧URL | `/serie/{slug}/` | `/ver-pelicula/{id}-{slug}-online-espanol.html` (共用) |
| 剧集URL | `/episodio/{slug}-{season}x{episode}` | 无独立URL，在详情页内 |
| 卡片选择器 | `div.TPost` | `article.item.movies` |
| 评分位置 | `p.meta span` | `.rating` |
| 原标题 | `h2.SubTitle` | `.custom_fields .valor` |
| 季集结构 | 独立剧集页面 | 详情页内 `div[id^="season-"]` |
| 区分电影/电视剧 | URL路径不同 | `.quality` 标签内容 |
| 分页 | 类似 | `.pagination` |
| 按年份搜索 | `/estreno/{year}/` | `/xfsearch/year/{year}` |

---

## 附录 B: 完整文件结构

```
repelishd_scraper/
├── main.py                 # 主程序和命令行接口
├── base_scraper.py         # 基础爬虫类
├── movie_scraper.py        # 电影爬虫模块
├── tv_scraper.py           # 电视剧爬虫模块
├── database.py             # 数据库管理模块
├── config_manager.py       # 配置管理模块
├── requirements.txt        # Python 依赖
├── repelishd.db            # SQLite 数据库（运行后生成）
├── config.json             # 配置文件（运行后生成）
├── repelishd_launcher.bat  # Windows 一键启动脚本
├── schedule_task.bat       # Windows 定时任务脚本
├── exports/                # CSV 导出目录
│   ├── repelishd_movies_YYYYMMDD_HHMMSS.csv
│   └── repelishd_tv_episodes_YYYYMMDD_HHMMSS.csv
├── logs/                   # 日志目录
│   └── update_YYYYMMDD.log
├── .vscode/                # VS Code 配置
│   ├── tasks.json
│   ├── launch.json
│   └── settings.json
└── README.md               # 使用文档
```

---

**文档结束**

本文档基于对 repelishd.city 网站的实际访问和分析编写，所有 CSS 选择器和 HTML 结构均经过验证。如网站结构发生变化，请重新分析并更新相应的选择器。
