#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重启爬虫脚本 - 使用慢速请求
"""

import subprocess
import sys
import time

def restart_crawl():
    print("正在重启爬虫，使用慢速请求模式...")
    
    # 电影爬取 - 从第1页开始，使用较慢的40线程
    print("\n=== 开始电影爬取 (CID=1) ===")
    result = subprocess.run([
        sys.executable, "main.py", "movie", 
        "--start-page", "1", 
        "--threads", "40"
    ], capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    print(f"电影爬取完成，返回码: {result.returncode}")
    
    # 等待一段时间
    time.sleep(10)
    
    # 电视剧爬取 - 包含所有分类
    categories = [
        ("电视剧", "2", 549),
        ("综艺", "3", 111), 
        ("动漫", "4", 238),
        ("短剧", "30", 319),
        ("伦理MV", "36", 177)
    ]
    
    for name, cid, max_pages in categories:
        print(f"\n=== 开始{name}爬取 (CID={cid}) ===")
        result = subprocess.run([
            sys.executable, "main.py", "tv",
            "--start-page", "1",
            "--threads", "40", 
            "--cid", cid,
            "--category-name", name
        ], capture_output=True, text=True)
        
        if result.stdout:
            print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        print(f"{name}爬取完成，返回码: {result.returncode}")
        time.sleep(5)  # 分类之间等待5秒
    
    print("\n=== 所有爬取任务完成 ===")
    print("开始导出数据到Excel...")
    
    # 导出数据
    result = subprocess.run([
        sys.executable, "main.py", "export", "excel"
    ], capture_output=True, text=True)
    
    if result.stdout:
        print("导出STDOUT:", result.stdout)
    if result.stderr:
        print("导出STDERR:", result.stderr)
        
    print(f"数据导出完成，返回码: {result.returncode}")

if __name__ == "__main__":
    restart_crawl()