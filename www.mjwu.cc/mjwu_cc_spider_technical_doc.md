# 美剧屋 (mjwu.cc) 爬虫系统技术文档

**版本**: v1.0  
**日期**: 2026-03-04  
**目标网站**: https://www.mjwu.cc  
**网站名称**: 美剧屋  
**文档类型**: 爬虫实现技术指南（仅调研，不执行爬虫）

---

## 📋 文档说明

本文档详细分析美剧屋 (mjwu.cc) 网站结构，提供完整的爬虫实现技术方案，包括电影和电视剧数据的爬取、存储、导出等功能。

**核心功能**:
1. 🎬 电影数据爬取（按年份、自动翻页、倒序优先）
2. 📺 电视剧数据爬取（提取所有季和集、支持数量限制）
3. 💾 SQLite 数据库存储（自动去重、增量更新）
4. 📊 CSV 数据导出（增量/全量、分表导出）

---

## 1. 网站结构分析

### 1.1 基本信息

| 属性 | 值 |
|------|-----|
| 域名 | mjwu.cc |
| 网站名称 | 美剧屋 |
| CMS系统 | 苹果CMS (MacCMS) v10 |
| 模板 | Conch海螺模板 |
| 编码 | UTF-8 |
| 图片CDN | cdn.04pic.com |
| 总影视数 | 约 30,000+ |

### 1.2 内容分类体系

| 大类 | 分类ID | URL路径 | 估计总量 |
|------|--------|---------|---------|
| 美剧 | meiju | /type/meiju/ | ~15,000+ |
| 电影 | dianying | /type/dianying/ | ~10,000+ |
| 综艺 | zongyi | /type/zongyi/ | ~2,000+ |
| 动漫 | dongman | /type/dongman/ | ~3,000+ |

### 1.3 导航菜单

| 名称 | URL |
|------|-----|
| 首页 | / |
| 美剧 | /type/meiju/ |
| 电影 | /type/dianying/ |
| 专题 | /topic |
| 留言 | /gbook |
| 最新 | /map |
| 排行 | /label/rank.html |

---

## 2. URL路由体系

### 2.1 URL格式表

| 页面类型 | URL格式 | 示例 |
|---------|---------|------|
| 分类首页 | `/type/{type}/` | `/type/meiju/` |
| 分页 | `/type/{type}/page/{page}/` | `/type/meiju/page/2/` |
| 年份筛选 | `/type/{type}/year/{year}/` | `/type/meiju/year/2025/` |
| 年份+分页 | `/type/{type}/year/{year}/page/{page}/` | `/type/meiju/year/2025/page/2/` |
| 详情页 | `/vod/{id}/` | `/vod/13252/` |
| 播放页 | `/play/{id}-{source}-{episode}/` | `/play/13252-1-1/` |
| 搜索页 | `/search/--/` (POST参数wd) | `/search/--/?wd=关键词` |

### 2.2 URL参数解析

**Python构造函数**:

```python
def build_list_url(content_type, page=1, year=None):
    """构造列表页URL
    
    Args:
        content_type: 内容类型 ('meiju', 'dianying', 'zongyi', 'dongman')
        page: 页码 (默认1)
        year: 年份 (可选)
    """
    base = f"/type/{content_type}"
    
    if year and page > 1:
        return f"{base}/year/{year}/page/{page}/"
    elif year:
        return f"{base}/year/{year}/"
    elif page > 1:
        return f"{base}/page/{page}/"
    else:
        return f"{base}/"

def build_search_url(keyword):
    """构造搜索URL"""
    import urllib.parse
    encoded = urllib.parse.quote(keyword)
    return f"/search/--/?wd={encoded}"
```

### 2.3 播放页URL解析

```
/play/{id}-{source}-{episode}/
```

| 参数 | 说明 | 示例 |
|------|------|------|
| id | 视频ID | 13252 |
| source | 播放源编号 | 1 = 云播, 2 = 备用线路 |
| episode | 集数编号 | 1 = 第01集 |

### 2.4 季(Season)和集(Episode)解析规则

**季数提取**（从标题中解析）：
- 中文格式：`第X季` → 如"乔治和曼迪的头婚生活**第二季**" → season=2
- 英文格式：`Season X` → 如"The Witcher Season 3" → season=3
- 默认：无季数信息时 season=1

**集数提取**（从播放列表解析）：
- 格式：`第XX集` → 如"第01集" → episode=1
- URL中的episode参数：`/play/13252-1-1/` → episode=1

**多播放源处理**：
- 每个播放源可能有不同的集数列表
- 需要分别记录每个播放源的集数

---

## 3. HTML结构与CSS选择器

### 3.1 列表页结构

```html
<li class="hl-list-item hl-col-xs-3 hl-col-sm-2 hl-col-md-2">
  <a class="hl-item-thumb hl-lazy" 
     href="/vod/13252/" 
     title="56天"
     data-original="https://cdn.04pic.com/image/6995dca2ec5dc.jpg">
    <div class="hl-pic-tag">
      <span>8集全</span>
    </div>
  </a>
  <div class="hl-item-title hl-text-site hl-lc-1">
    <a href="/vod/13252/" title="56天">56天</a>
  </div>
</li>
```

**CSS选择器速查表**：

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 卡片容器 | `li.hl-list-item` | 遍历所有 |
| 详情页URL | `a.hl-item-thumb` | `.get('href')` |
| 标题 | `a.hl-item-thumb` | `.get('title')` |
| 海报图URL | `a.hl-item-thumb` | `.get('data-original')` |
| 状态/清晰度 | `.hl-pic-tag span` | `.text.strip()` |
| 标题链接 | `.hl-item-title a` | `.text.strip()` |

### 3.2 分页结构

```html
<div class="hl-page-wrap">
  <ul class="hl-page-info">
    <li><a href="/type/meiju/">首页</a></li>
    <li><a href="/type/meiju/page/1/">上一页</a></li>
    <li class="active"><a href="/type/meiju/page/1/">1</a></li>
    <li><a href="/type/meiju/page/2/">2</a></li>
    <li><a href="/type/meiju/page/3/">3</a></li>
    ...
    <li><a href="/type/meiju/page/100/">尾页</a></li>
  </ul>
</div>
```

**提取总页数**:
```python
# 从分页信息中提取总页数
page_wrap = soup.select_one('.hl-page-wrap')
if page_wrap:
    # 查找尾页链接
    last_page_link = page_wrap.find('a', string='尾页')
    if last_page_link:
        match = re.search(r'/page/(\d+)/', last_page_link.get('href', ''))
        if match:
            total_pages = int(match.group(1))
```

### 3.3 详情页结构

