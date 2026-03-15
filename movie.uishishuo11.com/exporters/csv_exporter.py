#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据导出器 (CSV/Excel)
"""

import csv
import os
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path


class DataExporter:
    """数据导出器"""
    
    def __init__(self, db_path='spider.db', output_dir='./exports'):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export_movies(self, export_type='full', file_format='csv'):
        """导出电影"""
        return self._export_table('movies', export_type, file_format)
    
    def export_tv(self, export_type='full', file_format='csv'):
        """导出电视剧"""
        return self._export_table('tv', export_type, file_format)
    
    def _export_table(self, table_name, export_type='full', file_format='csv'):
        """导出指定表"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = 'xlsx' if file_format == 'excel' else 'csv'
        filename = f"{table_name}_{export_type}_{timestamp}.{ext}"
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
            
            row_count = 0
            try:
                if file_format == 'excel':
                    # 使用Pandas导出Excel
                    df = pd.read_sql_query(query, conn, params=params)
                    if not df.empty:
                        df.to_excel(filepath, index=False)
                        row_count = len(df)
                else:
                    # 默认CSV导出
                    cursor = conn.execute(query, params)
                    headers = [d[0] for d in cursor.description]
                    
                    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        
                        for row in cursor:
                            writer.writerow(row)
                            row_count += 1
                
                # 记录日志
                self._record_export_log(conn, table_name, export_type, filepath, row_count)
                
            except Exception as e:
                print(f"导出失败 {table_name}: {e}")
                return None, 0
        
        print(f"导出完成: {filepath} ({row_count}条记录)")
        return filepath, row_count
    
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
