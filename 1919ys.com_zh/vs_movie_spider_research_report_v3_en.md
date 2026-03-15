# VS影院 (1919ys.com) 爬虫技术调研报告 V3 (宽表架构版)

## 核心架构变更说明

为了优化搜索引擎的查询效率，本方案采用了**“以播放单元为核心”的统一宽表设计**。

*   **旧架构**：按照影视类型分表（电影/电视剧/综艺等），且剧集信息与集数信息分离（规范化设计）。
*   **新架构（当前）**：所有类型的资源统一存储在单张 `media_resources` 表中。每一行代表一个**独立的可播放资源**（如：一部电影、电视剧的一集、综艺的一期）。
*   **优势**：搜索引擎可以直接索引单表，实现“搜剧名 -> 直达播放列表”或“搜单集 -> 直接播放”，无需复杂的连表查询。

---

## 调研概述

| 项目 | 内容 |
|------|------|
| 目标网站 | https://www.1919ys.com |
| 反爬等级 | 中等 (需User-Agent + gzip解压 + SSL验证绕过) |
| 页面类型 | 纯静态HTML，无JS动态渲染 |
| 架构模式 | **单表宽表模式 (Flat Table)** |
| 并发策略 | 多线程 (ThreadPoolExecutor)，支持 5-100 线程 |

### 全站内容统计 (参考)

| 分类 | 类型ID | 说明 |
|------|--------|------|
| 电影 | 1 | 存储为单行记录 (episode_name="Full Movie") |
| 电视剧 | 2 | 存储为多行记录 (每集一行) |
| 综艺 | 3 | 存储为多行记录 (每期一行) |
| 动漫 | 4 | 存储为多行记录 (每集一行) |
| 短剧 | 34 | 存储为多行记录 (每集一行) |

---

## 数据库设计方案

### 核心表：`media_resources`

所有数据均存储于此表，不再区分影视类型表。

```sql
CREATE TABLE media_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,          -- 分类: movie, tv_series, variety_show, anime, short_drama
    title TEXT NOT NULL,             -- 剧集/电影名称 (核心搜索字段)
    episode_name TEXT NOT NULL,      -- 集数/副标题 (如: "第01集 [量子源]", "Full Movie")
    play_url TEXT UNIQUE NOT NULL,   -- 【播放详情页URL】(唯一索引)
    detail_url TEXT,                 -- 来源详情页URL
    poster_url TEXT,                 -- 海报URL
    year INTEGER,                    -- 年份
    quality TEXT,                    -- 清晰度 (HD中字/正片等)
    genre TEXT,                      -- 类型 (剧情片/动作片等)
    region TEXT,                     -- 地区
    director TEXT,                   -- 导演
    actors TEXT,                     -- 主演
    status TEXT,                     -- 状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引设计 (优化搜索)
CREATE UNIQUE INDEX idx_play_url ON media_resources(play_url);  -- 核心去重
CREATE INDEX idx_title ON media_resources(title);               -- 标题搜索
CREATE INDEX idx_category ON media_resources(category);         -- 分类过滤
CREATE INDEX idx_year ON media_resources(year);                 -- 年份过滤
```

---

## 爬虫实现细节

### 1. 核心类设计 (`spider.py`)

采用了 `ThreadPoolExecutor` 实现多线程爬取，并使用 `threading.Lock` 保证数据库写入安全。

```python
class VS1919Spider:
    # ... (常量定义)
    
    def __init__(self, max_workers=10):
        # 初始化 Session
        self.session = requests.Session()
        self.session.verify = False  # 关键：关闭SSL验证以解决证书错误
        # ...
        self.max_workers = max_workers
        self.db_lock = threading.Lock() # 数据库写入锁

    def crawl_category(self, category_id, max_items=20):
        """多线程爬取指定分类"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 1. 获取列表页
            # ...
            # 2. 提交详情页任务到线程池
            future = executor.submit(self._fetch_detail_data, ...)
            # ...
            # 3. 获取结果并写入数据库 (加锁)
            with self.db_lock:
                self._save_data(category_id, data)
```

