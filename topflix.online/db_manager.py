import sqlite3
import os

class DBManager:
    def __init__(self, db_name="topflix.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.init_db()

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()

    def init_db(self):
        self.connect()
        # Movies table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER,
            rating REAL,
            quality TEXT,
            poster_url TEXT,
            detail_url TEXT UNIQUE,
            player_url TEXT,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # TV Shows table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tv_shows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            original_title TEXT,
            year INTEGER,
            rating REAL,
            poster_url TEXT,
            detail_url TEXT UNIQUE,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # TV Episodes table
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tv_episodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            show_id INTEGER,
            season_number INTEGER,
            episode_number INTEGER,
            title TEXT,
            detail_url TEXT UNIQUE,
            player_url TEXT,
            crawled_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(show_id) REFERENCES tv_shows(id)
        );
        """)
        self.conn.commit()
        self.close()

    def save_movie(self, movie_data):
        self.connect()
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO movies (title, year, rating, quality, poster_url, detail_url, player_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                movie_data.get('title'),
                movie_data.get('year'),
                movie_data.get('rating'),
                movie_data.get('quality'),
                movie_data.get('poster_url'),
                movie_data.get('detail_url'),
                movie_data.get('player_url')
            ))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            print(f"Error saving movie: {e}")
        finally:
            self.close()

    def movie_exists(self, detail_url):
        self.connect()
        try:
            self.cursor.execute("SELECT id FROM movies WHERE detail_url=?", (detail_url,))
            res = self.cursor.fetchone()
            return res[0] if res else None
        finally:
            self.close()

    def save_tv_show(self, show_data):
        self.connect()
        try:
            self.cursor.execute("""
                INSERT OR IGNORE INTO tv_shows (title, original_title, year, rating, poster_url, detail_url)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                show_data.get('title'),
                show_data.get('original_title'),
                show_data.get('year'),
                show_data.get('rating'),
                show_data.get('poster_url'),
                show_data.get('detail_url')
            ))
            self.conn.commit()
            
            # Get the ID (whether inserted or existing)
            self.cursor.execute("SELECT id FROM tv_shows WHERE detail_url=?", (show_data.get('detail_url'),))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error saving TV show: {e}")
            return None
        finally:
            self.close()
            
    def tv_show_exists(self, detail_url):
        self.connect()
        try:
            self.cursor.execute("SELECT id FROM tv_shows WHERE detail_url=?", (detail_url,))
            res = self.cursor.fetchone()
            return res[0] if res else None
        finally:
            self.close()

    def save_episode(self, episode_data):
        self.connect()
        try:
            self.cursor.execute("""
                INSERT INTO tv_episodes (show_id, season_number, episode_number, title, detail_url, player_url)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(detail_url) DO UPDATE SET
                    season_number=excluded.season_number,
                    episode_number=excluded.episode_number,
                    title=excluded.title,
                    player_url=excluded.player_url,
                    show_id=excluded.show_id
            """, (
                episode_data.get('show_id'),
                episode_data.get('season_number'),
                episode_data.get('episode_number'),
                episode_data.get('title'),
                episode_data.get('detail_url'),
                episode_data.get('player_url')
            ))
            self.conn.commit()
        except Exception as e:
            print(f"Error saving episode: {e}")
        finally:
            self.close()
