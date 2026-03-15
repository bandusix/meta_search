import time
import subprocess
import sys
import logging
from datetime import datetime

# 配置
INTERVAL_HOURS = 24  # 每24小时运行一次
PYTHON_EXEC = sys.executable
SCRIPT_PATH = "main.py"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("auto_run.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("AutoRun")

def run_task(command, args):
    cmd = [PYTHON_EXEC, SCRIPT_PATH, command] + args
    logger.info(f"启动任务: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"任务完成:\n{result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"任务失败:\n{e.stderr}")

def main():
    logger.info("自动爬虫系统启动...")
    
    while True:
        start_time = datetime.now()
        logger.info(f"开始新一轮抓取: {start_time}")
        
        # 1. 爬取电影 (限制页数以避免过长，可根据需求调整)
        # 这里示例全量爬取，实际可设置 --max-pages
        run_task("movie", [])
        
        # 2. 爬取电视剧
        run_task("tv", [])
        
        # 3. 导出数据
        run_task("export", ["--export-type", "incremental"])
        
        end_time = datetime.now()
        duration = end_time - start_time
        logger.info(f"本轮抓取结束，耗时: {duration}")
        
        # 等待下一次运行
        wait_seconds = INTERVAL_HOURS * 3600
        logger.info(f"等待 {INTERVAL_HOURS} 小时后再次运行...")
        time.sleep(wait_seconds)

if __name__ == "__main__":
    main()
