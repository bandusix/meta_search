# RepelisHD 全量项目部署指南 (Full Project Deployment Guide)

本压缩包包含 RepelisHD 爬虫项目的完整源代码、当前数据库进度 (`repelishd.db`) 以及导出状态 (`export_state.json`)。云端部署后可直接基于现有进度继续爬取。

## 📦 包含内容

- **源代码**: 所有 Python 脚本 (`.py`)
- **数据库**: `repelishd.db` (包含截至打包时的所有电影和剧集数据)
- **导出状态**: `export_state.json` (记录了上次导出的时间点，用于增量导出)
- **依赖列表**: `requirements.txt`
- **文档**: `README.md` (项目详细说明)

## 🚀 部署步骤

### 1. 解压项目
将压缩包上传至服务器并解压：

```bash
tar -xzvf repelishd_full_package.tar.gz
cd repelishd_scraper
```

### 2. 安装依赖
确保服务器安装了 Python 3.10+。

```bash
pip install -r requirements.txt
```

### 3. 验证数据 (可选)
运行统计命令，确认数据库包含现有数据：

```bash
python main.py stats
```
*你应该能看到数万条电影和剧集记录。*

### 4. 继续爬取任务
使用 `task` 命令继续爬取。由于数据库已包含历史数据，爬虫会自动跳过已存在的 URL (去重逻辑已内置)。

```bash
# 示例：爬取最新的 50 部电影和 50 部电视剧，使用 40 个并发线程
python main.py task --movies 50 --tv 50 --threads 40
```

### 5. 导出数据
由于包含了 `export_state.json`，你可以直接运行增量导出，获取自上次打包后新爬取的数据。

```bash
# 增量导出 (推荐)
python main.py export --mode incremental

# 全量导出 (如果需要重新生成所有数据的 CSV)
python main.py export --mode full
```

## ⚠️ 注意事项

- **相对路径**: 本项目所有文件路径（数据库、日志、导出目录）均使用**相对路径**。
  - 数据库: `./repelishd.db`
  - 导出目录: `./exports/`
  - 日志文件: `./crawl.log`
- **迁移**: 如果需要移动项目，只需移动整个文件夹即可，只要保持相对结构不变，程序即可正常运行。
