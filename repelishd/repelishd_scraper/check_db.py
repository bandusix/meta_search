import sqlite3
import json

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def check_db():
    conn = sqlite3.connect('repelishd.db')
    conn.row_factory = dict_factory
    cursor = conn.cursor()
    
    print("\n=== 检查最新 3 部电影 ===")
    cursor.execute("SELECT * FROM movies ORDER BY updated_at DESC LIMIT 3")
    movies = cursor.fetchall()
    for movie in movies:
        print(json.dumps(movie, indent=2, ensure_ascii=False))
        
    print("\n=== 检查最新 3 个剧集 ===")
    cursor.execute("SELECT * FROM tv_episodes ORDER BY updated_at DESC LIMIT 3")
    episodes = cursor.fetchall()
    for ep in episodes:
        print(json.dumps(ep, indent=2, ensure_ascii=False))
        
    conn.close()

if __name__ == '__main__':
    check_db()
