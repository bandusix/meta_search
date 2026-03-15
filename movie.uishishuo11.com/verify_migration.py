
import sqlite3

def verify():
    conn = sqlite3.connect('spider.db')
    cursor = conn.cursor()
    
    # Check movies table
    cursor.execute("SELECT count(*) FROM movies WHERE title LIKE '%短剧%' OR category LIKE '%短剧%'")
    movies_count = cursor.fetchone()[0]
    print(f"Movies table short dramas: {movies_count}")
    
    # Check tv table
    cursor.execute("SELECT count(*) FROM tv WHERE title LIKE '%短剧%' OR category LIKE '%短剧%'")
    tv_count = cursor.fetchone()[0]
    print(f"TV table short dramas: {tv_count}")
    
    conn.close()

if __name__ == "__main__":
    verify()
