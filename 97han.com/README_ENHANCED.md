# 97韩剧爬虫增强版

## 🚀 功能特性

### 核心功能
- ✅ **全分类爬取**: 支持电影、电视剧、综艺、动漫、短剧、伦理MV等全部分类
- ✅ **播放线路提取**: 自动提取播放线路名称和网页播放器页面信息
- ✅ **结构化日志**: 标准化日志格式，支持Excel/Pandas导入分析
- ✅ **终端实时输出**: 详细显示每次爬取的请求、响应、异常信息
- ✅ **自动优化**: 每100条日志或5分钟自动扫描并调整参数
- ✅ **数据完整性校验**: 重复ID检测、哈希去重、布隆过滤器
- ✅ **零侵入集成**: 仅需替换或包裹原logger，无需修改核心逻辑

### 性能优化
- 🔄 **智能并发**: 根据响应时间自动调整并发数
- 🔄 **指数退避**: 失败时自动启用重试机制
- 🔄 **布隆过滤器**: 高效重复ID检测
- 🔄 **内存优化**: 日志轮转和缓冲区管理

## 📦 安装依赖

```bash
pip install requests beautifulsoup4 pandas openpyxl
```

## 🎯 快速开始

### 1. 使用增强版爬虫

```bash
# 爬取电影（慢速模式）
python enhanced_main.py --spider movie --cid 1 --max-pages 10 --delay 3 5

# 爬取电视剧
cd .. && python enhanced_main.py --spider tv --cid 2 --category-name "电视剧" --max-pages 5 --delay 3 5

# 爬取综艺
python enhanced_main.py --spider tv --cid 3 --category-name "综艺" --max-pages 3 --delay 3 5

# 爬取动漫
python enhanced_main.py --spider tv --cid 4 --category-name "动漫" --max-pages 3 --delay 3 5
```

### 2. 显示统计信息

```bash
# 查看爬取统计
python enhanced_main.py --show-stats

# 导出到Excel
python enhanced_main.py --export-excel
```

### 3. 运行单元测试

```bash
# 运行所有测试
python -m pytest tests/test_enhanced_logging.py -v

# 运行特定测试类
python -m pytest tests/test_enhanced_logging.py::TestEnhancedLogger -v

# 生成覆盖率报告
python -m pytest tests/test_enhanced_logging.py --cov=utils --cov-report=html
```

## 📊 日志分析

### 日志格式说明

日志文件 `crawl_progress.log` 使用管道符分隔的格式：

```
timestamp|spider_name|request_url|response_status|saved_data_fields|saved_id|item_count|elapsed_ms
```

示例：
```
2024-01-15 14:30:45.123|movie|http://www.97han.com/show/1-123-----------.html|200|["title","year","category"]|12345|1|1500
```

### 使用Pandas分析日志

```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取日志文件
df = pd.read_csv('crawl_progress.log', sep='|', 
                 names=['timestamp', 'spider_name', 'request_url', 'response_status', 
                        'saved_data_fields', 'saved_id', 'item_count', 'elapsed_ms'])

# 转换时间戳
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['elapsed_s'] = df['elapsed_ms'] / 1000

# 基本统计
print("📊 爬取统计:")
print(f"总请求数: {len(df)}")
print(f"成功请求: {len(df[df['response_status'] == 200])}")
print(f"失败请求: {len(df[df['response_status'] != 200])}")
print(f"平均响应时间: {df['elapsed_s'].mean():.2f}秒")
print(f"保存数据条数: {df['item_count'].sum()}")

# 按爬虫类型统计
spider_stats = df.groupby('spider_name').agg({
    'request_url': 'count',
    'elapsed_s': 'mean',
    'item_count': 'sum'
}).round(2)
print("\n📈 按爬虫类型统计:")
print(spider_stats)

# 响应时间分布
plt.figure(figsize=(10, 6))
plt.hist(df['elapsed_s'], bins=50, alpha=0.7, edgecolor='black')
plt.xlabel('响应时间 (秒)')
plt.ylabel('请求数')
plt.title('响应时间分布')
plt.grid(True, alpha=0.3)
plt.savefig('response_time_distribution.png', dpi=300, bbox_inches='tight')
plt.show()

# 每小时爬取数量
df['hour'] = df['timestamp'].dt.hour
hourly_stats = df.groupby('hour').size()

plt.figure(figsize=(12, 6))
hourly_stats.plot(kind='bar', color='skyblue', alpha=0.8)
plt.xlabel('小时')
plt.ylabel('请求数')
plt.title('每小时爬取数量')
plt.xticks(rotation=0)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('hourly_crawl_stats.png', dpi=300, bbox_inches='tight')
plt.show()
```

### 使用Excel分析日志

1. **打开Excel** → **数据** → **从文本/CSV**
2. 选择 `crawl_progress.log` 文件
3. 设置分隔符为 `|` (管道符)
4. 设置列名为：
   - timestamp, spider_name, request_url, response_status, 
   - saved_data_fields, saved_id, item_count, elapsed_ms
5. 使用Excel的数据透视表功能进行分析

## 🔧 配置选项

### 自动优化配置

在 `utils/auto_optimizer_config.json` 中可以配置：

```json
{
  "concurrency": 1,
  "retry_enabled": false,
  "bloom_filter_enabled": false,
  "response_time_threshold": 3.0,
  "failure_threshold": 0.1,
  "duplicate_threshold": 0.05,
  "monitoring_interval": 300,
  "log_buffer_size": 10,
  "auto_optimize_enabled": true
}
```

