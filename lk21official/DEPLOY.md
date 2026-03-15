# LK21 Movie Scraper Deployment Guide

## 1. 项目简介 (Project Overview)

本项目是针对 **Layarkaca21 (LK21)** 网站的电影/电视剧数据爬虫。

*   **目标网站 (Target Website)**: `https://tv8.lk21official.cc` (及相关镜像)
*   **目标国家 (Target Country)**: **印度尼西亚 (Indonesia)**
    *   该网站主要服务于印尼地区的流媒体用户。
*   **目标语言 (Target Language)**: **印尼语 (Indonesian / Bahasa Indonesia)**
    *   网站界面、电影简介、字幕信息等均为印尼语。
    *   爬虫抓取的数据（如 `description`、`genre`）主要为印尼语或英语。

*   **主要功能**:
    *   全站电影数据抓取 (2026年至今)
    *   每日增量数据更新 (Daily Incremental Update)
    *   自动分类 (电影 vs 电视剧)
    *   断点续传与去重
    *   数据导出 (Excel/CSV)

## 2. 部署前准备 (Prerequisites)

*   **Python 版本**: 3.9+
*   **依赖库**: 见 `requirements.txt`
*   **网络环境**: 需要能够访问目标网站 (可能需要代理，代码中已集成 Webshare 代理配置)

## 3. 安装与配置 (Installation)

1.  **解压项目包**:
    ```bash
    unzip lk21_scraper.zip
    cd lk21_scraper
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置代理 (可选)**:
    *   代码中 `movie_scraper.py` 已内置代理 API。如需更换，请修改 `LK21MovieScraper.PROXY_LIST_URL`。

## 4. 运行指南 (Usage Guide)

### 4.1 全量初始化爬取 (Initial Full Scan)
首次部署时，建议运行全量扫描以建立基准数据库。

```bash
# 从 2026 年开始倒序爬取所有年份，开启断点续传，50 个线程
python main.py scrape --full-scan --resume --threads 50
```
*   **注意**: 全量爬取耗时较长，进度会自动保存至 `scraper_progress.json`。中断后再次运行相同命令即可恢复。

### 4.2 每日增量爬取 (Daily Incremental Update)
用于生产环境的日常维护，仅检查当年和去年的新数据，遇到已存在记录会自动停止。

```bash
# 每日运行一次
python main.py daily --threads 10
```
*   建议设置 Crontab 每天执行。

### 4.3 导出数据 (Export Data)
将数据库导出为 Excel 文件。

```bash
# 导出全量数据
python main.py export --all --excel

# 导出最近 1 天新增的数据
python main.py export --days 1 --excel
```
*   导出文件保存在 `exports/` 目录。

### 4.4 数据库清理与修复 (Database Cleanup)
如果发现数据格式有问题（如时长、标题），可运行清理命令。

```bash
python main.py cleanup
```

## 5. 生产环境部署 (Production Deployment)

### 方案 A: Docker 部署 (推荐)

1.  **构建镜像**:
    ```bash
    docker build -t lk21-scraper .
    ```

2.  **运行每日任务 (Crontab / Scheduler)**:
    使用 Docker 运行每日增量任务，并将数据卷挂载到宿主机以持久化数据库。
    ```bash
    # 示例: 每天凌晨 2 点运行
    docker run --rm -v $(pwd)/data:/app/data lk21-scraper python main.py daily
    ```
    *注意*: 确保数据库路径配置正确，建议修改代码或挂载时将 `lk21.db` 放在持久化目录。

### 方案 B: Linux Systemd / Crontab

1.  **设置 Crontab**:
    ```bash
    crontab -e
    ```
    添加如下行 (每天 03:00 执行):
    ```cron
    0 3 * * * cd /path/to/lk21_scraper && /usr/bin/python3 main.py daily >> daily.log 2>&1
    ```

## 6. 文件结构说明

*   `main.py`: 主入口程序 (包含 CLI 命令)
*   `movie_scraper.py`: 核心爬虫逻辑 (包含反爬、解析、增量判断)
*   `database.py`: SQLite 数据库操作
*   `csv_exporter.py`: 数据导出逻辑
*   `lk21.db`: SQLite 数据库文件 (核心数据)
*   `scraper_progress.json`: 全量爬取进度记录
*   `failed_urls.txt`: 失败 URL 记录

## 7. 维护与监控

*   **日志**: 查看控制台输出或重定向的日志文件。
*   **反爬策略**: 如果发现大量 403/404，请检查代理池是否有效 (`movie_scraper.py` 中的 `PROXY_LIST_URL`)。
*   **数据库备份**: 定期备份 `lk21.db`。

---
**交付清单**:
*   源代码文件夹
*   `requirements.txt`
*   `Dockerfile`
*   `DEPLOY.md` (本文档)