```html
<div class="hl-data-list">
  <ul class="clearfix">
    <li class="hl-col-xs-12 hl-hide-sm">
      <em class="hl-text-muted">片名：</em><span>56天</span>
    </li>
    <li class="hl-col-xs-12">
      <em class="hl-text-muted">主演：</em>
      <a href="/search/-%E5%BE%B7%E8%8A%99%C2%B7%E5%8D%A1%E6%A2%85%E9%9A%86-/" target="_blank">德芙·卡梅隆</a><i>/</i>
      <a href="/search/-%E9%98%BF%E4%B8%87%C2%B7%E4%B9%94%E8%B4%BE-/" target="_blank">阿万·乔贾</a>
    </li>
    <li class="hl-col-xs-12">
      <em class="hl-text-muted">导演：</em>
      <a href="/search/--%E8%8E%8E%E5%A8%9C%C2%B7%E6%96%AF%E5%9D%A6/" target="_blank">莎娜·斯坦</a>
    </li>
    <li class="hl-col-xs-12 hl-col-sm-4">
      <em class="hl-text-muted">年份：</em>2026
    </li>
    <li class="hl-col-xs-12 hl-col-sm-4">
      <em class="hl-text-muted">地区：</em>美国
    </li>
    <li class="hl-col-xs-12 hl-col-sm-4">
      <em class="hl-text-muted">类型：</em>
      <a href="/search/--/class/%E5%89%A7%E6%83%85/" target="_blank">剧情</a>
    </li>
    <li class="hl-col-xs-12 blurb">
      <em class="hl-text-muted">简介：</em>Oliver和Ciara在超市偶遇相识...
    </li>
  </ul>
</div>

<!-- 评分 -->
<span class="hl-score-nums hl-text-conch hl-alert-items hl-half-items">8.0</span>
<span class="hl-score-data hl-text-muted hl-pull-right">1次评分</span>

<!-- 播放源 -->
<div class="hl-play-source hl-hidden">
  <ul class="hl-plays-list hl-sort-list hl-list-hide-xs clearfix" id="hl-plays-list">
    <li class="hl-col-xs-4 hl-col-sm-2 hl-col-md-6">
      <a href="/play/13252-1-1/" class="hl-text-conch active">
        <em class="hl-play-active hl-bg-conch"></em>第01集
      </a>
    </li>
    <li class="hl-col-xs-4 hl-col-sm-2 hl-col-md-6">
      <a href="/play/13252-1-2/">第02集</a>
    </li>
    ...
  </ul>
</div>
```

**CSS选择器速查表**：

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 标题 | `.hl-data-list li:contains("片名") span` | `.text.strip()` |
| 主演 | `li:contains("主演") a` | 多个`a`文本拼接 |
| 导演 | `li:contains("导演") a` | 多个`a`文本拼接 |
| 年份 | `li:contains("年份")` | `int(去掉前缀)` |
| 地区 | `li:contains("地区")` | 去掉"地区："前缀 |
| 类型 | `li:contains("类型") a` | 多个`a`文本拼接 |
| 简介 | `li.blurb` | 去掉"简介："前缀 |
| 海报图 | `.hl-item-thumb` | `.get('data-original')` |
| 评分 | `.hl-score-nums` | `float(.text)` |
| 评分次数 | `.hl-score-data` | 正则提取数字 |
| 播放列表 | `#hl-plays-list li a` | `.get('href')` |

**多播放源结构**：
```html
<div class="hl-plays-from hl-tabs swiper-wrapper clearfix">
  <li class="active" data-href="/play/11571-1-1/">
    <span class="hl-from-juhe">云播</span>
  </li>
  <li data-href="/play/11571-2-1/">
    <span class="hl-from-beiyong">备用线路</span>
  </li>
</div>
<ul class="hl-plays-list hl-sort-list hl-list-hide-xs clearfix" id="hl-plays-list">
  <li><a href="/play/11571-1-1/" class="active">第01集</a></li>
  <li><a href="/play/11571-1-2/">第02集</a></li>
  ...
</ul>
```

**CSS选择器速查表（多播放源）**：

| 数据字段 | CSS选择器 | 提取方式 |
|---------|----------|---------|
| 播放源列表 | `.hl-plays-from li` | 遍历所有播放源 |
| 播放源名称 | `.hl-plays-from li span` | `.text.strip()` |
| 播放源链接 | `.hl-plays-from li` | `.get('data-href')` |
| 当前播放源集数 | `#hl-plays-list li a` | 遍历当前源的所有集 |

### 3.4 播放页结构

```html
<script type="text/javascript">
var player_aaaa = {
  "flag": "play",
  "encrypt": 0,
  "trysee": 0,
  "points": 0,
  "link": "\/play\/13252-1-1\/",
  "link_next": "\/play\/13252-1-2\/",
  "link_pre": "",
  "vod_data": {
    "vod_name": "56天",
    "vod_actor": "德芙·卡梅隆,阿万·乔贾,梅根·佩塔·希尔...",
    "vod_director": "莎娜·斯坦,阿莱西娅·琼斯",
    "vod_class": "剧情,爱情,悬疑"
  },
  "url": "CMjQ0MDdfMG1hYw==",
  "url_next": "CMjQ0MDdfMW1hYw==",
  "from": "juhe",
  "server": "",
  "note": "",
  "id": "13252",
  "sid": 1,
  "nid": 1
};
</script>
```

**提取方式**:

```python
import re
import json

# 从页面中提取player_aaaa变量
script_pattern = r'var player_aaaa=(\{.*?\});'
match = re.search(script_pattern, html, re.DOTALL)
if match:
    player_data = json.loads(match.group(1))
    video_url = player_data.get('url')  # 注意：可能是加密的
    video_id = player_data.get('id')
    source_id = player_data.get('sid')
    episode_id = player_data.get('nid')
    next_episode = player_data.get('link_next')
    vod_name = player_data.get('vod_data', {}).get('vod_name')
```

### 3.5 电影 vs 电视剧区分方法

**方法1：通过URL路径区分**（推荐）

```python
def get_content_type_from_url(url):
    """根据URL判断内容类型"""
    if '/type/meiju/' in url or '/type/zongyi/' in url:
        return 'tv_series'
    elif '/type/dianying/' in url:
        return 'movie'
    elif '/type/dongman/' in url:
        return 'anime'
    return 'unknown'
```

**方法2：通过播放列表判断**

```python
def is_tv_series(soup):
    """通过播放列表判断是否为电视剧"""
    playlist = soup.select('#hl-plays-list li a')
    episode_links = [a for a in playlist if re.search(r'第\d+集', a.text)]
    return len(episode_links) > 1
```

**方法3：通过状态文本区分**

```python
def is_tv_by_status(status_text):
    """通过状态文本判断是否为电视剧"""
    tv_keywords = ['集', '完结', '更新至', '第', '全', '连载']
    return any(kw in status_text for kw in tv_keywords)
```

---

## 4. 数据库设计

### 4.1 电影表 (movies)

```sql
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vod_id INTEGER UNIQUE NOT NULL,          -- 视频ID（从URL提取）
    title TEXT NOT NULL,                      -- 电影标题
    original_title TEXT DEFAULT '',           -- 原标题（外文）
    category TEXT DEFAULT '',                 -- 分类（电影）
    genre TEXT DEFAULT '',                    -- 类型/标签
    region TEXT DEFAULT '',                   -- 地区
    year INTEGER DEFAULT 0,                  -- 年份
    language TEXT DEFAULT '',                -- 语言
    director TEXT DEFAULT '',                -- 导演
    actors TEXT DEFAULT '',                  -- 主演（逗号分隔）
    status TEXT DEFAULT '',                  -- 状态（HD中字、正片等）
    rating REAL DEFAULT 0.0,                 -- 评分
    rating_count INTEGER DEFAULT 0,          -- 评分次数
    poster_url TEXT DEFAULT '',              -- 海报图URL
    detail_url TEXT NOT NULL,                -- 详情页URL
    play_url TEXT DEFAULT '',                -- 播放页URL
    synopsis TEXT DEFAULT '',                -- 简介
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_movies_vod_id ON movies(vod_id);
CREATE INDEX idx_movies_year ON movies(year);
CREATE INDEX idx_movies_category ON movies(category);
CREATE INDEX idx_movies_created_at ON movies(created_at);
```

### 4.2 电视剧主表 (tv_series)

