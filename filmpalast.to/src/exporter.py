import sys
import os
import logging
from typing import List, Dict

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from src.database import DatabaseManager

class DataExporter:
    """数据导出器"""

    def __init__(self, db_path: str = "data/database.db", export_dir: str = "exports"):
        # 使用绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_path = os.path.join(base_dir, db_path)
        self.export_dir = os.path.join(base_dir, export_dir)
        
        self.db_manager = DatabaseManager(self.db_path)
        self.ensure_export_dir()
        
        # 日志配置
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def ensure_export_dir(self):
        """确保导出目录存在"""
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def export_to_excel(self) -> str:
        """导出数据到Excel文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"filmpalast_data_{timestamp}.xlsx"
        filepath = os.path.join(self.export_dir, filename)

        try:
            # 1. 获取电影数据
            self.logger.info("正在获取电影数据...")
            movies_data = self.db_manager.get_all_movies()
            movies_columns = [
                'ID', 'Title', 'Original Title', 'URL', 'Poster URL', 'Year',
                'Rating', 'IMDb Rating', 'Quality', 'Release Title',
                'Views', 'Votes', 'Duration', 'Description', 'Created At',
                'Last Crawled'
            ]
            df_movies = pd.DataFrame(movies_data, columns=movies_columns)

            # 2. 获取剧集数据
            self.logger.info("正在获取剧集数据...")
            episodes_data = self.db_manager.get_all_episodes()
            episodes_columns = [
                'ID', 'Series Title', 'Episode Title', 'Original Title', 'URL',
                'Poster URL', 'Year', 'Rating', 'IMDb Rating', 'Quality',
                'Season', 'Episode', 'Release Title', 'Views', 'Votes',
                'Description', 'Created At', 'Last Crawled'
            ]
            df_episodes = pd.DataFrame(episodes_data, columns=episodes_columns)

            # 3. 写入Excel
            self.logger.info(f"正在写入Excel文件: {filepath}")
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df_movies.to_excel(writer, sheet_name='Movies', index=False)
                df_episodes.to_excel(writer, sheet_name='TV Episodes', index=False)

            self.logger.info(f"数据成功导出到: {filepath}")
            self.logger.info(f"电影数量: {len(df_movies)}")
            self.logger.info(f"剧集数量: {len(df_episodes)}")
            
            return filepath

        except Exception as e:
            self.logger.error(f"导出失败: {e}")
            raise e

if __name__ == "__main__":
    exporter = DataExporter()
    exporter.export_to_excel()