### 2. 数据扁平化处理

在 `_save_data` 方法中，将抓取到的结构化数据（Series Info + Episodes List）“拍平”存入数据库。

```python
def _save_data(self, category_id, data):
    info = data['info']         # 剧集元数据 (标题, 海报, 导演等)
    episodes = data['episodes'] # 播放列表 [{'episode_title': '...', 'play_url': '...'}, ...]
    
    # ...
    
    for ep in episodes:
        # 每一集都插入一行，重复存储剧集元数据 (空间换时间)
        cursor.execute('''
            INSERT OR IGNORE INTO media_resources (
                category, title, episode_name, play_url, ...
            ) VALUES (?, ?, ?, ?, ...)
        ''', (
            category_name,
            info['title'],
            ep['episode_title'], # 集数
            ep['play_url'],      # 播放链接 (唯一键)
            # ... 下面是重复的元数据 ...
            info['poster_url'],
            info['director'],
            # ...
        ))
```

### 3. 播放链接提取逻辑

**核心原则**：只存储包含 `/vsbspy/` 的链接，确保是真实的播放详情页，过滤掉广告或无效链接。

```python
def _extract_episode_play_urls(self, soup):
    # ...
    for ep_link in episode_links:
        # 过滤非播放页链接
        if '/vsbspy/' not in play_url:
            continue
            
        # 拼接完整URL
        if not play_url.startswith('http'):
            play_url = urljoin(self.BASE_URL, play_url)
            
        # 为了区分不同源，将源名称拼接到集数标题中 (可选优化)
        # e.g. "第01集 [量子源]"
        full_title = f"{episode_title} [{source_name}]"
        
        episodes.append({
            'episode_title': full_title,
            'play_url': play_url
        })
    return episodes
```

---

## 导出方案 (Excel)

为了方便人工检查和搜索引擎导入，直接导出单一的 Excel 文件。

**文件路径**：`output/media_resources_full_YYYYMMDD_HHMMSS.xlsx`

**字段列表**：
*   category
*   title
*   episode_name
*   play_url
*   detail_url
*   poster_url
*   year
*   quality
*   genre
*   region
*   director
*   actors
*   status
*   updated_at

**代码实现 (`exporter.py`)**：

```python
def export_excel():
    # ...
    query = '''
    SELECT 
        category, title, episode_name, play_url, detail_url, poster_url,
        year, quality, genre, region, director, actors, status, updated_at
    FROM media_resources
    ORDER BY category, title, id
    '''
    df = pd.read_sql_query(query, conn)
    df.to_excel(filepath, index=False, engine='openpyxl')
```

---

## 运行指南

### 1. 环境依赖

```bash
pip install requests beautifulsoup4 lxml pandas openpyxl
```

### 2. 运行爬虫

默认配置：20个线程，每个分类爬取20部（及所有集数）。

```bash
# 默认运行
python main.py

# 指定每类爬取数量 (例如 50 部)
python main.py 50
```

### 3. 输出产物

*   **数据库**: `vs_1919_flat.db` (SQLite)
*   **Excel**: `output/media_resources_full_....xlsx`

---

## 验证报告 (示例)

在最近一次运行中（目标各20部），爬虫成功抓取并验证了以下数据：

*   **Movie**: 19 部电影 (单行记录)
*   **TV Series**: 20 部剧集 -> **1156** 个播放资源 (集)
*   **Variety**: 20 部综艺 -> **7051** 个播放资源 (期)
*   **Anime**: 20 部动漫 -> **13869** 个播放资源 (集)
*   **Short Drama**: 20 部短剧 -> **1245** 个播放资源 (集)

**总计**: **23,341** 条可直接播放的资源数据，完全满足搜索引擎快速查询的需求。
