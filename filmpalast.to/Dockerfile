# 使用官方 Python 运行时作为父镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Berlin

# 安装系统依赖（如 cron）
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目代码
COPY . .

# 创建必要的目录
RUN mkdir -p logs exports data

# 设置 cron 任务
# 每天凌晨 3 点运行增量更新
# 每周一凌晨 4 点运行全量更新（可选，视数据量而定）
RUN echo "0 3 * * * cd /app && /usr/local/bin/python run_incremental_crawl.py --pages 100 >> /app/logs/cron_incremental.log 2>&1" > /etc/cron.d/crawler-cron
RUN chmod 0644 /etc/cron.d/crawler-cron
RUN crontab /etc/cron.d/crawler-cron

# 创建启动脚本
RUN echo '#!/bin/bash\n\
printenv | grep -v "no_proxy" >> /etc/environment\n\
service cron start\n\
# 首次启动时可以选择是否运行一次增量更新\n\
if [ "$RUN_ON_START" = "true" ]; then\n\
    echo "Running initial incremental crawl..."\n\
    python run_incremental_crawl.py\n\
fi\n\
# 保持容器运行\n\
tail -f /dev/null' > /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 暴露数据卷
VOLUME ["/app/data", "/app/logs", "/app/exports"]

# 启动命令
CMD ["/app/entrypoint.sh"]
