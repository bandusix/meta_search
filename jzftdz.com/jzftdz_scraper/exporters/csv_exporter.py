# -*- coding: utf-8 -*-
"""
exporters/csv_exporter.py

Exports data from the database to CSV files.
"""

import csv
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class CSVExporter:
    """Handles exporting database data to CSV format."""
    
    def __init__(self, db_manager, output_dir, encoding='utf-8-sig'):
        """
        Initializes the CSVExporter.
        
        Args:
            db_manager: DatabaseManager instance.
            output_dir (str): Directory where CSV files will be saved.
            encoding (str): Encoding for CSV files (default: utf-8-sig for Excel compatibility).
        """
        self.db = db_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.encoding = encoding
    
    def export_movies(self, export_type='full'):
        """
        Exports movies to a CSV file.
        
        Args:
            export_type (str): 'full' for all data, 'incremental' for new data since last export.
        
        Returns:
            str: Path to the generated CSV file.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"movies_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        # Build query based on export type
        if export_type == 'incremental':
            last_export_time = self.db.get_last_export_time('movies')
            query = f"SELECT * FROM movies WHERE updated_at > '{last_export_time}' ORDER BY id"
        else:
            query = "SELECT * FROM movies ORDER BY id"
        
        cursor = self.db.conn.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning("No movie data to export.")
            return None
        
        # Write to CSV
        with open(filepath, 'w', newline='', encoding=self.encoding) as csvfile:
            writer = csv.writer(csvfile)
            # Write header
            writer.writerow([description[0] for description in cursor.description])
            # Write data
            writer.writerows(rows)
        
        row_count = len(rows)
        self.db.log_export('movies', export_type, filepath, row_count)
        logger.info(f"Exported {row_count} movies to {filepath}")
        
        return str(filepath)
    
    def export_tv_series(self, export_type='full'):
        """
        Exports TV series to a CSV file.
        
        Args:
            export_type (str): 'full' for all data, 'incremental' for new data since last export.
        
        Returns:
            str: Path to the generated CSV file.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tv_series_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        if export_type == 'incremental':
            last_export_time = self.db.get_last_export_time('tv_series')
            query = f"SELECT * FROM tv_series WHERE updated_at > '{last_export_time}' ORDER BY id"
        else:
            query = "SELECT * FROM tv_series ORDER BY id"
        
        cursor = self.db.conn.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning("No TV series data to export.")
            return None
        
        with open(filepath, 'w', newline='', encoding=self.encoding) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([description[0] for description in cursor.description])
            writer.writerows(rows)
        
        row_count = len(rows)
        self.db.log_export('tv_series', export_type, filepath, row_count)
        logger.info(f"Exported {row_count} TV series to {filepath}")
        
        return str(filepath)
    
    def export_tv_episodes(self, export_type='full'):
        """
        Exports TV episodes to a CSV file.
        
        Args:
            export_type (str): 'full' for all data, 'incremental' for new data.
        
        Returns:
            str: Path to the generated CSV file.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tv_episodes_{export_type}_{timestamp}.csv"
        filepath = self.output_dir / filename
        
        query = "SELECT * FROM tv_episodes ORDER BY series_vod_id, source_name, episode_num"
        
        cursor = self.db.conn.execute(query)
        rows = cursor.fetchall()
        
        if not rows:
            logger.warning("No TV episode data to export.")
            return None
        
        with open(filepath, 'w', newline='', encoding=self.encoding) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([description[0] for description in cursor.description])
            writer.writerows(rows)
        
        row_count = len(rows)
        self.db.log_export('tv_episodes', export_type, filepath, row_count)
        logger.info(f"Exported {row_count} TV episodes to {filepath}")
        
        return str(filepath)
    
    def export_all(self, export_type='full'):
        """
        Exports all tables to CSV files.
        
        Args:
            export_type (str): 'full' or 'incremental'.
        
        Returns:
            dict: Paths to all generated CSV files.
        """
        return {
            'movies': self.export_movies(export_type),
            'tv_series': self.export_tv_series(export_type),
            'tv_episodes': self.export_tv_episodes(export_type)
        }
