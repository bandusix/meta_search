import pandas as pd
import json
import os
from datetime import datetime
from database import Database

class Exporter:
    STATE_FILE = 'export_state.json'
    
    def __init__(self, db_path='repelishd.db', output_dir='./exports'):
        self.db = Database(db_path)
        self.output_dir = output_dir
        self.state = self._load_state()
        os.makedirs(output_dir, exist_ok=True)
        
    def _load_state(self):
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {'last_export_time': '1970-01-01 00:00:00'}
        
    def _save_state(self, timestamp):
        self.state['last_export_time'] = timestamp
        with open(self.STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def export(self, mode='full'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if mode == 'incremental':
            last_time = self.state['last_export_time']
            print(f"\n📥 开始增量导出 (自 {last_time} 起)...")
            movies = self.db.get_movies_after(last_time)
            episodes = self.db.get_tv_episodes_after(last_time)
            prefix = 'incremental'
        else:
            print("\n📦 开始全量导出 (所有历史数据)...")
            movies = self.db.get_all_movies()
            episodes = self.db.get_all_tv_episodes()
            prefix = 'full'
            
        if not movies and not episodes:
            print("⚠️ 没有数据需要导出。")
            return
            
        # 导出电影
        if movies:
            movie_filename = f'repelishd_movies_{prefix}_{file_timestamp}.csv' # 统一为 csv
            movie_filepath = os.path.abspath(os.path.join(self.output_dir, movie_filename))
            
            print(f"  🎬 正在导出电影数据: {len(movies)} 条")
            # 打印部分电影标题示例
            sample_titles = [m['title_spanish'] for m in movies[:3]]
            print(f"    ℹ️ 包含示例: {', '.join(sample_titles)} ...")
            
            df_movies = pd.DataFrame(movies)
            
            # 调整列顺序，确保关键信息在前
            columns = ['title_spanish', 'year', 'quality', 'rating', 'detail_url']
            # 保留其他列
            other_columns = [c for c in df_movies.columns if c not in columns]
            df_movies = df_movies[columns + other_columns]
            
            df_movies.to_csv(movie_filepath, index=False, encoding='utf-8-sig') # 导出为 CSV
            print(f"    ✅ 电影CSV已生成: {movie_filepath}")
            
        # 导出电视剧
        if episodes:
            tv_filename = f'repelishd_tv_{prefix}_{file_timestamp}.csv' # 修改为 csv
            tv_filepath = os.path.abspath(os.path.join(self.output_dir, tv_filename))
            
            print(f"  📺 正在导出电视剧集数据: {len(episodes)} 条")
            # 打印部分剧集示例
            sample_eps = [f"{e.get('title_spanish', e.get('series_title_spanish', '?'))} S{e['season']}E{e['episode']}" for e in episodes[:3]]
            print(f"    ℹ️ 包含示例: {', '.join(sample_eps)} ...")
            
            df_episodes = pd.DataFrame(episodes)
            # 调整列顺序，确保关键信息在前
            columns = ['title_spanish', 'season', 'episode', 'episode_title', 'detail_url', 'embed_url']
            # 保留其他列
            other_columns = [c for c in df_episodes.columns if c not in columns]
            df_episodes = df_episodes[columns + other_columns]
            
            df_episodes.to_csv(tv_filepath, index=False, encoding='utf-8-sig') # 导出为 CSV
            print(f"    ✅ 电视剧CSV已生成: {tv_filepath}")
        
        # 更新状态
        self._save_state(timestamp)
        print(f"\n✨ 导出任务完成! 状态已更新至: {timestamp}")
