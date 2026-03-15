# Cuevana3 爬虫系统

一个功能完整的 Cuevana3 网站爬虫系统，支持电影和电视剧数据爬取，包含详细元数据（评分、年份、清晰度、原标题等），支持定时任务每日自动更新，并使用 SQLite 数据库存储。

## ✨ 核心功能

### 🎬 电影爬取
- ✅ 按年份爬取电影数据
- ✅ 支持年份范围爬取（倒序，从最新年份开始）
- ✅ 自动分页处理
- ✅ 提取完整元数据：西语标题、原标题、年份、评分、清晰度、URL

### 📺 电视剧爬取
- ✅ 爬取所有电视剧列表
- ✅ 自动提取所有季和集
- ✅ 提取完整元数据：西语标题、原标题、年份、评分、清晰度、季数、集数、URL

### 💾 数据库管理
- ✅ SQLite 数据库存储
- ✅ 两个独立数据表（电影、电视剧）
- ✅ 自动去重（基于URL）
- ✅ 支持数据更新
- ✅ 导出为 CSV 格式

### ⏰ 定时任务
- ✅ 支持每日自动更新
- ✅ 完整的日志记录
- ✅ 自动清理旧日志
- ✅ 支持 Crontab、systemd timer、Windows 任务计划程序

### 🛡️ 反爬虫策略
- ✅ 随机 User-Agent
- ✅ 可配置延迟时间
- ✅ 请求失败自动重试
- ✅ SSL 验证禁用（应对证书问题）

## 📋 系统要求

- Python 3.7+
- 操作系统：Linux / macOS / Windows
- 网络：需要访问 ww9.cuevana3.to

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install requests beautifulsoup4 urllib3
```

### 2. 基本使用

#### 爬取电影

**爬取单个年份：**
```bash
python main.py movies --year-start 2025
```

**爬取年份范围（倒序）：**
```bash
python main.py movies --year-start 2020 --year-end 2025
```

**限制页数：**
```bash
python main.py movies --year-start 2025 --max-pages 5
```

#### 爬取电视剧

**爬取所有电视剧：**
```bash
python main.py tv
```

**限制电视剧数量：**
```bash
python main.py tv --max-series 20
```

**限制列表页数：**
```bash
python main.py tv --max-pages 3
```

#### 更新所有数据（推荐用于定时任务）

```bash
python main.py update
```

这个命令会：
- 更新最近2年的电影（每年最多5页）
- 更新最近20部电视剧（列表最多2页）

#### 导出数据

**导出电影：**
```bash
python main.py export --type movies
```

**导出电视剧：**
```bash
python main.py export --type tv
```

**导出所有数据：**
```bash
python main.py export --type all
```

#### 查看统计信息

```bash
python main.py stats
```

### 3. 配置参数

#### 全局参数

- `--database, -db`: 数据库文件路径（默认：cuevana3.db）
- `--delay-min`: 最小延迟时间（秒，默认：1.0）
- `--delay-max`: 最大延迟时间（秒，默认：3.0）

**示例：**
```bash
python main.py movies --year-start 2025 --database my_data.db --delay-min 2 --delay-max 5
```

## ⏰ 设置定时任务

### Linux/Mac (Crontab)

1. 编辑 crontab：
```bash
crontab -e
```

2. 添加定时任务（每天凌晨2点执行）：
```
0 2 * * * /path/to/cuevana3_v2/schedule_task.sh
```

3. 查看已设置的任务：
```bash
crontab -l
```

详细说明请参考：[CRONTAB_SETUP.md](CRONTAB_SETUP.md)

### Windows (任务计划程序)

1. 打开任务计划程序：Win + R → `taskschd.msc`
2. 创建基本任务
3. 设置触发器：每天凌晨2:00
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`main.py update`
   - 起始于：`C:\path\to\cuevana3_v2`

## 📁 项目结构

```
cuevana3_v2/
├── main.py                 # 主程序和命令行接口
├── database.py             # 数据库管理模块
├── movie_scraper.py        # 电影爬虫模块
├── tv_scraper.py           # 电视剧爬虫模块
├── schedule_task.sh        # 定时任务脚本
├── requirements.txt        # Python 依赖
├── README.md               # 本文档
├── CRONTAB_SETUP.md        # 定时任务设置详细说明
├── URL_STRUCTURE.md        # 网站URL结构分析
├── cuevana3.db             # SQLite 数据库（自动生成）
├── logs/                   # 日志目录（自动生成）
│   └── scraper_*.log
└── *.csv                   # 导出的CSV文件（手动生成）
```

## 📊 数据库结构

### movies 表（电影）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| title_spanish | TEXT | 西语标题 |
| title_original | TEXT | 原标题 |
| year | INTEGER | 年份 |
| rating | REAL | 评分（0-10） |
| quality | TEXT | 清晰度（HD, CAM等） |
| url | TEXT | 详情页URL（唯一） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### tv_series 表（电视剧）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| title_spanish | TEXT | 西语标题 |
| title_original | TEXT | 原标题 |
| year | INTEGER | 年份 |
| rating | REAL | 评分（0-10） |
| quality | TEXT | 清晰度 |
| season | INTEGER | 季数 |
| episode | INTEGER | 集数 |
| url | TEXT | 剧集详情页URL（唯一） |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 🔍 使用示例

### 示例1：爬取2024-2025年的所有电影

```bash
python main.py movies --year-start 2024 --year-end 2025
```

输出：
```
============================================================
🎬 开始爬取 2025 年的电影...
============================================================
📄 正在爬取第 1 页: https://ww9.cuevana3.to/year/2025
   找到 37 个电影链接
   [1/37] 正在爬取: https://ww9.cuevana3.to/22763/prikaznata-za-siljan
      ✅ Приказната за Силјан
   ...
