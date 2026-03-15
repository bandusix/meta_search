# 优化版97韩剧网爬虫
# Optimized 97han.com Web Crawler

## 项目概述

这是一个基于Python 3.10+的高性能异步爬虫系统，专门用于爬取97韩剧网的全站视频内容。系统采用asyncio + aiohttp实现高并发，支持自动重试、错误处理、数据验证等功能。

## 技术特性

### 🚀 性能优化
- **异步架构**: 基于asyncio + aiohttp，最大并发数30
- **智能限速**: 200ms/请求，避免触发反爬机制
- **连接池**: 复用TCP连接，提高请求效率
- **批量处理**: 支持批量URL请求和数据处理

### 🛡️ 稳定性保障
- **自动重试**: 5xx错误自动重试3次，退避策略1s/2s/4s
- **403处理**: 自动降级User-Agent，启用代理池
- **超时控制**: 请求超时30秒，连接超时10秒
- **异常处理**: 完善的异常捕获和日志记录

### 📊 数据完整性
- **唯一索引**: (detail_url, route_name)防止重复数据
- **事务提交**: 每200条commit一次，保证数据一致性
- **数据验证**: 1%抽样验证，通过率≥98%
- **增量更新**: 支持后续增量数据更新

### 📝 日志系统
- **分级日志**: INFO记录成功/失败，ERROR记录异常
- **滚动日志**: 每日自动分割，保留7天历史
- **实时监控**: 支持实时日志查看和状态监控
- **错误追踪**: 详细的错误信息和堆栈追踪

## 安装部署

### 环境要求
- Python 3.10+
- SQLite 3.0+
- 4GB+ RAM
- 10GB+ 磁盘空间

### 快速安装
```bash
# 克隆项目
git clone <repository-url>
cd optimized_crawler

# 安装依赖
pip install -r requirements.txt

# 启动爬虫
chmod +x start.sh
./start.sh start
```

### 依赖包
```
aiohttp>=3.8.0
lxml>=4.9.0
asyncio
datetime
logging
sqlite3
```

## 使用说明

### 启动爬虫
```bash
# 启动全站爬取（后台运行）
./start.sh start

# 查看实时状态
./start.sh status

# 查看实时日志
./start.sh log

# 停止爬虫
./start.sh stop

# 数据验证
./start.sh verify
```

### 爬取范围
| 分类 | 起始页 | 结束页 | 总页数 |
|------|--------|--------|--------|
| 电影 | 1 | 1027 | 1027 |
| 电视剧 | 1 | 549 | 549 |
| 综艺 | 1 | 111 | 111 |
| 动漫 | 1 | 238 | 238 |
| 短剧 | 1 | 319 | 319 |
| 伦理MV | 1 | 177 | 177 |

### 数据字段
- **基本信息**: 标题、封面图、上映年份、地区、类型、简介
- **播放信息**: 播放线路名称、播放器URL、详情页URL
- **元数据**: 分类、爬取时间、更新时间

## 数据库结构

### 主表结构
```sql
-- 电影表
CREATE TABLE movies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,           -- 分类
    title TEXT NOT NULL,              -- 标题
    cover TEXT,                       -- 封面图URL
    year INTEGER,                     -- 上映年份
    region TEXT,                      -- 地区
    genre TEXT,                       -- 类型
    intro TEXT,                       -- 简介
    detail_url TEXT NOT NULL,         -- 详情页URL
    route_name TEXT NOT NULL,         -- 播放线路名称
    play_url TEXT NOT NULL,           -- 播放器URL
    crawl_time TIMESTAMP,             -- 爬取时间
    created_at TIMESTAMP,              -- 创建时间
    updated_at TIMESTAMP               -- 更新时间
);

-- 唯一索引
CREATE UNIQUE INDEX idx_movies_detail_route ON movies(detail_url, route_name);
```

### 性能优化
- **WAL模式**: 启用预写日志，提高并发性能
- **索引优化**: 针对查询字段建立索引
- **批量提交**: 每200条数据commit一次
- **连接复用**: 使用连接池减少数据库连接开销

## 监控与维护

### 实时监控
```bash
# 查看爬虫状态
./start.sh status

# 实时日志监控
./start.sh log

# 查看数据库统计
python3 -c "
from database import DatabaseManager
db = DatabaseManager()
stats = db.get_statistics()
print('电影:', stats.get('movies', 0))
print('剧集:', stats.get('episodes', 0))
"
```

### 数据验证
```bash
# 运行数据验证
./start.sh verify

# 验证报告包含：
# - 抽样通过率（要求≥98%）
# - 分类统计信息
# - 无效链接详情
# - 验证耗时统计
```

### 日志管理
```bash
# 清理7天前的日志
./start.sh clean

# 手动查看日志文件
ls -la logs/
tail -f logs/crawler.log
tail -f logs/crawler_error.log
```

## 性能指标

### 爬取性能
- **并发数**: 最大30个并发请求
- **请求延迟**: 200ms/请求
- **重试机制**: 3次重试，退避策略
- **超时设置**: 30秒请求超时

### 数据质量
- **完整性**: 播放线路缺失率<0.5%
- **准确性**: 数据验证通过率≥98%
- **去重率**: 100%（基于唯一索引）
- **时效性**: 8小时内完成全站爬取

### 资源消耗
- **内存使用**: <4GB
- **磁盘空间**: <10GB
- **网络带宽**: 自适应限速
- **CPU占用**: 低CPU占用设计

## 故障排除

### 常见问题

**Q: 爬虫启动失败**
A: 检查Python版本、依赖包安装、网络连接

**Q: 数据库连接错误**
A: 检查SQLite版本、磁盘空间、文件权限

**Q: 请求超时频繁**
A: 检查网络状况、调整超时参数、降低并发数

**Q: 数据验证不通过**
A: 检查目标网站结构变化、更新解析规则

### 日志分析
```bash
# 查看错误日志
grep -i "error\|failed\|exception" logs/crawler_error.log

# 统计成功率
grep -c "成功" logs/crawler.log
grep -c "失败" logs/crawler.log

# 查看重试情况
grep -i "retry\|重试" logs/crawler.log
```

## 更新维护

### 定期维护
- 每周清理日志文件
- 每月备份数据库
- 季度性能优化
- 年度架构升级

### 版本更新
- 监控依赖包安全更新
- 跟进Python版本升级
- 适配目标网站结构变化
- 优化爬取策略

## 联系方式

如有问题或建议，请通过以下方式联系：
- 邮箱: [your-email]
- 项目地址: [repository-url]
- 技术支持: [support-contact]

---

**注意**: 本爬虫仅供学习和研究使用，请遵守目标网站的robots.txt规则，合理控制爬取频率，避免对目标网站造成过大负载。