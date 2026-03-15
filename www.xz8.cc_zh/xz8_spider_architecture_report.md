# xz8.cc 影视网站爬虫技术调研与架构设计报告

## 一、核心概念定义

### 播放详情页 vs 详情页

| 概念 | URL格式 | 是否有播放器 | 页面特征 |
|------|---------|--------------|----------|
| **播放详情页** | `/play/ID-SOURCE-EPISODE/` | ✅ **有** | 包含 `player-box` 播放器容器、player_aaaa JS变量、m3u8播放地址 |
| 详情页 | `/voddetail/ID/` | ❌ 无 | 只有影片信息、海报、播放列表链接 |

**核心原则：所有爬取存储的URL必须是播放详情页URL（带播放器）**

---

## 二、网页结构与URL规律分析

### 2.1 网站基本信息

| 项目 | 内容 |
|------|------|
| 目标域名 | www.xz8.cc |
| 实际解析域名 | www.59v.net (Cloudflare CDN) |
| 反爬等级 | 中等 (需User-Agent + Session Cookie) |
| 页面类型 | 纯静态HTML，无JS动态渲染 |
| 技术框架 | MxProCMS (maccms) |

### 2.2 URL结构分析

#### 分类列表页

| 分类 | 类型ID | 列表页URL | 分页URL |
|------|--------|-----------|---------|
| 电影 | 1 | `/vodtype/1/` | `/vodtype/1/page/PAGE/` |
| 剧集 | 2 | `/vodtype/2/` | `/vodtype/2/page/PAGE/` |
| 综艺 | 3 | `/vodtype/3/` | `/vodtype/3/page/PAGE/` |
| 动漫 | 4 | `/vodtype/4/` | `/vodtype/4/page/PAGE/` |

#### 筛选页URL

| 筛选类型 | URL格式 |
|----------|---------|
| 年份筛选 | `/vodshow/1--YEAR--------/` |
| 分类+年份 | `/vodshow/TYPE--YEAR--------/` |

#### 详情页与播放详情页

| 页面类型 | URL格式 | 示例 |
|----------|---------|------|
| 详情页 | `/voddetail/ID/` | `/voddetail/122498/` |
| **播放详情页** | `/play/ID-SOURCE-EPISODE/` | `/play/122498-1-1/` |

**URL参数说明：**
- `ID`: 影片唯一标识 (如: 122498)
- `SOURCE`: 播放源编号 (1=默认源, 可能有多个)
- `EPISODE`: 集数编号 (电影通常为1)
- `PAGE`: 页码
- `YEAR`: 年份 (如: 2026)
- `TYPE`: 分类ID (1=电影, 2=剧集, 3=综艺, 4=动漫)

### 2.3 页面HTML特征提取

#### 列表页结构

```html
<!-- 视频列表容器 -->
<div class="vodlist">
  <div class="vodlist-item">
    <a class="vodlist-thumb" href="/voddetail/122498/" title="疯狂的酒局">
      <img data-original="/upload/vod/20260314-1/df4388aa32d1b2114db25709107d9110.jpg">
      <span class="vodlist-status">正片</span>
    </a>
    <div class="vodlist-info">
      <h4 class="vodlist-title">疯狂的酒局</h4>
      <p class="vodlist-desc">2026 / 喜剧</p>
    </div>
  </div>
</div>

<!-- 分页 -->
<div class="pagination">
  <a href="/vodtype/1/page/2/">下一页</a>
</div>
```

**CSS选择器映射：**
| 字段 | 选择器 | 属性 |
|------|--------|------|
| 标题 | `.vodlist-thumb` | `title` |
| 详情页URL | `.vodlist-thumb` | `href` |
| 海报URL | `.vodlist-thumb img` | `data-original` |
| 状态 | `.vodlist-status` | text |
| 年份/类型 | `.vodlist-desc` | text |

#### 详情页结构

```html
<div class="detail-info">
  <h1 class="detail-title">疯狂的酒局</h1>
  <div class="detail-meta">
    <span>年份：2026</span>
    <span>地区：中国大陆</span>
    <span>类型：喜剧</span>
    <span>导演：张浩</span>
    <span>主演：张浩,李野</span>
  </div>
  <div class="detail-content">剧情简介...</div>
</div>

<!-- 播放列表 - 关键提取区域 -->
<div class="play-box">
  <div class="play-tabs">
    <a href="#tab-1" data-toggle="tab">源1</a>
    <a href="#tab-2" data-toggle="tab">源2</a>
  </div>
  <div class="play-list" id="tab-1">
    <a href="/play/122498-1-1/">正片</a>
  </div>
  <div class="play-list" id="tab-2">
    <a href="/play/122498-2-1/">正片</a>
  </div>
</div>
```

