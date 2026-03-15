# 策驰影院 (jbljc.com) 爬虫系统交付文档

## 1. 项目简介

本项目是一个针对 **策驰影院 (jbljc.com)** 的全量及增量数据爬取系统。
该网站主要提供 **中文 (简体/繁体)** 内容，覆盖 **电影** 和 **电视剧** 两大类资源。
受众群体主要是使用中文的影视爱好者。

**核心功能：**
*   **全量爬取**：从头遍历所有分页，采集所有历史数据。
*   **每日增量**：仅爬取最新的 N 页数据（默认前20页），高效更新。
*   **断点续传**：支持指定起始页码，应对意外中断。
*   **数据清洗**：自动规范化字段，处理缺失值。
*   **数据导出**：支持导出 CSV 格式数据（全量/增量）。

---

## 2. 环境要求

*   **操作系统**: Linux (推荐 Ubuntu 20.04+) / Windows / macOS
*   **Python 版本**: 3.8+
*   **依赖库**: 见 `requirements.txt`

---

## 3. 部署指南

### 3.1 获取代码
将项目包解压至服务器目标目录，例如 `/opt/spider_project`。

### 3.2 安装依赖
```bash
cd /opt/spider_project
pip3 install -r requirements.txt
```

### 3.3 初始化数据库
首次运行会自动创建 `spider_v2.db` SQLite 数据库文件。

---

## 4. 运行指南

### 4.1 全量初始化 (首次运行)
如果是第一次部署，建议执行全量爬取任务。

```bash
# 爬取所有电影和电视剧
python3 main.py --mode all --task init

# 仅爬取电影
python3 main.py --mode movie --task init

# 仅爬取电视剧
python3 main.py --mode tv --task init
```

*注意：全量爬取耗时较长，建议使用 `nohup` 或 `screen` 后台运行。*

### 4.2 每日增量更新 (推荐配置)
设置定时任务，每天定时执行增量爬取。默认爬取前 20 页更新内容。

```bash
# 执行每日增量任务（包含电影和电视剧）
python3 main.py --mode all --task daily
```

**Crontab 示例 (每天凌晨 2 点执行):**
```cron
0 2 * * * cd /opt/spider_project && /usr/bin/python3 main.py --mode all --task daily --export incremental >> /opt/spider_project/data/logs/cron.log 2>&1
```

### 4.3 数据导出
支持将数据库中的数据导出为 CSV 文件。

```bash
# 导出全量数据
python3 main.py --export full

# 导出本次运行的增量数据 (通常配合爬虫任务一起使用)
# python3 main.py --mode all --task daily --export incremental
```

数据将保存在 `data/exports/` 目录下。

### 4.4 断点续传
如果全量任务意外中断（例如在第 1000 页断开），可以通过 `--start-page` 参数恢复。

```bash
# 从第 1000 页开始继续爬取电影
python3 main.py --mode movie --task custom --start-page 1000
```

---

## 5. 项目结构说明

```
project/
├── config/
│   └── settings.yaml    # 配置文件 (URL, User-Agent, 延迟, 任务参数)
├── core/                # 核心库 (BaseSpider)
├── spiders/             # 具体爬虫实现
│   ├── movie_spider.py  # 电影爬虫
│   └── tv_spider.py     # 电视剧爬虫
├── exporters/           # 导出模块
├── data/
│   ├── logs/            # 运行日志
│   └── exports/         # 导出的 CSV 文件
├── main.py              # 程序入口
├── spider_v2.db         # SQLite 数据库 (自动生成)
└── requirements.txt     # 依赖列表
```

## 6. 维护说明

1.  **域名更换**: 如果目标网站域名变更（例如从 `jbljc.com` 变为其他），请修改 `config/settings.yaml` 中的 `base_url`。
2.  **反爬虫策略**:
    *   配置文件中 `delay_range` 控制请求随机延迟，默认为 `[2, 5]` 秒。
    *   如果遇到 403 错误，建议增大延迟或配置代理 IP（需修改代码中的 `requests` 部分）。
3.  **日志排查**: 查看 `data/logs/spider.log` 获取详细运行信息。

---

**交付日期**: 2026-03-02
**开发者**: Trae AI
