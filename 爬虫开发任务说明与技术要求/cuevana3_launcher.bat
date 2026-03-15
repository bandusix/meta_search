@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: ============================================================
:: Cuevana3 爬虫系统 - Windows 一键启动脚本
:: 版本: 1.0
:: ============================================================

:: 设置颜色（需要 Windows 10+）
color 0A

:: 设置标题
title Cuevana3 爬虫系统 - 一键启动器

:: 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

:: 配置文件路径
set "CONFIG_FILE=%SCRIPT_DIR%config.ini"

:: 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ 错误: 未检测到 Python！
    echo.
    echo 请先安装 Python 3.7+ 并添加到系统 PATH
    echo 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: 检查依赖是否安装
python -c "import requests, bs4" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ⚠️  检测到缺少依赖包，正在自动安装...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ❌ 依赖安装失败！请手动执行: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo ✅ 依赖安装完成！
    timeout /t 2 >nul
)

:MAIN_MENU
cls
echo.
echo ============================================================
echo           Cuevana3 爬虫系统 - Windows 一键启动器
echo ============================================================
echo.
echo 当前配置:
python config_manager.py --show-brief 2>nul
if errorlevel 1 (
    echo   数据库: cuevana3.db
    echo   导出目录: 当前目录
)
echo.
echo ============================================================
echo.
echo 【电影爬取】
echo   1. 爬取单个年份的电影
echo   2. 爬取年份范围的电影（倒序）
echo   3. 快速爬取最近2年电影
echo.
echo 【电视剧爬取】
echo   4. 爬取电视剧（自定义数量）
echo   5. 快速爬取20部电视剧
echo.
echo 【数据管理】
echo   6. 更新所有数据（推荐定时任务）
echo   7. 导出数据到 CSV
echo   8. 查看数据库统计
echo   9. 清空数据库
echo.
echo 【系统设置】
echo   A. 配置管理（数据库路径、导出目录等）
echo   B. 查看日志
echo   C. 打开项目目录
echo.
echo   0. 退出程序
echo.
echo ============================================================
echo.
set /p choice="请选择功能 (0-9, A-C): "

if /i "%choice%"=="1" goto SCRAPE_SINGLE_YEAR
if /i "%choice%"=="2" goto SCRAPE_YEAR_RANGE
if /i "%choice%"=="3" goto SCRAPE_RECENT_MOVIES
if /i "%choice%"=="4" goto SCRAPE_TV_CUSTOM
if /i "%choice%"=="5" goto SCRAPE_TV_QUICK
if /i "%choice%"=="6" goto UPDATE_ALL
if /i "%choice%"=="7" goto EXPORT_DATA
if /i "%choice%"=="8" goto SHOW_STATS
if /i "%choice%"=="9" goto CLEAR_DATABASE
if /i "%choice%"=="A" goto CONFIG_MENU
if /i "%choice%"=="a" goto CONFIG_MENU
if /i "%choice%"=="B" goto VIEW_LOGS
if /i "%choice%"=="b" goto VIEW_LOGS
if /i "%choice%"=="C" goto OPEN_FOLDER
if /i "%choice%"=="c" goto OPEN_FOLDER
if /i "%choice%"=="0" goto EXIT

echo.
echo ❌ 无效选择，请重新输入！
timeout /t 2 >nul
goto MAIN_MENU

:: ============================================================
:: 电影爬取功能
:: ============================================================

:SCRAPE_SINGLE_YEAR
cls
echo.
echo ============================================================
echo                    爬取单个年份的电影
echo ============================================================
echo.
set /p year="请输入年份 (例如: 2025): "

