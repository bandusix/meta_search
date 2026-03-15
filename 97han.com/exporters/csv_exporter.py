#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV导出器
"""

import csv
import os
import sqlite3
from datetime import datetime
from pathlib import Path


class CSVExporter:
    """CSV导出器"""
    
    def __init__(self, db_path='spider.db', output_dir='./exports'):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_movies(self, export_type='full'):
        """导出电影"""
        return self._export_table('movies', export_type)
    
    def export_tv_series(self, export_type='full'):
        """导出电视剧"""
        return self._export_table('tv_series', export_type)
    
    def export_tv_episodes(self, export_type='full'):
        """导出电视剧集数"""
        return self._export_table('tv_episodes', export_type)
    
    def _export_table(self, table_name, export_type='full'):
        """导出指定表"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{table_name}_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        with sqlite3.connect(self.db_path) as conn:
            # 构建查询
            if export_type == 'incremental':
                last_time = self._get_last_export_time(conn, table_name)
                query = f"SELECT * FROM {table_name} WHERE created_at > ?"
                params = (last_time,)
            else:
                query = f"SELECT * FROM {table_name}"
                params = ()
            
            # 执行导出
            try:
                cursor = conn.execute(query, params)
                if cursor.description:
                    headers = [d[0] for d in cursor.description]
                    
                    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        
                        row_count = 0
                        for row in cursor:
                            writer.writerow(row)
                            row_count += 1
                    
                    # 记录日志
                    self._record_export_log(conn, table_name, export_type, filepath, row_count)
                    print(f"导出完成: {filepath} ({row_count}条记录)")
                    return filepath, row_count
                else:
                    print(f"表 {table_name} 为空或不存在")
                    return None, 0
            except sqlite3.OperationalError as e:
                print(f"导出错误: {e}")
                return None, 0
        
    
    def _get_last_export_time(self, conn, table_name):
        """获取上次导出时间"""
        try:
            cursor = conn.execute("""
                SELECT created_at FROM export_logs 
                WHERE table_name = ? AND status = 'success'
                ORDER BY created_at DESC LIMIT 1
            """, (table_name,))
            result = cursor.fetchone()
            return result[0] if result else '1970-01-01 00:00:00'
        except sqlite3.OperationalError:
            return '1970-01-01 00:00:00'
    
    def _record_export_log(self, conn, table_name, export_type, filepath, row_count):
        """记录导出日志"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS export_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                export_type TEXT NOT NULL,
                filepath TEXT NOT NULL,
                row_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'success',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT INTO export_logs (table_name, export_type, filepath, row_count)
            VALUES (?, ?, ?, ?)
        """, (table_name, export_type, str(filepath), row_count))
        conn.commit()
    
    def export_all(self):
        """导出所有数据"""
        results = {}
        results['movies'] = self.export_movies('full')
        results['tv_series'] = self.export_tv_series('full')
        results['tv_episodes'] = self.export_tv_episodes('full')
        return results
