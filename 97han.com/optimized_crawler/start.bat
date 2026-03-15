@echo off
REM 优化版97韩剧网爬虫启动脚本 (Windows版)

setlocal enabledelayedexpansion

REM 设置工作目录
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%"
cd /d "%PROJECT_DIR%"

REM 创建必要的目录
if not exist "logs" mkdir logs
if not exist "data" mkdir data
if not exist "backup" mkdir backup

REM 配置参数
set "PYTHON_CMD=python"
set "LOG_FILE=logs\crawler_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "ERROR_LOG=logs\crawler_error_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "PID_FILE=logs\crawler.pid"

REM 替换时间中的空格和冒号
set "LOG_FILE=!LOG_FILE: =0!"
set "LOG_FILE=!LOG_FILE::=!"
set "ERROR_LOG=!ERROR_LOG: =0!"
set "ERROR_LOG=!ERROR_LOG::=!"

REM 函数：检查进程是否在运行
:check_running
tasklist /FI "PID eq %1" 2>nul | find /I "%1" >nul
if "%errorlevel%"=="0" (
    echo ⚠️  爬虫进程已在运行 (PID: %1)
    exit /b 0
) else (
    exit /b 1
)

REM 函数：启动爬虫
:start_crawler
echo 🚀 启动优化版97韩剧网爬虫...

REM 检查是否已在运行
if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    call :check_running !PID!
    if "%errorlevel%"=="0" (
        echo ⚠️  爬虫进程已在运行 (PID: !PID!)
        exit /b 1
    ) else (
        del "%PID_FILE%" 2>nul
    )
)

REM 备份旧数据库（如果存在）
if exist "optimized_crawler.db" (
    set "BACKUP_FILE=backup\crawler_db_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.db"
    set "BACKUP_FILE=!BACKUP_FILE: =0!"
    set "BACKUP_FILE=!BACKUP_FILE::=!"
    copy "optimized_crawler.db" "!BACKUP_FILE!" >nul
    echo 💾 数据库已备份到: !BACKUP_FILE!
)

REM 启动爬虫（后台运行）
echo 📊 开始全站爬取任务...
echo 📄 日志文件: %LOG_FILE%
echo ❌ 错误日志: %ERROR_LOG%

start /B %PYTHON_CMD% -u optimized_crawler\main_crawler.py > "%LOG_FILE%" 2> "%ERROR_LOG%"
set PID=!errorlevel!

if "%PID%"=="0" (
    echo ❌ 爬虫启动失败
    exit /b 1
)

echo !PID! > "%PID_FILE%"
echo ✅ 爬虫已启动 (PID: !PID!)
echo 📝 查看日志: type "%LOG_FILE%"
echo 🛑 停止爬虫: %0 stop
exit /b 0

REM 函数：停止爬虫
:stop_crawler
echo 🛑 停止爬虫进程...

if exist "%PID_FILE%" (
    set /p PID=<"%PID_FILE%"
    taskkill /PID !PID! /T /F >nul 2>&1
    if "%errorlevel%"=="0" (
        echo ✅ 爬虫进程已停止 (PID: !PID!)
    ) else (
        echo ⚠️  进程不存在或已停止
    )
    del "%PID_FILE%" 2>nul
) else (
    echo ⚠️  没有找到PID文件，尝试查找Python爬虫进程...
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main_crawler*" >nul 2>&1
    echo ✅ 已尝试停止相关进程
)
exit /b 0

REM 函数：查看状态
:status_crawler
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *main_crawler*" 2>nul | find "python.exe" >nul
if "%errorlevel%"=="0" (
    echo 🟢 爬虫运行中
    
    REM 显示进程信息
    tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq *main_crawler*" /FO LIST | find "PID"
    
    REM 显示最近的日志
    echo.
    echo 📊 最近10条日志:
    if exist "logs\crawler_*.log" (
        for /f "delims=" %%i in ('dir /b /od logs\crawler_*.log') do set "LATEST_LOG=logs\%%i"
        if exist "!LATEST_LOG!" (
            type "!LATEST_LOG!" | findstr /C:"成功" /C:"失败" /C:"错误" /C:"完成" | tail -n 10 2>nul || echo 暂无相关日志
        )
    ) else (
        echo 暂无日志文件
    )
    
    REM 显示数据库统计
    echo.
    echo 💾 数据库统计:
    %PYTHON_CMD% -c "
import sqlite3
try:
    conn = sqlite3.connect('optimized_crawler.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM movies')
    movies = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM episodes')
    episodes = cursor.fetchone()[0]
    print(f'电影: {movies} 部')
    print(f'剧集: {episodes} 集')
    conn.close()
except:
    print('无法获取数据库统计')
" 2>nul || echo 无法获取数据库统计
) else (
    echo 🔴 爬虫未运行
)
exit /b 0

REM 函数：查看实时日志
:log_crawler
if exist "logs\crawler_*.log" (
    for /f "delims=" %%i in ('dir /b /od logs\crawler_*.log') do set "LATEST_LOG=logs\%%i"
    if exist "!LATEST_LOG!" (
        echo 📊 查看实时日志 (按 Ctrl+C 退出)...
        type "!LATEST_LOG!" | more
    ) else (
        echo ❌ 没有找到日志文件
    )
) else (
    echo ❌ 没有找到日志文件
)
exit /b 0

REM 函数：运行数据验证
:verify_data
echo 🔍 开始数据验证...
%PYTHON_CMD% optimized_crawler\verify.py
exit /b 0

REM 函数：清理日志
:clean_logs
echo 🧹 清理日志文件...
forfiles /p logs /s /m *.log /d -7 /c "cmd /c del @path" 2>nul
echo ✅ 已清理7天前的日志文件
exit /b 0

REM 函数：显示帮助
:show_help
echo 优化版97韩剧网爬虫控制脚本
echo 用法: %0 {start^|stop^|status^|log^|verify^|clean^|help}
echo.
echo 命令:
echo   start   - 启动爬虫 (后台运行)
echo   stop    - 停止爬虫
echo   status  - 查看爬虫状态
echo   log     - 查看实时日志
echo   verify  - 运行数据验证
echo   clean   - 清理旧日志
echo   help    - 显示帮助信息
echo.
echo 示例:
echo   %0 start    # 启动爬虫
echo   %0 status   # 查看状态
echo   %0 stop     # 停止爬虫
exit /b 0

REM 主逻辑
if "%1"=="" goto show_help
if /i "%1"=="start" goto start_crawler
if /i "%1"=="stop" goto stop_crawler
if /i "%1"=="status" goto status_crawler
if /i "%1"=="log" goto log_crawler
if /i "%1"=="verify" goto verify_data
if /i "%1"=="clean" goto clean_logs
if /i "%1"=="help" goto show_help
if /i "%1"=="--help" goto show_help
if /i "%1"=="-h" goto show_help

echo ❌ 未知命令: %1
goto show_help