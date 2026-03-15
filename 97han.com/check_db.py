#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库状态
"""

import sqlite3
import os

def check_database():
    """检查数据库状态"""
    db_path = "movies.db"
    
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"数据库表: {[t[0] for t in tables]}")
        
        # 检查movies表
        if ('movies',) in tables:
            cursor.execute("SELECT COUNT(*) as total_movies, COUNT(DISTINCT vod_id) as unique_movies FROM movies")
            result = cursor.fetchone()
            print(f"总电影数: {result[0]}, 唯一电影数: {result[1]}")
            
            # 检查最新的几条记录
            cursor.execute("SELECT vod_id, title, category, play_line_name, player_page_url FROM movies ORDER BY id DESC LIMIT 3")
            recent_movies = cursor.fetchall()
            print("\n最新的3部电影:")
            for movie in recent_movies:
                print(f"ID: {movie[0]}, 标题: {movie[1]}, 分类: {movie[2]}")
                print(f"  播放线路: {movie[3]}, 播放器页面: {movie[4]}")
        
        # 检查tv_episodes表
        if ('tv_episodes',) in tables:
            cursor.execute("SELECT COUNT(*) as total_episodes FROM tv_episodes")
            result = cursor.fetchone()
            print(f"\n总剧集数: {result[0]}")
            
            # 检查最新的几条记录
            cursor.execute("SELECT vod_id, episode_number, play_url, play_line_name, player_page_url FROM tv_episodes ORDER BY id DESC LIMIT 3")
            recent_episodes = cursor.fetchall()
            print("\n最新的3个剧集:")
            for episode in recent_episodes:
                print(f"剧集ID: {episode[0]}, 集数: {episode[1]}, 播放URL: {episode[2]}")
                print(f"  播放线路: {episode[3]}, 播放器页面: {episode[4]}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()