#### 播放详情页结构（必须存储的URL）

```html
<!-- 播放器容器 -->
<div class="player-box">
  <div class="player-video">
    <script type="text/javascript">
      var player_aaaa = {
        "flag": "play",
        "encrypt": 0,
        "link": "/play/122498-1-1/",
        "link_next": "",
        "link_pre": "",
        "vod_data": {
          "vod_name": "疯狂的酒局",
          "vod_actor": "张浩,李野",
          "vod_director": "张浩",
          "vod_class": "喜剧"
        },
        "url": "https://v5.qsstvw.com/wjv5/202603/14/xxxxx/video/index.m3u8",
        "url_next": "",
        "from": "wjm3u8",
        "server": "no",
        "id": "122498",
        "sid": 1,
        "nid": 1
      };
    </script>
    <script src="/static/js/playerconfig.js"></script>
    <script src="/static/js/player.js"></script>
  </div>
</div>
```

### 2.4 反爬机制分析

| 机制 | 说明 | 解决方案 |
|------|------|----------|
| User-Agent检测 | 无UA返回403 | 设置Mozilla/5.0等常见UA |
| Session Cookie | 首次访问设置session | 使用requests.Session保持会话 |
| Cloudflare CDN | 使用CF加速 | 正常请求即可，无特殊防护 |
| 请求频率 | 未明确限制 | 建议1-2秒/请求，避免被封 |
| 验证码 | 未检测到 | 暂不需要处理 |

**推荐请求头：**
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}
```

---

## 三、爬虫抓取逻辑设计

### 3.1 播放详情页URL提取流程

```
列表页 (/vodtype/1/)
    ↓ 提取 .vodlist-thumb[href]
详情页 (/voddetail/122498/)
    ↓ 提取 .play-list a[href]
播放详情页 (/play/122498-1-1/) ← 存储这个URL
```

### 3.2 核心提取代码

```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

class XZ8Extractor:
    BASE_URL = "https://www.xz8.cc"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate, br',
        })
    
    def fetch(self, url):
        """发送请求并解析HTML"""
        response = self.session.get(url)
        response.encoding = 'utf-8'
        return BeautifulSoup(response.text, 'lxml')
    
    def extract_list_items(self, list_url):
        """从列表页提取所有视频项"""
        soup = self.fetch(list_url)
        items = []
        
        for item in soup.select('.vodlist-item'):
            thumb = item.select_one('.vodlist-thumb')
            items.append({
                'title': thumb.get('title', ''),
                'detail_url': urljoin(self.BASE_URL, thumb.get('href', '')),
                'poster_url': urljoin(self.BASE_URL, 
                    item.select_one('.vodlist-thumb img').get('data-original', '')),
                'status': item.select_one('.vodlist-status').text if item.select_one('.vodlist-status') else '',
                'desc': item.select_one('.vodlist-desc').text if item.select_one('.vodlist-desc') else '',
            })
        
        return items
    
    def extract_detail_info(self, detail_url):
        """从详情页提取影片信息和播放列表"""
        soup = self.fetch(detail_url)
        
        # 提取元数据
        meta = soup.select_one('.detail-meta')
        info = {
            'title': soup.select_one('.detail-title').text if soup.select_one('.detail-title') else '',
            'year': self._extract_meta(meta, '年份'),
            'region': self._extract_meta(meta, '地区'),
            'genre': self._extract_meta(meta, '类型'),
            'director': self._extract_meta(meta, '导演'),
            'actors': self._extract_meta(meta, '主演'),
            'description': soup.select_one('.detail-content').text if soup.select_one('.detail-content') else '',
        }
        
        # 提取播放详情页URL列表（关键！）
        play_urls = []
        for tab in soup.select('.play-tabs a'):
            source_name = tab.text.strip()
            tab_id = tab.get('href', '').replace('#', '')
            
            play_list = soup.select_one(f'#{tab_id}')
            if play_list:
                for ep_link in play_list.select('a'):
                    play_urls.append({
                        'source': source_name,
                        'episode_name': ep_link.text.strip(),
                        'play_url': urljoin(self.BASE_URL, ep_link.get('href', '')),
                    })
        
        return info, play_urls
    
    def _extract_meta(self, meta_soup, key):
        """从meta区域提取指定字段"""
        if not meta_soup:
            return ''
        pattern = re.compile(rf'{key}[:：]([^\s]+)')
        match = pattern.search(meta_soup.text)
        return match.group(1) if match else ''
