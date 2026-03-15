@echo off
cd /d "%~dp0"
echo Starting incremental crawl...
python mjwu_spider/main.py --mode all --incremental
echo Done.
pause
