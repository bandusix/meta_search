#!/usr/bin/env python3
"""
验证增量爬取功能
"""
import os
import sys
import subprocess
import time
from pathlib import Path

def run_incremental_crawl():
    print("\n🚀 运行增量爬取测试...")
    cmd = [
        sys.executable, 
        "mjwu_spider/main.py", 
        "--mode", "all", 
        "--incremental"
    ]
    try:
        subprocess.run(cmd, check=True)
        print("✅ 增量爬取执行成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 增量爬取失败: {e}")
        sys.exit(1)

def check_exports():
    print("\n🔍 检查导出文件...")
    # Check both potential locations
    export_dirs = [Path("mjwu_spider/data/exports"), Path("data/exports")]
    found_dir = None
    for d in export_dirs:
        if d.exists():
            found_dir = d
            break
    
    if not found_dir:
        print(f"⚠️ 未找到导出目录: {export_dirs}")
    else:
        # 查找最新的增量导出文件
        inc_files = list(found_dir.glob("*_incremental_*.csv"))
        if not inc_files:
            # Try the other directory just in case
            other_dir = export_dirs[1] if found_dir == export_dirs[0] else export_dirs[0]
            if other_dir.exists():
                inc_files = list(other_dir.glob("*_incremental_*.csv"))
        
        if not inc_files:
            print("⚠️ 未找到增量导出文件 (可能是首次运行或无数据更新)")
        else:
            # Group by type
            latest_files = {}
            for f in inc_files:
                type_name = f.name.split('_')[0] # movies, tv
                if type_name not in latest_files or f.stat().st_mtime > latest_files[type_name].stat().st_mtime:
                    latest_files[type_name] = f

            for type_name, f in latest_files.items():
                print(f"✅ 最新 {type_name} 增量文件: {f.name} ({f.stat().st_size} bytes)")
        
    # Check DB counts (Run regardless of export success)
    import sqlite3
    if os.path.exists("spider.db"):
        conn = sqlite3.connect("spider.db")
        c = conn.cursor()
        for table in ['movies', 'tv_series', 'tv_episodes']:
            try:
                c.execute(f"SELECT count(*) FROM {table}")
                print(f"📊 DB {table}: {c.fetchone()[0]}")
            except Exception as e:
                print(f"⚠️ DB {table} error: {e}")
        conn.close()

def main():
    # 模拟3次运行
    for i in range(1, 4):
        print(f"\n{'='*40}")
        print(f"第 {i}/3 次验证")
        print(f"{'='*40}")
        run_incremental_crawl()
        check_exports()
        if i < 3:
            print("\n⏳ 等待 5 秒后进行下一次测试...")
            time.sleep(5)

if __name__ == "__main__":
    main()
