# PeliCineHD 爬虫系统技术实现文档

## 文档信息

- **项目名称**：PeliCineHD 影视数据爬虫系统
- **目标网站**：https://pelicinehd.com
- **文档版本**：v1.0
- **创建日期**：2026-02-07
- **文档类型**：技术实现指南

---

## 目录

1. [项目概述](#1-项目概述)
2. [需求分析](#2-需求分析)
3. [网站结构分析](#3-网站结构分析)
4. [技术架构设计](#4-技术架构设计)
5. [数据库设计](#5-数据库设计)
6. [核心模块实现](#6-核心模块实现)
7. [代码实现示例](#7-代码实现示例)
8. [反爬虫策略](#8-反爬虫策略)
9. [性能优化方案](#9-性能优化方案)
10. [测试方案](#10-测试方案)
11. [部署指南](#11-部署指南)
12. [常见问题与解决方案](#12-常见问题与解决方案)

---

## 1. 项目概述

### 1.1 项目目标

开发一个功能完整的影视数据爬虫系统，用于从 PeliCineHD 网站爬取电影和电视剧数据，并存储到本地数据库中，支持数据导出和增量更新。

### 1.2 功能需求

#### 电影数据爬取 🎬
- ✅ 按年份爬取（1932-2026）
- ✅ 年份范围爬取，倒序优先（从最新年份开始）
- ✅ 自动翻页，爬取所有电影
- ✅ 提取：西语标题、原标题、年份、评分、清晰度、详情页URL

#### 电视剧数据爬取 📺
- ✅ 爬取所有电视剧列表
- ✅ 自动提取所有季(Season)和集(Episode)
- ✅ 支持限制爬取数量
- ✅ 提取：西语标题、原标题、年份、评分、清晰度、季数、集数、剧集URL

#### 数据管理 💾
- ✅ SQLite 数据库存储
- ✅ 两个独立表：movies（电影）、tv_episodes（电视剧）
- ✅ 自动去重（基于URL）
- ✅ 支持增量更新

#### 数据导出 📊
- ✅ 导出为 CSV 格式
- ✅ 分别导出电影和电视剧
- ✅ 自动创建导出目录
- ✅ 文件名包含时间戳

### 1.3 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.7+ | 主要开发语言 |
| requests | 2.31+ | HTTP 请求 |
| BeautifulSoup4 | 4.12+ | HTML 解析 |
| SQLite | 3.x | 数据存储 |
| pandas | 1.5+ | 数据处理和导出 |

---

## 2. 需求分析

### 2.1 数据字段需求

#### 电影数据字段

| 字段名 | 类型 | 必填 | 说明 | 来源 |
|--------|------|------|------|------|
| title_spanish | TEXT | ✅ | 西语标题 | 列表页 `.entry-title` |
| title_original | TEXT | ❌ | 原标题 | 详情页（可能不存在） |
| year | INTEGER | ✅ | 年份 | 列表页 `.year` |
| rating | REAL | ✅ | TMDB评分 | 列表页 `.vote` |
| quality | TEXT | ❌ | 清晰度 | 列表页 `.Qlty` |
| duration | TEXT | ❌ | 时长 | 详情页 `.duration` |
| url | TEXT | ✅ | 详情页URL | 列表页 `a.lnk-blk[href]` |
| poster_url | TEXT | ❌ | 海报URL | 列表页 `img[src]` |
| media_type | TEXT | ✅ | 固定为 "Movie" | 程序设定 |

#### 电视剧数据字段

| 字段名 | 类型 | 必填 | 说明 | 来源 |
|--------|------|------|------|------|
| series_title_spanish | TEXT | ✅ | 剧集西语标题 | 列表页 `.entry-title` |
| series_title_original | TEXT | ❌ | 剧集原标题 | 详情页（可能不存在） |
| year | INTEGER | ✅ | 年份 | 列表页 `.year` |
| rating | REAL | ✅ | TMDB评分 | 列表页 `.vote` |
| quality | TEXT | ❌ | 清晰度 | 详情页播放选项 |
| season | INTEGER | ✅ | 季数 | URL提取 |
| episode | INTEGER | ✅ | 集数 | URL提取 |
| episode_title | TEXT | ❌ | 单集标题 | 剧集页 `h1` |
| url | TEXT | ✅ | 剧集详情页URL | 详情页剧集链接 |
| series_url | TEXT | ✅ | 电视剧主页URL | 列表页 |
| poster_url | TEXT | ❌ | 海报URL | 列表页 |
| media_type | TEXT | ✅ | 固定为 "TV Series" | 程序设定 |

### 2.2 年份范围需求

**可用年份列表：**
```
1932, 1959, 1966, 1968, 1970, 1971, 1973, 1977, 1978, 1979,
1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
2020, 2021, 2022, 2023, 2024, 2025, 2026
```

**爬取顺序：** 倒序（2026 → 2025 → 2024 → ... → 1932）

---

## 3. 网站结构分析

### 3.1 URL 结构

#### 电影相关 URL

| 类型 | URL 格式 | 示例 |
|------|----------|------|
| 年份列表第1页 | `/release/{year}/` | `https://pelicinehd.com/release/2025/` |
| 年份列表分页 | `/release/{year}/page/{page}/` | `https://pelicinehd.com/release/2025/page/22/` |
| 电影详情 | `/movies/{slug}/` | `https://pelicinehd.com/movies/el-retorno/` |

#### 电视剧相关 URL

| 类型 | URL 格式 | 示例 |
|------|----------|------|
| 电视剧列表第1页 | `/series/` | `https://pelicinehd.com/series/` |
| 电视剧列表分页 | `/series/page/{page}/` | `https://pelicinehd.com/series/page/9/` |
| 电视剧详情 | `/series/{slug}/` | `https://pelicinehd.com/series/spartacus-house-of-ashur/` |
| 剧集详情 | `/episode/{slug}-{season}x{episode}/` | `https://pelicinehd.com/episode/spartacus-house-of-ashur-1x1/` |

### 3.2 HTML 结构分析

#### 电影/电视剧卡片结构

```html
<article class="post dfx fcl movies">
    <header class="entry-header">
        <h2 class="entry-title">El retorno</h2>
        <div class="entry-meta">
            <span class="vote"><span>TMDB</span> 0</span>
        </div>
    </header>
    <div class="post-thumbnail or-1">
        <figure>
            <img loading="lazy" src="//image.tmdb.org/t/p/w500/xxx.jpg" alt="Image El retorno">
        </figure>
        <span class="post-ql">
            <span class="Qlty">FHD 1080P</span>
        </span>
        <span class="year">2025</span>
        <span class="watch btn sm">Ver pelicula</span>  <!-- 电影 -->
        <!-- <span class="watch btn sm">Ver Serie</span> --> <!-- 电视剧 -->
    </div>
    <a href="https://pelicinehd.com/movies/el-retorno/" class="lnk-blk"></a>
</article>
```

**关键CSS选择器：**

| 数据 | CSS 选择器 | 备注 |
|------|-----------|------|
| 卡片容器 | `article.movies` | 电影和电视剧共用 |
| 标题 | `.entry-title` | - |
| 评分 | `.vote` | 格式: "TMDB 4.5" |
| 清晰度 | `.Qlty` | 可能为空 |
| 年份 | `.year` | - |
| 详情链接 | `a.lnk-blk[href]` | - |
| 海报 | `img[src]` | - |

#### 剧集链接结构

在电视剧详情页中：

```html
<a href="https://pelicinehd.com/episode/spartacus-house-of-ashur-1x1/"></a>
<a href="https://pelicinehd.com/episode/spartacus-house-of-ashur-1x2/"></a>
...
```

**提取季和集信息：**
- 正则表达式：`-(\d+)x(\d+)`
- 示例：`spartacus-house-of-ashur-1x1` → Season 1, Episode 1

### 3.3 分页机制

**分页链接示例：**
```html
<a href="/release/2025/page/1/">1</a>
<a href="/release/2025/page/2/">2</a>
...
<a href="/release/2025/page/22/">22</a>
<a href="/release/2025/page/23/">SIGUIENTE</a>
```

**分页检测逻辑：**
1. 查找包含 "SIGUIENTE" 的链接
2. 或查找 `a[href*="/page/"]` 并提取最大页码
3. 如果当前页没有电影卡片，说明已到最后一页

---

## 4. 技术架构设计

### 4.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     PeliCineHD 爬虫系统                      │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
   │ 电影爬虫 │          │电视剧爬虫│          │ 配置管理 │
   │ Module  │          │ Module  │          │ Module  │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                        ┌─────▼─────┐
                        │ 数据库管理 │
                        │  Module   │
                        └─────┬─────┘
                              │
                    ┌─────────┼─────────┐
                    │                   │
              ┌─────▼─────┐       ┌────▼────┐
              │  SQLite   │       │  CSV    │
              │  Database │       │ Export  │
              └───────────┘       └─────────┘
```

### 4.2 模块划分

#### 核心模块

| 模块名 | 文件名 | 功能描述 |
|--------|--------|----------|
| 数据库管理 | `database.py` | 数据库连接、表创建、数据插入、查询、导出 |
| 电影爬虫 | `movie_scraper.py` | 爬取电影列表和详情 |
| 电视剧爬虫 | `tv_scraper.py` | 爬取电视剧列表、详情和剧集 |
| 配置管理 | `config_manager.py` | 管理配置文件、路径设置 |
| 主程序 | `main.py` | 命令行接口、任务调度 |

#### 辅助模块

| 模块名 | 文件名 | 功能描述 |
|--------|--------|----------|
| 工具函数 | `utils.py` | 通用工具函数（延迟、User-Agent等） |
| 日志管理 | `logger.py` | 日志记录和输出 |

### 4.3 数据流向

```
1. 用户输入命令
   ↓
2. main.py 解析参数
   ↓
3. 调用相应的爬虫模块
   ↓
4. 爬虫模块发起HTTP请求
   ↓
5. 解析HTML，提取数据
   ↓
6. 调用 database.py 保存数据
   ↓
7. 数据存入 SQLite 数据库
   ↓
8. 可选：导出为 CSV 文件
```

---

## 5. 数据库设计

### 5.1 数据库选型

**选择 SQLite 的原因：**
- ✅ 轻量级，无需独立服务器
- ✅ 单文件存储，易于备份和迁移
- ✅ Python 内置支持
- ✅ 适合中小规模数据（预计 10万+ 条记录）
- ✅ 支持 SQL 查询和索引

### 5.2 表结构设计

#### 电影表 (movies)

```sql
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title_spanish TEXT NOT NULL,
    title_original TEXT,
    year INTEGER NOT NULL,
    rating REAL,
    quality TEXT,
    duration TEXT,
    url TEXT NOT NULL UNIQUE,
    poster_url TEXT,
    media_type TEXT DEFAULT 'Movie',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_movies_year ON movies(year);
CREATE INDEX idx_movies_rating ON movies(rating);
CREATE INDEX idx_movies_url ON movies(url);
```

**字段说明：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自动递增主键 |
| title_spanish | TEXT | NOT NULL | 西语标题 |
| title_original | TEXT | - | 原标题（可为空） |
| year | INTEGER | NOT NULL | 年份 |
| rating | REAL | - | TMDB评分 |
| quality | TEXT | - | 清晰度 |
| duration | TEXT | - | 时长 |
| url | TEXT | NOT NULL UNIQUE | 详情页URL（唯一索引） |
| poster_url | TEXT | - | 海报URL |
| media_type | TEXT | DEFAULT 'Movie' | 媒体类型 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 电视剧剧集表 (tv_episodes)

```sql
CREATE TABLE IF NOT EXISTS tv_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_title_spanish TEXT NOT NULL,
    series_title_original TEXT,
    year INTEGER NOT NULL,
    rating REAL,
    quality TEXT,
    season INTEGER NOT NULL,
    episode INTEGER NOT NULL,
    episode_title TEXT,
    url TEXT NOT NULL UNIQUE,
    series_url TEXT NOT NULL,
    poster_url TEXT,
    media_type TEXT DEFAULT 'TV Series',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tv_year ON tv_episodes(year);
CREATE INDEX idx_tv_rating ON tv_episodes(rating);
CREATE INDEX idx_tv_season_episode ON tv_episodes(season, episode);
CREATE INDEX idx_tv_series_url ON tv_episodes(series_url);
CREATE INDEX idx_tv_url ON tv_episodes(url);
```

**字段说明：**

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 自动递增主键 |
| series_title_spanish | TEXT | NOT NULL | 剧集西语标题 |
| series_title_original | TEXT | - | 剧集原标题（可为空） |
| year | INTEGER | NOT NULL | 年份 |
| rating | REAL | - | TMDB评分 |
| quality | TEXT | - | 清晰度 |
| season | INTEGER | NOT NULL | 季数 |
| episode | INTEGER | NOT NULL | 集数 |
| episode_title | TEXT | - | 单集标题 |
| url | TEXT | NOT NULL UNIQUE | 剧集详情页URL（唯一索引） |
| series_url | TEXT | NOT NULL | 电视剧主页URL |
| poster_url | TEXT | - | 海报URL |
| media_type | TEXT | DEFAULT 'TV Series' | 媒体类型 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

### 5.3 索引设计

**索引目的：**
- 提高查询性能
- 加速数据去重
- 优化按年份、评分排序

**创建的索引：**

| 表 | 索引名 | 字段 | 用途 |
|-----|--------|------|------|
| movies | idx_movies_year | year | 按年份查询 |
| movies | idx_movies_rating | rating | 按评分排序 |
| movies | idx_movies_url | url | 数据去重 |
| tv_episodes | idx_tv_year | year | 按年份查询 |
| tv_episodes | idx_tv_rating | rating | 按评分排序 |
| tv_episodes | idx_tv_season_episode | season, episode | 按季集查询 |
| tv_episodes | idx_tv_series_url | series_url | 按剧集分组 |
| tv_episodes | idx_tv_url | url | 数据去重 |

---

## 6. 核心模块实现

### 6.1 数据库管理模块 (database.py)

**功能：**
- 数据库连接管理
- 表创建和初始化
- 数据插入（支持去重）
- 数据查询和统计
- CSV 导出

**关键方法：**

```python
class Database:
    def __init__(self, db_path='pelicinehd.db')
    def create_tables()
    def insert_movie(movie_data)
    def insert_tv_episode(episode_data)
    def get_movie_count()
    def get_tv_episode_count()
    def export_movies_to_csv(output_path)
    def export_tv_episodes_to_csv(output_path)
    def get_statistics()
```

### 6.2 电影爬虫模块 (movie_scraper.py)

**功能：**
- 爬取指定年份的电影列表
- 自动处理分页
- 提取电影元数据
- 可选：爬取详情页获取更多信息

**关键方法：**

```python
class MovieScraper:
    def __init__(self, db, delay_min=1, delay_max=3)
    def scrape_year(year, max_pages=None)
    def scrape_year_range(start_year, end_year, reverse=True)
    def _fetch_movie_list_page(url)
    def _extract_movies_from_page(soup)
    def _extract_movie_detail(url)  # 可选
    def _parse_rating(rating_text)
```

### 6.3 电视剧爬虫模块 (tv_scraper.py)

**功能：**
- 爬取电视剧列表
- 自动处理分页
- 提取电视剧元数据
- 爬取所有剧集链接
- 从URL提取季和集信息

**关键方法：**

```python
class TVSeriesScraper:
    def __init__(self, db, delay_min=1, delay_max=3)
    def scrape_series(max_series=None, max_pages=None)
    def _fetch_series_list_page(url)
    def _extract_series_from_page(soup)
    def _scrape_series_episodes(series_url, series_data)
    def _extract_season_episode_from_url(url)
```

### 6.4 配置管理模块 (config_manager.py)

**功能：**
- 读取和保存配置文件
- 管理数据库路径
- 管理导出目录
- 管理延迟时间等参数

**配置文件格式 (config.json)：**

```json
{
    "database": {
        "path": "./pelicinehd.db"
    },
    "export": {
        "directory": "./exports"
    },
    "scraper": {
        "delay_min": 1,
        "delay_max": 3,
        "user_agent_rotation": true
    }
}
```

### 6.5 主程序模块 (main.py)

**功能：**
- 命令行参数解析
- 任务调度
- 进度显示
- 错误处理

**命令行接口：**

```bash
# 爬取电影
python main.py movie --year 2025
python main.py movie --year-range 2020 2025

# 爬取电视剧
python main.py tv --max-series 50 --max-pages 5

# 导出数据
python main.py export --type movies
python main.py export --type tv

# 查看统计
python main.py stats

# 更新所有数据
python main.py update
```

---

## 7. 代码实现示例

### 7.1 数据库管理模块示例

```python
import sqlite3
import pandas as pd
from datetime import datetime

class Database:
    def __init__(self, db_path='pelicinehd.db'):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
    
    def create_tables(self):
        """创建数据表"""
        cursor = self.conn.cursor()
        
        # 创建电影表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_spanish TEXT NOT NULL,
                title_original TEXT,
                year INTEGER NOT NULL,
                rating REAL,
                quality TEXT,
                duration TEXT,
                url TEXT NOT NULL UNIQUE,
                poster_url TEXT,
                media_type TEXT DEFAULT 'Movie',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建电视剧表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tv_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                series_title_spanish TEXT NOT NULL,
                series_title_original TEXT,
                year INTEGER NOT NULL,
                rating REAL,
                quality TEXT,
                season INTEGER NOT NULL,
                episode INTEGER NOT NULL,
                episode_title TEXT,
                url TEXT NOT NULL UNIQUE,
                series_url TEXT NOT NULL,
                poster_url TEXT,
                media_type TEXT DEFAULT 'TV Series',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_url ON movies(url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_year ON tv_episodes(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_url ON tv_episodes(url)')
        
        self.conn.commit()
    
    def insert_movie(self, movie_data):
        """插入电影数据"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO movies 
                (title_spanish, title_original, year, rating, quality, duration, url, poster_url, media_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                movie_data.get('title_spanish'),
                movie_data.get('title_original'),
                movie_data.get('year'),
                movie_data.get('rating'),
                movie_data.get('quality'),
                movie_data.get('duration'),
                movie_data.get('url'),
                movie_data.get('poster_url'),
                'Movie'
            ))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"插入电影数据失败: {e}")
            return False
    
    def insert_tv_episode(self, episode_data):
        """插入电视剧剧集数据"""
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO tv_episodes 
                (series_title_spanish, series_title_original, year, rating, quality, 
                 season, episode, episode_title, url, series_url, poster_url, media_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                episode_data.get('series_title_spanish'),
                episode_data.get('series_title_original'),
                episode_data.get('year'),
                episode_data.get('rating'),
                episode_data.get('quality'),
                episode_data.get('season'),
                episode_data.get('episode'),
                episode_data.get('episode_title'),
                episode_data.get('url'),
                episode_data.get('series_url'),
                episode_data.get('poster_url'),
                'TV Series'
            ))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"插入电视剧数据失败: {e}")
            return False
    
    def export_movies_to_csv(self, output_path):
        """导出电影数据到CSV"""
        query = "SELECT * FROM movies ORDER BY year DESC, rating DESC"
        df = pd.read_sql_query(query, self.conn)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return len(df)
    
    def export_tv_episodes_to_csv(self, output_path):
        """导出电视剧数据到CSV"""
        query = "SELECT * FROM tv_episodes ORDER BY year DESC, season, episode"
        df = pd.read_sql_query(query, self.conn)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return len(df)
    
    def get_statistics(self):
        """获取统计信息"""
        cursor = self.conn.cursor()
        
        # 电影统计
        cursor.execute("SELECT COUNT(*) FROM movies")
        movie_count = cursor.fetchone()[0]
        
        # 电视剧统计
        cursor.execute("SELECT COUNT(*) FROM tv_episodes")
        tv_count = cursor.fetchone()[0]
        
        # 按年份统计电影
        cursor.execute('''
            SELECT year, COUNT(*) as count 
            FROM movies 
            GROUP BY year 
            ORDER BY year DESC 
            LIMIT 10
        ''')
        movies_by_year = cursor.fetchall()
        
        return {
            'movie_count': movie_count,
            'tv_episode_count': tv_count,
            'movies_by_year': movies_by_year
        }
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
```

### 7.2 电影爬虫模块示例

```python
import requests
from bs4 import BeautifulSoup
import time
import random
import re

class MovieScraper:
    # 可用年份列表
    AVAILABLE_YEARS = [
        1932, 1959, 1966, 1968, 1970, 1971, 1973, 1977, 1978, 1979,
        1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
        1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
        2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
        2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
        2020, 2021, 2022, 2023, 2024, 2025, 2026
    ]
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    ]
    
    def __init__(self, db, delay_min=1, delay_max=3):
        self.db = db
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
    
    def _get_headers(self):
        """获取随机 User-Agent"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }
    
    def _delay(self):
        """随机延迟"""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def scrape_year(self, year, max_pages=None):
        """爬取指定年份的电影"""
        if year not in self.AVAILABLE_YEARS:
            print(f"⚠️  警告：年份 {year} 不在可用年份列表中")
            return 0
        
        print(f"\n{'='*60}")
        print(f"📅 开始爬取 {year} 年的电影...")
        print(f"{'='*60}\n")
        
        page = 1
        total_movies = 0
        
        while True:
            if max_pages and page > max_pages:
                print(f"✅ 已达到最大页数限制 ({max_pages} 页)")
                break
            
            # 构建URL
            if page == 1:
                url = f"https://pelicinehd.com/release/{year}/"
            else:
                url = f"https://pelicinehd.com/release/{year}/page/{page}/"
            
            print(f"📄 正在爬取第 {page} 页: {url}")
            
            # 获取页面
            soup = self._fetch_page(url)
            if not soup:
                print(f"❌ 第 {page} 页获取失败")
                break
            
            # 提取电影
            movies = self._extract_movies_from_page(soup)
            
            if not movies:
                print(f"✅ 第 {page} 页没有更多电影，结束爬取")
                break
            
            print(f"   找到 {len(movies)} 部电影")
            
            # 保存到数据库
            saved_count = 0
            for movie in movies:
                if self.db.insert_movie(movie):
                    saved_count += 1
            
            print(f"   保存 {saved_count} 部新电影")
            total_movies += saved_count
            
            # 检查是否有下一页
            next_page = soup.select_one('a:contains("SIGUIENTE")')
            if not next_page:
                print(f"✅ 没有更多页面，结束爬取")
                break
            
            page += 1
            self._delay()
        
        print(f"\n✨ {year} 年电影爬取完成！共 {total_movies} 部电影\n")
        return total_movies
    
    def scrape_year_range(self, start_year, end_year, reverse=True):
        """爬取年份范围的电影"""
        # 过滤出可用年份
        years = [y for y in self.AVAILABLE_YEARS if start_year <= y <= end_year]
        
        if reverse:
            years = sorted(years, reverse=True)
        else:
            years = sorted(years)
        
        print(f"\n{'#'*60}")
        print(f"# 开始爬取 {start_year}-{end_year} 年的电影")
        print(f"# 共 {len(years)} 个年份")
        print(f"# 爬取顺序: {years[0]} → {years[-1]}")
        print(f"{'#'*60}\n")
        
        total_movies = 0
        for year in years:
            count = self.scrape_year(year)
            total_movies += count
        
        print(f"\n{'='*60}")
        print(f"🎉 所有年份爬取完成！")
        print(f"📊 总计: {total_movies} 部电影")
        print(f"{'='*60}\n")
        
        return total_movies
    
    def _fetch_page(self, url):
        """获取页面内容"""
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'  # 关键！设置编码
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
            return None
    
    def _extract_movies_from_page(self, soup):
        """从页面提取电影数据"""
        movies = []
        movie_cards = soup.select('article.movies')
        
        for card in movie_cards:
            try:
                # 提取标题
                title_elem = card.select_one('.entry-title')
                if not title_elem:
                    continue
                title_spanish = title_elem.text.strip()
                
                # 提取评分
                rating_elem = card.select_one('.vote')
                rating = self._parse_rating(rating_elem.text.strip() if rating_elem else None)
                
                # 提取清晰度
                quality_elem = card.select_one('.Qlty')
                quality = quality_elem.text.strip() if quality_elem else None
                
                # 提取年份
                year_elem = card.select_one('.year')
                year = int(year_elem.text.strip()) if year_elem else None
                
                # 提取URL
                link_elem = card.select_one('a.lnk-blk')
                if not link_elem:
                    continue
                url = link_elem.get('href')
                
                # 检查是否为电影（不是电视剧）
                if '/movies/' not in url:
                    continue
                
                # 提取海报
                img_elem = card.select_one('img')
                poster_url = img_elem.get('src') if img_elem else None
                if poster_url and poster_url.startswith('//'):
                    poster_url = 'https:' + poster_url
                
                movie = {
                    'title_spanish': title_spanish,
                    'title_original': None,  # 需要从详情页获取
                    'year': year,
                    'rating': rating,
                    'quality': quality,
                    'duration': None,  # 需要从详情页获取
                    'url': url,
                    'poster_url': poster_url
                }
                
                movies.append(movie)
                
            except Exception as e:
                print(f"   ⚠️  提取电影数据失败: {e}")
                continue
        
        return movies
    
    def _parse_rating(self, rating_text):
        """解析评分"""
        if not rating_text:
            return None
        
        # 格式: "TMDB 4.5" 或 "4.5TMDB"
        match = re.search(r'(\d+\.?\d*)', rating_text)
        if match:
            return float(match.group(1))
        return None
```

### 7.3 电视剧爬虫模块示例

```python
import requests
from bs4 import BeautifulSoup
import time
import random
import re

class TVSeriesScraper:
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    def __init__(self, db, delay_min=1, delay_max=3):
        self.db = db
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
    
    def _get_headers(self):
        """获取随机 User-Agent"""
        return {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
    
    def _delay(self):
        """随机延迟"""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def scrape_series(self, max_series=None, max_pages=None):
        """爬取电视剧"""
        print(f"\n{'='*60}")
        print(f"📺 开始爬取电视剧列表...")
        print(f"{'='*60}\n")
        
        page = 1
        total_series = 0
        total_episodes = 0
        
        while True:
            if max_pages and page > max_pages:
                print(f"✅ 已达到最大页数限制 ({max_pages} 页)")
                break
            
            # 构建URL
            if page == 1:
                url = "https://pelicinehd.com/series/"
            else:
                url = f"https://pelicinehd.com/series/page/{page}/"
            
            print(f"📄 正在爬取电视剧列表第 {page} 页: {url}")
            
            # 获取页面
            soup = self._fetch_page(url)
            if not soup:
                print(f"❌ 第 {page} 页获取失败")
                break
            
            # 提取电视剧
            series_list = self._extract_series_from_page(soup)
            
            if not series_list:
                print(f"✅ 第 {page} 页没有更多电视剧，结束爬取")
                break
            
            print(f"   找到 {len(series_list)} 部电视剧")
            
            # 爬取每部电视剧的剧集
            for idx, series_data in enumerate(series_list, 1):
                if max_series and total_series >= max_series:
                    print(f"✅ 已达到最大电视剧数量限制 ({max_series} 部)")
                    break
                
                print(f"\n   [{idx}/{len(series_list)}] 正在爬取: {series_data['title_spanish']}")
                episode_count = self._scrape_series_episodes(series_data)
                total_episodes += episode_count
                total_series += 1
                
                self._delay()
            
            if max_series and total_series >= max_series:
                break
            
            # 检查是否有下一页
            next_page = soup.select_one('a:contains("SIGUIENTE")')
            if not next_page:
                print(f"✅ 没有更多页面，结束爬取")
                break
            
            page += 1
            self._delay()
        
        print(f"\n{'='*60}")
        print(f"🎉 所有电视剧爬取完成！")
        print(f"📊 总计: {total_series} 部电视剧, {total_episodes} 个剧集")
        print(f"{'='*60}\n")
        
        return total_episodes
    
    def _fetch_page(self, url):
        """获取页面内容"""
        try:
            response = self.session.get(url, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'  # 关键！
            return BeautifulSoup(response.text, 'html.parser')
        except requests.RequestException as e:
            print(f"   ❌ 请求失败: {e}")
            return None
    
    def _extract_series_from_page(self, soup):
        """从页面提取电视剧数据"""
        series_list = []
        series_cards = soup.select('article.movies')
        
        for card in series_cards:
            try:
                # 提取URL
                link_elem = card.select_one('a.lnk-blk')
                if not link_elem:
                    continue
                url = link_elem.get('href')
                
                # 检查是否为电视剧（不是电影）
                if '/series/' not in url:
                    continue
                
                # 提取标题
                title_elem = card.select_one('.entry-title')
                if not title_elem:
                    continue
                title_spanish = title_elem.text.strip()
                
                # 提取评分
                rating_elem = card.select_one('.vote')
                rating = self._parse_rating(rating_elem.text.strip() if rating_elem else None)
                
                # 提取年份
                year_elem = card.select_one('.year')
                year = int(year_elem.text.strip()) if year_elem else None
                
                # 提取海报
                img_elem = card.select_one('img')
                poster_url = img_elem.get('src') if img_elem else None
                if poster_url and poster_url.startswith('//'):
                    poster_url = 'https:' + poster_url
                
                series_data = {
                    'title_spanish': title_spanish,
                    'title_original': None,
                    'year': year,
                    'rating': rating,
                    'url': url,
                    'poster_url': poster_url
                }
                
                series_list.append(series_data)
                
            except Exception as e:
                print(f"   ⚠️  提取电视剧数据失败: {e}")
                continue
        
        return series_list
    
    def _scrape_series_episodes(self, series_data):
        """爬取电视剧的所有剧集"""
        url = series_data['url']
        
        # 获取电视剧详情页
        soup = self._fetch_page(url)
        if not soup:
            return 0
        
        # 提取所有剧集链接
        episode_links = soup.select('a[href*="/episode/"]')
        
        if not episode_links:
            print(f"      ⚠️  未找到剧集链接")
            return 0
        
        print(f"      找到 {len(episode_links)} 个剧集")
        
        saved_count = 0
        for link in episode_links:
            episode_url = link.get('href')
            if not episode_url:
                continue
            
            # 从URL提取季和集信息
            season, episode = self._extract_season_episode_from_url(episode_url)
            if season is None or episode is None:
                continue
            
            episode_data = {
                'series_title_spanish': series_data['title_spanish'],
                'series_title_original': series_data.get('title_original'),
                'year': series_data['year'],
                'rating': series_data['rating'],
                'quality': None,
                'season': season,
                'episode': episode,
                'episode_title': f"{series_data['title_spanish']} {season}x{episode}",
                'url': episode_url,
                'series_url': series_data['url'],
                'poster_url': series_data.get('poster_url')
            }
            
            if self.db.insert_tv_episode(episode_data):
                saved_count += 1
        
        print(f"      保存 {saved_count} 个新剧集")
        return saved_count
    
    def _extract_season_episode_from_url(self, url):
        """从URL提取季和集信息"""
        # 格式: /episode/spartacus-house-of-ashur-1x1/
        match = re.search(r'-(\d+)x(\d+)', url)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return season, episode
        return None, None
    
    def _parse_rating(self, rating_text):
        """解析评分"""
        if not rating_text:
            return None
        match = re.search(r'(\d+\.?\d*)', rating_text)
        if match:
            return float(match.group(1))
        return None
```

---

## 8. 反爬虫策略

### 8.1 User-Agent 轮换

**目的：** 模拟不同浏览器和设备的访问

**实现：**
```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36...'
]

headers = {'User-Agent': random.choice(USER_AGENTS)}
```

### 8.2 随机延迟

**目的：** 避免请求过于频繁，模拟人类行为

**实现：**
```python
import time
import random

def delay(min_seconds=1, max_seconds=3):
    time.sleep(random.uniform(min_seconds, max_seconds))
```

**建议延迟时间：**
- 列表页之间：1-3秒
- 详情页之间：2-4秒
- 出错重试：5-10秒

### 8.3 会话保持

**目的：** 保持 Cookie 和连接状态

**实现：**
```python
import requests

session = requests.Session()
response = session.get(url, headers=headers)
```

### 8.4 请求头完善

**目的：** 使请求更像真实浏览器

**实现：**
```python
headers = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

### 8.5 错误处理和重试

**目的：** 应对网络波动和临时错误

**实现：**
```python
def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"尝试 {attempt + 1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))  # 递增延迟
            else:
                return None
```

### 8.6 IP 代理（可选）

**目的：** 避免 IP 被封禁

**实现：**
```python
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'https://proxy.example.com:8080'
}

response = requests.get(url, headers=headers, proxies=proxies)
```

---

## 9. 性能优化方案

### 9.1 并发爬取

**方案1：使用 ThreadPoolExecutor**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def scrape_years_concurrent(years, max_workers=3):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(scrape_year, year): year for year in years}
        
        for future in as_completed(futures):
            year = futures[future]
            try:
                count = future.result()
                print(f"年份 {year} 完成，共 {count} 部电影")
            except Exception as e:
                print(f"年份 {year} 失败: {e}")
```

**注意：**
- 控制并发数量（建议 3-5）
- 每个线程使用独立的 Session
- 避免共享状态导致的竞争条件

### 9.2 数据库批量插入

**优化前：**
```python
for movie in movies:
    db.insert_movie(movie)
```

**优化后：**
```python
def insert_movies_batch(self, movies):
    cursor = self.conn.cursor()
    cursor.executemany('''
        INSERT OR IGNORE INTO movies 
        (title_spanish, year, rating, quality, url, poster_url, media_type)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [(m['title_spanish'], m['year'], m['rating'], m['quality'], 
           m['url'], m['poster_url'], 'Movie') for m in movies])
    self.conn.commit()
    return cursor.rowcount
```

### 9.3 缓存机制

**方案：使用 Redis 或本地文件缓存**

```python
import hashlib
import json
import os

class PageCache:
    def __init__(self, cache_dir='./cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get(self, url):
        """获取缓存"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def set(self, url, data):
        """设置缓存"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
```

### 9.4 增量更新

**策略：**
1. 记录上次爬取时间
2. 只爬取新增或更新的内容
3. 使用 URL 去重

**实现：**
```python
def is_url_exists(self, url):
    """检查 URL 是否已存在"""
    cursor = self.conn.cursor()
    cursor.execute("SELECT 1 FROM movies WHERE url = ? LIMIT 1", (url,))
    return cursor.fetchone() is not None

# 在爬虫中使用
if db.is_url_exists(movie['url']):
    print(f"   ⏭️  跳过已存在的电影: {movie['title_spanish']}")
    continue
```

---

## 10. 测试方案

### 10.1 单元测试

**测试数据库模块：**

```python
import unittest

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(':memory:')  # 使用内存数据库
    
    def test_insert_movie(self):
        movie = {
            'title_spanish': 'Test Movie',
            'year': 2025,
            'rating': 7.5,
            'quality': 'HD',
            'url': 'https://example.com/test'
        }
        result = self.db.insert_movie(movie)
        self.assertTrue(result)
    
    def test_duplicate_url(self):
        movie = {
            'title_spanish': 'Test Movie',
            'year': 2025,
            'url': 'https://example.com/test'
        }
        self.db.insert_movie(movie)
        result = self.db.insert_movie(movie)  # 重复插入
        self.assertFalse(result)
    
    def tearDown(self):
        self.db.close()
```

### 10.2 集成测试

**测试爬虫模块：**

```python
def test_movie_scraper():
    db = Database('test.db')
    scraper = MovieScraper(db)
    
    # 测试爬取单个年份（限制1页）
    count = scraper.scrape_year(2025, max_pages=1)
    assert count > 0, "应该爬取到电影"
    
    # 验证数据库
    stats = db.get_statistics()
    assert stats['movie_count'] > 0, "数据库应该有电影数据"
    
    db.close()
```

### 10.3 性能测试

**测试爬取速度：**

```python
import time

def test_performance():
    db = Database('test.db')
    scraper = MovieScraper(db, delay_min=0.5, delay_max=1)
    
    start_time = time.time()
    count = scraper.scrape_year(2025, max_pages=5)
    elapsed_time = time.time() - start_time
    
    print(f"爬取 {count} 部电影，耗时 {elapsed_time:.2f} 秒")
    print(f"平均速度: {count / elapsed_time:.2f} 部/秒")
    
    db.close()
```

---

## 11. 部署指南

### 11.1 环境准备

**系统要求：**
- Python 3.7+
- 2GB+ RAM
- 1GB+ 磁盘空间

**安装依赖：**

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

**requirements.txt：**
```
requests>=2.31.0
beautifulsoup4>=4.12.0
pandas>=1.5.0
lxml>=4.9.0
```

### 11.2 配置文件

**创建 config.json：**

```json
{
    "database": {
        "path": "./data/pelicinehd.db"
    },
    "export": {
        "directory": "./exports"
    },
    "scraper": {
        "delay_min": 1,
        "delay_max": 3,
        "max_retries": 3,
        "timeout": 30
    },
    "logging": {
        "level": "INFO",
        "file": "./logs/scraper.log"
    }
}
```

### 11.3 目录结构

```
pelicinehd_scraper/
├── main.py
├── database.py
├── movie_scraper.py
├── tv_scraper.py
├── config_manager.py
├── utils.py
├── requirements.txt
├── config.json
├── README.md
├── data/
│   └── pelicinehd.db
├── exports/
│   ├── movies_2026-02-07.csv
│   └── tv_episodes_2026-02-07.csv
└── logs/
    └── scraper.log
```

### 11.4 运行方式

**命令行运行：**

```bash
# 爬取2025年电影
python main.py movie --year 2025

# 爬取2020-2025年电影（倒序）
python main.py movie --year-range 2020 2025

# 爬取50部电视剧
python main.py tv --max-series 50

# 导出数据
python main.py export --type movies
python main.py export --type tv

# 查看统计
python main.py stats
```

**定时任务（Linux）：**

```bash
# 编辑 crontab
crontab -e

# 每天凌晨2点更新数据
0 2 * * * cd /path/to/pelicinehd_scraper && /path/to/venv/bin/python main.py update >> /path/to/logs/cron.log 2>&1
```

**定时任务（Windows）：**

创建 `update_task.bat`：
```batch
@echo off
cd /d X:\path\to\pelicinehd_scraper
call venv\Scripts\activate
python main.py update
pause
```

使用 Windows 任务计划程序设置定时执行。

---

## 12. 常见问题与解决方案

### 12.1 编码问题

**问题：** 出现乱码或 "Some characters could not be decoded" 错误

**解决方案：**
```python
response = requests.get(url)
response.encoding = 'utf-8'  # 关键！必须设置
soup = BeautifulSoup(response.text, 'html.parser')
```

### 12.2 找不到数据

**问题：** 爬虫运行但找不到电影/电视剧

**可能原因：**
1. 网站HTML结构变化
2. CSS选择器错误
3. 编码问题导致解析失败

**解决方案：**
1. 检查网页源代码，确认HTML结构
2. 使用浏览器开发者工具测试CSS选择器
3. 确保设置了正确的编码

### 12.3 请求被拒绝

**问题：** 403 Forbidden 或 429 Too Many Requests

**解决方案：**
1. 增加延迟时间
2. 更换 User-Agent
3. 使用代理IP
4. 降低并发数量

### 12.4 数据库锁定

**问题：** SQLite database is locked

**解决方案：**
1. 避免多进程同时写入
2. 使用事务批量提交
3. 增加超时时间：`sqlite3.connect(db_path, timeout=30)`

### 12.5 内存占用过高

**问题：** 爬取大量数据时内存不足

**解决方案：**
1. 使用批量插入代替单条插入
2. 及时关闭数据库连接
3. 清理不需要的变量
4. 分批处理数据

---

## 附录

### A. 完整的年份列表

```python
AVAILABLE_YEARS = [
    1932, 1959, 1966, 1968, 1970, 1971, 1973, 1977, 1978, 1979,
    1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
    2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
    2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
    2020, 2021, 2022, 2023, 2024, 2025, 2026
]
```

### B. CSS 选择器速查表

| 数据 | CSS 选择器 | 位置 |
|------|-----------|------|
| 电影/电视剧卡片 | `article.movies` | 列表页 |
| 标题 | `.entry-title` | 列表页/详情页 |
| 评分 | `.vote` | 列表页/详情页 |
| 清晰度 | `.Qlty` | 列表页 |
| 年份 | `.year` | 列表页/详情页 |
| 详情链接 | `a.lnk-blk[href]` | 列表页 |
| 海报 | `img[src]` | 列表页/详情页 |
| 剧集链接 | `a[href*="/episode/"]` | 电视剧详情页 |
| 下一页 | `a:contains("SIGUIENTE")` | 列表页 |

### C. 正则表达式速查表

| 用途 | 正则表达式 | 示例 |
|------|-----------|------|
| 提取评分 | `(\d+\.?\d*)` | "TMDB 4.5" → 4.5 |
| 提取季集信息 | `-(\d+)x(\d+)` | "spartacus-1x1" → (1, 1) |
| 检查电影URL | `/movies/` | 判断是否为电影 |
| 检查电视剧URL | `/series/` | 判断是否为电视剧 |
| 检查剧集URL | `/episode/` | 判断是否为剧集 |

### D. 参考资源

- [Requests 文档](https://requests.readthedocs.io/)
- [BeautifulSoup 文档](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [SQLite 文档](https://www.sqlite.org/docs.html)
- [Pandas 文档](https://pandas.pydata.org/docs/)

---

## 总结

本技术文档详细描述了 PeliCineHD 爬虫系统的完整实现方案，包括：

1. ✅ **需求分析**：明确了电影和电视剧数据的爬取需求
2. ✅ **网站结构分析**：详细分析了HTML结构和URL模式
3. ✅ **技术架构设计**：设计了模块化的系统架构
4. ✅ **数据库设计**：设计了两个独立的数据表
5. ✅ **核心模块实现**：提供了完整的代码示例
6. ✅ **反爬虫策略**：实现了多种反爬虫措施
7. ✅ **性能优化方案**：提供了并发、缓存等优化方案
8. ✅ **测试方案**：包含单元测试和集成测试
9. ✅ **部署指南**：提供了完整的部署步骤
10. ✅ **常见问题**：列出了常见问题和解决方案

**关键技术点：**
- ✅ 编码处理：`response.encoding = 'utf-8'`
- ✅ CSS 选择器：`article.movies`
- ✅ URL 模式识别：`/movies/` vs `/series/`
- ✅ 正则表达式：提取季集信息
- ✅ 数据去重：使用 URL 作为唯一标识
- ✅ 反爬虫：User-Agent 轮换 + 随机延迟

**实现难度：⭐⭐ (简单)**

PeliCineHD 的HTML结构规范，爬取难度较低，适合作为爬虫学习项目。

---

**文档版本：** v1.0  
**最后更新：** 2026-02-07  
**作者：** Manus AI Agent  
**状态：** ✅ 已完成，可直接实施
