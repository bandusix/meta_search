# Cuevana3 爬虫 - 5分钟快速入门

## 📦 第一步：安装依赖

```bash
pip install requests beautifulsoup4 urllib3
```

## 🚀 第二步：开始使用

### 场景1：爬取2025年的电影

```bash
python main.py movies --year-start 2025
```

**预期输出：**
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
```

### 场景2：爬取2020-2025年的电影（倒序）

```bash
python main.py movies --year-start 2020 --year-end 2025
```

系统会自动从2025年开始，倒序爬取到2020年。

### 场景3：爬取电视剧（限制10部）

```bash
python main.py tv --max-series 10
```

### 场景4：查看数据库统计

```bash
python main.py stats
```

**输出示例：**
```
============================================================
📊 数据库统计信息
============================================================

电影:
  总数: 37
  年份数: 1
  平均评分: 6.65

电视剧:
  剧集总数: 0
  独立剧集数: 0
  平均评分: 0

最新添加的电影 (前5部):
  - Приказната за Силјан (2025) - 8.0/10
  - La voz de Hind Rajab (2025) - 8.2/10
  ...
```

### 场景5：导出数据到CSV

```bash
# 导出电影
python main.py export --type movies

# 导出电视剧
python main.py export --type tv

# 导出所有数据
python main.py export --type all
```

## ⏰ 第三步：设置定时任务（可选）

### Linux/Mac

1. 编辑 crontab：
```bash
crontab -e
```

2. 添加每天凌晨2点执行的任务：
```
0 2 * * * /path/to/cuevana3_v2/schedule_task.sh
```

### Windows

1. 打开任务计划程序：Win + R → `taskschd.msc`
2. 创建基本任务
3. 触发器：每天凌晨 2:00
4. 操作：启动程序
   - 程序：`python.exe`
   - 参数：`main.py update`
   - 起始于：项目目录路径

## 📊 数据格式

### 电影 CSV 格式

```csv
id,title_spanish,title_original,year,rating,quality,url,created_at,updated_at
1,Приказната за Силјан,Приказната за Силјан,2025,8.0,HD,https://ww9.cuevana3.to/22763/prikaznata-za-siljan,2026-02-01 01:47:38,2026-02-01 01:47:38
```

### 电视剧 CSV 格式

```csv
id,title_spanish,title_original,year,rating,quality,season,episode,url,created_at,updated_at
1,Teherán,طهران,2020,7.5,HD,1,1,https://ww9.cuevana3.to/episodio/teheran-1x1,2026-02-01 02:00:00,2026-02-01 02:00:00
```

## 🔧 常用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--database, -db` | 数据库文件路径 | cuevana3.db |
| `--delay-min` | 最小延迟时间（秒） | 1.0 |
| `--delay-max` | 最大延迟时间（秒） | 3.0 |
| `--max-pages` | 最大页数限制 | 无限制 |
| `--max-series` | 最大电视剧数量 | 无限制 |

**示例：**
```bash
python main.py movies --year-start 2025 --max-pages 5 --delay-min 2 --delay-max 4
```

## 📝 所有可用命令

```bash
# 爬取电影
python main.py movies --year-start 2025
python main.py movies --year-start 2020 --year-end 2025
python main.py movies --year-start 2025 --max-pages 5

# 爬取电视剧
python main.py tv
python main.py tv --max-series 20
python main.py tv --max-pages 3

# 更新所有数据（推荐用于定时任务）
python main.py update

# 导出数据
python main.py export --type movies
python main.py export --type tv
python main.py export --type all

# 查看统计
python main.py stats

# 帮助信息
python main.py --help
python main.py movies --help
```

## 🎯 推荐工作流

### 初次使用

1. 爬取最近2年的电影：
```bash
python main.py movies --year-start 2024 --year-end 2025
```

2. 爬取20部热门电视剧：
```bash
python main.py tv --max-series 20
```

3. 查看统计信息：
```bash
python main.py stats
```

4. 导出数据：
```bash
python main.py export --type all
```

### 日常更新

设置定时任务，每天自动执行：
```bash
python main.py update
```

这个命令会自动：
- 更新最近2年的电影（每年最多5页）
- 更新最近20部电视剧（列表最多2页）

## 🐛 常见问题

**Q: 爬取速度太慢？**
A: 减少延迟时间（但不建议低于1秒）：
```bash
python main.py movies --year-start 2025 --delay-min 0.5 --delay-max 1
```

**Q: 数据重复了？**
A: 数据库会自动去重（基于URL），重复数据会被忽略。

**Q: 想要更详细的输出？**
A: 查看日志文件：
```bash
tail -f logs/scraper_*.log
```

**Q: 如何清空数据库重新开始？**
A: 删除数据库文件：
```bash
rm cuevana3.db
```

## 📚 更多信息

- 完整文档：[README.md](README.md)
- 定时任务设置：[CRONTAB_SETUP.md](CRONTAB_SETUP.md)
- 网站结构分析：[URL_STRUCTURE.md](URL_STRUCTURE.md)

---

**祝您使用愉快！** 🎉
