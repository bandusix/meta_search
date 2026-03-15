import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
import os
import logging

class DatabaseManager:
    """数据库管理类"""

    def __init__(self, db_path: str = "data/database.db"):
        self.db_path = db_path
        self.ensure_db_dir()
        self.init_database()
        self.logger = logging.getLogger(__name__)

    def ensure_db_dir(self):
        """确保数据库目录存在"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def init_database(self):
        """初始化数据库表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 电影表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        original_title TEXT,
                        url TEXT UNIQUE NOT NULL,
                        poster_url TEXT,
                        year INTEGER,
                        rating REAL,
                        imdb_rating REAL,
                        quality TEXT,
                        release_title TEXT,
                        views INTEGER DEFAULT 0,
                        votes INTEGER DEFAULT 0,
                        duration TEXT,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_crawled TIMESTAMP
                    );
                """)
                # 索引优化
                conn.execute("CREATE INDEX IF NOT EXISTS idx_movies_year ON movies (year);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_movies_rating ON movies (rating DESC);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_movies_url ON movies (url);")

                # 电视剧集表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tv_episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        series_title TEXT NOT NULL,
                        episode_title TEXT NOT NULL,
                        original_title TEXT,
                        url TEXT UNIQUE NOT NULL,
                        poster_url TEXT,
                        year INTEGER,
                        rating REAL,
                        imdb_rating REAL,
                        quality TEXT,
                        season INTEGER NOT NULL,
                        episode INTEGER NOT NULL,
                        release_title TEXT,
                        views INTEGER DEFAULT 0,
                        votes INTEGER DEFAULT 0,
                        description TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_crawled TIMESTAMP
                    );
                """)
                # 复合索引用于快速查询
                conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_tv_unique ON tv_episodes (series_title, season, episode);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tv_series_title ON tv_episodes (series_title);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tv_season_episode ON tv_episodes (season, episode);")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_tv_url ON tv_episodes (url);")

                # 爬取状态表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS crawl_status (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        last_page_crawled INTEGER DEFAULT 0,
                        last_movie_id_crawled INTEGER,
                        last_tv_id_crawled INTEGER,
                        last_crawl_time TIMESTAMP,
                        total_movies INTEGER DEFAULT 0,
                        total_episodes INTEGER DEFAULT 0,
                        last_full_crawl TIMESTAMP
                    );
                """)

                # 导出历史表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS export_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        export_type TEXT NOT NULL,
                        export_mode TEXT NOT NULL,
                        file_path TEXT NOT NULL,
                        record_count INTEGER DEFAULT 0,
                        export_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        start_date DATE,
                        end_date DATE
                    );
                """)
                conn.commit()
        except sqlite3.Error as e:
            print(f"初始化数据库失败: {e}")

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
                        INSERT INTO movies (
                            title, original_title, url, poster_url, year,
                            rating, imdb_rating, quality, release_title,
                            views, votes, duration, description,
                            created_at, updated_at, last_crawled
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (
                        movie_data['title'], movie_data.get('original_title'),
                        movie_data['url'], movie_data['poster_url'],
                        movie_data['year'], movie_data['rating'],
                        movie_data['imdb_rating'], movie_data['quality'],
                        movie_data['release_title'], movie_data['views'],
                        movie_data['votes'], movie_data.get('duration'),
                        movie_data.get('description')
                    ))

                conn.commit()
                return True

        except sqlite3.Error as e:
            self.logger.error(f"保存电影数据失败: {e}")
            return False

    def save_episode(self, episode_data: Dict) -> bool:
        """保存电视剧集数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 1. 尝试通过 URL 查找
                cursor = conn.execute(
                    "SELECT id FROM tv_episodes WHERE url = ?",
                    (episode_data['url'],)
                )
                row = cursor.fetchone()
                
                # 2. 如果 URL 没找到，尝试通过 复合键(series_title, season, episode) 查找
                # 这能防止 URL 变更导致的唯一性冲突
                if not row:
                    cursor = conn.execute(
                        "SELECT id FROM tv_episodes WHERE series_title = ? AND season = ? AND episode = ?",
                        (episode_data['series_title'], episode_data['season'], episode_data['episode'])
                    )
                    row = cursor.fetchone()

                if row:
                    # 更新
                    episode_id = row[0]
                    conn.execute("""
                        UPDATE tv_episodes SET
                            series_title = ?, episode_title = ?, poster_url = ?,
                            year = ?, rating = ?, imdb_rating = ?, quality = ?,
                            season = ?, episode = ?, release_title = ?,
                            views = ?, votes = ?, updated_at = CURRENT_TIMESTAMP,
                            last_crawled = CURRENT_TIMESTAMP,
                            url = ?  -- 更新 URL
                        WHERE id = ?
                    """, (
                        episode_data['series_title'], episode_data['episode_title'],
                        episode_data['poster_url'], episode_data['year'],
                        episode_data['rating'], episode_data['imdb_rating'],
                        episode_data['quality'], episode_data['season'],
                        episode_data['episode'], episode_data['release_title'],
                        episode_data['views'], episode_data['votes'],
                        episode_data['url'],
                        episode_id
                    ))
                else:
                    # 插入
                    conn.execute("""
                        INSERT INTO tv_episodes (
                            series_title, episode_title, original_title, url,
                            poster_url, year, rating, imdb_rating, quality,
                            season, episode, release_title, views, votes,
                            description, created_at, updated_at, last_crawled
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, (
                        episode_data['series_title'], episode_data['episode_title'],
                        episode_data.get('original_title'), episode_data['url'],
                        episode_data['poster_url'], episode_data['year'],
                        episode_data['rating'], episode_data['imdb_rating'],
                        episode_data['quality'], episode_data['season'],
                        episode_data['episode'], episode_data['release_title'],
                        episode_data['views'], episode_data['votes'],
                        episode_data.get('description')
                    ))
                conn.commit()
                return True
        except sqlite3.Error as e:
            self.logger.error(f"保存剧集数据失败: {e}")
            return False

    def get_movies_count(self) -> int:
        """获取电影总数"""
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]

    def get_episodes_count(self) -> int:
        """获取剧集总数"""
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT COUNT(*) FROM tv_episodes").fetchone()[0]

    def get_all_movies(self) -> List[tuple]:
        """获取所有电影数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, title, original_title, url, poster_url, year,
                       rating, imdb_rating, quality, release_title,
                       views, votes, duration, description, created_at,
                       last_crawled
                FROM movies
                ORDER BY id ASC
            """)
            return cursor.fetchall()

    def get_all_episodes(self) -> List[tuple]:
        """获取所有剧集数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT id, series_title, episode_title, original_title, url,
                       poster_url, year, rating, imdb_rating, quality,
                       season, episode, release_title, views, votes,
                       description, created_at, last_crawled
                FROM tv_episodes
                ORDER BY series_title, season, episode
            """)
            return cursor.fetchall()

    def get_existing_items(self) -> tuple[set, set]:
        """
        获取已存在的项目标识，用于去重
        返回: (movie_urls_set, episode_keys_set)
        movie_urls_set: 包含所有电影 URL 的集合
        episode_keys_set: 包含所有剧集 (series_title, season, episode) 的集合
        """
        movie_urls = set()
        episode_keys = set()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取电影 URL
                cursor = conn.execute("SELECT url FROM movies")
                for row in cursor:
                    movie_urls.add(row[0])
                    
                # 获取剧集唯一键
                cursor = conn.execute("SELECT series_title, season, episode FROM tv_episodes")
                for row in cursor:
                    episode_keys.add((row[0], row[1], row[2]))
                    
        except sqlite3.Error as e:
            self.logger.error(f"获取已存在项目失败: {e}")
            
        return movie_urls, episode_keys