```sql
CREATE TABLE IF NOT EXISTS tv_series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vod_id INTEGER UNIQUE NOT NULL,          -- 视频ID
    title TEXT NOT NULL,                      -- 剧名
    original_title TEXT DEFAULT '',           -- 原标题
    category TEXT DEFAULT '',                 -- 分类（美剧、综艺等）
    genre TEXT DEFAULT '',                    -- 类型/标签
    region TEXT DEFAULT '',                   -- 地区
    year INTEGER DEFAULT 0,                  -- 年份
    language TEXT DEFAULT '',                -- 语言
    director TEXT DEFAULT '',                -- 导演
    actors TEXT DEFAULT '',                  -- 主演
    status TEXT DEFAULT '',                  -- 状态（8集全、连载中等）
    total_episodes INTEGER,                  -- 总集数
    current_episode INTEGER,                 -- 当前更新到的集数
    rating REAL DEFAULT 0.0,                 -- 评分
    rating_count INTEGER DEFAULT 0,          -- 评分次数
    poster_url TEXT DEFAULT '',              -- 海报图URL
    detail_url TEXT NOT NULL,                -- 详情页URL
    synopsis TEXT DEFAULT '',                -- 简介
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_tv_series_vod_id ON tv_series(vod_id);
CREATE INDEX idx_tv_series_year ON tv_series(year);
CREATE INDEX idx_tv_series_category ON tv_series(category);
```

### 4.3 电视剧集数表 (tv_episodes)

```sql
CREATE TABLE IF NOT EXISTS tv_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vod_id INTEGER NOT NULL,                 -- 关联tv_series.vod_id
    season_number INTEGER DEFAULT 1,         -- 季数（从标题解析：第X季）
    episode_number INTEGER NOT NULL,         -- 集数编号（从播放列表解析：第XX集）
    episode_title TEXT DEFAULT '',           -- 集数标题（如"第01集"）
    play_url TEXT NOT NULL,                  -- 播放页URL
    video_url TEXT DEFAULT '',               -- 视频直链（可选）
    source_name TEXT DEFAULT '',             -- 播放源名称（如云播、备用线路）
    source_index INTEGER DEFAULT 1,          -- 播放源编号（URL中的source参数）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vod_id, season_number, episode_number, source_index)  -- 去重
);

-- 索引
CREATE INDEX idx_tv_episodes_vod_id ON tv_episodes(vod_id);
CREATE INDEX idx_tv_episodes_season ON tv_episodes(season_number);
CREATE INDEX idx_tv_episodes_episode ON tv_episodes(episode_number);
CREATE INDEX idx_tv_episodes_play_url ON tv_episodes(play_url);
```

**季和集维度说明**：
- **season_number**: 从剧集标题中解析（如"第二季"→2），默认为1
- **episode_number**: 从播放列表中解析（如"第01集"→1）
- **source_index**: 对应URL中的source参数，区分不同播放源
- **同一部剧的多季**: 在美剧屋中，不同季是独立的vod_id（如"第一季"和"第二季"是不同的详情页）
- **同一季的多播放源**: 同一季的集数可能在不同播放源中有不同的链接

### 4.4 爬取进度表 (crawl_progress)

```sql
CREATE TABLE IF NOT EXISTS crawl_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,                 -- 'movie' 或 'tv'
    content_type TEXT NOT NULL,              -- 'meiju', 'dianying', 'zongyi', 'dongman'
    year INTEGER,                            -- 年份
    current_page INTEGER DEFAULT 1,          -- 当前页码
    total_pages INTEGER,                     -- 总页数
    status TEXT DEFAULT 'running',           -- 'running', 'paused', 'completed', 'failed'
    last_vod_id INTEGER,                     -- 最后处理的视频ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_type, content_type, year)
);
```

### 4.5 数据导出日志表 (export_logs)

```sql
CREATE TABLE IF NOT EXISTS export_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    export_type TEXT NOT NULL,               -- 'full' 或 'incremental'
    filepath TEXT NOT NULL,
    row_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'success',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.6 Upsert操作（去重与增量更新）

```python
def upsert_movie(conn, movie_data):
    """插入或更新电影数据（SQLite 3.24+支持ON CONFLICT）"""
    conn.execute("""
        INSERT INTO movies (vod_id, title, original_title, category, genre, region, 
                           year, language, director, actors, status, rating, rating_count,
                           poster_url, detail_url, play_url, synopsis)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(vod_id) DO UPDATE SET
            title = excluded.title,
            original_title = excluded.original_title,
            category = excluded.category,
            genre = excluded.genre,
            region = excluded.region,
            year = excluded.year,
            language = excluded.language,
            director = excluded.director,
            actors = excluded.actors,
            status = excluded.status,
            rating = excluded.rating,
            rating_count = excluded.rating_count,
            poster_url = excluded.poster_url,
            play_url = excluded.play_url,
            synopsis = excluded.synopsis,
            updated_at = CURRENT_TIMESTAMP
    """, tuple(movie_data.values()))
    conn.commit()
```

---

## 5. 核心架构设计

### 5.1 项目结构

```
mjwu_spider/
├── config/
│   ├── __init__.py
│   ├── settings.yaml          # 主配置文件
│   └── logging.yaml           # 日志配置
├── core/
│   ├── __init__.py
│   ├── base_spider.py         # 爬虫基类
│   ├── database.py            # 数据库管理
│   ├── request_handler.py     # 请求处理器
│   └── progress_manager.py    # 进度管理（断点续传）
├── spiders/
│   ├── __init__.py
│   ├── movie_spider.py        # 电影爬虫
│   └── tv_spider.py           # 电视剧爬虫
├── parsers/
│   ├── __init__.py
│   ├── list_parser.py         # 列表页解析
│   ├── detail_parser.py       # 详情页解析
│   └── play_parser.py         # 播放页解析
├── exporters/
│   ├── __init__.py
│   └── csv_exporter.py        # CSV导出器
├── utils/
│   ├── __init__.py
│   ├── validators.py          # 数据校验
│   └── helpers.py             # 辅助函数
├── data/
│   ├── exports/               # 导出文件目录
│   └── logs/                  # 日志目录
├── spider.db                  # SQLite数据库
├── main.py                    # 主程序入口
└── requirements.txt
```

### 5.2 配置文件 (settings.yaml)

```yaml
# 爬虫配置
spider:
  base_url: "https://www.mjwu.cc"
  # iPhone 17 UA (iOS 18)
  iphone_ua: "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
  # PC UA
  pc_ua: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  delay_range: [1, 3]           # 请求延迟范围（秒）
  max_retries: 3                # 最大重试次数
  timeout: 15                   # 请求超时（秒）
  concurrent_requests: 1        # 并发数（建议保持1，避免被封）

# 数据库配置
database:
  path: "spider.db"

# 爬取范围配置
crawl:
  movie:
    enabled: true
    content_type: "dianying"    # 电影分类
    year_start: 1945            # 开始年份
    year_end: 2026              # 结束年份
    max_pages: null             # null=不限制
    fetch_rating: true          # 是否获取评分
  tv:
    enabled: true
    content_type: "meiju"       # 美剧分类
    year_start: 1945
    year_end: 2026
    max_pages: null
    max_episodes: null          # 每部剧最大集数限制（null=不限制）

# 导出配置
export:
  output_dir: "./data/exports"
  encoding: "utf-8-sig"
  delimiter: ","

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./data/logs/spider.log"
  max_bytes: 10485760           # 10MB
  backup_count: 5
```

---

## 6. 核心代码实现

### 6.1 爬虫基类 (base_spider.py)

```python
#!/usr/bin/env python3
"""爬虫基类"""

