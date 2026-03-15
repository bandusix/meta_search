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
    
    def _table_exists(self, conn, table_name):
        """检查表是否存在"""
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
        return cursor.fetchone()[0] > 0

    def export_movies(self, export_type='full'):
        """导出电影数据
        
        Args:
            export_type: 'full' 或 'incremental'
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"movies_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with sqlite3.connect(self.db_path) as conn:
            if not self._table_exists(conn, 'movies'):
                print(f"⚠️ 表 'movies' 不存在，跳过导出")
                return None

            cursor = conn.cursor()
            
            # Ensure export_logs table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS export_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    export_type TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    row_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            if export_type == 'incremental':
                # 获取上次导出时间
                cursor.execute("""
                    SELECT MAX(created_at) FROM export_logs 
                    WHERE table_name='movies' AND export_type='incremental'
                """)
                result = cursor.fetchone()
                last_export = result[0] if result else None
                
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
            if not self._table_exists(conn, 'tv_series'):
                print(f"⚠️ 表 'tv_series' 不存在，跳过导出")
                return None

            cursor = conn.cursor()
            
            # Ensure export_logs table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS export_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    export_type TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    row_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            if export_type == 'incremental':
                cursor.execute("""
                    SELECT MAX(created_at) FROM export_logs 
                    WHERE table_name='tv_series' AND export_type='incremental'
                """)
                result = cursor.fetchone()
                last_export = result[0] if result else None
                
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
            if not self._table_exists(conn, 'tv_episodes'):
                print(f"⚠️ 表 'tv_episodes' 不存在，跳过导出")
                return None

            cursor = conn.cursor()
            
            # Ensure export_logs table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS export_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    export_type TEXT NOT NULL,
                    filepath TEXT NOT NULL,
                    row_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'success',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            if export_type == 'incremental':
                cursor.execute("""
                    SELECT MAX(created_at) FROM export_logs 
                    WHERE table_name='tv_episodes' AND export_type='incremental'
                """)
                result = cursor.fetchone()
                last_export = result[0] if result else None
                
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
