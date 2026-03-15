#!/bin/bash
#
# Cuevana3 爬虫定时任务脚本
# 用于每日自动更新电影和电视剧数据
#

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 设置日志目录
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# 设置日志文件
LOG_FILE="$LOG_DIR/scraper_$(date +%Y%m%d_%H%M%S).log"

# 记录开始时间
echo "========================================" | tee -a "$LOG_FILE"
echo "Cuevana3 爬虫定时任务" | tee -a "$LOG_FILE"
echo "开始时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 执行更新命令
python3 main.py update 2>&1 | tee -a "$LOG_FILE"

# 记录结束时间
echo "" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "结束时间: $(date '+%Y-%m-%d %H:%M:%S')" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 清理30天前的日志
find "$LOG_DIR" -name "scraper_*.log" -type f -mtime +30 -delete

# 可选：导出数据到CSV（取消注释以启用）
# python3 main.py export --type all

echo "✅ 定时任务执行完成，日志已保存到: $LOG_FILE"