```

---

## 四、数据库与存储架构设计

### 4.1 核心设计原则

**采用"以播放单元为核心"的统一宽表 (Flat Table) 设计**

- 每一行代表一个**独立的可播放资源**
- 电影：1行（1个播放详情页）
- 40集电视剧：40行（每行重复剧集元数据，不同集数名称和播放链接）
- 基于 `play_url` 实现唯一索引和自动去重

### 4.2 宽表结构 DDL

```sql
-- SQLite 宽表设计：media_resources
-- 每一行代表一个独立的可播放资源

CREATE TABLE media_resources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- ========== 核心字段（必须）==========
    play_url TEXT UNIQUE NOT NULL,          -- 【播放详情页URL】唯一标识
    detail_url TEXT,                        -- 来源详情页URL
    
    -- ========== 基础元数据 ==========
    title TEXT NOT NULL,                    -- 影视标题
    poster_url TEXT,                        -- 海报URL
    year INTEGER,                           -- 年份
    
    -- ========== 分类信息 ==========
    category TEXT,                          -- 大类：movie/tv/variety/anime
    category_id INTEGER,                    -- 分类ID：1/2/3/4
    genre TEXT,                             -- 类型：喜剧/动作/剧情等
    region TEXT,                            -- 地区
    
    -- ========== 人员信息 ==========
    director TEXT,                          -- 导演
    actors TEXT,                            -- 主演/嘉宾
    
    -- ========== 状态信息 ==========
    status TEXT,                            -- 状态：正片/更新至XX集/已完结
    quality TEXT,                           -- 清晰度/状态标签
    
    -- ========== 剧集特有字段 ==========
    is_series BOOLEAN DEFAULT 0,            -- 是否为剧集类
    episode_name TEXT,                      -- 集数名称：正片/第01集/20260314期
    episode_num INTEGER,                    -- 集数编号
    total_episodes INTEGER,                 -- 总集数（如有）
    
    -- ========== 播放源信息 ==========
    source_name TEXT,                       -- 播放源名称：源1/源2
    source_id INTEGER,                      -- 播放源编号
    
    -- ========== 时间戳 ==========
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========== 索引设计（极致搜索优化）==========

-- 唯一索引：基于播放详情页URL去重
CREATE UNIQUE INDEX idx_play_url ON media_resources(play_url);

-- 搜索优化索引
CREATE INDEX idx_title ON media_resources(title);
CREATE INDEX idx_year ON media_resources(year);
CREATE INDEX idx_category ON media_resources(category);
CREATE INDEX idx_genre ON media_resources(genre);
CREATE INDEX idx_region ON media_resources(region);
CREATE INDEX idx_status ON media_resources(status);
CREATE INDEX idx_is_series ON media_resources(is_series);

-- 复合索引（常用查询组合）
CREATE INDEX idx_category_year ON media_resources(category, year);
CREATE INDEX idx_genre_year ON media_resources(genre, year);
CREATE INDEX idx_title_year ON media_resources(title, year);
```

### 4.3 数据插入与去重逻辑

```python
import sqlite3
from datetime import datetime