if "%year%"=="" (
    echo ❌ 年份不能为空！
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
set /p max_pages="请输入最大页数限制 (留空表示不限制): "

echo.
echo 开始爬取 %year% 年的电影...
echo.

if "%max_pages%"=="" (
    python main.py movies --year-start %year%
) else (
    python main.py movies --year-start %year% --max-pages %max_pages%
)

echo.
echo ============================================================
echo 爬取完成！
echo ============================================================
pause
goto MAIN_MENU

:SCRAPE_YEAR_RANGE
cls
echo.
echo ============================================================
echo              爬取年份范围的电影（倒序）
echo ============================================================
echo.
set /p year_start="请输入起始年份 (例如: 2020): "
set /p year_end="请输入结束年份 (例如: 2025): "

if "%year_start%"=="" (
    echo ❌ 起始年份不能为空！
    timeout /t 2 >nul
    goto MAIN_MENU
)

if "%year_end%"=="" (
    echo ❌ 结束年份不能为空！
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
set /p max_pages="请输入每年最大页数限制 (留空表示不限制): "

echo.
echo 开始爬取 %year_start%-%year_end% 年的电影（倒序）...
echo 顺序: %year_end% → %year_start%
echo.

if "%max_pages%"=="" (
    python main.py movies --year-start %year_start% --year-end %year_end%
) else (
    python main.py movies --year-start %year_start% --year-end %year_end% --max-pages %max_pages%
)

echo.
echo ============================================================
echo 爬取完成！
echo ============================================================
pause
goto MAIN_MENU

:SCRAPE_RECENT_MOVIES
cls
echo.
echo ============================================================
echo                快速爬取最近2年电影
echo ============================================================
echo.

:: 获取当前年份
for /f "tokens=1-3 delims=/ " %%a in ('date /t') do (
    set current_year=%%c
)

set /a last_year=%current_year%-1

echo 将爬取 %last_year% 和 %current_year% 年的电影（每年最多10页）
echo.
echo 开始爬取...
echo.

python main.py movies --year-start %last_year% --year-end %current_year% --max-pages 10

echo.
echo ============================================================
echo 爬取完成！
echo ============================================================
pause
goto MAIN_MENU

:: ============================================================
:: 电视剧爬取功能
:: ============================================================

:SCRAPE_TV_CUSTOM
cls
echo.
echo ============================================================
echo              爬取电视剧（自定义数量）
echo ============================================================
echo.
set /p max_series="请输入要爬取的电视剧数量 (例如: 50): "

if "%max_series%"=="" (
    echo ❌ 数量不能为空！
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
set /p max_pages="请输入电视剧列表最大页数 (留空表示不限制): "

echo.
echo 开始爬取 %max_series% 部电视剧...
echo.

if "%max_pages%"=="" (
    python main.py tv --max-series %max_series%
) else (
    python main.py tv --max-series %max_series% --max-pages %max_pages%
)

echo.
echo ============================================================
echo 爬取完成！
echo ============================================================
pause
goto MAIN_MENU

:SCRAPE_TV_QUICK
cls
echo.
echo ============================================================
echo                快速爬取20部电视剧
echo ============================================================
echo.
echo 将爬取最近20部电视剧的所有剧集...
echo.
echo 开始爬取...
echo.

python main.py tv --max-series 20 --max-pages 2

echo.
echo ============================================================
echo 爬取完成！
echo ============================================================
pause
goto MAIN_MENU

:: ============================================================
:: 数据管理功能
:: ============================================================

:UPDATE_ALL
cls
echo.
echo ============================================================
echo                  更新所有数据
echo ============================================================
echo.
echo 此操作将：
echo   - 更新最近2年的电影（每年最多5页）
echo   - 更新最近20部电视剧（列表最多2页）
echo.
echo 推荐用于定时任务！
echo.
set /p confirm="确认执行？(Y/N): "

if /i not "%confirm%"=="Y" (
    echo 已取消操作
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
echo 开始更新...
echo.

python main.py update

echo.
echo ============================================================
echo 更新完成！
echo ============================================================
pause
goto MAIN_MENU

:EXPORT_DATA
cls
echo.
echo ============================================================
echo                  导出数据到 CSV
echo ============================================================
echo.
echo 请选择导出类型:
echo   1. 仅导出电影
echo   2. 仅导出电视剧
echo   3. 导出所有数据
echo   0. 返回主菜单
echo.
set /p export_choice="请选择 (0-3): "

if "%export_choice%"=="1" set export_type=movies
if "%export_choice%"=="2" set export_type=tv
if "%export_choice%"=="3" set export_type=all
if "%export_choice%"=="0" goto MAIN_MENU

if not defined export_type (
    echo ❌ 无效选择！
    timeout /t 2 >nul
    goto EXPORT_DATA
)

echo.
echo 开始导出 %export_type% 数据...
echo.

python main.py export --type %export_type%

echo.
echo ============================================================
echo 导出完成！
echo ============================================================
echo.
echo 是否打开导出目录？(Y/N): 
set /p open_folder=""

if /i "%open_folder%"=="Y" (
    start explorer "%SCRIPT_DIR%"
)

pause
goto MAIN_MENU

:SHOW_STATS
cls
echo.
echo ============================================================
echo                  数据库统计信息
echo ============================================================
echo.

python main.py stats

echo.
echo ============================================================
pause
goto MAIN_MENU

:CLEAR_DATABASE
cls
echo.
echo ============================================================
echo                    清空数据库
echo ============================================================
echo.
echo ⚠️  警告: 此操作将删除所有数据，无法恢复！
echo.
set /p confirm="确认清空数据库？(输入 YES 确认): "

if /i not "%confirm%"=="YES" (
    echo 已取消操作
    timeout /t 2 >nul
    goto MAIN_MENU
)

echo.
echo 正在清空数据库...

python config_manager.py --get database_path > temp_db_path.txt
set /p db_path=<temp_db_path.txt
del temp_db_path.txt

if exist "%db_path%" (
    del "%db_path%"
    echo ✅ 数据库已清空！
) else (
    echo ⚠️  数据库文件不存在
)

echo.
pause
goto MAIN_MENU

:: ============================================================
:: 系统设置功能
:: ============================================================

:CONFIG_MENU
cls
echo.
echo ============================================================
echo                      配置管理
echo ============================================================
echo.
echo 当前配置:
python config_manager.py --show
echo.
echo ============================================================
echo.
echo   1. 设置数据库路径
echo   2. 设置导出目录
echo   3. 设置延迟时间
echo   4. 重置为默认配置
echo   0. 返回主菜单
echo.
set /p config_choice="请选择 (0-4): "

if "%config_choice%"=="1" goto SET_DATABASE_PATH
if "%config_choice%"=="2" goto SET_EXPORT_DIR
if "%config_choice%"=="3" goto SET_DELAY
if "%config_choice%"=="4" goto RESET_CONFIG
if "%config_choice%"=="0" goto MAIN_MENU

echo ❌ 无效选择！
timeout /t 2 >nul
goto CONFIG_MENU

:SET_DATABASE_PATH
echo.
echo 当前数据库路径:
python config_manager.py --get database_path
echo.
set /p new_path="请输入新的数据库路径 (留空取消): "

if not "%new_path%"=="" (
    python config_manager.py --set database_path "%new_path%"
    echo ✅ 数据库路径已更新！
) else (
    echo 已取消操作
)

timeout /t 2 >nul
goto CONFIG_MENU

:SET_EXPORT_DIR
echo.
echo 当前导出目录:
python config_manager.py --get export_directory
echo.
set /p new_dir="请输入新的导出目录 (留空取消): "

if not "%new_dir%"=="" (
    python config_manager.py --set export_directory "%new_dir%"
    echo ✅ 导出目录已更新！
) else (
    echo 已取消操作
)

timeout /t 2 >nul
goto CONFIG_MENU

:SET_DELAY
echo.
echo 当前延迟时间:
python config_manager.py --get delay_min
python config_manager.py --get delay_max
echo.
set /p delay_min="请输入最小延迟时间（秒，留空取消）: "

if not "%delay_min%"=="" (
    set /p delay_max="请输入最大延迟时间（秒）: "
    python config_manager.py --set delay_min %delay_min%
    python config_manager.py --set delay_max %delay_max%
    echo ✅ 延迟时间已更新！
) else (
    echo 已取消操作
)

timeout /t 2 >nul
goto CONFIG_MENU

:RESET_CONFIG
echo.
echo ⚠️  确认重置所有配置为默认值？(Y/N): 
set /p confirm=""

if /i "%confirm%"=="Y" (
    python config_manager.py --reset
    echo ✅ 配置已重置！
) else (
    echo 已取消操作
)

timeout /t 2 >nul
goto CONFIG_MENU

:VIEW_LOGS
cls
echo.
echo ============================================================
echo                      查看日志
echo ============================================================
echo.

if not exist "logs\" (
    echo ⚠️  日志目录不存在
    pause
    goto MAIN_MENU
)

echo 最近的日志文件:
echo.
dir /b /o-d logs\scraper_*.log 2>nul | findstr /n "^" | findstr "^[1-5]:"

echo.
echo 是否打开日志目录？(Y/N): 
set /p open_logs=""

if /i "%open_logs%"=="Y" (
    start explorer "logs"
)

pause
goto MAIN_MENU

:OPEN_FOLDER
start explorer "%SCRIPT_DIR%"
goto MAIN_MENU

:EXIT
cls
echo.
echo ============================================================
echo              感谢使用 Cuevana3 爬虫系统！
echo ============================================================
echo.
timeout /t 2 >nul
exit /b 0
