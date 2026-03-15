# -*- coding: utf-8 -*-
"""
core/database.py

Handles all database interactions for the scraper, including table creation,
data insertion/updating (upserting), and progress management.
"""

import sqlite3
import logging
import threading
from pathlib import Path

# Get a logger for this module
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages the SQLite database connection and operations."""

    def __init__(self, db_path):
        """
        Initializes the DatabaseManager.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self.lock = threading.Lock()

    def connect(self):
        """Establishes a connection to the database."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            logger.info(f"Successfully connected to database at '{self.db_path}'")
        except sqlite3.Error as e:
            logger.critical(f"Database connection failed: {e}")
            raise

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")

    def create_tables(self):
        """Creates all necessary tables if they don't exist."""
        if not self.conn:
            self.connect()

        try:
            with self.conn:
                self.conn.executescript('''
                    -- Enable foreign key support
                    PRAGMA foreign_keys = ON;

                    -- Movies table
                    CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vod_id INTEGER UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        poster_url TEXT,
                        year INTEGER,
                        rating REAL,
                        rating_text TEXT,
                        category TEXT,
                        region TEXT,
                        director TEXT,
                        actors TEXT,
                        synopsis TEXT,
                        detail_url TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Movie sources table
                    CREATE TABLE IF NOT EXISTS movie_sources (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        movie_vod_id INTEGER NOT NULL,
                        source_name TEXT NOT NULL,
                        play_url TEXT NOT NULL UNIQUE,
                        quality TEXT,
                        FOREIGN KEY (movie_vod_id) REFERENCES movies(vod_id) ON DELETE CASCADE
                    );

                    -- TV series table
                    CREATE TABLE IF NOT EXISTS tv_series (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        vod_id INTEGER UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        poster_url TEXT,
                        year INTEGER,
                        rating REAL,
                        rating_text TEXT,
                        category TEXT,
                        region TEXT,
                        director TEXT,
                        actors TEXT,
                        synopsis TEXT,
                        status_text TEXT,
                        total_episodes INTEGER,
                        detail_url TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- TV episodes table
                    CREATE TABLE IF NOT EXISTS tv_episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        series_vod_id INTEGER NOT NULL,
                        source_name TEXT NOT NULL,
                        episode_num INTEGER NOT NULL,
                        episode_title TEXT,
                        play_url TEXT NOT NULL UNIQUE,
                        FOREIGN KEY (series_vod_id) REFERENCES tv_series(vod_id) ON DELETE CASCADE
                    );

                    -- Crawl progress table
                    CREATE TABLE IF NOT EXISTS crawl_progress (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_key TEXT UNIQUE NOT NULL, -- e.g., "movie_2025_1"
                        category_id INTEGER NOT NULL,
                        year INTEGER NOT NULL,
                        current_page INTEGER DEFAULT 1,
                        status TEXT DEFAULT 'pending' -- pending, running, completed, failed
                    );

                    -- Export logs table
                    CREATE TABLE IF NOT EXISTS export_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT NOT NULL,
                        export_type TEXT NOT NULL, -- full, incremental
                        filepath TEXT NOT NULL,
                        row_count INTEGER DEFAULT 0,
                        status TEXT DEFAULT 'success',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

                    -- Create indexes for performance
                    CREATE INDEX IF NOT EXISTS idx_movies_vod_id ON movies(vod_id);
                    CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);
                    CREATE INDEX IF NOT EXISTS idx_tv_series_vod_id ON tv_series(vod_id);
                    CREATE INDEX IF NOT EXISTS idx_tv_series_year ON tv_series(year);
                    CREATE INDEX IF NOT EXISTS idx_episodes_series_id ON tv_episodes(series_vod_id);
                    CREATE INDEX IF NOT EXISTS idx_sources_movie_id ON movie_sources(movie_vod_id);
                ''')
            logger.info("All database tables created or verified successfully.")
        except sqlite3.Error as e:
            logger.error(f"Failed to create tables: {e}")
            raise

    def upsert_movie(self, movie_data):
        """
        Inserts a new movie or updates an existing one based on vod_id.
        Handles related data in the movie_sources table.
        """
        with self.lock:
            if not self.conn:
                self.connect()

            movie_fields = ['vod_id', 'title', 'poster_url', 'year', 'rating', 'rating_text',
                            'category', 'region', 'director', 'actors', 'synopsis', 'detail_url']
            
            # Prepare data for the main movie table
            movie_tuple = tuple(movie_data.get(f) for f in movie_fields)

            try:
                with self.conn:
                    # Upsert into movies table
                    cursor = self.conn.execute('''
                        INSERT INTO movies (vod_id, title, poster_url, year, rating, rating_text, category, region, director, actors, synopsis, detail_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(vod_id) DO UPDATE SET
                            title=excluded.title,
                            poster_url=excluded.poster_url,
                            year=excluded.year,
                            rating=excluded.rating,
                            rating_text=excluded.rating_text,
                            category=excluded.category,
                            region=excluded.region,
                            director=excluded.director,
                            actors=excluded.actors,
                            synopsis=excluded.synopsis,
                            updated_at=CURRENT_TIMESTAMP;
                    ''', movie_tuple)

                    # Handle movie sources
                    sources = movie_data.get('sources', [])
                    if sources:
                        # First, clear old sources for this movie to handle updates
                        self.conn.execute("DELETE FROM movie_sources WHERE movie_vod_id = ?", (movie_data['vod_id'],))

                        # Insert new sources
                        for source in sources:
                            for episode in source.get('episodes', []):
                                self.conn.execute('''
                                    INSERT INTO movie_sources (movie_vod_id, source_name, play_url, quality)
                                    VALUES (?, ?, ?, ?)
                                    ON CONFLICT(play_url) DO NOTHING;
                                ''', (movie_data['vod_id'], source['source_name'], episode['url'], episode['title']))
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                logger.warning(f"Integrity error for movie {movie_data.get('vod_id')}: {e}")
            except sqlite3.Error as e:
                logger.error(f"Failed to upsert movie {movie_data.get('vod_id')}: {e}")
            return None

    def upsert_tv_series(self, series_data):
        """
        Inserts a new TV series or updates an existing one.
        Handles related episodes in the tv_episodes table.
        """
        with self.lock:
            if not self.conn:
                self.connect()

            series_fields = ['vod_id', 'title', 'poster_url', 'year', 'rating', 'rating_text',
                             'category', 'region', 'director', 'actors', 'synopsis',
                             'status_text', 'total_episodes', 'detail_url']
            series_tuple = tuple(series_data.get(f) for f in series_fields)

            try:
                with self.conn:
                    # Upsert into tv_series table
                    cursor = self.conn.execute('''
                        INSERT INTO tv_series (vod_id, title, poster_url, year, rating, rating_text, category, region, director, actors, synopsis, status_text, total_episodes, detail_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(vod_id) DO UPDATE SET
                            title=excluded.title,
                            poster_url=excluded.poster_url,
                            year=excluded.year,
                            rating=excluded.rating,
                            rating_text=excluded.rating_text,
                            category=excluded.category,
                            region=excluded.region,
                            director=excluded.director,
                            actors=excluded.actors,
                            synopsis=excluded.synopsis,
                            status_text=excluded.status_text,
                            total_episodes=excluded.total_episodes,
                            updated_at=CURRENT_TIMESTAMP;
                    ''', series_tuple)

                    # Handle episodes
                    sources = series_data.get('sources', [])
                    if sources:
                        # A simple approach: clear and re-insert. For large-scale apps, a more granular update would be better.
                        self.conn.execute("DELETE FROM tv_episodes WHERE series_vod_id = ?", (series_data['vod_id'],))

                        for source in sources:
                            for i, episode in enumerate(source.get('episodes', [])):
                                self.conn.execute('''
                                    INSERT INTO tv_episodes (series_vod_id, source_name, episode_num, episode_title, play_url)
                                    VALUES (?, ?, ?, ?, ?)
                                    ON CONFLICT(play_url) DO NOTHING;
                                ''', (series_data['vod_id'], source['source_name'], i + 1, episode['title'], episode['url']))
                return cursor.lastrowid
            except sqlite3.IntegrityError as e:
                logger.warning(f"Integrity error for TV series {series_data.get('vod_id')}: {e}")
            except sqlite3.Error as e:
                logger.error(f"Failed to upsert TV series {series_data.get('vod_id')}: {e}")
            return None

    def get_max_completed_page(self, category_id, year):
        """
        Gets the maximum page number that has been fully completed for a given category and year.
        Used for resuming crawls.
        """
        if not self.conn:
            self.connect()
        
        # We look for the highest page number with status 'completed'
        # Note: task_key format is "spider_type_category_year_page"
        # But we also store category_id and year separately, which is better.
        cursor = self.conn.execute('''
            SELECT MAX(current_page) FROM crawl_progress
            WHERE category_id = ? AND year = ? AND status = 'completed'
        ''', (category_id, year))
        result = cursor.fetchone()
        return result[0] if result and result[0] else 0

    def exists(self, vod_id):
        """Checks if a VOD ID already exists in the database."""
        if not self.conn:
            self.connect()
        
        # Check both movies and tv_series tables
        cursor = self.conn.execute("SELECT 1 FROM movies WHERE vod_id = ?", (vod_id,))
        if cursor.fetchone():
            return True
            
        cursor = self.conn.execute("SELECT 1 FROM tv_series WHERE vod_id = ?", (vod_id,))
        if cursor.fetchone():
            return True
            
        return False

    def get_crawl_progress(self, task_key):
        """Gets the crawl progress for a specific task."""
        if not self.conn:
            self.connect()
        cursor = self.conn.execute("SELECT * FROM crawl_progress WHERE task_key = ?", (task_key,))
        return cursor.fetchone()

    def update_crawl_progress(self, task_key, category_id, year, current_page, status):
        """Updates or inserts crawl progress."""
        if not self.conn:
            self.connect()
        with self.conn:
            self.conn.execute('''
                INSERT INTO crawl_progress (task_key, category_id, year, current_page, status)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(task_key) DO UPDATE SET
                    current_page=excluded.current_page,
                    status=excluded.status;
            ''', (task_key, category_id, year, current_page, status))

    def log_export(self, table_name, export_type, filepath, row_count):
        """Logs a data export event."""
        if not self.conn:
            self.connect()
        with self.conn:
            self.conn.execute('''
                INSERT INTO export_logs (table_name, export_type, filepath, row_count)
                VALUES (?, ?, ?, ?);
            ''', (table_name, export_type, str(filepath), row_count))

    def get_last_export_time(self, table_name):
        """Gets the timestamp of the last successful export for a table."""
        if not self.conn:
            self.connect()
        cursor = self.conn.execute('''
            SELECT MAX(created_at) FROM export_logs
            WHERE table_name = ? AND status = 'success' AND export_type = 'incremental'
        ''', (table_name,))
        result = cursor.fetchone()
        return result[0] if result and result[0] else '1970-01-01 00:00:00'