class MediaRepository:
    def __init__(self, db_path='xz8_media.db'):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建主表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media_resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                play_url TEXT UNIQUE NOT NULL,
                detail_url TEXT,
                title TEXT NOT NULL,
                poster_url TEXT,
                year INTEGER,
                category TEXT,
                category_id INTEGER,
                genre TEXT,
                region TEXT,
                director TEXT,
                actors TEXT,
                status TEXT,
                quality TEXT,
                is_series BOOLEAN DEFAULT 0,
                episode_name TEXT,
                episode_num INTEGER,
                total_episodes INTEGER,
                source_name TEXT,
                source_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_play_url ON media_resources(play_url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON media_resources(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_year ON media_resources(year)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON media_resources(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_genre ON media_resources(genre)')
        
        conn.commit()
        conn.close()
    
    def insert_or_ignore(self, media_data):
        """插入数据，基于play_url自动去重"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO media_resources (
                    play_url, detail_url, title, poster_url, year,
                    category, category_id, genre, region, director, actors,
                    status, quality, is_series, episode_name, episode_num,
                    total_episodes, source_name, source_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                media_data['play_url'],
                media_data.get('detail_url', ''),
                media_data['title'],
                media_data.get('poster_url', ''),
                media_data.get('year'),
                media_data.get('category'),
                media_data.get('category_id'),
                media_data.get('genre'),
                media_data.get('region'),
                media_data.get('director'),
                media_data.get('actors'),
                media_data.get('status'),
                media_data.get('quality'),
                media_data.get('is_series', False),
                media_data.get('episode_name'),
                media_data.get('episode_num'),
                media_data.get('total_episodes'),
                media_data.get('source_name'),
                media_data.get('source_id')
            ))
            
            conn.commit()
            return cursor.rowcount  # 返回插入行数（0表示已存在）
        
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0
        finally:
            conn.close()
    
    def get_existing_urls(self):
        """获取所有已存在的play_url（用于增量更新）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT play_url FROM media_resources')
        urls = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        return urls
    
    def query(self, filters=None, limit=None):
        """查询数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM media_resources WHERE 1=1'
        params = []
        
        if filters:
            if 'category' in filters:
                query += ' AND category = ?'
                params.append(filters['category'])
            if 'year' in filters:
                query += ' AND year = ?'
                params.append(filters['year'])
            if 'genre' in filters:
                query += ' AND genre LIKE ?'
                params.append(f'%{filters["genre"]}%')
            if 'title' in filters:
                query += ' AND title LIKE ?'
                params.append(f'%{filters["title"]}%')
        
        query += ' ORDER BY created_at DESC'
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return results
```

---

## 五、多线程爬虫架构设计

### 5.1 核心架构类

```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time
import random
import re
import sqlite3
from datetime import datetime

class XZ8Spider:
    """
    xz8.cc 多线程爬虫
    支持按年份、分类爬取，自动翻页，多线程并发
    """
    
    BASE_URL = "https://www.xz8.cc"
    
    # 分类配置
    CATEGORIES = {
        'movie': {'id': 1, 'name': '电影', 'is_series': False},
        'tv': {'id': 2, 'name': '剧集', 'is_series': True},
        'variety': {'id': 3, 'name': '综艺', 'is_series': True},
        'anime': {'id': 4, 'name': '动漫', 'is_series': True},
    }
    
    def __init__(self, db_path='xz8_media.db', max_workers=10, delay=(0.5, 1.5)):
        """
        初始化爬虫
        
        Args:
            db_path: 数据库路径
            max_workers: 最大线程数 (5-100)
            delay: 请求延迟范围 (min, max)秒
        """
        self.db = MediaRepository(db_path)
        self.max_workers = max_workers
        self.delay = delay
        self.session = self._create_session()
        self.lock = threading.Lock()
        self.stats = {'processed': 0, 'inserted': 0, 'failed': 0}
    
    def _create_session(self):
        """创建请求会话"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
        })
        return session
    
    def fetch(self, url):
        """发送请求并解析HTML（带延迟）"""
        time.sleep(random.uniform(*self.delay))
        try:
            response = self.session.get(url, timeout=30)
            response.encoding = 'utf-8'
            return BeautifulSoup(response.text, 'lxml')
        except Exception as e:
            print(f"Fetch error: {url}, {e}")
            return None
    
    def crawl_by_year(self, category, start_year=2026, end_year=2000, max_items=None):
        """
        按年份倒序爬取指定分类
        
        Args:
            category: 分类标识 movie/tv/variety/anime
            start_year: 起始年份（倒序，从最新开始）
            end_year: 结束年份
            max_items: 最大爬取数量（None表示无限制）
        """
        cat_config = self.CATEGORIES[category]
        cat_id = cat_config['id']
        is_series = cat_config['is_series']
        
        print(f"开始爬取 [{cat_config['name']}] {start_year}-{end_year} 年数据...")
        
        for year in range(start_year, end_year - 1, -1):
            print(f"  正在处理 {year} 年...")
            
            page = 1
            while True:
                # 构造年份筛选URL
                list_url = f"{self.BASE_URL}/vodshow/{cat_id}--{year}--------/"
                if page > 1:
                    list_url = f"{self.BASE_URL}/vodshow/{cat_id}--{year}--------{page}/"
                
                items = self._parse_list_page(list_url)
                if not items:
                    break
                
                # 多线程处理详情页
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = {
                        executor.submit(self._process_detail, item, category, cat_id, is_series): item 
                        for item in items
                    }
                    
                    for future in as_completed(futures):
                        try:
                            result = future.result()
                            if result:
                                self._update_stats(inserted=result)
                        except Exception as e:
                            print(f"Process error: {e}")
                            self._update_stats(failed=1)
                
                # 检查是否达到限制
                if max_items and self.stats['processed'] >= max_items:
                    print(f"  已达到最大数量限制: {max_items}")
                    return
                
                # 检查下一页
                if len(items) < 24:  # 假设每页24条
                    break
                page += 1
        
        print(f"爬取完成: {self.stats}")
    
    def crawl_category(self, category, max_pages=None, max_items=None):
        """
        爬取整个分类（不按年份筛选）
        
        Args:
            category: 分类标识
            max_pages: 最大页数
            max_items: 最大条目数
        """
        cat_config = self.CATEGORIES[category]
        cat_id = cat_config['id']
        is_series = cat_config['is_series']
        
        print(f"开始爬取 [{cat_config['name']}] 全部分页数据...")
        
        page = 1
        while True:
            if max_pages and page > max_pages:
                break
            
            list_url = f"{self.BASE_URL}/vodtype/{cat_id}/page/{page}/"
            items = self._parse_list_page(list_url)
            
            if not items:
                break
            
            # 多线程处理
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(self._process_detail, item, category, cat_id, is_series): item 
                    for item in items
                }
                
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            self._update_stats(inserted=result)
                    except Exception as e:
                        self._update_stats(failed=1)
            
            if max_items and self.stats['processed'] >= max_items:
                break
            
            page += 1
    
    def _parse_list_page(self, url):
        """解析列表页，返回视频项列表"""
        soup = self.fetch(url)
        if not soup:
            return []
        
        items = []
        for item in soup.select('.vodlist-item'):
            try:
                thumb = item.select_one('.vodlist-thumb')
                items.append({
                    'title': thumb.get('title', ''),
                    'detail_url': urljoin(self.BASE_URL, thumb.get('href', '')),
                    'poster_url': urljoin(self.BASE_URL, 
                        item.select_one('.vodlist-thumb img').get('data-original', '')),
                    'status': item.select_one('.vodlist-status').text if item.select_one('.vodlist-status') else '',
                    'desc': item.select_one('.vodlist-desc').text if item.select_one('.vodlist-desc') else '',
                })
            except Exception as e:
                continue
        
        return items
    
    def _process_detail(self, item, category, category_id, is_series):
        """
        处理详情页，提取所有播放详情页URL并保存
        
        Returns:
            int: 插入的行数
        """
        soup = self.fetch(item['detail_url'])
        if not soup:
            return 0
        
        # 提取元数据
        meta = soup.select_one('.detail-meta')
        info = {
            'title': item['title'],
            'detail_url': item['detail_url'],
            'poster_url': item['poster_url'],
            'year': self._extract_year(meta),
            'category': category,
            'category_id': category_id,
            'genre': self._extract_meta(meta, '类型'),
            'region': self._extract_meta(meta, '地区'),
            'director': self._extract_meta(meta, '导演'),
            'actors': self._extract_meta(meta, '主演'),
            'status': item['status'],
            'quality': item['status'],
            'is_series': is_series,
        }
        
        # 提取播放详情页URL列表
        inserted_count = 0
        play_tabs = soup.select('.play-tabs a')
        
        for source_idx, tab in enumerate(play_tabs):
            source_name = tab.text.strip()
            tab_id = tab.get('href', '').replace('#', '')
            
            play_list = soup.select_one(f'#{tab_id}')
            if not play_list:
                continue
            
            for ep_idx, ep_link in enumerate(play_list.select('a')):
                episode_name = ep_link.text.strip()
                play_url = urljoin(self.BASE_URL, ep_link.get('href', ''))
                
                # 提取集数
                episode_num = self._extract_episode_num(episode_name)
                
                # 构建完整数据
                media_data = {
                    **info,
                    'play_url': play_url,
                    'episode_name': episode_name,
                    'episode_num': episode_num,
                    'source_name': source_name,
                    'source_id': source_idx + 1,
                }
                
                # 插入数据库（自动去重）
                inserted = self.db.insert_or_ignore(media_data)
                inserted_count += inserted
                
                with self.lock:
                    self.stats['processed'] += 1
        
        return inserted_count
    
    def _extract_meta(self, meta_soup, key):
        """提取元数据字段"""
        if not meta_soup:
            return ''
        pattern = re.compile(rf'{key}[:：]([^\s]+)')
        match = pattern.search(meta_soup.text)
        return match.group(1) if match else ''
    
    def _extract_year(self, meta_soup):
        """提取年份"""
        year_str = self._extract_meta(meta_soup, '年份')
        try:
            return int(year_str) if year_str else None
        except:
            return None
    
    def _extract_episode_num(self, episode_name):
        """提取集数编号"""
        match = re.search(r'第(\d+)集', episode_name)
        if match:
            return int(match.group(1))
        match = re.search(r'(\d+)', episode_name)
        if match:
            return int(match.group(1))
        return None
    
    def _update_stats(self, inserted=0, failed=0):
        """更新统计信息"""
        with self.lock:
            self.stats['inserted'] += inserted
            self.stats['failed'] += failed