import re
import time
import random
import logging
import sqlite3
import requests
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class BaseSpider(ABC):
    """爬虫基类"""
    
    # iPhone 17 UA (iOS 18)
    IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
    
    # PC UA
    PC_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def __init__(self, config_path='config/settings.yaml'):
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.base_url = self.config['spider']['base_url']
        self.delay_range = tuple(self.config['spider']['delay_range'])
        self.max_retries = self.config['spider']['max_retries']
        self.timeout = self.config['spider']['timeout']
        
        # 初始化日志
        self.logger = self._init_logger()
        
        # 初始化Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.IPHONE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # 初始化数据库
        self.db_path = self.config['database']['path']
        self._init_database()
    
    def _init_logger(self):
        """初始化日志"""
        log_config = self.config['logging']
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, log_config['level']))
        
        # 控制台处理器
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(log_config['format']))
        logger.addHandler(console)
        
        # 文件处理器（带轮转）
        from logging.handlers import RotatingFileHandler
        Path(log_config['file']).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_config['file'],
            maxBytes=log_config['max_bytes'],
            backupCount=log_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_config['format']))
        logger.addHandler(file_handler)
        
        return logger
    
    def _get_random_ua(self):
        """获取随机User-Agent（iPhone/PC轮换）"""
        return random.choice([self.IPHONE_UA, self.PC_UA])
    
    def _init_database(self):
        """初始化数据库（子类实现具体表结构）"""
        pass
    
    def request(self, url, max_retries=None):
        """发送HTTP请求，带重试和随机延迟"""
        max_retries = max_retries or self.max_retries
        full_url = url if url.startswith('http') else urljoin(self.base_url, url)
        
        for attempt in range(max_retries):
            try:
                # 轮换UA
                self.session.headers['User-Agent'] = self._get_random_ua()
                response = self.session.get(full_url, timeout=self.timeout)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    time.sleep(random.uniform(*self.delay_range))
                    return response
                elif response.status_code == 404:
                    self.logger.warning(f"页面不存在: {full_url}")
                    return None
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {full_url}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"请求超时 ({attempt+1}/{max_retries}): {full_url}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"请求错误 ({attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def build_list_url(self, content_type, page=1, year=None):
        """构造列表页URL"""
        base = f"/type/{content_type}"
        if year and page > 1:
            return f"{base}/year/{year}/page/{page}/"
        elif year:
            return f"{base}/year/{year}/"
        elif page > 1:
            return f"{base}/page/{page}/"
        else:
            return f"{base}/"
    
    @staticmethod
    def extract_vod_id(url):
        """从URL中提取视频ID"""
        match = re.search(r'/(?:vod|play)/(\d+)', url)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def extract_year_from_url(url):
        """从URL中提取年份"""
        match = re.search(r'/year/(\d{4})', url)
        return int(match.group(1)) if match else None
    
    @abstractmethod
    def run(self):
        """运行爬虫（子类实现）"""
        pass
```

### 6.2 电影爬虫 (movie_spider.py)

```python
#!/usr/bin/env python3
"""电影爬虫"""

import re
import sqlite3
from core.base_spider import BaseSpider
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class MovieSpider(BaseSpider):
    """电影爬虫"""
    
    def _init_database(self):
        """初始化电影表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    original_title TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    genre TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    language TEXT DEFAULT '',
                    director TEXT DEFAULT '',
                    actors TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    rating REAL DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    play_url TEXT DEFAULT '',
                    synopsis TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
                CREATE INDEX IF NOT EXISTS idx_movies_category ON movies(category);
            """)
    
    def parse_list_page(self, soup):
        """解析列表页，返回电影列表和是否有下一页"""
        movies = []
        
        for card in soup.select('li.hl-list-item'):
            try:
                # 获取详情页链接
                link = card.select_one('a.hl-item-thumb')
                if not link:
                    continue
                
                href = link.get('href', '')
                detail_url = urljoin(self.base_url, href)
                vod_id = self.extract_vod_id(href)
                
                if not vod_id:
                    continue
                
                # 获取海报图
                poster_url = link.get('data-original', '')
                
                # 获取标题
                title = link.get('title', '').strip()
                
                # 获取状态/清晰度
                status_el = card.select_one('.hl-pic-tag span')
                status = status_el.text.strip() if status_el else ''
                
                movies.append({
                    'vod_id': vod_id,
                    'title': title,
                    'poster_url': poster_url,
                    'detail_url': detail_url,
                    'status': status,
                })
            except Exception as e:
                self.logger.error(f"解析卡片失败: {e}")
        
        # 检查是否有下一页
        has_next = bool(soup.select_one('.hl-page-wrap a[href*="/page/"]'))
        return movies, has_next
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        # 标题
        title_el = soup.select_one('.hl-data-list li:contains("片名") span')
        if title_el:
            data['title'] = title_el.text.strip()
        
        # 评分
        score_el = soup.select_one('.hl-score-nums')
        if score_el:
            try:
                data['rating'] = float(score_el.text.strip())
            except:
                data['rating'] = 0.0
        
        # 评分次数
        rating_count_el = soup.select_one('.hl-score-data')
        if rating_count_el:
            match = re.search(r'(\d+)次评分', rating_count_el.text)
            if match:
                data['rating_count'] = int(match.group(1))
        
        # 解析信息列表
        for li in soup.select('.hl-data-list li'):
            text = li.text.strip()
            
            if '主演：' in text:
                actors_links = li.select('a')
                data['actors'] = ','.join(a.text.strip() for a in actors_links)
            
            elif '导演：' in text:
                director_links = li.select('a')
                data['director'] = ','.join(a.text.strip() for a in director_links)
            
            elif '类型：' in text:
                category_links = li.select('a')
                if category_links:
                    data['category'] = category_links[0].text.strip()
                    data['genre'] = ','.join(a.text.strip() for a in category_links)
            
            elif '地区：' in text:
                data['region'] = text.replace('地区：', '').strip()
            
            elif '年份：' in text:
                try:
                    data['year'] = int(text.replace('年份：', '').strip())
                except:
                    data['year'] = 0
        
        # 海报图
        poster_el = soup.select_one('.hl-item-thumb')
        if poster_el:
            data['poster_url'] = poster_el.get('data-original', '')
        
        # 简介
        synopsis_el = soup.select_one('li.blurb')
        if synopsis_el:
            data['synopsis'] = synopsis_el.text.replace('简介：', '').strip()[:500]
        
        # 播放链接（取第一集）
        play_link = soup.select_one('#hl-plays-list li a')
        if play_link:
            data['play_url'] = urljoin(self.base_url, play_link.get('href', ''))
        
        return data
    
    def save_movie(self, conn, movie):
        """保存电影（Upsert）"""
        conn.execute("""
            INSERT INTO movies (vod_id, title, original_title, category, genre, region, 
                               year, language, director, actors, status, rating, rating_count,
                               poster_url, detail_url, play_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title, original_title=excluded.original_title,
                category=excluded.category, genre=excluded.genre,
                region=excluded.region, year=excluded.year,
                language=excluded.language, director=excluded.director,
                actors=excluded.actors, status=excluded.status,
                rating=excluded.rating, rating_count=excluded.rating_count,
                poster_url=excluded.poster_url, play_url=excluded.play_url,
                synopsis=excluded.synopsis, updated_at=CURRENT_TIMESTAMP
        """, (
            movie.get('vod_id'), movie.get('title', ''),
            movie.get('original_title', ''), movie.get('category', ''),
            movie.get('genre', ''), movie.get('region', ''),
            movie.get('year', 0), movie.get('language', ''),
            movie.get('director', ''), movie.get('actors', ''),
            movie.get('status', ''), movie.get('rating', 0.0),
            movie.get('rating_count', 0), movie.get('poster_url', ''),
            movie.get('detail_url', ''), movie.get('play_url', ''),
            movie.get('synopsis', '')
        ))
        conn.commit()
    
    def run(self, content_type='dianying', year_start=None, year_end=None, max_pages=None):
        """运行电影爬虫
        
        Args:
            content_type: 内容类型（默认dianying=电影）
            year_start: 开始年份（默认从配置读取）
            year_end: 结束年份（默认从配置读取）
            max_pages: 每年份最大页数（None=不限制）
        """
        config = self.config['crawl']['movie']
        content_type = content_type or config.get('content_type', 'dianying')
        year_start = year_start or config.get('year_start', 1945)
        year_end = year_end or config.get('year_end', 2026)
        
        # 构建年份列表（倒序，从最新年份开始）
        years = list(range(year_end, year_start - 1, -1))
        
        total_count = 0
        
        for year in years:
            self.logger.info(f"\n{'='*60}\n开始爬取 {year} 年电影\n{'='*60}")
            
            page = 1
            year_movies = 0
            
            while True:
                if max_pages and page > max_pages:
                    break
                
                url = self.build_list_url(content_type, page, year)
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
                            
                            self.save_movie(conn, movie)
                            total_count += 1
                            year_movies += 1
                            self.logger.info(f"✅ [{total_count}] {movie['title']} ({movie.get('year', 'N/A')}) - {movie.get('status', '')}")
                            
                        except Exception as e:
                            self.logger.error(f"❌ 处理失败: {movie.get('title', 'Unknown')} - {e}")
                
                if not has_next:
                    break
                page += 1
            
            self.logger.info(f"{year}年共爬取 {year_movies} 部电影")
        
        self.logger.info(f"\n🎉 电影爬取完成！共 {total_count} 部")
        return total_count
```

### 6.3 电视剧爬虫 (tv_spider.py)

```python
#!/usr/bin/env python3
"""电视剧爬虫 - 支持季(Season)和集(Episode)两个维度"""

import re
import sqlite3
from core.base_spider import BaseSpider
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class TVSpider(BaseSpider):
    """电视剧爬虫
    
    支持维度：
    - 季(Season): 从标题解析（如"第二季"→2）
    - 集(Episode): 从播放列表解析（如"第01集"→1）
    - 播放源(Source): 支持多播放源（如云播、备用线路）
    """
    
    def _init_database(self):
        """初始化电视剧表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS tv_series (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    original_title TEXT DEFAULT '',
                    category TEXT DEFAULT '',
                    genre TEXT DEFAULT '',
                    region TEXT DEFAULT '',
                    year INTEGER DEFAULT 0,
                    language TEXT DEFAULT '',
                    director TEXT DEFAULT '',
                    actors TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    total_episodes INTEGER,
                    current_episode INTEGER,
                    rating REAL DEFAULT 0.0,
                    rating_count INTEGER DEFAULT 0,
                    poster_url TEXT DEFAULT '',
                    detail_url TEXT NOT NULL,
                    synopsis TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS tv_episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vod_id INTEGER NOT NULL,
                    season_number INTEGER DEFAULT 1,
                    episode_number INTEGER NOT NULL,
                    episode_title TEXT DEFAULT '',
                    play_url TEXT NOT NULL,
                    video_url TEXT DEFAULT '',
                    source_name TEXT DEFAULT '',
                    source_index INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(vod_id, season_number, episode_number, source_index)
                );
                
                CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
                CREATE INDEX IF NOT EXISTS idx_tv_series_year ON tv_series(year);
                CREATE INDEX IF NOT EXISTS idx_tv_episodes_vod_id ON tv_episodes(vod_id);
            """)
    
    def parse_season_from_title(self, title):
        """从标题中解析季数
        
        Args:
            title: 剧集标题（如"乔治和曼迪的头婚生活第二季"）
        
        Returns:
            season_number: 季数（默认为1）
        """
        if not title:
            return 1
        
        # 中文格式：第X季
        season_match = re.search(r'第(\d+)季', title)
        if season_match:
            return int(season_match.group(1))
        
        # 英文格式：Season X
        season_match = re.search(r'[Ss]eason\s*(\d+)', title)
        if season_match:
            return int(season_match.group(1))
        
        # 简写格式：S1, S2...
        season_match = re.search(r'[Ss](\d+)\s*[Ee]\d+', title)
        if season_match:
            return int(season_match.group(1))
        
        return 1  # 默认第1季
    
    def parse_status(self, status_text):
        """解析状态文本，提取集数信息"""
        result = {'total_episodes': None, 'current_episode': None}
        
        if not status_text:
            return result
        
        # XX集全 / 全XX集
        full_match = re.search(r'(\d+)集全|全(\d+)集', status_text)
        if full_match:
            episodes = int(full_match.group(1) or full_match.group(2))
            result['total_episodes'] = episodes
            result['current_episode'] = episodes
            return result
        
        # 连载中 / 更新至XX集
        update_match = re.search(r'更新至[第]?(\d+)集', status_text)
        if update_match:
            result['current_episode'] = int(update_match.group(1))
        
        return result
    
    def parse_list_page(self, soup):
        """解析列表页"""
        tv_series = []
        
        for card in soup.select('li.hl-list-item'):
            try:
                link = card.select_one('a.hl-item-thumb')
                if not link:
                    continue
                
                href = link.get('href', '')
                detail_url = urljoin(self.base_url, href)
                vod_id = self.extract_vod_id(href)
                
                if not vod_id:
                    continue
                
                poster_url = link.get('data-original', '')
                title = link.get('title', '').strip()
                
                status_el = card.select_one('.hl-pic-tag span')
                status = status_el.text.strip() if status_el else ''
                
                tv_series.append({
                    'vod_id': vod_id,
                    'title': title,
                    'poster_url': poster_url,
                    'detail_url': detail_url,
                    'status': status,
                })
            except Exception as e:
                self.logger.error(f"解析卡片失败: {e}")
        
        has_next = bool(soup.select_one('.hl-page-wrap a[href*="/page/"]'))
        return tv_series, has_next
    
    def parse_detail_page(self, soup):
        """解析详情页"""
        data = {}
        
        # 标题
        title_el = soup.select_one('.hl-data-list li:contains("片名") span')
        if title_el:
            data['title'] = title_el.text.strip()
        
        # 评分
        score_el = soup.select_one('.hl-score-nums')
        if score_el:
            try:
                data['rating'] = float(score_el.text.strip())
            except:
                pass
        
        # 评分次数
        rating_count_el = soup.select_one('.hl-score-data')
        if rating_count_el:
            match = re.search(r'(\d+)次评分', rating_count_el.text)
            if match:
                data['rating_count'] = int(match.group(1))
        
        # 解析信息列表
        for li in soup.select('.hl-data-list li'):
            text = li.text.strip()
            
            if '主演：' in text:
                actors_links = li.select('a')
                data['actors'] = ','.join(a.text.strip() for a in actors_links)
            
            elif '导演：' in text:
                director_links = li.select('a')
                data['director'] = ','.join(a.text.strip() for a in director_links)
            
            elif '类型：' in text:
                category_links = li.select('a')
                if category_links:
                    data['category'] = category_links[0].text.strip()
                    data['genre'] = ','.join(a.text.strip() for a in category_links)
            
            elif '地区：' in text:
                data['region'] = text.replace('地区：', '').strip()
            
            elif '年份：' in text:
                try:
                    data['year'] = int(text.replace('年份：', '').strip())
                except:
                    data['year'] = 0
        
        # 海报图
        poster_el = soup.select_one('.hl-item-thumb')
        if poster_el:
            data['poster_url'] = poster_el.get('data-original', '')
        
        # 简介
        synopsis_el = soup.select_one('li.blurb')
        if synopsis_el:
            data['synopsis'] = synopsis_el.text.replace('简介：', '').strip()[:500]
        
        # 从标题中解析季数
        data['season_number'] = self.parse_season_from_title(data.get('title', ''))
        
        return data
    
    def parse_episodes(self, soup, vod_id, season_number=1):
        """解析剧集列表（支持多播放源）
        
        Args:
            soup: BeautifulSoup对象
            vod_id: 视频ID
            season_number: 季数（从标题解析得到）
        
        Returns:
            episodes: 剧集列表，包含季、集、播放源信息
        """
        episodes = []
        
        # 获取所有播放源
        source_tabs = soup.select('.hl-plays-from li')
        
        # 如果没有播放源标签，直接使用默认播放源
        if not source_tabs:
            source_tabs = [{'name': '云播', 'index': 1}]
        
        for source_idx, source_tab in enumerate(source_tabs, 1):
            # 获取播放源名称
            source_name_el = source_tab.select_one('span')
            source_name = source_name_el.text.strip() if source_name_el else f'播放源{source_idx}'
            
            # 获取播放源编号（从data-href中提取）
            data_href = source_tab.get('data-href', '')
            source_match = re.search(r'/play/\d+-(\d+)-\d+/', data_href)
            source_index = int(source_match.group(1)) if source_match else source_idx
            
            # 获取当前播放源的集数列表
            # 注意：美剧屋的集数列表是动态加载的，所有播放源共享同一个#hl-plays-list
            # 需要点击不同播放源来切换集数列表
            # 这里我们解析当前显示的集数列表
            playlist = soup.select('#hl-plays-list li a')
            
            for link in playlist:
                try:
                    href = link.get('href', '')
                    play_url = urljoin(self.base_url, href)
                    episode_title = link.text.strip()
                    
                    # 提取集数编号（支持"第01集"、"第1集"等格式）
                    episode_match = re.search(r'第(\d+)集', episode_title)
                    episode_number = int(episode_match.group(1)) if episode_match else 0
                    
                    # 从URL中提取source_index进行验证
                    url_match = re.search(r'/play/\d+-(\d+)-(\d+)/', href)
                    if url_match:
                        url_source_index = int(url_match.group(1))
                        url_episode = int(url_match.group(2))
                        # 如果URL中的episode与解析的一致，使用URL中的source_index
                        if url_episode == episode_number:
                            source_index = url_source_index
                    
                    episodes.append({
                        'vod_id': vod_id,
                        'season_number': season_number,  # 从标题解析的季数
                        'episode_number': episode_number,  # 从集数标题解析
                        'episode_title': episode_title,
                        'play_url': play_url,
                        'source_name': source_name,
                        'source_index': source_index,
                    })
                except Exception as e:
                    self.logger.error(f"解析剧集失败: {e}")
        
        return episodes
    
    def save_tv_series(self, conn, series):
        """保存电视剧主表"""
        conn.execute("""
            INSERT INTO tv_series (vod_id, title, original_title, category, genre, region, 
                                  year, language, director, actors, status, 
                                  total_episodes, current_episode, rating, rating_count,
                                  poster_url, detail_url, synopsis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(vod_id) DO UPDATE SET
                title=excluded.title, original_title=excluded.original_title,
                category=excluded.category, genre=excluded.genre,
                region=excluded.region, year=excluded.year,
                language=excluded.language, director=excluded.director,
                actors=excluded.actors, status=excluded.status,
                total_episodes=excluded.total_episodes, 
                current_episode=excluded.current_episode,
                rating=excluded.rating, rating_count=excluded.rating_count,
                poster_url=excluded.poster_url, synopsis=excluded.synopsis,
                updated_at=CURRENT_TIMESTAMP
        """, (
            series.get('vod_id'), series.get('title', ''),
            series.get('original_title', ''), series.get('category', ''),
            series.get('genre', ''), series.get('region', ''),
            series.get('year', 0), series.get('language', ''),
            series.get('director', ''), series.get('actors', ''),
            series.get('status', ''), series.get('total_episodes'),
            series.get('current_episode'), series.get('rating', 0.0),
            series.get('rating_count', 0), series.get('poster_url', ''),
            series.get('detail_url', ''), series.get('synopsis', '')
        ))
        conn.commit()
    
    def save_episodes(self, conn, episodes):
        """保存剧集"""
        for ep in episodes:
            conn.execute("""
                INSERT INTO tv_episodes (vod_id, season_number, episode_number, 
                                        episode_title, play_url, source_name, source_index)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(vod_id, season_number, episode_number, source_index) DO UPDATE SET
                    episode_title=excluded.episode_title,
                    play_url=excluded.play_url,
                    source_name=excluded.source_name,
                    updated_at=CURRENT_TIMESTAMP
            """, (
                ep['vod_id'], ep['season_number'], ep['episode_number'],
                ep['episode_title'], ep['play_url'], ep['source_name'], ep['source_index']
            ))
        conn.commit()
    
    def run(self, content_type='meiju', year_start=None, year_end=None, max_pages=None, max_episodes=None):
        """运行电视剧爬虫
        
        Args:
            content_type: 内容类型（默认meiju=美剧）
            year_start: 开始年份
            year_end: 结束年份
            max_pages: 每年份最大页数
            max_episodes: 每部剧最大集数限制
        """
        config = self.config['crawl']['tv']
        content_type = content_type or config.get('content_type', 'meiju')
        year_start = year_start or config.get('year_start', 1945)
        year_end = year_end or config.get('year_end', 2026)
        max_episodes = max_episodes or config.get('max_episodes')
        
        # 构建年份列表（倒序）
        years = list(range(year_end, year_start - 1, -1))
        
        total_series = 0
        total_episodes = 0
        
        for year in years:
            self.logger.info(f"\n{'='*60}\n开始爬取 {year} 年电视剧\n{'='*60}")
            
            page = 1
            year_series = 0
            
            while True:
                if max_pages and page > max_pages:
                    break
                
                url = self.build_list_url(content_type, page, year)
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
                                
                                # 获取季数（从标题解析）
                                season_number = series.get('season_number', 1)
                                
                                # 解析剧集（传入季数）
                                episodes = self.parse_episodes(detail_soup, series['vod_id'], season_number)
                                
                                # 限制集数
                                if max_episodes and len(episodes) > max_episodes:
                                    episodes = episodes[:max_episodes]
                                
                                # 保存剧集
                                if episodes:
                                    self.save_episodes(conn, episodes)
                                    total_episodes += len(episodes)
                                    series['total_episodes'] = len(episodes)
                            
                            # 保存电视剧主表
                            self.save_tv_series(conn, series)
                            total_series += 1
                            year_series += 1
                            
                            ep_info = f"({len(episodes)}集)" if series.get('total_episodes') else ""
                            self.logger.info(f"✅ [{total_series}] {series['title']} {ep_info} - {series.get('status', '')}")
                            
                        except Exception as e:
                            self.logger.error(f"❌ 处理失败: {series.get('title', 'Unknown')} - {e}")
                
                if not has_next:
                    break
                page += 1
            
            self.logger.info(f"{year}年共爬取 {year_series} 部电视剧")
        
        self.logger.info(f"\n🎉 电视剧爬取完成！共 {total_series} 部，{total_episodes} 集")
        return total_series, total_episodes
