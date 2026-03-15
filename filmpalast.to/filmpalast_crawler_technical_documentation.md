# Filmpalast.to 爬虫技术实现文档

**创建日期：** 2026-02-24
**文档版本：** 1.0
**作者：** LobsterAI

## 目录

1. [网站结构分析](#网站结构分析)
2. [核心功能设计](#核心功能设计)
3. [技术实现方案](#技术实现方案)
4. [数据库设计](#数据库设计)
5. [数据导出系统](#数据导出系统)
6. [部署与运行](#部署与运行)
7. [附录](#附录)

## 网站结构分析

### 基本特征

- **域名：** filmpalast.to
- **语言：** 德语（German）
- **类型：** 电影/电视剧流媒体网站
- **访问限制：** 德国地区可能面临DNS封锁，需要提供绕过方案

### URL 模式

| 页面类型 | URL 模式 | 示例 |
|---------|----------|------|
| 首页 | `https://filmpalast.to/` | 默认页面 |
| 分页列表 | `https://filmpalast.to/page/{page_number}` | `https://filmpalast.to/page/4` |
| 电影详情页 | `https://filmpalast.to/stream/{movie-slug}` | `https://filmpalast.to/stream/the-cabin-in-the-woods` |
| 电视剧详情页 | `https://filmpalast.to/stream/{series-slug}-s{season}e{episode}` | `https://filmpalast.to/stream/breaking-bad-s04e06` |
| 图片资源 | `/files/movies/{id}/{slug}.jpg` | `/files/movies/240/die-my-love.jpg` |

### 最大页数检测

- 当前最大页数：714（`/page/714`）
- 需要动态检测，可能随时间变化
- 首页为最新内容，倒序爬取从 page=1 开始

### 页面结构分析

#### 列表页结构（`/page/{n}`）
```html
<article class="liste rb pHome">
  <a href="/stream/{slug}" title="{title}">
    <img src="/files/movies/{id}/{slug}.jpg" alt="{title}" />
  </a>
  <div class="toggle-content nBox rb">
    <h2 class="h2-start">
      <a href="/stream/{slug}">{title}</a>
    </h2>
    <ul class="clearfix">
      <li>
        <!-- 评分星星 -->
        <div class="rStars">
          <img class="raStars" src="/images/star_on.png" /> <!-- 亮星 -->
          <img class="raStars" src="/images/star_off.png" /> <!-- 暗星 -->
        </div>
        Views:<strong>{views}</strong> / Votes:<strong>{votes}</strong> | Ø <strong>{rating}/10</strong>
      </li>
      <li>
        <span>Imdb: {imdb_rating}/10</span>
        <span class="releaseTitleHome coverDetails">
          Release: {release_title}
        </span>
      </li>
    </ul>
  </div>
</article>
```

#### 关键数据字段提取

1. **标题（Title）**：`<h2><a href="...">{title}</a></h2>`
2. **年份（Year）**：`Jahr: <b>{year}</b>` 或从 release_title 提取
3. **评分（Rating）**：
   - 星星数量（0-10颗）
   - IMDb 评分：`Imdb: {rating}/10`
   - 平均评分：`Ø {rating}/10`
4. **清晰度（Quality）**：从 release_title 提取（720p, 1080p, WEB-DL等）
5. **播放数据**：
   - Views: 观看次数
   - Votes: 投票次数
6. **Release标题**：完整发布信息，包含编码、分辨率等

## 核心功能设计

### 1. 电影数据爬取 🎬

#### 功能需求
- ✅ 按年份爬取（支持自定义年份范围）
- ✅ 年份范围：1945到2026及未来年份
- ✅ 倒序优先：从最新年份开始
- ✅ 自动翻页：爬取所有电影页面
- ✅ 数据提取：完整电影信息

#### 实现策略

```python
# 年份筛选逻辑
def filter_movies_by_year(movies, start_year, end_year):
    """按年份过滤电影列表"""
    filtered = []
    for movie in movies:
        year = extract_year(movie)
        if year and start_year <= year <= end_year:
            filtered.append(movie)
    return filtered

# 爬取流程
def crawl_movies(start_year=1945, end_year=2026, descending=True):
    """
    主爬取函数
    start_year: 起始年份
    end_year: 结束年份
    descending: 是否倒序（最新优先）
    """
    # 1. 获取最大页数
    max_page = detect_max_pages()

    # 2. 确定爬取顺序
    if descending:
        page_range = range(1, max_page + 1)  # 最新在前
    else:
        page_range = range(max_page, 0, -1)  # 最旧在前

    # 3. 逐页爬取
    for page in page_range:
        movies = extract_movies_from_page(page)

        # 4. 年份过滤
        filtered_movies = filter_movies_by_year(movies, start_year, end_year)

        # 5. 存储到数据库
        save_to_database(filtered_movies)

        # 6. 进度控制
        update_progress(page, max_page, len(filtered_movies))
```

#### 数据提取字段

| 字段名 | 描述 | 提取方法 |
|--------|------|----------|
| movie_title | 电影标题 | `<h2><a>` 标签内容 |
| url | 详情页URL | `href` 属性 |
| poster_url | 海报URL | `img` 标签的 `src` 属性 |
| year | 年份 | "Jahr: <b>" 标签或 release_title 提取 |
| rating | 评分（0-10） | 星星数量计算 |
| imdb_rating | IMDb评分 | "Imdb: " 文本提取 |
| quality | 清晰度 | release_title 中的分辨率信息 |
| release_title | 发布标题 | `.releaseTitleHome` 内容 |
| views | 观看次数 | "Views:" 后数字 |
| votes | 投票次数 | "Votes:" 后数字 |
| duration | 时长 | 如果有时长信息 |
| description | 描述 | 可能需要进入详情页获取 |

### 2. 电视剧数据爬取 📺

#### 功能需求
- ✅ 爬取所有电视剧列表
- ✅ 自动提取所有季和集
- ✅ 支持限制爬取数量
- ✅ 剧集信息完整提取

#### 剧集识别算法

```python
import re

def is_tv_episode_url(url):
    """检测URL是否为电视剧集"""
    episode_patterns = [
        r'-s\d+e\d+',           # 标准格式: -s01e08
        r'-\d+x\d+',            # 备用格式: -1x08
        r'-season-\d+-episode-\d+',  # 长格式
        r'-\d+\.\d+',           # 点格式: -1.08
        r'/season/\d+/episode/\d+'   # 路径格式
    ]

    for pattern in episode_patterns:
        if re.search(pattern, url):
            return True
    return False

def extract_season_episode(url):
    """从URL提取季和集信息"""
    patterns = [
        (r'-s(\d+)e(\d+)', 's01e08'),      # 标准格式
        (r'-(\d+)x(\d+)', '1x08'),         # 备用格式
        (r'-season-(\d+)-episode-(\d+)', 'season-1-episode-8'),  # 长格式
    ]

    for pattern, example in patterns:
        match = re.search(pattern, url)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            return season, episode

    return None, None

def extract_series_title(url):
    """从URL提取剧集系列标题"""
    # 移除季集信息
    series_slug = re.sub(r'-s\d+e\d+.*', '', url)
    series_slug = re.sub(r'-\d+x\d+.*', '', series_slug)
    series_slug = re.sub(r'-season-\d+.*', '', series_slug)

    # 转换为可读标题
    title = series_slug.replace('-', ' ').title()
    return title
```

#### 爬取策略

```python
def crawl_tv_episodes(limit=None, batch_size=100):
    """
    爬取电视剧集
    limit: 限制爬取数量（None表示无限制）
    batch_size: 批次大小
    """
    max_page = detect_max_pages()
    episodes_crawled = 0

    for page in range(1, max_page + 1):
        items = extract_items_from_page(page)

        for item in items:
            if not is_tv_episode_url(item['url']):
                continue  # 跳过非剧集

            # 提取剧集信息
            episode_info = extract_episode_info(item)

            # 存储到数据库
            save_episode_to_db(episode_info)

            episodes_crawled += 1

            # 检查数量限制
            if limit and episodes_crawled >= limit:
                return

        # 批量提交
        if episodes_crawled % batch_size == 0:
            commit_batch()
```

#### 数据提取字段

| 字段名 | 描述 | 提取方法 |
|--------|------|----------|
| series_title | 剧集系列标题 | URL解析或页面标题 |
| episode_title | 单集标题 | 页面标题 |
| original_title | 原标题 | release_title 提取 |
| url | 详情页URL | 完整URL |
| poster_url | 图片URL | 海报图片链接 |
| year | 年份 | 页面或release_title提取 |
| rating | 评分 | 同电影提取方法 |
| imdb_rating | IMDb评分 | 同电影提取方法 |
| quality | 清晰度 | release_title提取 |
| season | 季数 | URL模式匹配 |
| episode | 集数 | URL模式匹配 |
| release_title | 发布标题 | `.releaseTitleHome` 内容 |
| views | 观看次数 | "Views:" 后数字 |
| votes | 投票次数 | "Votes:" 后数字 |
| description | 描述 | 可能需要进入详情页获取 |

### 3. 数据库存储 💾

#### SQLite 数据库 Schema

```sql
-- 电影表
CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,              -- 电影标题
    original_title TEXT,              -- 原标题（如有）
    url TEXT UNIQUE NOT NULL,         -- 详情页URL（唯一索引）
    poster_url TEXT,                  -- 海报URL
    year INTEGER,                     -- 年份
    rating REAL,                      -- 评分（0-10）
    imdb_rating REAL,                 -- IMDb评分
    quality TEXT,                     -- 清晰度（720p, 1080p等）
    release_title TEXT,               -- Release标题
    views INTEGER DEFAULT 0,          -- 播放次数
    votes INTEGER DEFAULT 0,          -- 投票数
    duration TEXT,                    -- 时长（如 "119 Min."）
    description TEXT,                 -- 描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_crawled TIMESTAMP,           -- 最后爬取时间

    -- 索引优化
    INDEX idx_movies_year (year),
    INDEX idx_movies_rating (rating DESC),
    INDEX idx_movies_url (url)
);

-- 电视剧集表
CREATE TABLE tv_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    series_title TEXT NOT NULL,       -- 剧集系列标题
    episode_title TEXT NOT NULL,      -- 单集标题
    original_title TEXT,              -- 原标题
    url TEXT UNIQUE NOT NULL,         -- 详情页URL（唯一索引）
    poster_url TEXT,                  -- 图片URL
    year INTEGER,                     -- 年份
    rating REAL,                      -- 评分
    imdb_rating REAL,                 -- IMDb评分
    quality TEXT,                     -- 清晰度
    season INTEGER NOT NULL,          -- 季数
    episode INTEGER NOT NULL,         -- 集数
    release_title TEXT,               -- Release标题
    views INTEGER DEFAULT 0,          -- 播放次数
    votes INTEGER DEFAULT 0,          -- 投票数
    description TEXT,                 -- 描述
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_crawled TIMESTAMP,           -- 最后爬取时间

    -- 复合索引用于快速查询
    UNIQUE(series_title, season, episode),
    INDEX idx_tv_series_title (series_title),
    INDEX idx_tv_season_episode (season, episode),
    INDEX idx_tv_url (url)
);

-- 爬取状态表（用于增量更新）
CREATE TABLE crawl_status (
    id INTEGER PRIMARY KEY DEFAULT 1,
    last_page_crawled INTEGER DEFAULT 0,
    last_movie_id_crawled INTEGER,
    last_tv_id_crawled INTEGER,
    last_crawl_time TIMESTAMP,
    total_movies INTEGER DEFAULT 0,
    total_episodes INTEGER DEFAULT 0,
    last_full_crawl TIMESTAMP
);

-- 导出历史表
CREATE TABLE export_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    export_type TEXT NOT NULL,        -- 'movies' 或 'tv_episodes'
    export_mode TEXT NOT NULL,        -- 'full' 或 'incremental'
    file_path TEXT NOT NULL,
    record_count INTEGER DEFAULT 0,
    export_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_date DATE,                  -- 数据开始日期
    end_date DATE                     -- 数据结束日期
);
```

#### 数据库操作类

```python
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseManager:
    """数据库管理类"""

    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            # 创建表（如果不存在）
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS movies (...);
                CREATE TABLE IF NOT EXISTS tv_episodes (...);
                CREATE TABLE IF NOT EXISTS crawl_status (...);
                CREATE TABLE IF NOT EXISTS export_history (...);
            """)
            conn.commit()

    def save_movie(self, movie_data: Dict) -> bool:
        """保存电影数据（自动去重）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 检查是否已存在
                cursor = conn.execute(
                    "SELECT id FROM movies WHERE url = ?",
                    (movie_data['url'],)
                )

                if cursor.fetchone():
                    # 更新现有记录
                    conn.execute("""
                        UPDATE movies SET
                            title = ?, poster_url = ?, year = ?,
                            rating = ?, imdb_rating = ?, quality = ?,
                            release_title = ?, views = ?, votes = ?,
                            updated_at = CURRENT_TIMESTAMP,
                            last_crawled = CURRENT_TIMESTAMP
                        WHERE url = ?
                    """, (
                        movie_data['title'], movie_data['poster_url'],
                        movie_data['year'], movie_data['rating'],
                        movie_data['imdb_rating'], movie_data['quality'],
                        movie_data['release_title'], movie_data['views'],
                        movie_data['votes'], movie_data['url']
                    ))
                else:
                    # 插入新记录
                    conn.execute("""
                        INSERT INTO movies (...)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (
                        movie_data['title'], movie_data['original_title'],
                        movie_data['url'], movie_data['poster_url'],
                        movie_data['year'], movie_data['rating'],
                        movie_data['imdb_rating'], movie_data['quality'],
                        movie_data['release_title'], movie_data['views'],
                        movie_data['votes'], movie_data['duration'],
                        movie_data['description']
                    ))

                conn.commit()
                return True

        except sqlite3.Error as e:
            print(f"数据库错误: {e}")
            return False

    def get_last_crawl_status(self) -> Dict:
        """获取最后爬取状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM crawl_status WHERE id = 1"
            )
            row = cursor.fetchone()

            if row:
                return {
                    'last_page_crawled': row[1],
                    'last_movie_id_crawled': row[2],
                    'last_tv_id_crawled': row[3],
                    'last_crawl_time': row[4],
                    'total_movies': row[5],
                    'total_episodes': row[6],
                    'last_full_crawl': row[7]
                }
            return {}

    def update_crawl_status(self, status_data: Dict):
        """更新爬取状态"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO crawl_status
                (id, last_page_crawled, last_movie_id_crawled,
                 last_tv_id_crawled, last_crawl_time, total_movies,
                 total_episodes, last_full_crawl)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
            """, (
                status_data.get('last_page_crawled', 0),
                status_data.get('last_movie_id_crawled'),
                status_data.get('last_tv_id_crawled'),
                datetime.now(),
                status_data.get('total_movies', 0),
                status_data.get('total_episodes', 0),
                status_data.get('last_full_crawl')
            ))
            conn.commit()
```

### 4. 数据导出系统 📊

#### 导出功能设计

```python
import csv
import os
from datetime import datetime
from pathlib import Path

class DataExporter:
    """数据导出器"""

    def __init__(self, db_path: str, export_dir: str = "exports"):
        self.db_path = db_path
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def export_movies(self, mode: str = 'full', device: str = 'pc') -> str:
        """
        导出电影数据
        mode: 'full' 全量导出, 'incremental' 增量导出
        device: 'pc' 或 'iphone'（用于文件名标识）
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 确定文件名
        if mode == 'full':
            filename = f"movies_full_{timestamp}_{device}.csv"
        else:
            filename = f"movies_incremental_{timestamp}_{device}.csv"

        filepath = self.export_dir / "movies" / filename
        filepath.parent.mkdir(exist_ok=True)

        # 查询数据
        if mode == 'full':
            query = """
                SELECT id, title, url, poster_url, year, rating,
                       imdb_rating, quality, release_title, views,
                       votes, duration, created_at
                FROM movies
                ORDER BY year DESC, created_at DESC
            """
        else:
            # 增量导出：最近24小时的数据
            query = """
                SELECT id, title, url, poster_url, year, rating,
                       imdb_rating, quality, release_title, views,
                       votes, duration, created_at
                FROM movies
                WHERE last_crawled >= datetime('now', '-1 day')
                ORDER BY last_crawled DESC
            """

        # 写入CSV
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # 写入表头
                writer.writerow([
                    'id', 'title', 'url', 'poster_url', 'year', 'rating',
                    'imdb_rating', 'quality', 'release_title', 'views',
                    'votes', 'duration', 'created_at'
                ])

                # 写入数据
                writer.writerows(rows)

        # 记录导出历史
        self.record_export_history('movies', mode, str(filepath), len(rows))

        return str(filepath)

    def export_tv_episodes(self, mode: str = 'full', device: str = 'pc') -> str:
        """
        导出电视剧数据
        mode: 'full' 全量导出, 'incremental' 增量导出
        device: 'pc' 或 'iphone'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if mode == 'full':
            filename = f"tv_episodes_full_{timestamp}_{device}.csv"
        else:
            filename = f"tv_episodes_incremental_{timestamp}_{device}.csv"

        filepath = self.export_dir / "tv_episodes" / filename
        filepath.parent.mkdir(exist_ok=True)

        # 查询数据
        if mode == 'full':
            query = """
                SELECT id, series_title, episode_title, season, episode,
                       url, poster_url, year, rating, imdb_rating, quality,
                       release_title, views, votes, created_at
                FROM tv_episodes
                ORDER BY series_title, season, episode
            """
        else:
            query = """
                SELECT id, series_title, episode_title, season, episode,
                       url, poster_url, year, rating, imdb_rating, quality,
                       release_title, views, votes, created_at
                FROM tv_episodes
                WHERE last_crawled >= datetime('now', '-1 day')
                ORDER BY last_crawled DESC
            """

        # 写入CSV
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # 写入表头
                writer.writerow([
                    'id', 'series_title', 'episode_title', 'season', 'episode',
                    'url', 'poster_url', 'year', 'rating', 'imdb_rating',
                    'quality', 'release_title', 'views', 'votes', 'created_at'
                ])

                writer.writerows(rows)

        # 记录导出历史
        self.record_export_history('tv_episodes', mode, str(filepath), len(rows))

        return str(filepath)

    def record_export_history(self, export_type: str, export_mode: str,
                             file_path: str, record_count: int):
        """记录导出历史"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO export_history
                (export_type, export_mode, file_path, record_count, export_time)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (export_type, export_mode, file_path, record_count))
            conn.commit()
```

#### 目录结构设计

```
exports/
├── movies/
│   ├── full_export_20250224_120000_pc.csv
│   ├── full_export_20250224_120000_iphone.csv
│   ├── incremental_20250224_130000_pc.csv
│   ├── incremental_20250224_130000_iphone.csv
│   └── archive/           # 归档历史文件
│       ├── 2025-01/
│       └── 2025-02/
├── tv_episodes/
│   ├── full_export_20250224_120000_pc.csv
│   ├── full_export_20250224_120000_iphone.csv
│   ├── incremental_20250224_130000_pc.csv
│   ├── incremental_20250224_130000_iphone.csv
│   └── archive/
│       ├── 2025-01/
│       └── 2025-02/
└── logs/                  # 导出日志
    ├── export_20250224.log
    └── error_20250224.log
```

#### UA模拟配置

```python
# user_agents.py
USER_AGENTS = {
    'pc': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
    ],
    'iphone': [
        'Mozilla/5.0 (iPhone 17; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        'Mozilla/5.0 (iPhone 17; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1'
    ]
}

def get_user_agent(device='pc'):
    """获取随机User-Agent"""
    import random
    agents = USER_AGENTS.get(device, USER_AGENTS['pc'])
    return random.choice(agents)
```

## 技术实现方案

### 爬虫架构设计

```python
# crawler.py
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin

class FilmPalastCrawler:
    """Filmpalast.to 爬虫主类"""

    def __init__(self, config: Dict):
        self.base_url = "https://filmpalast.to"
        self.config = config
        self.session = requests.Session()
        self.db_manager = DatabaseManager(config['database']['path'])
        self.setup_session()

        # 日志配置
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/crawler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_session(self):
        """设置会话配置"""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # 设置代理（如果需要）
        if 'proxy' in self.config['crawler']:
            self.session.proxies = self.config['crawler']['proxy']

    def detect_max_pages(self) -> int:
        """检测最大页数"""
        try:
            # 尝试从页面导航中提取最大页数
            response = self.request_with_retry(f"{self.base_url}/page/1")
            soup = BeautifulSoup(response.text, 'lxml')

            # 查找分页链接
            page_links = soup.find_all('a', href=True)
            max_page = 1

            for link in page_links:
                href = link['href']
                if '/page/' in href:
                    try:
                        page_num = int(href.split('/page/')[1].split('/')[0])
                        max_page = max(max_page, page_num)
                    except (IndexError, ValueError):
                        continue

            # 如果没找到，尝试探测
            if max_page == 1:
                max_page = self.probe_max_pages()

            self.logger.info(f"检测到最大页数: {max_page}")
            return max_page

        except Exception as e:
            self.logger.error(f"检测最大页数失败: {e}")
            return self.config['crawler'].get('max_pages', 714)  # 默认值

    def probe_max_pages(self) -> int:
        """探测最大页数（二分查找）"""
        low, high = 1, 1000  # 初始范围

        while low <= high:
            mid = (low + high) // 2
            url = f"{self.base_url}/page/{mid}"

            response = self.request_with_retry(url, check_valid=True)

            if response.status_code == 200:
                # 页面有效，继续向右探测
                low = mid + 1
            else:
                # 页面无效，向左探测
                high = mid - 1

        return high

    def extract_movies_from_page(self, page: int) -> List[Dict]:
        """从页面提取电影数据"""
        url = f"{self.base_url}/page/{page}"
        self.logger.info(f"正在爬取页面: {url}")

        try:
            response = self.request_with_retry(url)
            soup = BeautifulSoup(response.text, 'lxml')

            movies = []
            articles = soup.find_all('article', class_='liste')

            for article in articles:
                movie_data = self.parse_movie_article(article)
                if movie_data:
                    movies.append(movie_data)

            # 随机延时，避免被封
            time.sleep(random.uniform(1.0, 3.0))

            self.logger.info(f"页面 {page} 提取到 {len(movies)} 个电影")
            return movies

        except Exception as e:
            self.logger.error(f"提取页面 {page} 数据失败: {e}")
            return []

    def parse_movie_article(self, article) -> Optional[Dict]:
        """解析单个电影文章块"""
        try:
            # 提取标题和URL
            title_elem = article.find('h2').find('a')
            title = title_elem.get_text(strip=True)
            url_path = title_elem['href']
            full_url = urljoin(self.base_url, url_path)

            # 提取图片
            img_elem = article.find('img')
            poster_url = urljoin(self.base_url, img_elem['src']) if img_elem else None

            # 提取评分信息
            rating_info = self.extract_rating_info(article)

            # 提取Release标题
            release_elem = article.find('span', class_='releaseTitleHome')
            release_title = release_elem.get_text(strip=True).replace('Release: ', '') if release_elem else ''

            # 提取年份（从release_title或页面）
            year = self.extract_year(release_title, article)

            # 提取质量信息
            quality = self.extract_quality(release_title)

            # 提取观看数据
            views, votes = self.extract_view_stats(article)

            movie_data = {
                'title': title,
                'url': full_url,
                'poster_url': poster_url,
                'year': year,
                'rating': rating_info.get('rating'),
                'imdb_rating': rating_info.get('imdb_rating'),
                'quality': quality,
                'release_title': release_title,
                'views': views,
                'votes': votes,
                'crawled_at': datetime.now()
            }

            return movie_data

        except Exception as e:
            self.logger.warning(f"解析电影文章失败: {e}")
            return None

    def extract_rating_info(self, article) -> Dict:
        """提取评分信息"""
        rating_info = {'rating': 0.0, 'imdb_rating': 0.0}

        try:
            # 提取星星评分
            stars = article.find_all('img', class_='raStars')
            if stars:
                on_stars = sum(1 for star in stars if 'star_on.png' in star.get('src', ''))
                rating_info['rating'] = on_stars  # 0-10分制

            # 提取IMDb评分
            text_content = article.get_text()
            import re
            imdb_match = re.search(r'Imdb:\s*([\d.]+)/10', text_content)
            if imdb_match:
                rating_info['imdb_rating'] = float(imdb_match.group(1))

        except Exception as e:
            self.logger.warning(f"提取评分信息失败: {e}")

        return rating_info

    def extract_year(self, release_title: str, article) -> Optional[int]:
        """提取年份信息"""
        try:
            # 先从release_title尝试
            import re
            year_match = re.search(r'\.(\d{4})\.', release_title)
            if year_match:
                return int(year_match.group(1))

            # 从页面文本尝试
            text_content = article.get_text()
            year_match = re.search(r'Jahr:\s*<b>(\d{4})</b>', text_content)
            if year_match:
                return int(year_match.group(1))

            # 其他模式
            patterns = [
                r'\b(19\d{2}|20\d{2})\b',
                r'\((\d{4})\)',
                r'\b\d{4}\b'
            ]

            for pattern in patterns:
                match = re.search(pattern, text_content)
                if match:
                    try:
                        year = int(match.group(1))
                        if 1900 <= year <= 2100:
                            return year
                    except (ValueError, IndexError):
                        continue

            return None

        except Exception as e:
            self.logger.warning(f"提取年份失败: {e}")
            return None

    def extract_quality(self, release_title: str) -> str:
        """提取清晰度信息"""
        quality_keywords = {
            '720p': ['720p', '720'],
            '1080p': ['1080p', '1080', 'fullhd', 'full.hd'],
            '2160p': ['2160p', '4k', 'uhd', 'ultra.hd'],
            '480p': ['480p', '480', 'sd'],
            'WEB-DL': ['web-dl', 'web.dl', 'webrip', 'web.rip'],
            'BluRay': ['bluray', 'blu-ray', 'bdrip', 'bd.rip'],
            'HDTV': ['hdtv', 'hd.tv']
        }

        release_lower = release_title.lower()

        for quality, keywords in quality_keywords.items():
            for keyword in keywords:
                if keyword in release_lower:
                    return quality

        return 'Unknown'

    def extract_view_stats(self, article) -> tuple:
        """提取观看和投票统计数据"""
        views, votes = 0, 0

        try:
            text_content = article.get_text()
            import re

            # 提取Views
            views_match = re.search(r'Views:\s*<strong>([\d,]+)</strong>', text_content)
            if views_match:
                views_str = views_match.group(1).replace(',', '')
                views = int(views_str)

            # 提取Votes
            votes_match = re.search(r'Votes:\s*<strong>([\d,]+)</strong>', text_content)
            if votes_match:
                votes_str = votes_match.group(1).replace(',', '')
                votes = int(votes_str)

        except Exception as e:
            self.logger.warning(f"提取统计数据失败: {e}")

        return views, votes

    def request_with_retry(self, url: str, max_retries: int = 3,
                          check_valid: bool = False) -> requests.Response:
        """带重试的请求函数"""
        for attempt in range(max_retries):
            try:
                # 随机延时
                if attempt > 0:
                    delay = random.uniform(2.0, 5.0) * attempt
                    time.sleep(delay)

                # 发送请求
                response = self.session.get(
                    url,
                    timeout=self.config['crawler'].get('timeout', 30),
                    headers={'User-Agent': get_user_agent(self.config.get('device', 'pc'))}
                )

                # 检查响应
                if check_valid and response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")

                return response

            except Exception as e:
                self.logger.warning(f"请求失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise

        # 如果所有重试都失败
        raise Exception(f"请求失败，URL: {url}")

    def crawl_movies_by_year_range(self, start_year: int = 1945,
                                   end_year: int = 2026) -> Dict:
        """
        按年份范围爬取电影
        返回爬取统计信息
        """
        self.logger.info(f"开始爬取电影，年份范围: {start_year}-{end_year}")

        stats = {
            'total_pages': 0,
            'total_movies': 0,
            'filtered_movies': 0,
            'start_time': datetime.now(),
            'end_time': None
        }

        try:
            # 获取最大页数
            max_page = self.detect_max_pages()
            stats['total_pages'] = max_page

            # 爬取所有页面
            for page in range(1, max_page + 1):
                movies = self.extract_movies_from_page(page)
                stats['total_movies'] += len(movies)

                # 按年份过滤
                filtered_movies = [
                    movie for movie in movies
                    if movie['year'] and start_year <= movie['year'] <= end_year
                ]
                stats['filtered_movies'] += len(filtered_movies)

                # 保存到数据库
                for movie in filtered_movies:
                    self.db_manager.save_movie(movie)

                # 更新进度
                self.logger.info(
                    f"进度: {page}/{max_page} | "
                    f"本页电影: {len(movies)} | "
                    f"符合年份: {len(filtered_movies)}"
                )

                # 检查是否应该停止（如果连续多页没有符合条件的数据）
                if self.should_stop_crawling(page, filtered_movies):
                    self.logger.info(f"提前停止爬取，在页面 {page}")
                    break

            # 更新爬取状态
            self.db_manager.update_crawl_status({
                'last_page_crawled': max_page,
                'total_movies': stats['filtered_movies'],
                'last_full_crawl': datetime.now()
            })

        except Exception as e:
            self.logger.error(f"爬取过程出错: {e}")

        stats['end_time'] = datetime.now()
        stats['duration'] = stats['end_time'] - stats['start_time']

        self.logger.info(f"爬取完成，统计: {stats}")
        return stats

    def should_stop_crawling(self, current_page: int,
                            filtered_movies: List) -> bool:
        """判断是否应该停止爬取"""
        # 如果连续5页没有找到符合年份条件的电影，停止爬取
        if current_page < 5:
            return False

        # 这里可以添加更复杂的停止逻辑
        # 例如：已经达到目标数量、时间限制等

        return False
```

### 配置文件示例

```yaml
# config.yaml
crawler:
  base_url: "https://filmpalast.to"
  max_pages: "auto"  # 自动检测或固定值
  request_delay: 1.5  # 请求间隔（秒）
  timeout: 30  # 请求超时（秒）
  retry_times: 3  # 重试次数
  max_concurrent: 5  # 最大并发数
  user_agent_rotation: true  # 是否轮换User-Agent

  # 代理配置（可选）
  proxy:
    http: "http://user:pass@proxy:port"
    https: "http://user:pass@proxy:port"

  # 设备模拟
  device: "pc"  # pc 或 iphone

database:
  path: "./data/database.db"
  backup_enabled: true
  backup_interval: 86400  # 备份间隔（秒）
  backup_count: 7  # 保留备份数量

export:
  directory: "./exports"
  keep_days: 30  # 保留天数
  archive_enabled: true
  compression: "zip"  # 归档压缩格式

  # CSV导出选项
  csv:
    encoding: "utf-8"
    delimiter: ","
    quotechar: '"'
    quoting: "minimal"

year_filter:
  start_year: 1945
  end_year: 2026
  descending: true  # 倒序优先
  stop_on_empty: true  # 连续空页时停止

tv_series:
  enabled: true
  limit: null  # null表示无限制
  batch_size: 100  # 批次大小
  episode_patterns:  # 剧集URL模式
    - "-s\\d+e\\d+"
    - "-\\d+x\\d+"
    - "-season-\\d+-episode-\\d+"

logging:
  level: "INFO"
  file: "./logs/crawler.log"
  max_size_mb: 100
  backup_count: 5

performance:
  memory_limit_mb: 1024
  batch_commit_size: 50
  cache_enabled: true
  cache_ttl: 3600  # 缓存有效期（秒）

monitoring:
  enabled: true
  progress_interval: 60  # 进度报告间隔（秒）
  health_check: true
  alert_threshold: 10  # 错误阈值
```

### 项目文件结构

```
filmpalast_crawler/
├── README.md                      # 项目说明
├── requirements.txt               # Python依赖
├── config/
│   ├── config.yaml               # 主配置文件
│   ├── user_agents.yaml          # User-Agent列表
│   └── proxy_list.yaml           # 代理列表（可选）
├── src/
│   ├── __init__.py
│   ├── crawler.py                # 主爬虫类
│   ├── database.py               # 数据库管理器
│   ├── parser.py                 # HTML解析器
│   ├── exporter.py               # 数据导出器
│   ├── utils.py                  # 工具函数
│   ├── config_loader.py          # 配置加载器
│   └── models.py                 # 数据模型
├── data/
│   ├── database.db               # SQLite数据库
│   ├── database_backup/          # 数据库备份
│   └── cache/                    # 爬取缓存
├── exports/
│   ├── movies/                   # 电影导出
│   │   ├── full/
│   │   ├── incremental/
│   │   └── archive/
│   ├── tv_episodes/              # 剧集导出
│   │   ├── full/
│   │   ├── incremental/
│   │   └── archive/
│   └── logs/                     # 导出日志
├── logs/
│   ├── crawler.log              # 爬虫日志
│   ├── error.log                # 错误日志
│   └── access.log               # 访问日志
├── tests/
│   ├── test_crawler.py          # 爬虫测试
│   ├── test_database.py         # 数据库测试
│   ├── test_parser.py           # 解析器测试
│   └── test_export.py           # 导出测试
├── scripts/
│   ├── run_crawler.py           # 运行脚本
│   ├── export_data.py           # 导出脚本
│   ├── cleanup.py               # 清理脚本
│   └── monitor.py               # 监控脚本
└── docs/
    ├── api.md                   # API文档
    ├── deployment.md            # 部署指南
    └── troubleshooting.md       # 故障排除
```

## 部署与运行

### 环境要求

```txt
# requirements.txt
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
sqlalchemy>=2.0.0
pandas>=2.0.0
python-dotenv>=1.0.0
PyYAML>=6.0
aiohttp>=3.9.0
aiofiles>=23.2.0
tqdm>=4.66.0
colorlog>=6.8.0
```

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/filmpalast-crawler.git
cd filmpalast-crawler

# 2. 创建虚拟环境
python -m venv venv

# 3. 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 配置项目
cp config/config.example.yaml config/config.yaml
# 编辑 config/config.yaml 文件

# 6. 初始化数据库
python scripts/init_database.py

# 7. 运行爬虫
python scripts/run_crawler.py
```

### 运行命令示例

```bash
# 基本爬取（电影，1945-2026）
python scripts/run_crawler.py --type movies --start-year 1945 --end-year 2026

# 电视剧爬取（限制100集）
python scripts/run_crawler.py --type tv --limit 100

# 增量更新
python scripts/run_crawler.py --type all --incremental

# 指定设备UA
python scripts/run_crawler.py --device iphone --type movies

# 导出数据
python scripts/export_data.py --type movies --mode full --device pc
python scripts/export_data.py --type tv --mode incremental --device iphone

# 查看状态
python scripts/monitor.py --status

# 清理旧数据
python scripts/cleanup.py --days 30 --type exports
```

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/exports /app/logs

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 运行入口
CMD ["python", "scripts/run_crawler.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  crawler:
    build: .
    container_name: filmpalast-crawler
    volumes:
      - ./data:/app/data
      - ./exports:/app/exports
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - TZ=Europe/Berlin
    restart: unless-stopped
    networks:
      - crawler-network

  scheduler:
    image: alpine:latest
    container_name: crawler-scheduler
    command: >
      sh -c "
      echo '0 2 * * * cd /app && python scripts/run_crawler.py --incremental' > /etc/crontabs/root &&
      echo '0 3 * * * cd /app && python scripts/export_data.py --incremental' >> /etc/crontabs/root &&
      crond -f
      "
    volumes:
      - .:/app
    restart: unless-stopped
    networks:
      - crawler-network

networks:
  crawler-network:
    driver: bridge
```

## 附录

### 反爬虫策略应对

#### 1. 请求频率控制
```python
class RateLimiter:
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.request_times = []

    def wait_if_needed(self):
        now = time.time()

        # 移除超过1分钟的请求记录
        self.request_times = [t for t in self.request_times
                             if now - t < 60]

        # 如果达到限制，等待
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.request_times.append(now)
```

#### 2. IP轮换策略
```python
class ProxyManager:
    def __init__(self, proxy_file='config/proxy_list.yaml'):
        self.proxies = self.load_proxies(proxy_file)
        self.current_index = 0

    def get_next_proxy(self):
        if not self.proxies:
            return None

        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)

        return {
            'http': f"http://{proxy['user']}:{proxy['pass']}@{proxy['host']}:{proxy['port']}",
            'https': f"http://{proxy['user']}:{proxy['pass']}@{proxy['host']}:{proxy['port']}"
        }
```

#### 3. 浏览器指纹模拟
```python
def generate_browser_fingerprint():
    """生成浏览器指纹"""
    return {
        'user_agent': get_user_agent(),
        'accept_language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'accept_encoding': 'gzip, deflate, br',
        'connection': 'keep-alive',
        'upgrade_insecure_requests': '1',
        'sec_fetch_dest': 'document',
        'sec_fetch_mode': 'navigate',
        'sec_fetch_site': 'none',
        'sec_fetch_user': '?1',
        'cache_control': 'max-age=0'
    }
```

### 错误处理与恢复

#### 1. 断点续爬
```python
class ResumeManager:
    def __init__(self, state_file='data/crawl_state.json'):
        self.state_file = state_file
        self.state = self.load_state()

    def load_state(self):
        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'last_page': 0,
                'last_movie_id': 0,
                'last_tv_id': 0,
                'start_time': None,
                'errors': []
            }

    def save_state(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def update_page(self, page):
        self.state['last_page'] = page
        self.save_state()
```

#### 2. 错误重试机制
```python
def retry_on_failure(max_retries=3, delay=2, backoff=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries - 1:
                        sleep_time = delay * (backoff ** attempt)
                        time.sleep(sleep_time)
                        continue

            raise last_exception

        return wrapper
    return decorator
```

### 性能优化建议

1. **数据库优化**
   - 使用连接池
   - 批量插入操作
   - 适当的索引策略

2. **内存优化**
   - 流式处理大数据
   - 及时释放资源
   - 使用生成器

3. **网络优化**
   - 连接复用
   - 请求压缩
   - 缓存策略

4. **并发控制**
   - 限制并发数量
   - 使用异步IO
   - 任务队列管理

### 监控与报警

```python
class Monitor:
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_failed': 0,
            'movies_crawled': 0,
            'episodes_crawled': 0,
            'start_time': datetime.now()
        }

    def record_request(self, success=True):
        self.metrics['requests_total'] += 1
        if success:
            self.metrics['requests_success'] += 1
        else:
            self.metrics['requests_failed'] += 1

    def get_report(self):
        duration = datetime.now() - self.metrics['start_time']

        return {
            'duration': str(duration),
            'requests_per_second': self.metrics['requests_total'] / duration.total_seconds(),
            'success_rate': self.metrics['requests_success'] / max(self.metrics['requests_total'], 1),
            'movies_crawled': self.metrics['movies_crawled'],
            'episodes_crawled': self.metrics['episodes_crawled']
        }
```

### 法律与合规声明

1. **数据使用限制**
   - 仅用于个人学习和研究
   - 不得用于商业用途
   - 遵守网站服务条款

2. **robots.txt 遵守**
   ```txt
   User-agent: *
   Disallow: /admin/
   Disallow: /private/
   # 其他规则...
   ```

3. **请求频率限制**
   - 尊重服务器负载
   - 避免影响正常用户访问
   - 遵守网站访问限制

4. **数据隐私**
   - 不收集用户个人信息
   - 不存储敏感数据
   - 遵守数据保护法规

### 更新与维护

#### 定期维护任务
1. **数据库维护**
   - 定期备份
   - 索引优化
   - 数据清理

2. **代码更新**
   - 依赖包更新
   - 安全补丁
   - 功能改进

3. **配置调整**
   - 根据网站变化调整解析规则
   - 优化爬取参数
   - 更新User-Agent列表

#### 版本管理
```txt
版本 1.0.0 (2026-02-24)
- 初始版本发布
- 支持电影按年份爬取
- 支持电视剧集识别
- SQLite数据库存储
- CSV数据导出

版本 1.1.0 (规划中)
- 异步爬取支持
- Redis缓存集成
- API服务接口
- 可视化监控面板
```

---

**文档结束**

*最后更新：2026年2月24日*
*维护者：LobsterAI*
*许可证：MIT License*