import sqlite3
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class Database:
    """Database management class for LK21 scraper"""
    
    def __init__(self, db_path: str = "lk21.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
        
    def _get_connection(self):
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
        
    def _init_db(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create movies table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT DEFAULT 'Movie',
            title_original TEXT,
            year INTEGER,
            rating REAL,
            quality TEXT,
            resolution TEXT,
            duration TEXT,
            image_url TEXT,
            movie_url TEXT NOT NULL UNIQUE,
            genre TEXT,
            country TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Migration: Add new columns if they don't exist
        try:
            cursor.execute("ALTER TABLE movies ADD COLUMN page_title TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute("ALTER TABLE movies ADD COLUMN url_slug TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
            
        try:
            cursor.execute("ALTER TABLE movies ADD COLUMN type TEXT DEFAULT 'Movie'")
        except sqlite3.OperationalError:
            pass
        
        # Create indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_year ON movies(year);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_created_at ON movies(created_at);")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_movies_url ON movies(movie_url);")
        
        conn.commit()
        conn.close()
        
    def get_all_movie_urls(self) -> List[Dict[str, Any]]:
        """
        Get all movie URLs and IDs from database
        
        Returns:
            List of dicts with 'id' and 'movie_url'
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, movie_url FROM movies")
            return [{'id': row['id'], 'movie_url': row['movie_url']} for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all movie URLs: {e}")
            return []
        finally:
            conn.close()

    def delete_movie(self, movie_id: int) -> bool:
        """
        Delete a movie by ID
        
        Args:
            movie_id: Movie ID
            
        Returns:
            True if deleted, False otherwise
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting movie {movie_id}: {e}")
            return False
        finally:
            conn.close()
            
    def insert_movie(self, movie: Dict[str, Any]) -> bool:
        """
        Insert or update a movie
        
        Args:
            movie: Movie data dictionary
            
        Returns:
            True if inserted/updated, False if error
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Prepare data with defaults
            data = {
                'title': movie.get('title', ''),
                'type': movie.get('type', 'Movie'),
                'title_original': movie.get('title_original', ''),
                'year': movie.get('year'),
                'rating': movie.get('rating'),
                'quality': movie.get('quality', ''),
                'resolution': movie.get('resolution', ''),
                'duration': movie.get('duration', ''),
                'image_url': movie.get('image_url', ''),
                'movie_url': movie.get('movie_url', ''),
                'genre': movie.get('genre', ''),
                'country': movie.get('country', ''),
                'description': movie.get('description', ''),
                'page_title': movie.get('page_title', ''),
                'url_slug': movie.get('url_slug', '')
            }
            
            # Use UPSERT to handle duplicates (requires SQLite 3.24+)
            cursor.execute("""
            INSERT INTO movies (
                title, type, title_original, year, rating, quality, resolution, 
                duration, image_url, movie_url, genre, country, description, 
                page_title, url_slug, updated_at
            ) VALUES (
                :title, :type, :title_original, :year, :rating, :quality, :resolution,
                :duration, :image_url, :movie_url, :genre, :country, :description, 
                :page_title, :url_slug, CURRENT_TIMESTAMP
            )
            ON CONFLICT(movie_url) DO UPDATE SET
                title = excluded.title,
                type = excluded.type,
                rating = excluded.rating,
                quality = excluded.quality,
                resolution = excluded.resolution,
                image_url = excluded.image_url,
                page_title = excluded.page_title,
                url_slug = excluded.url_slug,
                updated_at = CURRENT_TIMESTAMP
            """, data)
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error inserting movie {movie.get('title', 'Unknown')}: {e}")
            return False
        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        try:
            # Total movies
            cursor.execute("SELECT COUNT(*) FROM movies")
            stats['total_movies'] = cursor.fetchone()[0]
            
            # Year range
            cursor.execute("SELECT MIN(year), MAX(year) FROM movies")
            min_year, max_year = cursor.fetchone()
            stats['min_year'] = min_year
            stats['max_year'] = max_year
            
            # Latest update
            cursor.execute("SELECT MAX(updated_at) FROM movies")
            stats['latest_update'] = cursor.fetchone()[0]
            
            # Movies by year
            cursor.execute("""
                SELECT year, COUNT(*) as count 
                FROM movies 
                WHERE year IS NOT NULL 
                GROUP BY year 
                ORDER BY year DESC
            """)
            stats['movies_by_year'] = [(row[0], row[1]) for row in cursor.fetchall()]
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            stats = {
                'total_movies': 0,
                'min_year': None,
                'max_year': None,
                'latest_update': None,
                'movies_by_year': []
            }
        finally:
            conn.close()
            
        return stats
