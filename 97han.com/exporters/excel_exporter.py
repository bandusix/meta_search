#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel导出器
"""

import os
import sqlite3
from datetime import datetime
from pathlib import Path
import openpyxl
from openpyxl.utils import get_column_letter


class ExcelExporter:
    """Excel导出器"""
    
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
        filename = f"{table_name}_{export_type}_{timestamp}.xlsx"
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
                    
                    # 创建Excel工作簿
                    wb = openpyxl.Workbook()
                    ws = wb.active
                    ws.title = table_name
                    
                    # 写入表头
                    ws.append(headers)
                    
                    row_count = 0
                    for row in cursor:
                        # 处理可能的非法字符
                        cleaned_row = []
                        for cell in row:
                            if isinstance(cell, str):
                                # 移除可能导致Excel报错的非法字符
                                cleaned_row.append(''.join(c for c in cell if c.isprintable()))
                            else:
                                cleaned_row.append(cell)
                        ws.append(cleaned_row)
                        row_count += 1
                    
                    # 自动调整列宽 (简单的估算)
                    for col in ws.columns:
                        max_length = 0
                        column = col[0].column_letter # Get the column name
                        for cell in col:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = (max_length + 2) * 1.2
                        # 限制最大宽度，避免过宽
                        adjusted_width = min(adjusted_width, 50)
                        ws.column_dimensions[column].width = adjusted_width

                    wb.save(filepath)
                    
                    # 记录日志
                    self._record_export_log(conn, table_name, export_type, filepath, row_count)
                    print(f"Excel导出完成: {filepath} ({row_count}条记录)")
                    return filepath, row_count
                else:
                    print(f"表 {table_name} 为空或不存在")
                    return None, 0
            except sqlite3.OperationalError as e:
                print(f"导出错误: {e}")
                return None, 0
            except Exception as e:
                print(f"Excel写入错误: {e}")
                return None, 0
        
    
    def _get_last_export_time(self, conn, table_name):
        """获取上次导出时间"""
        try:
            cursor = conn.execute("""
                SELECT created_at FROM export_logs 
                WHERE table_name = ? AND status = 'success' AND filepath LIKE '%.xlsx'
                ORDER BY created_at DESC LIMIT 1
            """, (table_name,))
            result = cursor.fetchone()
            return result[0] if result else '1970-01-01 00:00:00'
        except sqlite3.OperationalError:
            return '1970-01-01 00:00:00'
    
    def _record_export_log(self, conn, table_name, export_type, filepath, row_count):
        """记录导出日志"""
        # 确保表存在 (CSV导出器可能已经创建了)
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