✨ 2025 年爬取完成！共 37 部电影

💾 正在保存到数据库...
✅ 成功保存 37/37 部电影
📊 数据库统计:
   电影总数: 37
   平均评分: 6.65
```

### 示例2：爬取前10部电视剧的所有剧集

```bash
python main.py tv --max-series 10
```

### 示例3：查看数据库统计

```bash
python main.py stats
```

输出：
```
============================================================
📊 数据库统计信息
============================================================

电影:
  总数: 37
  年份数: 1
  平均评分: 6.65

电视剧:
  剧集总数: 120
  独立剧集数: 10
  平均评分: 7.8

最新添加的电影 (前5部):
  - Приказната за Силјан (2025) - 8.0/10
  - La voz de Hind Rajab (2025) - 8.2/10
  ...

最新添加的剧集 (前5集):
  - Teherán 1x1 (2020) - 7.5/10
  ...
```

### 示例4：导出数据并查看

```bash
# 导出电影数据
python main.py export --type movies

# 查看CSV文件
head -10 movies.csv
```

## 📝 日志管理

日志文件保存在 `logs/` 目录下，文件名格式：`scraper_YYYYMMDD_HHMMSS.log`

**查看最新日志：**
```bash
ls -lt logs/ | head -5
tail -100 logs/scraper_*.log
```

**日志自动清理：**
- 脚本会自动清理30天前的日志
- 可在 `schedule_task.sh` 中修改保留天数

## ⚙️ 高级配置

### 自定义延迟时间

```bash
python main.py movies --year-start 2025 --delay-min 2 --delay-max 5
```

### 使用自定义数据库

```bash
python main.py movies --year-start 2025 --database /path/to/my_database.db
```

### 导出到指定文件

```bash
python main.py export --type movies --output my_movies.csv
```

## 🐛 故障排除

### 问题1：SSL 证书错误

**症状：** `SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]`

**解决方案：** 脚本已自动禁用 SSL 验证，如果仍有问题，请检查网络连接。

### 问题2：请求超时

**症状：** `Timeout: HTTPSConnectionPool`

**解决方案：**
1. 检查网络连接
2. 增加延迟时间：`--delay-min 3 --delay-max 6`
3. 检查网站是否可访问

### 问题3：没有找到电影

**症状：** `找到 0 个电影链接`

**解决方案：**
1. 确认年份是否有数据
2. 检查网站URL结构是否变化
3. 查看 `URL_STRUCTURE.md` 确认最新结构

### 问题4：数据库锁定

**症状：** `database is locked`

**解决方案：**
1. 确保没有其他进程在使用数据库
2. 关闭所有数据库连接
3. 重启程序

## 📚 相关文档

- [CRONTAB_SETUP.md](CRONTAB_SETUP.md) - 定时任务设置详细说明
- [URL_STRUCTURE.md](URL_STRUCTURE.md) - 网站URL结构分析

## ⚠️ 注意事项

1. **合法使用**：本工具仅供学习和研究使用，请遵守网站的使用条款和robots.txt规定
2. **请求频率**：建议使用默认延迟时间（1-3秒），避免对服务器造成过大压力
3. **数据备份**：定期备份 `cuevana3.db` 数据库文件
4. **网站变化**：如果网站结构发生变化，可能需要更新爬虫代码
5. **Credit 消耗**：长时间运行会消耗大量网络流量和计算资源

## 🔄 更新日志

### v1.0.0 (2026-02-01)
- ✅ 初始版本发布
- ✅ 支持电影和电视剧爬取
- ✅ SQLite 数据库存储
- ✅ 定时任务支持
- ✅ CSV 导出功能
- ✅ 完整的命令行接口

## 📧 技术支持

如有问题或建议，请查看相关文档或提交 Issue。

## 📄 许可证

本项目仅供学习和研究使用。
