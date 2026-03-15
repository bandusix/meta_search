# TopFlix 爬虫系统技术实现文档

## 1. 项目概述
本项目旨在构建一个针对 `topflix.online` 的自动化爬虫系统，用于采集电影和电视剧的详细信息及播放源。系统需支持按年份筛选、自动翻页、增量更新、数据去重及导出功能，并模拟移动端设备（iPhone 17 / Android 16）进行访问以规避反爬策略。

## 2. 技术栈选型
*   **开发语言**: Python 3.10+
*   **网络请求**: `requests` (配合 `urllib3` 进行重试与超时控制)
*   **HTML 解析**: `BeautifulSoup4` (配合 `lxml` 解析器)
*   **数据存储**: `SQLite` (轻量级关系型数据库)
*   **数据处理**: `pandas` (用于生成 CSV 报表)
*   **配置管理**: `YAML` 或 `Env` 环境变量

## 3. 核心功能需求分析

### 3.1 电影数据采集 (Movies Crawler)
*   **入口 URL**: `https://topflix.online/filmes/page/{page}/`
*   **遍历策略**:
    *   **正序遍历**: 从第 1 页（最新内容）开始，向后遍历（页码从小到大：1, 2, 3...）。
    *   **年份筛选**: 采用 **"全量扫描 + 客户端过滤"** 策略。即爬取列表页所有条目，检查条目元数据中的年份，符合目标年份（如 2024）则进入详情页爬取，否则跳过。
    *   **停止条件**: 连续 3 次请求返回 404 或页面无内容列表时停止。
*   **数据提取**:
    *   列表页: 标题、年份、评分、海报 URL、详情页 URL。
    *   详情页: 清晰度（从描述文本提取）、播放器页面 URL。

### 3.2 电视剧数据采集 (TV Series Crawler)
*   **入口 URL**: `https://topflix.online/series/page/{page}/`
*   **遍历策略**: 同电影，支持数量限制（如只爬取前 100 部）。
*   **层级结构**: 剧集列表 -> 剧集详情 -> 季 (Season) -> 集 (Episode)。
*   **数据提取**:
    *   剧集信息: 标题、原标题（如有）、海报、年份、评分。
    *   分集信息: 季号、集号、分集标题、分集详情页 URL、播放器页面 URL。

### 3.3 数据存储与导出
*   **数据库设计**:
    *   表 `movies`: 存储电影元数据，以 `detail_url` 为唯一键进行去重。
    *   表 `tv_episodes`: 存储分集详情，包含外键关联所属剧集。
*   **增量更新**:
    *   入库前查询 `detail_url` 是否存在。若存在且无需强制刷新，则跳过；若不存在则插入。
*   **导出模块**:
    *   自动创建 `exports/{date}/` 目录。
    *   分别导出 `movies_{timestamp}.csv` 和 `tv_series_{timestamp}.csv`。

## 4. 详细实现方案

### 4.1 数据库设计 (Schema)

```sql
-- 电影表
CREATE TABLE IF NOT EXISTS movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    year INTEGER,
    rating REAL,
    quality TEXT, -- 清晰度
    poster_url TEXT,
    detail_url TEXT UNIQUE, -- 去重键
    player_url TEXT, -- 播放器页面URL
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 电视剧表（主表）
CREATE TABLE IF NOT EXISTS tv_shows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    original_title TEXT,
    year INTEGER,
    rating REAL,
    poster_url TEXT,
    detail_url TEXT UNIQUE,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 电视剧集表（分集）
CREATE TABLE IF NOT EXISTS tv_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    show_id INTEGER,
    season_number INTEGER,
    episode_number INTEGER,
    title TEXT,
    detail_url TEXT UNIQUE,
    player_url TEXT,
    crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(show_id) REFERENCES tv_shows(id)
);
```

### 4.2 核心代码实现参考 (Python Script Reference)

以下脚本展示了核心爬取逻辑的实现结构。

