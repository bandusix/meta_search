@echo off
chcp 65001
echo ============================================================
echo 每日增量爬取 (电影 + 电视剧)
echo ============================================================
cd /d %~dp0

:: 激活 Python 环境 (如果有虚拟环境，请取消注释并修改路径)
:: call venv\Scripts\activate

:: 执行增量爬取
:: --threads 20: 使用20线程
:: 增量模式会自动检测旧数据并停止
python main.py incremental --threads 20

echo.
echo 🎉 增量更新完成！
pause
