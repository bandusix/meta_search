# -*- coding: utf-8 -*-
"""
exporters/excel_exporter.py

Exports data from the database to Excel (.xlsx) files using pandas.
Supports both full (stock) and incremental exports.
"""

import logging
import pandas as pd
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Handles exporting database data to Excel format."""
    
    def __init__(self, db_manager, output_dir):
        """
        Initializes the ExcelExporter.
        
        Args:
            db_manager: DatabaseManager instance.
            output_dir (str): Directory where Excel files will be saved.
        """
        self.db = db_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def export(self, export_type='full'):
        """
        Exports data to an Excel file.
        
        Args:
            export_type (str): 'full' for all data, 'incremental' for new data since last export.
        
        Returns:
            str: Path to the generated Excel file, or None if no data.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"jzftdz_data_{export_type}_{timestamp}.xlsx"
        filepath = self.output_dir / filename
        
        has_data = False
        
        try:
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # 1. Export Movies (with Play URL)
                if self._export_movies_to_sheet(writer, 'Movies', export_type, filepath):
                    has_data = True
                
                # 2. Export Movie Sources
                if self._export_movie_sources_to_sheet(writer, 'Movie Sources', export_type, filepath):
                    has_data = True

                # 3. Export TV Series Episodes (Merged)
                if self._export_tv_merged_to_sheet(writer, 'TV Series Episodes', export_type, filepath):
                    has_data = True
                    
                # 4. (Optional) Export TV Series Metadata only if needed, but user requested merge.
                # We can keep the separate sheet or remove it. User said "merge... so search efficiency is higher".
                # I'll keep the separate series sheet for reference but focus on the merged one.
                if self._export_table_to_sheet(writer, 'tv_series', 'TV Series Metadata', export_type, filepath):
                    has_data = True

            if has_data:
                logger.info(f"Successfully exported {export_type} data to {filepath}")
                return str(filepath)
            else:
                logger.info(f"No {export_type} data found to export.")
                # Remove empty file
                if filepath.exists():
                    filepath.unlink()
                return None

        except Exception as e:
            logger.error(f"Failed to export Excel file: {e}", exc_info=True)
            return None

    def _export_movies_to_sheet(self, writer, sheet_name, export_type, filepath):
        """Helper to export movies with play_url."""
        # Join with movie_sources to get the first play_url
        query = """
            SELECT m.*, s.play_url 
            FROM movies m
            LEFT JOIN (
                SELECT movie_vod_id, play_url 
                FROM movie_sources 
                GROUP BY movie_vod_id
            ) s ON m.vod_id = s.movie_vod_id
        """
        params = []
        
        if export_type == 'incremental':
            last_export_time = self.db.get_last_export_time('movies')
            query += " WHERE m.updated_at > ?"
            params.append(last_export_time)
        
        query += " ORDER BY m.id"
        
        df = pd.read_sql_query(query, self.db.conn, params=params)
        
        if not df.empty:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            self.db.log_export('movies', export_type, str(filepath), len(df))
            logger.info(f"Added {len(df)} rows to sheet '{sheet_name}'")
            return True
        return False

    def _export_movie_sources_to_sheet(self, writer, sheet_name, export_type, filepath):
        """Helper to export movie sources."""
        query = "SELECT * FROM movie_sources"
        params = []
        
        if export_type == 'incremental':
            # Get sources belonging to movies that were updated recently
            last_export_time = self.db.get_last_export_time('movies')
            query = """
                SELECT s.* FROM movie_sources s
                JOIN movies m ON s.movie_vod_id = m.vod_id
                WHERE m.updated_at > ?
            """
            params.append(last_export_time)
            
        query += " ORDER BY movie_vod_id"
        
        df = pd.read_sql_query(query, self.db.conn, params=params)
        
        if not df.empty:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            # Log under movie_sources
            self.db.log_export('movie_sources', export_type, str(filepath), len(df))
            logger.info(f"Added {len(df)} rows to sheet '{sheet_name}'")
            return True
        return False

    def _export_tv_merged_to_sheet(self, writer, sheet_name, export_type, filepath):
        """Helper to export merged TV series and episodes data."""
        # Join tv_series and tv_episodes
        query = """
            SELECT 
                s.vod_id as series_id, s.title as series_title, s.poster_url, s.year, s.category, s.region, 
                s.director, s.actors, s.status_text, s.total_episodes,
                e.source_name, e.episode_num, e.episode_title, e.play_url
            FROM tv_series s
            JOIN tv_episodes e ON s.vod_id = e.series_vod_id
        """
        params = []
        
        if export_type == 'incremental':
            last_export_time = self.db.get_last_export_time('tv_series')
            query += " WHERE s.updated_at > ?"
            params.append(last_export_time)
            
        query += " ORDER BY s.vod_id, e.source_name, e.episode_num"
        
        df = pd.read_sql_query(query, self.db.conn, params=params)
        
        if not df.empty:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            # Log under tv_episodes as it contains the bulk of data
            self.db.log_export('tv_episodes_merged', export_type, str(filepath), len(df))
            logger.info(f"Added {len(df)} rows to sheet '{sheet_name}'")
            return True
        return False

    def _export_table_to_sheet(self, writer, table_name, sheet_name, export_type, filepath):
        """Helper to export a table to an Excel sheet."""
        query = f"SELECT * FROM {table_name}"
        params = []
        
        if export_type == 'incremental':
            last_export_time = self.db.get_last_export_time(table_name)
            query += " WHERE updated_at > ?"
            params.append(last_export_time)
        
        query += " ORDER BY id"
        
        df = pd.read_sql_query(query, self.db.conn, params=params)
        
        if not df.empty:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            self.db.log_export(table_name, export_type, str(filepath), len(df))
            logger.info(f"Added {len(df)} rows to sheet '{sheet_name}'")
            return True
        return False

    def _export_episodes_to_sheet(self, writer, sheet_name, export_type, filepath):
        """Helper to export TV episodes."""
        # For episodes, if full export, just dump all.
        # If incremental, strictly speaking we should only dump new episodes.
        # But since we clear/re-insert episodes on update, we can just fetch all episodes
        # for the series that were updated.
        
        query = "SELECT * FROM tv_episodes"
        params = []
        
        if export_type == 'incremental':
            # Get episodes belonging to series that were updated recently
            last_export_time = self.db.get_last_export_time('tv_series')
            query = """
                SELECT e.* FROM tv_episodes e
                JOIN tv_series s ON e.series_vod_id = s.vod_id
                WHERE s.updated_at > ?
            """
            params.append(last_export_time)
        
        query += " ORDER BY series_vod_id, source_name, episode_num"
        
        df = pd.read_sql_query(query, self.db.conn, params=params)
        
        if not df.empty:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            # We log this under 'tv_episodes' even though it's triggered by series update
            self.db.log_export('tv_episodes', export_type, str(filepath), len(df))
            logger.info(f"Added {len(df)} rows to sheet '{sheet_name}'")
            return True
        return False
