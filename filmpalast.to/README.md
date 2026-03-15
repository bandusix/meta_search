# Filmpalast.to Crawler 🕷️

这是一个基于 Python 的高性能爬虫项目，专门用于抓取 Filmpalast.to 网站的电影和电视剧信息。支持全量爬取、增量更新、多线程并发、数据自动去重以及 Docker 容器化部署。

## ✨ 核心特性

- **多线程并发**：支持配置线程数，大幅提升爬取速度。
- **智能去重**：基于 SQLite 数据库和内存缓存，自动跳过已存在的电影和剧集，节省资源。
- **自动页数探测**：智能识别网站最大页数，支持自适应扩展。
- **增量更新**：提供专门的增量更新脚本，仅检查最新发布的页面。
- **抗反爬机制**：内置随机 User-Agent、请求重试和延时策略。
- **完整数据提取**：提取标题、海报、评分（IMDb/站内）、清晰度、播放量、年份等详细信息。
- **播放器链接修正**：自动为所有详情页链接添加 `#video_player` 锚点，便于直接调起播放器。
- **Docker 支持**：提供完整的 Docker 环境配置，支持一键部署和定时任务。

## 📂 目录结构

```
filmpalast_crawler/
├── config/
│   └── config.yaml          # 爬虫配置文件
├── src/
│   ├── crawler.py           # 核心爬虫逻辑
│   ├── database.py          # 数据库管理
│   └── exporter.py          # 数据导出工具
├── data/
│   └── database.db          # SQLite 数据库文件（自动生成）
├── logs/                    # 运行日志
├── exports/                 # 导出的 Excel/CSV 文件
├── run_full_crawl.py        # 全量爬取脚本
├── run_incremental_crawl.py # 增量更新脚本
├── deploy.sh                # Linux/Mac 部署脚本
├── deploy.bat               # Windows 部署脚本
├── Dockerfile               # Docker 构建文件
├── docker-compose.yml       # Docker 编排文件
└── requirements.txt         # Python 依赖
```

## 🚀 快速开始 (本地运行)

### 前置条件
- Python 3.9+
- pip

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行爬虫

**全量爬取**（适合首次运行）：
```bash
# 默认使用 10 个线程
python run_full_crawl.py

# 指定 20 个线程
python run_full_crawl.py --threads 20
```

**增量更新**（适合日常维护）：
```bash
# 默认检查前 50 页
python run_incremental_crawl.py

# 指定检查前 100 页
python run_incremental_crawl.py --pages 100
```

### 3. 导出数据
将数据库中的数据导出为 Excel 文件：
```bash
python src/exporter.py
```

## 🐳 云端/Docker 部署

本项目已针对云环境优化，支持一键 Docker 部署。

### 1. 一键部署
**Linux / macOS**:
```bash
chmod +x deploy.sh
./deploy.sh
```

**Windows**:
双击运行 `deploy.bat`

### 2. 手动 Docker 部署
```bash
docker-compose up -d --build
```

### 3. 定时任务
容器启动后，内置的 Cron 服务会自动运行：
- **每天凌晨 03:00**：执行增量更新（检查前 100 页）。

### 4. 常用管理命令

查看日志：
```bash
docker-compose logs -f
```

在容器内手动运行全量爬取：
```bash
docker-compose exec crawler python run_full_crawl.py --threads 20
```

进入容器 Shell：
```bash
docker-compose exec crawler bash
```

## ⚙️ 配置说明

修改 `config/config.yaml` 可以调整爬虫行为：

```yaml
crawler:
  base_url: "https://filmpalast.to"
  timeout: 30          # 请求超时时间
  # ... 其他配置
```

## 📊 数据结构

数据存储在 SQLite `movies` 和 `tv_episodes` 表中。主要字段包括：
- `title`: 标题
- `url`: 详情页链接（已包含 #video_player）
- `poster_url`: 海报链接
- `year`: 年份
- `rating`: 站内评分
- `imdb_rating`: IMDb 评分
- `quality`: 清晰度 (1080p, 720p 等)
- `views`: 播放量
- `season`/`episode`: 季/集信息（仅剧集）

## ⚠️ 注意事项

1. **频率限制**：建议不要设置过高的线程数（推荐 10-50），以免对目标网站造成过大压力或被封禁。
2. **数据持久化**：Docker 部署时，`data` 目录已挂载到宿主机，重建容器不会丢失数据。
3. **网络环境**：如果部署在国外服务器，通常无需代理；如果在国内，可能需要配置 HTTP 代理。

---
*维护者：LobsterAI*
