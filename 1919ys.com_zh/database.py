import sqlite3
import os

DB_NAME = 'vs_1919_flat.db'

def init_db():
    # Only remove if we want a fresh start. For full crawl resuming, we might want to keep it?
    # User said "Full crawl", implying a fresh start or ensure everything is there.
    # Let's keep existing logic but enable WAL.
    
    # Check if DB exists to decide if we create tables
    db_exists = os.path.exists(DB_NAME)
    
    conn = sqlite3.connect(DB_NAME)
    
    # Enable Write-Ahead Logging for better concurrency
    conn.execute('PRAGMA journal_mode=WAL;')
    
    if not db_exists:
        cursor = conn.cursor()

        # Unified Flat Table
        cursor.execute('''
        CREATE TABLE media_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,          -- movie, tv, variety, anime, short_drama
            title TEXT NOT NULL,             -- Series/Movie Name
            episode_name TEXT NOT NULL,      -- "Full", "Ep 01", "20240314"
            play_url TEXT UNIQUE NOT NULL,   -- The Playable URL (Unique Key)
            detail_url TEXT,                 -- Source Page URL
            poster_url TEXT,                 -- 海报URL
            year INTEGER,
            quality TEXT,
            genre TEXT,
            region TEXT,
            director TEXT,
            actors TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')
        
        # Indices for fast search
        cursor.execute('CREATE UNIQUE INDEX idx_play_url ON media_resources(play_url);')
        cursor.execute('CREATE INDEX idx_title ON media_resources(title);')
        cursor.execute('CREATE INDEX idx_category ON media_resources(category);')
        cursor.execute('CREATE INDEX idx_year ON media_resources(year);')

        conn.commit()
        print("Database (Flat Schema) initialized successfully.")
    else:
        print("Database exists. Using existing database.")

    conn.close()

def get_connection():
    conn = sqlite3.connect(DB_NAME, timeout=30.0) # Increase timeout for concurrent writes
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn
