@echo off
cd /d "%~dp0"
echo Starting full crawl task...
echo Logs will be saved to crawl.log
set PYTHONIOENCODING=utf-8
REM 设置为 100000 以确保覆盖网站所有内容
REM 增加 --threads 40 参数以提高速度
python -u main.py task --movies 100000 --tv 100000 --threads 40
echo Task finished.
pause
