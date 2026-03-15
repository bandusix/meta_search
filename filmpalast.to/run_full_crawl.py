import sys
import os
import yaml
import logging
import argparse

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.crawler import FilmPalastCrawler
from src.database import DatabaseManager

def load_config(config_path="config/config.yaml"):
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(description='Run full site crawl')
    parser.add_argument('--threads', type=int, default=10, help='Number of threads (default: 10)')
    args = parser.parse_args()
    
    print(f"开始全站爬取，使用 {args.threads} 个线程...")
    
    # 加载配置
    config = load_config()
    
    # 初始化爬虫
    crawler = FilmPalastCrawler(config)
    
    # 执行全站爬取
    crawler.crawl_full_site(max_workers=args.threads)
    
    print("✅ 全站爬取任务完成！")

if __name__ == "__main__":
    main()
