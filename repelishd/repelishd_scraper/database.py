import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self, db_path='repelishd.db'):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 电影表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_spanish TEXT NOT NULL,
            title_original TEXT,
            year INTEGER,
            rating REAL,
            quality TEXT,
            image_url TEXT,
            detail_url TEXT UNIQUE NOT NULL,
            web_url_title TEXT,  -- 新增字段: 网页标题
            country TEXT,
            duration TEXT,
            genre TEXT,
            audio TEXT,
            imdb_rating REAL,
            tmdb_rating REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # 尝试添加新字段（如果表已存在）
        try:
            cursor.execute('ALTER TABLE movies ADD COLUMN web_url_title TEXT')
        except sqlite3.OperationalError:
            pass  # 字段已存在

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_rating ON movies(rating);')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_movies_url ON movies(detail_url);')
        
        # 电视剧剧集表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tv_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_spanish TEXT NOT NULL,  -- 统一字段名
            title_original TEXT,          -- 统一字段名
            year INTEGER,
            rating REAL,
            quality TEXT,
            image_url TEXT,
            detail_url TEXT NOT NULL,     -- 统一字段名 (原 series_url)
            web_url_title TEXT,           -- 新增字段: 网页标题
            season INTEGER NOT NULL,
            episode INTEGER NOT NULL,
            episode_title TEXT,
            episode_data_num TEXT,
            embed_url TEXT,               -- 新增字段: 视频嵌入链接
            country TEXT,
            duration TEXT,
            genre TEXT,
            audio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(detail_url, season, episode)
        );
        ''')

        # 尝试添加新字段（如果表已存在）
        try:
            cursor.execute('ALTER TABLE tv_episodes ADD COLUMN web_url_title TEXT')
        except sqlite3.OperationalError:
            pass
            
        try:
            cursor.execute('ALTER TABLE tv_episodes ADD COLUMN embed_url TEXT')
        except sqlite3.OperationalError:
            pass

        # 尝试重命名旧字段以统一命名 (SQLite ALTER TABLE 功能有限，这里做简单的兼容处理)
        # 注意：SQLite 不支持直接重命名列，通常需要重建表。
        # 为了不破坏现有数据，我们保持旧表结构，但在插入和查询时做映射，
        # 或者创建一个新表迁移数据。考虑到简便性，我们可以在这里只添加新字段，
        # 而在代码逻辑层面统一字典键名。
        
        # 但用户要求"数据库表头数据字段一致"，所以最好是迁移数据。
        # 检查是否需要迁移 tv_episodes 表
        cursor.execute("PRAGMA table_info(tv_episodes)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'series_title_spanish' in columns:
            print("正在迁移 tv_episodes 表结构以统一命名...")
            # 1. 重命名旧表
            cursor.execute('ALTER TABLE tv_episodes RENAME TO tv_episodes_old')
            
            # 2. 创建新表 (使用统一后的字段名)
            cursor.execute('''
            CREATE TABLE tv_episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_spanish TEXT NOT NULL,
                title_original TEXT,
                year INTEGER,
                rating REAL,
                quality TEXT,
                image_url TEXT,
                detail_url TEXT NOT NULL,
                web_url_title TEXT,
                season INTEGER NOT NULL,
                episode INTEGER NOT NULL,
                episode_title TEXT,
                episode_data_num TEXT,
                country TEXT,
                duration TEXT,
                genre TEXT,
                audio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(detail_url, season, episode)
            );
            ''')
            
            # 3. 迁移数据
            # 注意：series_url -> detail_url
            cursor.execute('''
            INSERT INTO tv_episodes (
                id, title_spanish, title_original, year, rating, quality, image_url, 
                detail_url, season, episode, episode_title, episode_data_num, 
                country, duration, genre, audio, created_at, updated_at
            )
            SELECT 
                id, series_title_spanish, series_title_original, year, rating, quality, image_url, 
                series_url, season, episode, episode_title, episode_data_num, 
                country, duration, genre, audio, created_at, updated_at
            FROM tv_episodes_old
            ''')
            
            # 4. 删除旧表
            cursor.execute('DROP TABLE tv_episodes_old')
            print("tv_episodes 表结构迁移完成。")
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_detail_url ON tv_episodes(detail_url);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_season ON tv_episodes(season);')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_year ON tv_episodes(year);')
        
        conn.commit()
        conn.close()

    def save_movies(self, movies):
        if not movies:
            return
            
        conn = self._get_conn()
        cursor = conn.cursor()
        
        count = 0
        for movie in movies:
            try:
                cursor.execute('''
                    INSERT INTO movies (title_spanish, title_original, year, rating, quality, 
                                       image_url, detail_url, web_url_title, country, duration, genre, audio,
                                       imdb_rating, tmdb_rating)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(detail_url) DO UPDATE SET
                        title_spanish = excluded.title_spanish,
                        title_original = excluded.title_original,
                        rating = excluded.rating,
                        quality = excluded.quality,
                        image_url = excluded.image_url,
                        web_url_title = excluded.web_url_title,
                        country = excluded.country,
                        duration = excluded.duration,
                        genre = excluded.genre,
                        audio = excluded.audio,
                        imdb_rating = excluded.imdb_rating,
                        tmdb_rating = excluded.tmdb_rating,
                        updated_at = CURRENT_TIMESTAMP
                ''', (movie.get('title_spanish'), movie.get('title_original'), 
                      movie.get('year'), movie.get('rating'), movie.get('quality'),
                      movie.get('image_url'), movie.get('detail_url'), movie.get('web_url_title'),
                      movie.get('country'), movie.get('duration'), movie.get('genre'),
                      movie.get('audio'), movie.get('imdb_rating'), movie.get('tmdb_rating')))
                count += 1
            except Exception as e:
                print(f"Error saving movie {movie.get('title_spanish')}: {e}")
                
        conn.commit()
        conn.close()
        print(f"Saved {count} movies to database.")

    def save_tv_episodes(self, episodes):
        if not episodes:
            return
            
        conn = self._get_conn()
        cursor = conn.cursor()
        
        count = 0
        for ep in episodes:
            try:
                cursor.execute('''
                    INSERT INTO tv_episodes (title_spanish, title_original, year, rating, quality, 
                                           image_url, detail_url, web_url_title, season, episode, episode_title, episode_data_num,
                                           embed_url, country, duration, genre, audio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(detail_url, season, episode) DO UPDATE SET
                        title_spanish = excluded.title_spanish,
                        title_original = excluded.title_original,
                        year = excluded.year,
                        rating = excluded.rating,
                        quality = excluded.quality,
                        image_url = excluded.image_url,
                        web_url_title = excluded.web_url_title,
                        episode_title = excluded.episode_title,
                        episode_data_num = excluded.episode_data_num,
                        embed_url = excluded.embed_url,
                        country = excluded.country,
                        duration = excluded.duration,
                        genre = excluded.genre,
                        audio = excluded.audio,
                        updated_at = CURRENT_TIMESTAMP
                ''', (ep.get('title_spanish'), ep.get('title_original'),
                      ep.get('year'), ep.get('rating'), ep.get('quality'),
                      ep.get('image_url'), ep.get('detail_url'), ep.get('web_url_title'), ep.get('season'),
                      ep.get('episode'), ep.get('episode_title'), ep.get('episode_data_num'),
                      ep.get('embed_url'), ep.get('country'), ep.get('duration'), ep.get('genre'), ep.get('audio')))
                count += 1
            except Exception as e:
                print(f"Error saving episode {ep.get('title_spanish')} S{ep.get('season')}E{ep.get('episode')}: {e}")
                
        conn.commit()
        conn.close()
        print(f"Saved {count} episodes to database.")

    def get_all_movies(self):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies ORDER BY year DESC, created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_tv_episodes(self):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tv_episodes ORDER BY title_spanish, season, episode")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
        
    def get_movies_after(self, timestamp):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM movies WHERE updated_at > ? ORDER BY year DESC, created_at DESC", (timestamp,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_tv_episodes_after(self, timestamp):
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tv_episodes WHERE updated_at > ? ORDER BY title_spanish, season, episode", (timestamp,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_existing_movie_urls(self):
        """返回 {url: has_title} 字典，用于判断是否需要更新"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT detail_url, web_url_title FROM movies")
        # 如果 web_url_title 不为空，则 has_title 为 True
        urls = {row[0]: bool(row[1]) for row in cursor.fetchall()}
        conn.close()
        return urls

    def get_existing_series_urls(self):
        """返回 {url: is_complete} 字典，用于判断是否需要更新"""
        conn = self._get_conn()
        cursor = conn.cursor()
        # 判断标准：web_url_title 不为空 且 embed_url 不为空
        cursor.execute("SELECT detail_url, MAX(web_url_title), MAX(embed_url) FROM tv_episodes GROUP BY detail_url")
        # 只要有任何一集有 embed_url 且系列有 title，就算"部分完整" (为了效率，我们假设这代表已处理过)
        # 更严格的检查可能需要检查所有集数，但这里先检查是否存在 embed_url
        urls = {row[0]: (bool(row[1]) and bool(row[2])) for row in cursor.fetchall()}
        conn.close()
        return urls
    
    def get_movie_count(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM movies")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_tv_series_count(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT detail_url) FROM tv_episodes")
        count = cursor.fetchone()[0]
        conn.close()
        return count
