import sqlite3
import logging
import pandas as pd
import os
from datetime import datetime
from .config import BASE_DIR

class DatabaseManager:
    def __init__(self, db_path="pelicinehd_data.db"):
        if not os.path.isabs(db_path):
             self.db_path = os.path.join(BASE_DIR, db_path)
        else:
             self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create movies table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS movies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title_spanish TEXT NOT NULL,
                        title_original TEXT,
                        year INTEGER NOT NULL,
                        rating REAL,
                        quality TEXT,
                        duration TEXT,
                        url TEXT NOT NULL UNIQUE,
                        poster_url TEXT,
                        genres TEXT,
                        media_type TEXT DEFAULT 'Movie',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create tv_episodes table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tv_episodes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        series_title_spanish TEXT NOT NULL,
                        series_title_original TEXT,
                        year INTEGER NOT NULL,
                        rating REAL,
                        quality TEXT,
                        season INTEGER NOT NULL,
                        episode INTEGER NOT NULL,
                        episode_title TEXT,
                        url TEXT NOT NULL UNIQUE,
                        series_url TEXT NOT NULL,
                        poster_url TEXT,
                        genres TEXT,
                        media_type TEXT DEFAULT 'TV Series',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Add genres column to movies if not exists
                try:
                    cursor.execute("ALTER TABLE movies ADD COLUMN genres TEXT")
                except sqlite3.OperationalError:
                    pass

                # Add genres column to tv_episodes if not exists
                try:
                    cursor.execute("ALTER TABLE tv_episodes ADD COLUMN genres TEXT")
                except sqlite3.OperationalError:
                    pass

                # Create indices
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_rating ON movies(rating)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_movies_url ON movies(url)')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_year ON tv_episodes(year)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_rating ON tv_episodes(rating)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_season_episode ON tv_episodes(season, episode)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_series_url ON tv_episodes(series_url)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tv_url ON tv_episodes(url)')

                conn.commit()
                logging.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")

    def save_movie(self, movie_data):
        """Save movie data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO movies 
                    (title_spanish, title_original, year, rating, quality, duration, url, poster_url, genres, media_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    movie_data.get('title_spanish'),
                    movie_data.get('title_original'),
                    movie_data.get('year'),
                    movie_data.get('rating'),
                    movie_data.get('quality'),
                    movie_data.get('duration'),
                    movie_data.get('url'),
                    movie_data.get('poster_url'),
                    movie_data.get('genres'),
                    'Movie'
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error saving movie {movie_data.get('url')}: {e}")
            return False

    def save_episode(self, episode_data):
        """Save episode data to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO tv_episodes 
                    (series_title_spanish, series_title_original, year, rating, quality, 
                     season, episode, episode_title, url, series_url, poster_url, genres, media_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    episode_data.get('series_title_spanish'),
                    episode_data.get('series_title_original'),
                    episode_data.get('year'),
                    episode_data.get('rating'),
                    episode_data.get('quality'),
                    episode_data.get('season'),
                    episode_data.get('episode'),
                    episode_data.get('episode_title'),
                    episode_data.get('url'),
                    episode_data.get('series_url'),
                    episode_data.get('poster_url'),
                    episode_data.get('genres'),
                    'TV Series'
                ))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Error saving episode {episode_data.get('url')}: {e}")
            return False

    def movie_exists(self, url):
        """Check if movie URL already exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM movies WHERE url = ?", (url,))
                return cursor.fetchone() is not None
        except Exception:
            return False

    def episode_exists(self, url):
        """Check if episode URL already exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM tv_episodes WHERE url = ?", (url,))
                return cursor.fetchone() is not None
        except Exception:
            return False

    def export_movies_to_csv(self, output_path, since_timestamp=None):
        """Export movies to CSV"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM movies"
                params = []
                
                if since_timestamp:
                    query += " WHERE created_at >= ?"
                    params.append(since_timestamp)
                    
                query += " ORDER BY year DESC, rating DESC"
                
                df = pd.read_sql_query(query, conn, params=params)
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                return len(df)
        except Exception as e:
            logging.error(f"Error exporting movies: {e}")
            return 0

    def export_tv_episodes_to_csv(self, output_path, since_timestamp=None):
        """Export TV episodes to CSV"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM tv_episodes"
                params = []
                
                if since_timestamp:
                    query += " WHERE created_at >= ?"
                    params.append(since_timestamp)
                    
                query += " ORDER BY year DESC, season, episode"
                
                df = pd.read_sql_query(query, conn, params=params)
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                return len(df)
        except Exception as e:
            logging.error(f"Error exporting TV episodes: {e}")
            return 0
            
    def get_movies_missing_data(self):
        """Get movies with missing genres, duration, or quality"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Check for empty/null in genres, duration, or quality
                cursor.execute("""
                    SELECT id, url 
                    FROM movies 
                    WHERE (genres IS NULL OR genres = '') 
                       OR (duration IS NULL OR duration = '')
                       OR (quality IS NULL OR quality = '')
                """)
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting movies missing data: {e}")
            return []

    def get_series_missing_data(self):
        """Get TV episodes with missing genres or quality (grouped by series_url)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # TV episodes don't have duration column, only quality and genres
                cursor.execute("""
                    SELECT DISTINCT series_url 
                    FROM tv_episodes 
                    WHERE (genres IS NULL OR genres = '')
                       OR (quality IS NULL OR quality = '')
                """)
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Error getting series missing data: {e}")
            return []

    def update_movie_details(self, movie_id, genres=None, duration=None, quality=None):
        """Update movie details"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                updates = []
                params = []
                
                if genres:
                    updates.append("genres = ?")
                    params.append(genres)
                if duration:
                    updates.append("duration = ?")
                    params.append(duration)
                if quality:
                    updates.append("quality = ?")
                    params.append(quality)
                
                if not updates:
                    return True
                    
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(movie_id)
                
                query = f"UPDATE movies SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating movie details: {e}")
            return False

    def update_series_details(self, series_url, genres=None, quality=None):
        """Update details for all episodes of a series"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                updates = []
                params = []
                
                if genres:
                    updates.append("genres = ?")
                    params.append(genres)
                if quality:
                    updates.append("quality = ?")
                    params.append(quality)
                
                if not updates:
                    return True
                    
                updates.append("updated_at = CURRENT_TIMESTAMP")
                params.append(series_url)
                
                query = f"UPDATE tv_episodes SET {', '.join(updates)} WHERE series_url = ?"
                cursor.execute(query, params)
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error updating series details: {e}")
            return False

    def delete_movie(self, movie_id):
        """Delete movie by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error deleting movie {movie_id}: {e}")
            return False

    def delete_series(self, series_url):
        """Delete series episodes by series_url"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tv_episodes WHERE series_url = ?", (series_url,))
                conn.commit()
                return True
        except Exception as e:
            logging.error(f"Error deleting series {series_url}: {e}")
            return False

    def get_statistics(self):
        """Get database statistics"""
        stats = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM movies")
                stats['movie_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM tv_episodes")
                stats['tv_episode_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT year, COUNT(*) FROM movies GROUP BY year ORDER BY year DESC LIMIT 10")
                stats['movies_by_year'] = cursor.fetchall()
                
        except Exception as e:
            logging.error(f"Error getting stats: {e}")
            
        return stats
