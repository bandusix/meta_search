FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖 (如有需要)
# RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建数据和导出目录
RUN mkdir -p data exports

# 环境变量
ENV PYTHONUNBUFFERED=1

# 默认命令 (可以被覆盖)
CMD ["python", "main.py", "daily"]