```python
import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
import time
import random
import os
from datetime import datetime

# --- 配置 ---
DB_NAME = "topflix.db"
BASE_URL = "https://topflix.online"
# 模拟移动端 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 16; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
]
TARGET_YEAR = None  # 设置为 2024 可只爬取该年份，None 为全部
MAX_RETRIES = 3

def get_random_header():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7"
    }

def fetch_url(url):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, headers=get_random_header(), timeout=10)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        retries += 1
        time.sleep(2)
    return None

def parse_movie_list(html):
    soup = BeautifulSoup(html, 'html.parser')
    items = []
    # 查找电影列表项
    for item in soup.select('.poster.grid-item'):
        try:
            title = item.select_one('.poster__title span').text.strip()
            link = item.select_one('.poster__title a')['href']
            year_tag = item.select_one('.bslide__meta span:first-child')
            year = int(year_tag.text.strip()) if year_tag and year_tag.text.strip().isdigit() else 0
            rating_tag = item.select_one('.rating.roundnum')
            rating = float(rating_tag.text.strip()) if rating_tag else 0.0
            img_tag = item.select_one('.poster__img img')
            poster = img_tag['src'] if img_tag else ""
            
            items.append({
                "title": title,
                "detail_url": link,
                "year": year,
                "rating": rating,
                "poster_url": poster
            })
        except Exception as e:
            print(f"Error parsing item: {e}")
    return items

def crawl_movies():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # (此处应包含建表 SQL)
    
    page = 1
    empty_pages_count = 0
    
    while True:
        print(f"Crawling Movies Page {page}...")
        url = f"{BASE_URL}/filmes/page/{page}/"
        html = fetch_url(url)
        
        if not html:
            print("Page not found or error.")
            empty_pages_count += 1
            if empty_pages_count >= 3:
                break
            page += 1
            continue
            
        movies = parse_movie_list(html)
        if not movies:
            empty_pages_count += 1
            if empty_pages_count >= 3:
                break
        else:
            empty_pages_count = 0
            
        for m in movies:
            # 年份过滤
            if TARGET_YEAR and m['year'] != TARGET_YEAR:
                continue
                
            # 去重检查
            cursor.execute("SELECT id FROM movies WHERE detail_url=?", (m['detail_url'],))
            if cursor.fetchone():
                print(f"Skipping existing: {m['title']}")
                continue
                
            # 爬取详情页获取更多信息 (如 quality, player_url)
            # detail_html = fetch_url(m['detail_url'])
            # ... 解析详情页逻辑 ...
            m['quality'] = "HD" # 示例默认
            m['player_url'] = m['detail_url'] # 默认详情页即播放页
            
            cursor.execute("""
                INSERT INTO movies (title, year, rating, quality, poster_url, detail_url, player_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (m['title'], m['year'], m['rating'], m['quality'], m['poster_url'], m['detail_url'], m['player_url']))
            conn.commit()
            print(f"Saved: {m['title']}")
            
        page += 1
        time.sleep(random.uniform(1, 3)) # 随机延时

def export_data():
    conn = sqlite3.connect(DB_NAME)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_dir = f"exports/{datetime.now().strftime('%Y-%m-%d')}"
    os.makedirs(export_dir, exist_ok=True)
    
    # 导出电影
    df_movies = pd.read_sql_query("SELECT * FROM movies", conn)
    df_movies.to_csv(f"{export_dir}/movies_{date_str}.csv", index=False)
    
    print(f"Exported to {export_dir}")

if __name__ == "__main__":
    # 初始化数据库表结构 (略)
    crawl_movies()
    # crawl_tv_series() # 类似逻辑
    export_data()
```

### 4.3 关键解析规则 (CSS Selectors)

*   **列表项**: `.poster.grid-item`
*   **标题**: `.poster__title span`
*   **年份**: `.bslide__meta span:first-child` 或 `.yearof` (详情页)
*   **评分**: `.rating.roundnum`
*   **海报**: `.poster__img img` (src 属性)
*   **季列表**: `.seasons-v2 .season-link`
*   **集列表**: `.seasoncontent-v2 .epi-link`
*   **集数/季数**: 通过统计上述列表长度获得。

### 4.4 防反爬与稳定性
1.  **User-Agent 轮询**: 准备 UA 池，每次请求随机切换（主要为 iOS/Android 移动端 UA）。
2.  **请求间隔**: 每次请求后随机休眠 `random.uniform(1.0, 3.0)` 秒。
3.  **异常处理**:
    *   捕获 `ConnectionError`, `Timeout`.
    *   404 处理：记录日志并跳过，若列表页 404 则作为结束信号。
    *   数据清洗：去除标题中的额外空白字符，处理图片 URL 的缩放参数（如去掉 `?w=...` 获取原图）。

## 5. 交付物清单
1.  `requirements.txt`: 依赖库列表 (requests, beautifulsoup4, pandas, lxml)。
2.  `spider_main.py`: 爬虫主程序入口。
3.  `db_manager.py`: 数据库操作封装。
4.  `exporters.py`: CSV 导出逻辑。
5.  `README.md`: 运行说明文档。
