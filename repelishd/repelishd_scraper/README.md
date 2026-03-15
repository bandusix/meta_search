# RepelisHD 爬虫项目 (RepelisHD Scraper)

本项目是一个针对 RepelisHD 网站的视频资源爬虫工具，专为云端数据采集和导出设计。它能够抓取电影和电视剧的详细信息，包括标题、年份、质量、评分以及**视频播放源链接 (embed_url)**，并将数据存储在 SQLite 数据库中，支持导出为 CSV 格式。

## 📅 最近更新 (Latest Updates)

- **[2026-02-09] 导出格式统一**: 电影和电视剧的导出格式统一为 CSV (`utf-8-sig` 编码)，完美兼容 Excel，且文件体积更小。
- **[2026-02-09] 视频源链接增强**: 电视剧集现在支持抓取多个播放源（如 Supervideo, Dropload 等），并在数据库和导出文件中以逗号分隔的形式存储 (`url1,url2`)。
- **[2026-02-09] 增量检查优化**: 修复了电视剧去重逻辑，现在会同时检查 `detail_url` 和 `embed_url`，确保所有剧集都能完整抓取到播放链接。

## 🚀 快速开始 (Quick Start)

### 1. 环境准备
确保已安装 Python 3.10+。

```bash
pip install -r requirements.txt
```

### 2. 常用命令

#### 🕷️ 启动爬取任务 (推荐)
使用 `task` 命令可以灵活控制爬取数量和并发线程数。

```bash
# 爬取 50 部电影和 50 部电视剧，使用 40 个并发线程
python main.py task --movies 50 --tv 50 --threads 40

# 仅爬取电视剧
python main.py task --tv 100 --threads 20
```

参数说明：
- `--movies N`: 爬取最新的 N 部电影。
- `--tv N`: 爬取最新的 N 部电视剧。
- `--threads N`: 并发线程数 (默认 10，建议 20-50 以提高速度)。
- `--delay-min`, `--delay-max`: 请求间隔随机延迟范围 (默认 0.1 - 0.5 秒)。

#### 📤 导出数据
将数据库中的数据导出为 CSV 文件。

```bash
# 导出所有数据 (全量导出)
python main.py export --mode full

# 导出自上次导出以来的新增数据 (增量导出)
python main.py export --mode incremental
```
导出文件位于 `./exports` 目录，格式为 `repelishd_{type}_{mode}_{timestamp}.csv`。

#### 📊 查看统计
查看当前数据库中的数据量。
```bash
python main.py stats
```

## 🛠️ 技术细节与逻辑 (Developer Guide)

### 1. 爬取逻辑
- **电影 (Movies)**:
  - 遍历电影列表页。
  - 进入详情页抓取元数据（标题、年份、海报、简介等）。
  - **去重**: 如果数据库中已存在该详情页 URL，则跳过抓取。

- **电视剧 (TV Series)**:
  - 遍历电视剧列表页。
  - 进入详情页，解析所有季 (Season) 和集 (Episode)。
  - **视频源 (Embed URL)**:
    - 脚本会进入每一集的播放页，提取 `embed_url`。
    - **多源支持**: 脚本会提取默认的 `data-link` 以及 `.mirrors` 列表中的所有备用链接。
    - 存储格式: 多个链接使用逗号 `,` 分隔。
  - **去重**: 检查数据库中是否存在该集记录。逻辑优化为：不仅检查 `detail_url` 是否存在，还检查 `embed_url` 是否非空。如果之前抓取过但没抓到视频链，会重新抓取。

### 2. 数据存储
- **数据库**: SQLite (`repelishd.db`)
- **表结构**:
  - `movies`: 存储电影信息。
  - `tv_series`: 存储电视剧基本信息。
  - `tv_episodes`: 存储分集信息，包含关键字段 `embed_url`。

### 3. 导出说明
导出功能由 `exporter.py` 处理，生成的 CSV 文件经过优化，字段排序如下：

- **Movies CSV**:
  - `title_spanish` (标题)
  - `year` (年份)
  - `quality` (画质)
  - `rating` (评分)
  - `detail_url` (详情页链接)
  - ...其他字段

- **TV Episodes CSV**:
  - `title_spanish` (剧名)
  - `season` (季)
  - `episode` (集)
  - `episode_title` (集名)
  - `detail_url` (详情页链接)
  - **`embed_url`** (视频嵌入链接，多个链接用逗号分隔)
  - ...其他字段

## 📂 目录结构

```
repelishd_scraper/
├── main.py           # 入口脚本 (命令行处理)
├── movie_scraper.py  # 电影爬虫逻辑
├── tv_scraper.py     # 电视剧爬虫逻辑 (含 embed_url 提取)
├── database.py       # 数据库操作 (SQLite)
├── exporter.py       # 数据导出 (CSV)
├── repelishd.db      # 数据库文件
├── exports/          # 导出文件存放目录
└── requirements.txt  # 依赖库
```

## ⚠️ 注意事项
- **网络问题**: 如果遇到请求超时，请检查网络连接或适当调大 `--delay-min`。
- **并发控制**: 虽然支持高并发 (`--threads`)，但建议不要设置过高以免被目标网站封禁 IP，建议 20-50 之间。
