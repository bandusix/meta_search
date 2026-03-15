#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库模块
管理 SQLite 数据库的创建、连接和操作
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional
import os


class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = "cuevana3.db"):
        """
        初始化数据库连接
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """建立数据库连接"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        self.cursor = self.conn.cursor()
    
    def _create_tables(self):
        """创建数据表"""
        # 创建电影表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_spanish TEXT NOT NULL,
                title_original TEXT,
                year INTEGER,
                rating REAL,
                quality TEXT,
                url TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建电视剧表
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tv_series (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title_spanish TEXT NOT NULL,
                title_original TEXT,
                year INTEGER,
                rating REAL,
                quality TEXT,
                season INTEGER,
                episode INTEGER,
                url TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建索引以提高查询性能
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_movies_year 
            ON movies(year)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_movies_url 
            ON movies(url)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tv_year 
            ON tv_series(year)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tv_season_episode 
            ON tv_series(season, episode)
        ''')
        
        self.cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tv_url 
            ON tv_series(url)
        ''')
        
        self.conn.commit()
    
    def insert_movie(self, movie_data: Dict) -> bool:
        """
        插入或更新电影数据
        
        Args:
            movie_data: 电影数据字典
            
        Returns:
            是否成功插入/更新
        """
        try:
            self.cursor.execute('''
                INSERT INTO movies (
                    title_spanish, title_original, year, rating, quality, url
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title_spanish = excluded.title_spanish,
                    title_original = excluded.title_original,
                    year = excluded.year,
                    rating = excluded.rating,
                    quality = excluded.quality,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                movie_data.get('title_spanish'),
                movie_data.get('title_original'),
                movie_data.get('year'),
                movie_data.get('rating'),
                movie_data.get('quality'),
                movie_data.get('url')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ 插入电影数据失败: {e}")
            self.conn.rollback()
            return False
    
    def insert_tv_series(self, tv_data: Dict) -> bool:
        """
        插入或更新电视剧数据
        
        Args:
            tv_data: 电视剧数据字典
            
        Returns:
            是否成功插入/更新
        """
        try:
            self.cursor.execute('''
                INSERT INTO tv_series (
                    title_spanish, title_original, year, rating, quality, 
                    season, episode, url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title_spanish = excluded.title_spanish,
                    title_original = excluded.title_original,
                    year = excluded.year,
                    rating = excluded.rating,
                    quality = excluded.quality,
                    season = excluded.season,
                    episode = excluded.episode,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                tv_data.get('title_spanish'),
                tv_data.get('title_original'),
                tv_data.get('year'),
                tv_data.get('rating'),
                tv_data.get('quality'),
                tv_data.get('season'),
                tv_data.get('episode'),
                tv_data.get('url')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ 插入电视剧数据失败: {e}")
            self.conn.rollback()
            return False
    
    def bulk_insert_movies(self, movies: List[Dict]) -> int:
        """
        批量插入电影数据
        
        Args:
            movies: 电影数据列表
            
        Returns:
            成功插入的数量
        """
        success_count = 0
        for movie in movies:
            if self.insert_movie(movie):
                success_count += 1
        return success_count
    
    def bulk_insert_tv_series(self, tv_series_list: List[Dict]) -> int:
        """
        批量插入电视剧数据
        
        Args:
            tv_series_list: 电视剧数据列表
            
        Returns:
            成功插入的数量
        """
        success_count = 0
        for tv_data in tv_series_list:
            if self.insert_tv_series(tv_data):
                success_count += 1
        return success_count
    
    def movie_exists(self, url: str) -> bool:
        """
        检查电影是否已存在
        
        Args:
            url: 电影URL
            
        Returns:
            是否存在
        """
        self.cursor.execute('SELECT 1 FROM movies WHERE url = ?', (url,))
        return self.cursor.fetchone() is not None
    
    def tv_series_exists(self, url: str) -> bool:
        """
        检查电视剧剧集是否已存在
        
        Args:
            url: 剧集URL
            
        Returns:
            是否存在
        """
        self.cursor.execute('SELECT 1 FROM tv_series WHERE url = ?', (url,))
        return self.cursor.fetchone() is not None
    
    def get_movies_count(self) -> int:
        """获取电影总数"""
        self.cursor.execute('SELECT COUNT(*) FROM movies')
        return self.cursor.fetchone()[0]
    
    def get_tv_series_count(self) -> int:
        """获取电视剧剧集总数"""
        self.cursor.execute('SELECT COUNT(*) FROM tv_series')
        return self.cursor.fetchone()[0]
    
    def get_movies_by_year(self, year: int) -> List[Dict]:
        """
        获取指定年份的电影
        
        Args:
            year: 年份
            
        Returns:
            电影列表
        """
        self.cursor.execute('SELECT * FROM movies WHERE year = ?', (year,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_latest_movies(self, limit: int = 10) -> List[Dict]:
        """
        获取最新添加的电影
        
        Args:
            limit: 数量限制
            
        Returns:
            电影列表
        """
        self.cursor.execute('''
            SELECT * FROM movies 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_latest_tv_series(self, limit: int = 10) -> List[Dict]:
        """
        获取最新添加的电视剧剧集
        
        Args:
            limit: 数量限制
            
        Returns:
            剧集列表
        """
        self.cursor.execute('''
            SELECT * FROM tv_series 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in self.cursor.fetchall()]
    
    def export_to_csv(self, table: str, output_file: str):
        """
        导出数据到 CSV
        
        Args:
            table: 表名 ('movies' 或 'tv_series')
            output_file: 输出文件路径
        """
        import csv
        
        self.cursor.execute(f'SELECT * FROM {table}')
        rows = self.cursor.fetchall()
        
        if not rows:
            print(f"⚠️  表 {table} 中没有数据")
            return
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # 写入表头
            writer.writerow([description[0] for description in self.cursor.description])
            # 写入数据
            writer.writerows(rows)
        
        print(f"✅ 数据已导出到: {output_file}")
    
    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        stats = {}
        
        # 电影统计
        self.cursor.execute('SELECT COUNT(*) FROM movies')
        stats['total_movies'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(DISTINCT year) FROM movies')
        stats['movie_years'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT AVG(rating) FROM movies WHERE rating IS NOT NULL')
        avg_rating = self.cursor.fetchone()[0]
        stats['avg_movie_rating'] = round(avg_rating, 2) if avg_rating else 0
        
        # 电视剧统计
        self.cursor.execute('SELECT COUNT(*) FROM tv_series')
        stats['total_tv_episodes'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT COUNT(DISTINCT title_spanish) FROM tv_series')
        stats['unique_tv_shows'] = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT AVG(rating) FROM tv_series WHERE rating IS NOT NULL')
        avg_rating = self.cursor.fetchone()[0]
        stats['avg_tv_rating'] = round(avg_rating, 2) if avg_rating else 0
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()


if __name__ == "__main__":
    # 测试数据库模块
    with Database("test_cuevana3.db") as db:
        print("✅ 数据库创建成功")
        
        # 测试插入电影
        test_movie = {
            'title_spanish': '测试电影',
            'title_original': 'Test Movie',
            'year': 2025,
            'rating': 8.5,
            'quality': 'HD',
            'url': 'https://test.com/movie/1'
        }
        db.insert_movie(test_movie)
        print(f"✅ 电影数量: {db.get_movies_count()}")
        
        # 测试插入电视剧
        test_tv = {
            'title_spanish': '测试剧集',
            'title_original': 'Test Series',
            'year': 2025,
            'rating': 9.0,
            'quality': 'HD',
            'season': 1,
            'episode': 1,
            'url': 'https://test.com/series/1x1'
        }
        db.insert_tv_series(test_tv)
        print(f"✅ 电视剧剧集数量: {db.get_tv_series_count()}")
        
        # 获取统计信息
        stats = db.get_statistics()
        print("\n📊 数据库统计:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # 清理测试数据库
    os.remove("test_cuevana3.db")
    print("\n✅ 测试完成")