```

### 6.4 CSV导出器 (csv_exporter.py)

```python
#!/usr/bin/env python3
"""CSV导出器"""

import csv
import sqlite3
from pathlib import Path
from datetime import datetime

class CSVExporter:
    """CSV导出器"""
    
    def __init__(self, db_path='spider.db', output_dir='./data/exports'):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_movies(self, export_type='full'):
        """导出电影数据
        
        Args:
            export_type: 'full' 或 'incremental'
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"movies_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if export_type == 'incremental':
                # 获取上次导出时间
                cursor.execute("""
                    SELECT MAX(created_at) FROM export_logs 
                    WHERE table_name='movies' AND export_type='incremental'
                """)
                last_export = cursor.fetchone()[0]
                
                if last_export:
                    cursor.execute("""
                        SELECT * FROM movies 
                        WHERE created_at > ? OR updated_at > ?
                    """, (last_export, last_export))
                else:
                    cursor.execute("SELECT * FROM movies")
            else:
                cursor.execute("SELECT * FROM movies")
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            # 写入CSV
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
            
            # 记录导出日志
            conn.execute("""
                INSERT INTO export_logs (table_name, export_type, filepath, row_count)
                VALUES (?, ?, ?, ?)
            """, ('movies', export_type, str(filepath), len(rows)))
            conn.commit()
        
        print(f"✅ 电影数据已导出: {filepath} ({len(rows)} 条)")
        return filepath
    
    def export_tv_series(self, export_type='full'):
        """导出电视剧数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tv_series_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if export_type == 'incremental':
                cursor.execute("""
                    SELECT MAX(created_at) FROM export_logs 
                    WHERE table_name='tv_series' AND export_type='incremental'
                """)
                last_export = cursor.fetchone()[0]
                
                if last_export:
                    cursor.execute("""
                        SELECT * FROM tv_series 
                        WHERE created_at > ? OR updated_at > ?
                    """, (last_export, last_export))
                else:
                    cursor.execute("SELECT * FROM tv_series")
            else:
                cursor.execute("SELECT * FROM tv_series")
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
            
            conn.execute("""
                INSERT INTO export_logs (table_name, export_type, filepath, row_count)
                VALUES (?, ?, ?, ?)
            """, ('tv_series', export_type, str(filepath), len(rows)))
            conn.commit()
        
        print(f"✅ 电视剧数据已导出: {filepath} ({len(rows)} 条)")
        return filepath
    
    def export_tv_episodes(self, export_type='full'):
        """导出剧集数据"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tv_episodes_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if export_type == 'incremental':
                cursor.execute("""
                    SELECT MAX(created_at) FROM export_logs 
                    WHERE table_name='tv_episodes' AND export_type='incremental'
                """)
                last_export = cursor.fetchone()[0]
                
                if last_export:
                    cursor.execute("""
                        SELECT * FROM tv_episodes 
                        WHERE created_at > ?
                    """, (last_export,))
                else:
                    cursor.execute("SELECT * FROM tv_episodes")
            else:
                cursor.execute("SELECT * FROM tv_episodes")
            
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
                writer.writerows(rows)
            
            conn.execute("""
                INSERT INTO export_logs (table_name, export_type, filepath, row_count)
                VALUES (?, ?, ?, ?)
            """, ('tv_episodes', export_type, str(filepath), len(rows)))
            conn.commit()
        
        print(f"✅ 剧集数据已导出: {filepath} ({len(rows)} 条)")
        return filepath
    
    def export_all(self, export_type='full'):
        """导出所有数据"""
        print(f"\n{'='*60}")
        print(f"开始导出数据 (类型: {export_type})")
        print(f"{'='*60}\n")
        
        movie_file = self.export_movies(export_type)
        tv_series_file = self.export_tv_series(export_type)
        tv_episodes_file = self.export_tv_episodes(export_type)
        
        print(f"\n{'='*60}")
        print("导出完成!")
        print(f"{'='*60}")
        
        return {
            'movies': movie_file,
            'tv_series': tv_series_file,
            'tv_episodes': tv_episodes_file
        }
```

### 6.5 主程序入口 (main.py)

```python
#!/usr/bin/env python3
"""主程序入口"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from spiders.movie_spider import MovieSpider
from spiders.tv_spider import TVSpider
from exporters.csv_exporter import CSVExporter

