# 快速入门指南

## 5分钟快速开始

### 第一步：安装依赖
```bash
pip install requests beautifulsoup4
```

### 第二步：运行脚本

#### 场景 1：爬取单个年份（例如 2024 年）
```bash
python cuevana3_scraper.py 2024
```

#### 场景 2：爬取多个年份（倒序，从最新开始）
```bash
# 爬取 2020-2025 年，顺序：2025 → 2024 → 2023 → 2022 → 2021 → 2020
python cuevana3_scraper.py 2020 2025
```

#### 场景 3：爬取多个年份（正序）
```bash
# 爬取 2020-2025 年，顺序：2020 → 2021 → 2022 → 2023 → 2024 → 2025
python cuevana3_scraper.py 2020 2025 --no-reverse
```

### 第三步：查看结果
```bash
# 单年份输出文件
cat cuevana3_2024.csv

# 年份范围输出文件
cat cuevana3_2020-2025.csv
```

## 常用命令

### 自定义输出文件名
```bash
python cuevana3_scraper.py 2024 -o my_movies.csv
```

### 调整延迟时间（加快或减慢爬取速度）
```bash
# 更快（0.5-1秒延迟，但可能触发反爬虫）
python cuevana3_scraper.py 2024 --delay 0.5 1

# 更慢（2-5秒延迟，更安全）
python cuevana3_scraper.py 2024 --delay 2 5
```

### 查看帮助信息
```bash
python cuevana3_scraper.py -h
```

## 输出示例

### 单年份输出（cuevana3_2024.csv）
```csv
Title,URL
Sin piedad,https://cuevana3.top/pelicula/sin-piedad/
Search and Destroy,https://cuevana3.top/pelicula/search-and-destroy/
Solo para mi,https://cuevana3.top/pelicula/solo-para-mi/
```

### 年份范围输出（cuevana3_2024-2025.csv）
```csv
Year,Title,URL
2025,Sin piedad,https://cuevana3.top/pelicula/sin-piedad/
2025,Search and Destroy,https://cuevana3.top/pelicula/search-and-destroy/
2024,Solo para mi,https://cuevana3.top/pelicula/solo-para-mi/
```

## 注意事项

- ⏱️ **爬取时间**：单个年份约需 1-5 分钟（取决于页面数量和延迟设置）
- 🔄 **倒序爬取**：默认从最新年份开始，确保优先获取最新数据
- 🛡️ **反爬虫**：脚本已内置延迟和随机 User-Agent，建议使用默认设置
- 📊 **数据量**：每页约 10 部电影，总数据量取决于目标年份

## 完整文档

详细使用说明请参考 [README.md](README.md)
