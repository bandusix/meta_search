
import subprocess
import sqlite3
import sys
import time

def run_command(command):
    """执行命令并打印输出"""
    print(f"🚀 正在执行: {command}")
    process = subprocess.Popen(command, shell=True)
    process.wait()
    return process.returncode

def verify_db():
    """验证数据库内容"""
    print("\n🔍 正在自检数据库...")
    try:
        conn = sqlite3.connect('spider.db')
        c = conn.cursor()
        
        # 检查电影数量
        c.execute("SELECT count(*) FROM movies")
        movie_count = c.fetchone()[0]
        
        # 检查电视剧数量
        c.execute("SELECT count(*) FROM tv")
        tv_count = c.fetchone()[0]
        
        # 检查电影表中是否混入短剧
        c.execute("SELECT count(*) FROM movies WHERE category LIKE '%短剧%' OR title LIKE '%短剧%'")
        short_in_movie = c.fetchone()[0]
        
        print(f"   📊 电影数量: {movie_count}")
        print(f"   📊 电视剧数量: {tv_count}")
        print(f"   ⚠️ 电影表混入短剧数: {short_in_movie}")
        
        conn.close()
        
        if short_in_movie > 0:
            print("❌ 验证失败: 电影表中存在短剧！")
            return False
            
        if movie_count == 0 and tv_count == 0:
            print("❌ 验证失败: 数据库为空！")
            return False
            
        print("✅ 数据库验证通过！")
        return True
        
    except Exception as e:
        print(f"❌ 验证出错: {e}")
        return False

def main():
    print("="*60)
    print("自动化爬虫测试与执行流程")
    print("="*60)
    
    # 1. 执行小规模测试
    print("\n[阶段 1] 小规模测试 (50条)...")
    code = run_command("python main.py all --limit 50 --threads 20")
    if code != 0:
        print("❌ 测试执行失败！")
        sys.exit(1)
        
    # 2. 验证结果
    if not verify_db():
        print("❌ 自检未通过，终止流程。")
        sys.exit(1)
        
    # 3. 执行全量爬取
    print("\n[阶段 2] 验证通过，开始全量爬取...")
    # 这里我们不设置 limit，让它一直跑，或者设置一个很大的 limit
    # 用户说“执行全量爬取”，通常意味着跑到结束
    # 但为了演示，我们这里直接启动命令
    
    run_command("python main.py all --threads 20")

if __name__ == "__main__":
    main()