def main():
    parser = argparse.ArgumentParser(description='美剧屋爬虫')
    parser.add_argument('--mode', choices=['movie', 'tv', 'all'], default='all',
                       help='爬取模式: movie=仅电影, tv=仅电视剧, all=全部')
    parser.add_argument('--year-start', type=int, default=1945,
                       help='开始年份 (默认: 1945)')
    parser.add_argument('--year-end', type=int, default=2026,
                       help='结束年份 (默认: 2026)')
    parser.add_argument('--max-pages', type=int, default=None,
                       help='每年份最大页数 (默认: 不限制)')
    parser.add_argument('--max-episodes', type=int, default=None,
                       help='每部剧最大集数限制 (默认: 不限制)')
    parser.add_argument('--export', choices=['full', 'incremental', 'none'], default='none',
                       help='导出数据: full=全量, incremental=增量, none=不导出')
    
    args = parser.parse_args()
    
    print("="*60)
    print("🎬 美剧屋 (mjwu.cc) 爬虫系统")
    print("="*60)
    print(f"模式: {args.mode}")
    print(f"年份范围: {args.year_start} - {args.year_end}")
    print(f"最大页数: {args.max_pages or '不限制'}")
    print(f"最大集数: {args.max_episodes or '不限制'}")
    print("="*60 + "\n")
    
    # 爬取电影
    if args.mode in ['movie', 'all']:
        print("\n" + "="*60)
        print("🎬 开始爬取电影")
        print("="*60 + "\n")
        
        movie_spider = MovieSpider()
        movie_count = movie_spider.run(
            content_type='dianying',
            year_start=args.year_start,
            year_end=args.year_end,
            max_pages=args.max_pages
        )
        
        print(f"\n✅ 电影爬取完成: {movie_count} 部")
    
    # 爬取电视剧
    if args.mode in ['tv', 'all']:
        print("\n" + "="*60)
        print("📺 开始爬取电视剧")
        print("="*60 + "\n")
        
        tv_spider = TVSpider()
        series_count, episodes_count = tv_spider.run(
            content_type='meiju',
            year_start=args.year_start,
            year_end=args.year_end,
            max_pages=args.max_pages,
            max_episodes=args.max_episodes
        )
        
        print(f"\n✅ 电视剧爬取完成: {series_count} 部, {episodes_count} 集")
    
    # 导出数据
    if args.export != 'none':
        print("\n" + "="*60)
        print("📊 开始导出数据")
        print("="*60 + "\n")
        
        exporter = CSVExporter()
        exporter.export_all(export_type=args.export)
    
    print("\n" + "="*60)
    print("🎉 所有任务完成!")
    print("="*60)

