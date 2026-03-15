import sqlite3
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database import DatabaseManager

def test_duplicate_episode_fix():
    print("开始测试重复剧集修复逻辑...")
    
    db_path = "data/test_db.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    db_manager = DatabaseManager(db_path)
    
    # 1. 插入一条初始数据
    episode1 = {
        'series_title': 'Test Series',
        'episode_title': 'Episode 1',
        'original_title': 'Original 1',
        'url': 'http://example.com/s1e1',
        'poster_url': 'http://example.com/poster.jpg',
        'year': 2023,
        'rating': 8.5,
        'imdb_rating': 8.0,
        'quality': '1080p',
        'season': 1,
        'episode': 1,
        'release_title': 'Test.S01E01.1080p',
        'views': 100,
        'votes': 10,
        'description': 'Test description'
    }
    
    print("插入第一条数据...")
    if db_manager.save_episode(episode1):
        print("✅ 第一条数据插入成功")
    else:
        print("❌ 第一条数据插入失败")
        return

    # 2. 尝试插入同一集，但 URL 不同
    # 这种情况以前会报错 UNIQUE constraint failed
    episode2 = episode1.copy()
    episode2['url'] = 'http://example.com/s1e1-new-url' # URL 变了
    episode2['views'] = 200 # 更新一些数据
    
    print("尝试插入同一集（新 URL）...")
    if db_manager.save_episode(episode2):
        print("✅ 第二条数据处理成功（应该更新了旧记录）")
    else:
        print("❌ 第二条数据处理失败")
        return

    # 3. 验证数据库中是否只有一条记录，且 URL 已更新
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT count(*), url, views FROM tv_episodes")
        row = cursor.fetchone()
        count = row[0]
        url = row[1]
        views = row[2]
        
        print(f"数据库记录数: {count}")
        print(f"当前 URL: {url}")
        print(f"当前 Views: {views}")
        
        if count == 1 and url == 'http://example.com/s1e1-new-url' and views == 200:
            print("✅ 验证成功！旧记录被正确更新，没有违反唯一约束。")
        else:
            print("❌ 验证失败！数据状态不正确。")

    # 清理
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    test_duplicate_episode_fix()
