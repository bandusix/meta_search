@echo off
echo 🚀 开始部署 Filmpalast Crawler...

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到 Docker。请先安装 Docker Desktop。
    pause
    exit /b 1
)

REM 构建并启动容器
echo 📦 构建 Docker 镜像...
docker-compose build

echo ▶️ 启动服务...
docker-compose up -d

echo ✅ 部署完成！
echo    - 容器已在后台运行
echo    - 数据将保存在 ./data 目录
echo    - 日志在 ./logs 目录
echo    - 定时任务已配置为每天凌晨 03:00 运行增量更新
echo.
echo 常用命令:
echo    - 查看日志: docker-compose logs -f
echo    - 手动运行增量更新: docker-compose exec crawler python run_incremental_crawl.py
echo    - 手动运行全量更新: docker-compose exec crawler python run_full_crawl.py
pause