if __name__ == '__main__':
    main()
```

---

## 7. 季(Season)和集(Episode)爬取策略

### 7.1 季数提取策略

美剧屋网站的季数信息包含在剧集标题中，需要从标题中解析：

**解析规则**：
```python
def parse_season_from_title(title):
    """从标题中解析季数"""
    # 1. 中文格式：第X季
    #    "乔治和曼迪的头婚生活第二季" → season=2
    #    "紧急呼救第九季" → season=9
    
    # 2. 英文格式：Season X
    #    "The Witcher Season 3" → season=3
    
    # 3. 简写格式：S1E1, S2E5
    #    "Game of Thrones S1E1" → season=1
    
    # 4. 无季数信息 → 默认 season=1
```

**实际案例**：
| 标题 | 解析结果 |
|------|---------|
| 乔治和曼迪的头婚生活**第二季** | season=2 |
| 紧急呼救**第九季** | season=9 |
| 间谍之城**第一季** | season=1 |
| 寻踪者**第三季** | season=3 |
| 56天（无季数） | season=1 |

### 7.2 集数提取策略

集数信息从播放列表中解析：

**解析规则**：
```python
def parse_episode_from_text(text):
    """从集数标题中解析集数"""
    # "第01集" → episode=1
    # "第1集" → episode=1
    # "第10集" → episode=10
