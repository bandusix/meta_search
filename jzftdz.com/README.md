# 八戒影院 (jzftdz.com) 爬虫系统

一个生产级的Python爬虫系统，用于抓取八戒影院网站的电影和电视剧数据。

## 项目特点

- ✅ **100%验证的CSS选择器**: 所有解析逻辑均经过实地验证
- ✅ **模块化架构**: 清晰的代码分层，易于维护和扩展
- ✅ **鲁棒的错误处理**: 完善的重试机制和异常处理
- ✅ **断点续传**: 支持从中断点恢复爬取
- ✅ **数据规范化**: 采用多表设计，避免数据冗余
- ✅ **日志轮转**: 自动管理日志文件大小
- ✅ **CSV导出**: 支持全量和增量数据导出

## 项目结构

```
jzftdz_scraper/
├── config/              # 配置文件
│   └── settings.yaml    # 主配置文件
├── core/                # 核心模块
│   ├── base_spider.py   # 爬虫基类
│   ├── database.py      # 数据库管理
│   └── request_handler.py  # HTTP请求处理
├── spiders/             # 爬虫实现
│   ├── movie_spider.py  # 电影爬虫
│   └── tv_spider.py     # 电视剧爬虫
├── parsers/             # HTML解析器
│   ├── list_parser.py   # 列表页解析
│   ├── detail_parser.py # 详情页解析
│   └── play_parser.py   # 播放页解析
├── exporters/           # 数据导出
│   └── csv_exporter.py  # CSV导出器
├── utils/               # 工具模块
│   ├── logger.py        # 日志配置
│   └── url_builder.py   # URL构造
├── data/                # 数据目录
│   ├── logs/            # 日志文件
│   └── exports/         # 导出的CSV文件
├── main.py              # 主入口
├── requirements.txt     # 依赖列表
└── README.md            # 本文件
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置参数

编辑 `config/settings.yaml` 文件，根据需要调整：

- 爬取范围（年份、分类）
- 请求延迟和重试次数
- 数据库路径
- 日志级别

### 3. 运行爬虫

```bash
# 爬取所有内容（电影+电视剧）
python main.py --type all

# 仅爬取电影
python main.py --type movie

# 仅爬取电视剧
python main.py --type tv

# 使用自定义配置文件
python main.py --config /path/to/custom_config.yaml
```

### 4. 导出数据

```python
from core.database import DatabaseManager
from exporters.csv_exporter import CSVExporter
import yaml

# 加载配置
with open('config/settings.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 初始化数据库和导出器
db = DatabaseManager(config['database']['path'])
db.connect()

exporter = CSVExporter(
    db_manager=db,
    output_dir=config['export']['output_dir'],
    encoding=config['export']['encoding']
)

# 导出所有数据
exporter.export_all(export_type='full')

db.close()
```

## 数据库结构

### movies 表
存储电影基本信息（标题、导演、主演、简介、评分等）

### movie_sources 表
存储电影的播放源信息（支持多播放源）

### tv_series 表
存储电视剧基本信息

### tv_episodes 表
存储电视剧的分集信息（播放源、集数、播放链接）

### crawl_progress 表
记录爬取进度，用于断点续传

### export_logs 表
记录数据导出历史

## 配置说明

### 爬虫设置 (spider)

- `base_url`: 目标网站URL
- `delay_range`: 请求间隔范围（秒）
- `max_retries`: 最大重试次数
- `timeout`: 请求超时时间
- `user_agents`: User-Agent列表（随机轮换）

### 爬取任务 (crawl)

- `year_start`: 起始年份
- `year_end`: 结束年份
- `max_pages_per_year`: 每年最大爬取页数（null表示不限制）
- `fetch_rating`: 是否获取评分（需额外请求播放页）
- `categories`: 分类ID配置

### 日志设置 (logging)

- `level`: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- `format`: 日志格式
- `file`: 日志文件路径
- `max_bytes`: 单个日志文件最大大小
- `backup_count`: 保留的备份日志文件数量

## 注意事项

1. **遵守网站规则**: 请合理设置请求延迟，避免对目标网站造成过大压力
2. **法律合规**: 仅用于学习和研究目的，请勿用于商业用途
3. **数据更新**: 网站结构可能发生变化，如遇解析错误请检查CSS选择器
4. **存储空间**: 完整爬取约95,000+资源需要较大存储空间

## 故障排查

### 问题：解析失败
- 检查网站HTML结构是否变化
- 查看日志文件中的详细错误信息
- 验证CSS选择器是否仍然有效

### 问题：数据库锁定
- 确保没有多个进程同时访问数据库
- 检查数据库文件权限

### 问题：请求被拒绝
- 增加 `delay_range` 的值
- 更换 User-Agent
- 检查IP是否被封禁

## 许可证

本项目仅供学习和研究使用。

## 作者

Manus AI

## 更新日志

### v3.0 (2026-02-12)
- 完全重写，采用模块化架构
- 修正所有CSS选择器错误
- 实现生产级数据库设计
- 添加完善的日志和错误处理
- 支持断点续传和增量导出
