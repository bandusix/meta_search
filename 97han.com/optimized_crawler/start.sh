#!/bin/bash
# 优化版97韩剧网爬虫启动脚本

# 设置工作目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# 创建必要的目录
mkdir -p logs
mkdir -p data
mkdir -p backup

# 配置参数
PYTHON_CMD="python3"
LOG_FILE="logs/crawler_$(date +%Y%m%d_%H%M%S).log"
ERROR_LOG="logs/crawler_error_$(date +%Y%m%d_%H%M%S).log"
PID_FILE="logs/crawler.pid"

# 函数：检查进程是否在运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "⚠️  爬虫进程已在运行 (PID: $pid)"
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# 函数：启动爬虫
start_crawler() {
    echo "🚀 启动优化版97韩剧网爬虫..."
    
    # 检查是否已在运行
    if check_running; then
        exit 1
    fi
    
    # 备份旧数据库（如果存在）
    if [ -f "optimized_crawler.db" ]; then
        backup_file="backup/crawler_db_$(date +%Y%m%d_%H%M%S).db"
        cp "optimized_crawler.db" "$backup_file"
        echo "💾 数据库已备份到: $backup_file"
    fi
    
    # 启动爬虫（后台运行）
    echo "📊 开始全站爬取任务..."
    echo "📄 日志文件: $LOG_FILE"
    echo "❌ 错误日志: $ERROR_LOG"
    
    nohup $PYTHON_CMD -u optimized_crawler/main_crawler.py > "$LOG_FILE" 2> "$ERROR_LOG" &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    echo "✅ 爬虫已启动 (PID: $pid)"
    echo "📝 查看日志: tail -f $LOG_FILE"
    echo "🛑 停止爬虫: ./start.sh stop"
}

# 函数：停止爬虫
stop_crawler() {
    echo "🛑 停止爬虫进程..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -TERM "$pid"
            echo "✅ 已发送停止信号 (PID: $pid)"
            
            # 等待进程结束
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
                sleep 1
                ((count++))
            done
            
            if ps -p "$pid" > /dev/null 2>&1; then
                echo "⚠️  进程未正常退出，强制终止..."
                kill -KILL "$pid"
            fi
            
            rm -f "$PID_FILE"
            echo "✅ 爬虫进程已停止"
        else
            echo "⚠️  进程不存在，清理PID文件"
            rm -f "$PID_FILE"
        fi
    else
        echo "⚠️  没有找到PID文件，尝试查找并停止Python爬虫进程..."
        local pids=$(pgrep -f "main_crawler.py" || true)
        if [ -n "$pids" ]; then
            echo "🛑 找到并停止以下进程: $pids"
            kill -TERM $pids
        else
            echo "✅ 没有找到运行的爬虫进程"
        fi
    fi
}

# 函数：查看状态
status_crawler() {
    if check_running; then
        local pid=$(cat "$PID_FILE")
        echo "🟢 爬虫运行中 (PID: $pid)"
        
        # 显示进程信息
        ps -p "$pid" -o pid,ppid,cmd,etime,%cpu,%mem --no-headers
        
        # 显示最近的日志
        echo ""
        echo "📊 最近10条日志:"
        tail -n 10 logs/crawler.log 2>/dev/null | grep -E "(成功|失败|错误|完成)" || echo "暂无日志"
        
        # 显示数据库统计
        if [ -f "optimized_crawler.db" ]; then
            echo ""
            echo "💾 数据库统计:"
            $PYTHON_CMD -c "
import sqlite3
conn = sqlite3.connect('optimized_crawler.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM movies')
movies = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM episodes')
episodes = cursor.fetchone()[0]
print(f'电影: {movies} 部')
print(f'剧集: {episodes} 集')
conn.close()
" 2>/dev/null || echo "无法获取数据库统计"
        fi
    else
        echo "🔴 爬虫未运行"
    fi
}

# 函数：查看实时日志
log_crawler() {
    if [ -f "logs/crawler.log" ]; then
        echo "📊 查看实时日志 (按 Ctrl+C 退出)..."
        tail -f logs/crawler.log
    else
        echo "❌ 没有找到日志文件"
    fi
}

# 函数：运行数据验证
verify_data() {
    echo "🔍 开始数据验证..."
    $PYTHON_CMD optimized_crawler/verify.py
}

# 函数：清理日志
clean_logs() {
    echo "🧹 清理日志文件..."
    find logs -name "*.log" -type f -mtime +7 -delete
    echo "✅ 已清理7天前的日志文件"
}

# 函数：显示帮助
show_help() {
    echo "优化版97韩剧网爬虫控制脚本"
    echo "用法: $0 {start|stop|status|log|verify|clean|help}"
    echo ""
    echo "命令:"
    echo "  start   - 启动爬虫 (后台运行)"
    echo "  stop    - 停止爬虫"
    echo "  status  - 查看爬虫状态"
    echo "  log     - 查看实时日志"
    echo "  verify  - 运行数据验证"
    echo "  clean   - 清理旧日志"
    echo "  help    - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动爬虫"
    echo "  $0 status   # 查看状态"
    echo "  $0 stop     # 停止爬虫"
}

# 主逻辑
case "$1" in
    start)
        start_crawler
        ;;
    stop)
        stop_crawler
        ;;
    status)
        status_crawler
        ;;
    log)
        log_crawler
        ;;
    verify)
        verify_data
        ;;
    clean)
        clean_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "❌ 未知命令: $1"
        show_help
        exit 1
        ;;
esac