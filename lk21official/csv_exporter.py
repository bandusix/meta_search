import pandas as pd
import sqlite3
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVExporter:
    """CSV 导出类"""
    
    def __init__(self, db_path: str, export_dir: str = "exports"):
        """
        初始化导出器
        
        Args:
            db_path: 数据库文件路径
            export_dir: 导出目录
        """
        self.db_path = db_path
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_timestamp(self) -> str:
        """获取时间戳字符串"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _export_dataframe(self, df: pd.DataFrame, base_filename: str, fmt: str = 'csv') -> str:
        """
        导出 DataFrame 到指定格式
        
        Args:
            df: Pandas DataFrame
            base_filename: 基础文件名（不含扩展名）
            fmt: 导出格式 ('csv' 或 'excel')
            
        Returns:
            导出文件路径
        """
        timestamp = self._get_timestamp()
        
        if fmt == 'excel':
            filename = f"{base_filename}_{timestamp}.xlsx"
            filepath = self.export_dir / filename
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            filename = f"{base_filename}_{timestamp}.csv"
            filepath = self.export_dir / filename
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
        logger.info(f"✅ 导出完成: {filepath}")
        logger.info(f"   共导出 {len(df)} 部电影")
        
        return str(filepath)

    def export_all_movies(self, fmt: str = 'csv') -> str:
        """
        导出所有电影（存量）
        
        Args:
            fmt: 导出格式 ('csv' 或 'excel')
            
        Returns:
            导出文件路径
        """
        logger.info(f"开始导出所有电影 ({fmt})...")
        
        conn = sqlite3.connect(self.db_path)
        
        # 查询所有电影
        query = """
        SELECT 
            id,
            title,
            type,
            title_original,
            year,
            rating,
            quality,
            resolution,
            duration,
            image_url,
            movie_url,
            page_title,
            url_slug,
            genre,
            country,
            description,
            created_at,
            updated_at
        FROM movies
        ORDER BY year DESC, created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return self._export_dataframe(df, "lk21_movies_all", fmt)
    
    def export_incremental_movies(self, days: int = 1, fmt: str = 'csv') -> str:
        """
        导出增量电影（最近N天新增）
        
        Args:
            days: 天数
            fmt: 导出格式 ('csv' 或 'excel')
            
        Returns:
            导出文件路径
        """
        logger.info(f"开始导出最近 {days} 天新增的电影 ({fmt})...")
        
        conn = sqlite3.connect(self.db_path)
        
        # 查询最近N天新增的电影
        query = f"""
        SELECT 
            id,
            title,
            type,
            title_original,
            year,
            rating,
            quality,
            resolution,
            duration,
            image_url,
            movie_url,
            page_title,
            url_slug,
            genre,
            country,
            description,
            created_at,
            updated_at
        FROM movies
        WHERE created_at >= datetime('now', '-{days} days')
        ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return self._export_dataframe(df, f"lk21_movies_incremental_{days}days", fmt)
    
    def export_by_year(self, year: int, fmt: str = 'csv') -> str:
        """
        导出指定年份的电影
        
        Args:
            year: 年份
            fmt: 导出格式 ('csv' 或 'excel')
            
        Returns:
            导出文件路径
        """
        logger.info(f"开始导出 {year} 年的电影 ({fmt})...")
        
        conn = sqlite3.connect(self.db_path)
        
        # 查询指定年份的电影
        query = """
        SELECT 
            id,
            title,
            type,
            title_original,
            year,
            rating,
            quality,
            resolution,
            duration,
            image_url,
            movie_url,
            page_title,
            url_slug,
            genre,
            country,
            description,
            created_at,
            updated_at
        FROM movies
        WHERE year = ?
        ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn, params=(year,))
        conn.close()
        
        return self._export_dataframe(df, f"lk21_movies_{year}", fmt)


# 使用示例
if __name__ == "__main__":
    exporter = CSVExporter(db_path="lk21.db", export_dir="exports")
    
    # 导出所有电影
    exporter.export_all_movies()
    
    # 导出最近1天新增的电影
    exporter.export_incremental_movies(days=1)
    
    # 导出2025年的电影
    exporter.export_by_year(2025)
