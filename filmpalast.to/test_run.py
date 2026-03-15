import sys
import os
import yaml
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.crawler import FilmPalastCrawler
from src.database import DatabaseManager

def load_config(config_path="config/config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    print("开始测试爬虫...")
    
    # 加载配置
    config = load_config()
    
    # 初始化爬虫
    crawler = FilmPalastCrawler(config)
    
    # 运行爬虫
    # 目标：100部电影，100集剧集
    target_movies = 100
    target_episodes = 100
    
    print(f"目标：电影 {target_movies} 部，剧集 {target_episodes} 集")
    
    # 执行爬取
    crawler.crawl_content(target_movies=target_movies, target_episodes=target_episodes)
    
    # 验证结果
    db = DatabaseManager(config['database']['path'])
    movies_count = db.get_movies_count()
    episodes_count = db.get_episodes_count()
    
    print("-" * 30)
    print("测试结果验证:")
    print(f"数据库中电影数量: {movies_count}")
    print(f"数据库中剧集数量: {episodes_count}")
    
    if movies_count >= target_movies and episodes_count >= target_episodes:
        print("✅ 测试成功！已达到目标数量。")
    else:
        print("❌ 测试失败！未达到目标数量。")
        # 如果失败，可能需要检查日志或增加爬取的页数
        # 这里可以添加简单的重试逻辑或手动干预提示

if __name__ == "__main__":
    main()