```

---

## 六、数据导出设计

### 6.1 导出模块

```python
import pandas as pd
import os
from datetime import datetime

class DataExporter:
    def __init__(self, db_path='xz8_media.db', output_dir='output'):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_full(self, format='xlsx'):
        """
        全量导出所有数据
        
        Args:
            format: 导出格式 xlsx 或 csv
        """
        conn = sqlite3.connect(self.db_path)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"media_resources_full_{timestamp}.{format}"
        filepath = os.path.join(self.output_dir, filename)
        
        # 读取所有数据
        df = pd.read_sql_query('SELECT * FROM media_resources ORDER BY created_at DESC', conn)
        
        # 导出
        if format == 'xlsx':
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        conn.close()
        print(f"全量导出完成: {filepath}")
        return filepath
    
    def export_incremental(self, format='xlsx'):
        """
        增量导出今日新增数据
        
        Args:
            format: 导出格式 xlsx 或 csv
        """
        conn = sqlite3.connect(self.db_path)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"media_resources_incremental_{timestamp}.{format}"
        filepath = os.path.join(self.output_dir, filename)
        
        # 读取今日新增数据
        df = pd.read_sql_query('''
            SELECT * FROM media_resources 
            WHERE date(created_at) = date('now') 
            ORDER BY created_at DESC
        ''', conn)
        
        # 导出
        if format == 'xlsx':
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        conn.close()
        print(f"增量导出完成: {filepath}, 共 {len(df)} 条记录")
        return filepath
    
    def export_by_category(self, category, format='xlsx'):
        """
        按分类导出
        
        Args:
            category: 分类标识 movie/tv/variety/anime
            format: 导出格式
        """
        conn = sqlite3.connect(self.db_path)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"media_resources_{category}_{timestamp}.{format}"
        filepath = os.path.join(self.output_dir, filename)
        
        df = pd.read_sql_query(
            'SELECT * FROM media_resources WHERE category = ? ORDER BY year DESC',
            conn, params=(category,)
        )
        
        if format == 'xlsx':
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        conn.close()
        print(f"[{category}] 导出完成: {filepath}, 共 {len(df)} 条记录")
        return filepath
```

---

## 七、使用示例

```python
# 1. 初始化爬虫
spider = XZ8Spider(db_path='xz8_media.db', max_workers=20, delay=(0.5, 1.0))

# 2. 按年份爬取电影（2026-2020年）
spider.crawl_by_year('movie', start_year=2026, end_year=2020)

# 3. 爬取剧集（限制100页）
spider.crawl_category('tv', max_pages=100)

# 4. 导出数据
exporter = DataExporter(db_path='xz8_media.db', output_dir='output')

# 全量导出Excel
exporter.export_full(format='xlsx')

# 增量导出CSV
exporter.export_incremental(format='csv')

# 按分类导出
exporter.export_by_category('movie', format='xlsx')
```

---

## 八、依赖库

```txt
requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
pandas>=1.5.0
openpyxl>=3.0.0
```

---

*报告生成时间: 2026-03-14*
*调研基于: https://www.xz8.cc*
*核心原则: 所有存储的URL必须是播放详情页URL（/play/...格式，带播放器）*
