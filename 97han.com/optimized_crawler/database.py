#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块 - SQLite数据库操作
"""

import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "crawler.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库和表结构"""
        with self.get_connection() as conn:
            # 创建主表
            conn.executescript("""
                -- 电影表
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    cover TEXT,
                    year INTEGER,
                    region TEXT,
                    genre TEXT,
                    intro TEXT,
                    detail_url TEXT NOT NULL,
                    route_name TEXT NOT NULL,
                    play_url TEXT NOT NULL,
                    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 电视剧表
                CREATE TABLE IF NOT EXISTS tv_series (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    cover TEXT,
                    year INTEGER,
                    region TEXT,
                    genre TEXT,
                    intro TEXT,
                    detail_url TEXT NOT NULL,
                    total_episodes INTEGER,
                    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- 剧集表
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id INTEGER,
                    vod_id INTEGER NOT NULL,
                    episode_number INTEGER NOT NULL,
                    episode_title TEXT,
                    route_name TEXT NOT NULL,
                    play_url TEXT NOT NULL,
                    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (series_id) REFERENCES tv_series(id),
                    UNIQUE(vod_id, episode_number, route_name)
                );
                
                -- 创建索引
                CREATE UNIQUE INDEX IF NOT EXISTS idx_movies_detail_route 
                ON movies(detail_url, route_name);
                
                CREATE INDEX IF NOT EXISTS idx_movies_category ON movies(category);
                CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title);
                CREATE INDEX IF NOT EXISTS idx_episodes_series ON episodes(series_id);
                CREATE INDEX IF NOT EXISTS idx_episodes_vod ON episodes(vod_id);
                
                -- 创建元数据表
                CREATE TABLE IF NOT EXISTS crawl_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    total_pages INTEGER,
                    current_page INTEGER,
                    items_found INTEGER,
                    status TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            logger.info("数据库初始化完成")
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # 启用WAL模式提高并发性能
        conn.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全性
        try:
            yield conn
        finally:
            conn.close()
    
    def batch_insert_movies(self, movies: List[Dict]) -> int:
        """批量插入电影数据"""
        if not movies:
            return 0
        
        inserted = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 准备数据
            for movie in movies:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO movies 
                        (category, title, cover, year, region, genre, intro, 
                         detail_url, route_name, play_url, crawl_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        movie.get('category'),
                        movie.get('title'),
                        movie.get('cover'),
                        movie.get('year'),
                        movie.get('region'),
                        movie.get('genre'),
                        movie.get('intro'),
                        movie.get('detail_url'),
                        movie.get('route_name'),
                        movie.get('play_url'),
                        datetime.now()
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    logger.error(f"插入电影数据失败: {e}, movie: {movie.get('title', 'Unknown')}")
            
            conn.commit()
        
        logger.info(f"批量插入电影完成: {inserted}/{len(movies)}")
        return inserted
    
    def batch_insert_episodes(self, episodes: List[Dict]) -> int:
        """批量插入剧集数据"""
        if not episodes:
            return 0
        
        inserted = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for episode in episodes:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO episodes 
                        (series_id, vod_id, episode_number, episode_title, 
                         route_name, play_url, crawl_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        episode.get('series_id'),
                        episode.get('vod_id'),
                        episode.get('episode_number'),
                        episode.get('episode_title'),
                        episode.get('route_name'),
                        episode.get('play_url'),
                        datetime.now()
                    ))
                    if cursor.rowcount > 0:
                        inserted += 1
                except Exception as e:
                    logger.error(f"插入剧集数据失败: {e}, episode: {episode.get('episode_title', 'Unknown')}")
            
            conn.commit()
        
        logger.info(f"批量插入剧集完成: {inserted}/{len(episodes)}")
        return inserted
    
    def get_existing_urls(self, category: str) -> set:
        """获取已存在的URL集合（用于去重）"""
        urls = set()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if category in ['movie']:
                cursor.execute("SELECT detail_url FROM movies WHERE category = ?", (category,))
            else:
                cursor.execute("SELECT detail_url FROM tv_series WHERE category = ?", (category,))
            
            urls.update(row[0] for row in cursor.fetchall())
        
        return urls
    
    def update_metadata(self, category: str, total_pages: int, current_page: int, 
                       items_found: int, status: str):
        """更新爬取元数据"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if status == 'running':
                cursor.execute("""
                    INSERT INTO crawl_metadata 
                    (category, total_pages, current_page, items_found, status, start_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (category, total_pages, current_page, items_found, status, datetime.now()))
            else:
                cursor.execute("""
                    UPDATE crawl_metadata 
                    SET current_page = ?, items_found = ?, status = ?, end_time = ?
                    WHERE category = ? AND status = 'running'
                    ORDER BY id DESC LIMIT 1
                """, (current_page, items_found, status, datetime.now(), category))
            
            conn.commit()
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 电影统计
            cursor.execute("SELECT COUNT(*) FROM movies")
            stats['movies'] = cursor.fetchone()[0]
            
            # 剧集统计
            cursor.execute("SELECT COUNT(*) FROM episodes")
            stats['episodes'] = cursor.fetchone()[0]
            
            # 分类统计
            cursor.execute("""
                SELECT category, COUNT(*) as count 
                FROM movies 
                GROUP BY category 
                ORDER BY count DESC
            """)
            stats['movie_categories'] = dict(cursor.fetchall())
            
            # 播放线路统计
            cursor.execute("""
                SELECT route_name, COUNT(*) as count 
                FROM movies 
                GROUP BY route_name 
                ORDER BY count DESC
                LIMIT 10
            """)
            stats['top_routes'] = dict(cursor.fetchall())
            
            return stats
    
    def vacuum(self):
        """清理数据库"""
        with self.get_connection() as conn:
            conn.execute("VACUUM")
            logger.info("数据库清理完成")