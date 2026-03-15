#!/usr/bin/env python3
"""
自动化测试与验证脚本
1. 运行爬虫 (50部电影, 50部电视剧)
2. 导出数据
3. 验证数据质量
"""

import os
import sys
import csv
import subprocess
import time
from pathlib import Path

def run_spider(mode, max_items):
    """运行爬虫"""
    print(f"\n🚀 开始测试: {mode} (Limit: {max_items})")
    cmd = [
        sys.executable, 
        "main.py", 
        "--mode", mode, 
        "--max-items", str(max_items),
        "--export", "full"  # Run export after crawl
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ {mode} 测试完成")
    except subprocess.CalledProcessError as e:
        print(f"❌ {mode} 测试失败: {e}")
        sys.exit(1)

def verify_csv(filepath, min_rows=1, required_fields=None):
    """验证CSV文件"""
    print(f"\n🔍 验证文件: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return False
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
        # 验证行数
        if len(rows) < min_rows:
            print(f"❌ 行数不足: {len(rows)} < {min_rows}")
            return False
        else:
            print(f"✅ 行数验证通过: {len(rows)} >= {min_rows}")
        
        # 验证字段
        if required_fields:
            missing_fields = [field for field in required_fields if field not in reader.fieldnames]
            if missing_fields:
                print(f"❌ 缺少字段: {missing_fields}")
                return False
            else:
                print(f"✅ 字段验证通过")
        
        # 验证数据完整性 (抽样检查)
        empty_count = 0
        for row in rows:
            if not row.get('title'):
                empty_count += 1
        
        if empty_count > 0:
            print(f"⚠️ 发现 {empty_count} 行标题为空")
        else:
            print(f"✅ 数据完整性验证通过 (标题非空)")
            
    return True

def main():
    # 切换到脚本所在目录
    os.chdir(Path(__file__).parent)
    
    # 1. 清理旧数据 (可选)
    if os.path.exists("spider.db"):
        print("🗑️ 清理旧数据库 spider.db")
        try:
            os.remove("spider.db")
        except Exception as e:
            print(f"⚠️ 清理失败: {e}")
    
    # 2. 运行爬虫测试
    run_spider("movie", 50)
    
    # Check if movies table exists
    import sqlite3
    conn = sqlite3.connect('spider.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='movies'")
    print(f"Movies table exists: {bool(c.fetchone())}")
    conn.close()

    run_spider("tv", 50)
    
    # Check if tv_series table exists
    conn = sqlite3.connect('spider.db')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tv_series'")
    print(f"TV Series table exists: {bool(c.fetchone())}")
    conn.close()

    # 3. 验证导出文件
    export_dir = Path("data/exports")
    
    # 查找最新的导出文件
    movie_files = sorted(export_dir.glob("movies_full_*.csv"), key=os.path.getmtime, reverse=True)
    tv_files = sorted(export_dir.glob("tv_series_full_*.csv"), key=os.path.getmtime, reverse=True)
    ep_files = sorted(export_dir.glob("tv_episodes_full_*.csv"), key=os.path.getmtime, reverse=True)
    
    success = True
    
    if movie_files:
        if not verify_csv(movie_files[0], min_rows=50, required_fields=['vod_id', 'title', 'play_url']):
            success = False
    else:
        print("❌ 未找到电影导出文件")
        success = False
        
    if tv_files:
        if not verify_csv(tv_files[0], min_rows=50, required_fields=['vod_id', 'title', 'detail_url']):
            success = False
    else:
        print("❌ 未找到电视剧导出文件")
        success = False
        
    if ep_files:
        # Episodes count depends on series, just check existence and fields
        if not verify_csv(ep_files[0], min_rows=50, required_fields=['vod_id', 'episode_title', 'play_url']):
            success = False
    else:
        print("❌ 未找到剧集导出文件")
        success = False
    
    print("\n" + "="*60)
    if success:
        print("🎉 所有测试通过!")
        
        # Run advanced verification
        print("\n🚀 运行高级验证...")
        import subprocess
        subprocess.run(["python", "advanced_verify.py"])
    else:
        print("❌ 测试存在问题，请检查日志")
    print("="*60)

if __name__ == "__main__":
    main()
