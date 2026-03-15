import csv
import os
import re
from pathlib import Path

def analyze_csv(filepath, type='movie'):
    print(f"\n📊 分析文件: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"❌ 文件不存在: {filepath}")
        return

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    total = len(rows)
    print(f"总行数: {total}")
    
    if total == 0:
        return

    # 1. 字段完整性检查
    empty_fields = {}
    for row in rows:
        for k, v in row.items():
            if not v or v.strip() == '':
                empty_fields[k] = empty_fields.get(k, 0) + 1
    
    print("\n[字段空值统计]")
    for k, v in empty_fields.items():
        if v > 0:
            print(f"  - {k}: {v} ({v/total*100:.1f}%)")

    # 2. 数据有效性检查
    print("\n[数据有效性]")
    
    # 年份检查
    years = [int(r['year']) for r in rows if r.get('year') and r['year'].isdigit() and int(r['year']) > 0]
    if years:
        print(f"  - 年份范围: {min(years)} - {max(years)}")
        print(f"  - 无效年份数: {total - len(years)}")
    
    # 评分检查
    ratings = [float(r['rating']) for r in rows if r.get('rating') and float(r['rating']) > 0]
    print(f"  - 有评分占比: {len(ratings)}/{total} ({len(ratings)/total*100:.1f}%)")
    if ratings:
        print(f"  - 平均分: {sum(ratings)/len(ratings):.2f}")

    # 3. URL检查
    valid_urls = 0
    for row in rows:
        url = row.get('detail_url', '')
        if url.startswith('http') and 'mjwu.cc' in url:
            valid_urls += 1
    print(f"  - 有效URL占比: {valid_urls}/{total} ({valid_urls/total*100:.1f}%)")

    # 4. 类型特定检查
    if type == 'tv':
        episodes = [int(r['total_episodes']) for r in rows if r.get('total_episodes') and r['total_episodes'].isdigit()]
        if episodes:
            print(f"  - 有集数占比: {len(episodes)}/{total} ({len(episodes)/total*100:.1f}%)")
            print(f"  - 最大集数: {max(episodes)}")
    
    elif type == 'episode':
        play_urls = [r for r in rows if r.get('play_url') and 'm3u8' in r.get('play_url', '')]
        # 注意：播放页URL通常不是m3u8，这里只检查是否有值
        valid_play = len([r for r in rows if r.get('play_url')])
        print(f"  - 播放链接占比: {valid_play}/{total}")

def main():
    export_dir = Path("mjwu_spider/data/exports")
    if not export_dir.exists():
        print("Export directory not found")
        return

    # 查找最新的导出文件
    movie_files = sorted(export_dir.glob("movies_full_*.csv"), key=os.path.getmtime, reverse=True)
    tv_files = sorted(export_dir.glob("tv_series_full_*.csv"), key=os.path.getmtime, reverse=True)
    ep_files = sorted(export_dir.glob("tv_episodes_full_*.csv"), key=os.path.getmtime, reverse=True)

    if movie_files:
        analyze_csv(movie_files[0], 'movie')
    
    if tv_files:
        analyze_csv(tv_files[0], 'tv')
        
    if ep_files:
        analyze_csv(ep_files[0], 'episode')

if __name__ == "__main__":
    main()