### 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| concurrency | 1 | 并发请求数 |
| retry_enabled | false | 是否启用重试机制 |
| bloom_filter_enabled | false | 是否启用布隆过滤器 |
| response_time_threshold | 3.0 | 响应时间阈值（秒） |
| failure_threshold | 0.1 | 失败率阈值（0.1=10%） |
| duplicate_threshold | 0.05 | 重复率阈值（0.05=5%） |
| monitoring_interval | 300 | 监控间隔（秒） |
| log_buffer_size | 10 | 日志缓冲区大小 |
| auto_optimize_enabled | true | 是否启用自动优化 |

## 🛠️ 开发指南

### 零侵入集成现有爬虫

#### 方法1：直接替换logger

```python
# 原代码
import logging
logger = logging.getLogger(__name__)

# 替换为增强版logger
from utils.enhanced_logger import logger as enhanced_logger
logger = enhanced_logger
```

#### 方法2：包装现有logger

```python
from utils.enhanced_logger import EnhancedLogger
from utils.data_validator import DataValidator
from utils.auto_optimizer import AutoOptimizer

class YourSpider:
    def __init__(self):
        # 初始化增强组件
        self.enhanced_logger = EnhancedLogger()
        self.validator = DataValidator()
        self.optimizer = AutoOptimizer()
        
        # 启动监控
        self.optimizer.start_monitoring()
    
    def crawl_page(self, url):
        """包装现有爬取方法"""
        # 记录请求开始
        self.enhanced_logger.log_request_start(self.spider_name, url)
        
        try:
            # 原有爬取逻辑
            result = self._original_crawl_page(url)
            
            # 记录请求完成
            self.enhanced_logger.log_request_complete(
                self.spider_name, url, 200,
                list(result.keys()), result.get('id'), 1, 1500.0
            )
            
            return result
            
        except Exception as e:
            # 记录错误
            self.enhanced_logger.log_error(
                self.spider_name, url, type(e).__name__, str(e)
            )
            raise
```

### 自定义日志字段

```python
# 添加自定义字段到日志
self.enhanced_logger.log_request_complete(
    spider_name="custom_spider",
    request_url="http://example.com",
    response_status=200,
    saved_data_fields=["title", "year", "custom_field"],  # 自定义字段
    saved_id=12345,
    item_count=1,
    elapsed_ms=1500.0
)
```

### 扩展数据验证

```python
from utils.data_validator import DataValidator

class CustomValidator(DataValidator):
    def validate_custom_data(self, data):
        """自定义数据验证逻辑"""
        # 添加你的验证逻辑
        if 'custom_field' not in data:
            return False, "缺少自定义字段"
        
        if len(data['title']) < 5:
            return False, "标题长度不足"
        
        return True, None
```

## 📈 性能监控

### 实时监控输出示例

```
🚀 [movie] 增强版爬虫已启动 - 慢速模式(3-5s延迟)
📄 [movie] 正在爬取第 1 页: http://www.97han.com/type/1.html
[2024-01-15 14:30:45.123] [movie] START → http://www.97han.com/type/1.html
📊 [movie] 第 1 页解析到 30 部电影
🎬 [movie] 正在处理第 1/30 部: 示例电影标题
[2024-01-15 14:30:46.623] [movie] DONE  ← 200 | saved_id=12345 | fields=["title","year","category"] | items=1 | cost=1500ms
📈 [movie] 进度: 5/30 完成, 已保存: 3
✅ [movie] 第 1 页数据校验完成 - 总计: 25 部电影
📊 [movie] 爬取统计:
   总请求: 35
   失败请求: 2
   重复ID: 1
   平均响应时间: 2.5s
   已保存: 25 部
```

### 自动优化触发

```
📊 [movie] 优化参数已更新: {'concurrency': 2, 'retry_enabled': True, 'bloom_filter_enabled': True}
⚠️  [movie] 检测到高失败率(15%), 启用重试机制
⚠️  [movie] 检测到高重复率(8%), 启用布隆过滤器
⚠️  [movie] 检测到高响应时间(4.2s), 降低并发数到 2
```

## 🔍 故障排除

### 常见问题

#### 1. 日志文件不生成
```bash
# 检查权限
ls -la crawl_progress.log
# 确保有写入权限
chmod 666 crawl_progress.log
```

#### 2. 爬虫运行缓慢
```bash
# 检查优化配置
python enhanced_main.py --show-stats
# 调整延迟参数
python enhanced_main.py --delay 1 2  # 减少延迟
```

#### 3. 重复数据过多
```bash
# 启用布隆过滤器
# 修改 auto_optimizer_config.json
# 设置 "bloom_filter_enabled": true
```

#### 4. 内存使用过高
```bash
# 减小日志缓冲区
# 修改 auto_optimizer_config.json
# 设置 "log_buffer_size": 5
# 启用日志轮转
# 设置 "log_rotation_enabled": true
```

## 📚 更新日志

### v2.0.0 (2024-01-15)
- ✨ 新增增强版日志系统
- ✨ 新增自动优化机制
- ✨ 新增数据完整性校验
- ✨ 新增零侵入集成方案
- ✨ 新增单元测试（覆盖率≥90%）
- ✨ 新增Excel导出功能
- ✨ 新增性能监控和可视化
- 🔧 优化慢速请求模式
- 🔧 优化错误处理和重试机制
- 🔧 优化内存使用和日志轮转

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [requests](https://requests.readthedocs.io/) - HTTP库
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - HTML解析
- [pandas](https://pandas.pydata.org/) - 数据分析
- [openpyxl](https://openpyxl.readthedocs.io/) - Excel处理

---

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**