```

**实际案例**：
| 集数标题 | 解析结果 |
|---------|---------|
| 第01集 | episode=1 |
| 第02集 | episode=2 |
| 第11集 | episode=11 |

### 7.3 多播放源处理

美剧屋支持多个播放源，每个播放源可能有不同的集数列表：

**播放源结构**：
```
播放源1（云播）:
  - 第01集: /play/11571-1-1/
  - 第02集: /play/11571-1-2/
  ...

播放源2（备用线路）:
  - 第01集: /play/11571-2-1/
  - 第02集: /play/11571-2-2/
  ...
```

**数据库设计**：
- 使用 `(vod_id, season_number, episode_number, source_index)` 作为唯一键
- 同一集的多个播放源会生成多条记录

### 7.4 数据示例

**《乔治和曼迪的头婚生活第二季》(vod_id=11692)**：

| vod_id | season_number | episode_number | source_index | source_name | play_url |
|--------|---------------|----------------|--------------|-------------|----------|
| 11692 | 2 | 1 | 1 | 云播 | /play/11692-1-1/ |
| 11692 | 2 | 2 | 1 | 云播 | /play/11692-1-2/ |
| ... | ... | ... | ... | ... | ... |
| 11692 | 2 | 11 | 1 | 云播 | /play/11692-1-11/ |

---

## 8. 使用说明

### 7.1 安装依赖

```bash
pip install requests beautifulsoup4 lxml pyyaml
```

### 7.2 运行爬虫

```bash
# 爬取所有内容（电影+电视剧）
python main.py --mode all

# 仅爬取电影
python main.py --mode movie

# 仅爬取电视剧
python main.py --mode tv

# 指定年份范围
python main.py --mode all --year-start 2020 --year-end 2025

# 限制页数（用于测试）
python main.py --mode movie --max-pages 5

# 限制每部剧的集数
python main.py --mode tv --max-episodes 10

# 爬取并导出全量数据
python main.py --mode all --export full

# 爬取并导出增量数据
python main.py --mode all --export incremental
```

### 7.3 目录结构说明

```
mjwu_spider/
├── config/settings.yaml       # 配置文件
├── spider.db                  # SQLite数据库
├── data/
│   ├── exports/               # CSV导出文件
│   │   ├── movies_full_20260304_120000.csv
│   │   ├── tv_series_full_20260304_120000.csv
│   │   └── tv_episodes_full_20260304_120000.csv
│   └── logs/                  # 日志文件
│       └── spider.log
└── main.py                    # 主程序
```

---

## 9. 注意事项

### 8.1 反爬虫策略

1. **请求延迟**: 默认1-3秒随机延迟，避免请求过快
2. **User-Agent轮换**: 使用iPhone 17 (iOS 18) 和 PC Chrome UA轮换
3. **重试机制**: 失败时自动重试3次
4. **单线程**: 建议保持单线程爬取，避免被封

### 8.2 数据去重

- 使用 `vod_id` 作为主键进行去重
- 重复数据会自动更新（UPSERT机制）
- 更新时间戳会记录最后修改时间

### 8.3 断点续传

- 爬取进度保存在 `crawl_progress` 表
- 支持从上次中断处继续爬取
- 可按年份、分类分别记录进度

### 8.4 错误处理

- 网络错误自动重试
- 解析错误记录日志继续执行
- 404页面自动跳过

---

## 10. 数据字段说明

### 9.1 电影表 (movies)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 自增主键 |
| vod_id | INTEGER | 视频唯一ID |
| title | TEXT | 电影标题 |
| original_title | TEXT | 原标题（外文） |
| category | TEXT | 分类（电影） |
| genre | TEXT | 类型标签 |
| region | TEXT | 地区 |
| year | INTEGER | 年份 |
| language | TEXT | 语言 |
| director | TEXT | 导演 |
| actors | TEXT | 主演（逗号分隔） |
| status | TEXT | 状态（HD中字、正片等） |
| rating | REAL | 评分 |
| rating_count | INTEGER | 评分次数 |
| poster_url | TEXT | 海报图URL |
| detail_url | TEXT | 详情页URL |
| play_url | TEXT | 播放页URL |
| synopsis | TEXT | 简介 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 9.2 电视剧主表 (tv_series)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 自增主键 |
| vod_id | INTEGER | 视频唯一ID |
| title | TEXT | 剧名 |
| original_title | TEXT | 原标题 |
| category | TEXT | 分类（美剧、综艺等） |
| genre | TEXT | 类型标签 |
| region | TEXT | 地区 |
| year | INTEGER | 年份 |
| language | TEXT | 语言 |
| director | TEXT | 导演 |
| actors | TEXT | 主演 |
| status | TEXT | 状态（8集全、连载中等） |
| total_episodes | INTEGER | 总集数 |
| current_episode | INTEGER | 当前更新到的集数 |
| rating | REAL | 评分 |
| rating_count | INTEGER | 评分次数 |
| poster_url | TEXT | 海报图URL |
| detail_url | TEXT | 详情页URL |
| synopsis | TEXT | 简介 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 9.3 剧集表 (tv_episodes)

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 自增主键 |
| vod_id | INTEGER | 关联电视剧ID |
| season_number | INTEGER | **季数**（从标题解析：如"第二季"→2） |
| episode_number | INTEGER | **集数编号**（从播放列表解析：如"第01集"→1） |
| episode_title | TEXT | 集数标题（如"第01集"） |
| play_url | TEXT | 播放页URL |
| video_url | TEXT | 视频直链（可选） |
| source_name | TEXT | 播放源名称（如云播、备用线路） |
| source_index | INTEGER | 播放源编号（URL中的source参数） |
| created_at | TIMESTAMP | 创建时间 |

**季和集维度说明**：
- **季(Season)**: 从剧集标题中解析（如"乔治和曼迪的头婚生活**第二季**" → season=2）
- **集(Episode)**: 从播放列表中解析（如"第01集" → episode=1）
- **多播放源**: 同一季的集数可能在不同播放源中有不同的链接，通过source_index区分
- **示例数据结构**：
  ```
  vod_id=11692, season_number=2, episode_number=1, source_index=1, source_name="云播"
  vod_id=11692, season_number=2, episode_number=2, source_index=1, source_name="云播"
  ...
  vod_id=11692, season_number=2, episode_number=11, source_index=1, source_name="云播"
  ```

---

## 11. 更新日志

### v1.0 (2026-03-04)
- ✅ 初始版本发布
- ✅ 支持电影数据爬取（按年份、自动翻页、倒序优先）
- ✅ 支持电视剧数据爬取（提取所有季和集、支持数量限制）
- ✅ SQLite数据库存储（自动去重、增量更新）
- ✅ CSV数据导出（增量/全量、分表导出）
- ✅ 使用iPhone 17 (iOS 18) 和 PC Chrome UA轮换

---

**文档结束**

*本文档仅供技术学习参考，请遵守目标网站的robots.txt和相关法律法规。*
