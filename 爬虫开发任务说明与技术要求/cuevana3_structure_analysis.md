# Cuevana3 网站结构分析（完整版）

## 域名
**新域名**: `https://ww9.cuevana3.to`

## 一、电影（Movies）

### 1. 列表页 URL
- 按年份：`https://ww9.cuevana3.to/estreno/{year}/`
- 分页：`https://ww9.cuevana3.to/estreno/{year}/page/{page_number}/`

### 2. 详情页 URL
- 格式：`https://ww9.cuevana3.to/{id}/{slug}`
- 示例：`https://ww9.cuevana3.to/22750/un-monde-merveilleux`

### 3. 数据字段
- **西语标题** (Title): `<h1 class="Title">`
- **原标题** (Original Title): `<h2 class="SubTitle">` (格式：Civil: {原标题})
- **评分** (Rating): `<p class="meta"><span>5.4/10</span>`
- **年份** (Year): `<p class="meta"><span>2025</span>`
- **清晰度** (Quality): `<p class="meta"><span class="Qlty">HD</span>`
- **类型** (Media Type): "Movie"
- **URL**: 详情页链接

## 二、电视剧（TV Series）

### 1. 列表页 URL
- 所有电视剧：`https://ww9.cuevana3.to/serie`
- 分页：`https://ww9.cuevana3.to/serie/page/{page_number}/`

### 2. 剧集详情页 URL
- 格式：`https://ww9.cuevana3.to/episodio/{slug}-{season}x{episode}`
- 示例：`https://ww9.cuevana3.to/episodio/teheran-1x1`

### 3. 数据字段
- **西语标题** (Title): `<h1 class="Title">` (包含季集信息，如 "Teherán 1x1")
- **原标题** (Original Title): `<h2 class="SubTitle">` (格式：Civil: {原标题})
- **评分** (Rating): `<p class="meta"><span>7.5/10</span>`
- **年份** (Year): `<p class="meta"><span>2020</span>`
- **清晰度** (Quality): `<p class="meta"><span class="Qlty">HD</span>`
- **类型** (Media Type): "TV Series"
- **季数** (Season): 从 URL 或标题提取 (如 "1x1" 中的 1)
- **集数** (Episode): 从 URL 或标题提取 (如 "1x1" 中的 1)
- **URL**: 剧集详情页链接

## 三、HTML 结构示例

### 电影详情页
```html
<header class="Header">
  <h1 class="Title">Un mundo maravilloso</h1>
  <h2 class="SubTitle">Civil: Un monde merveilleux</h2>
</header>

<p class="meta">
  <span>5.4/10</span>
  <span>2025</span>
  <span class="Qlty">HD</span>
</p>
```

### 电视剧剧集页
```html
<header class="Header">
  <h1 class="Title">Teherán 1x1</h1>
  <h2 class="SubTitle">Episode 1</h2>
</header>

<p class="meta">
  <span>7.5/10</span>
  <span>2020</span>
  <span class="Qlty">HD</span>
</p>
```

## 四、数据库表结构设计

### 表1: movies（电影）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增ID |
| title_spanish | TEXT | 西语标题 |
| title_original | TEXT | 原标题 |
| year | INTEGER | 年份 |
| rating | REAL | 评分 |
| quality | TEXT | 清晰度 (HD, CAM等) |
| url | TEXT UNIQUE | 详情页URL |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 表2: tv_series（电视剧）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PRIMARY KEY | 自增ID |
| title_spanish | TEXT | 西语标题 |
| title_original | TEXT | 原标题 |
| year | INTEGER | 年份 |
| rating | REAL | 评分 |
| quality | TEXT | 清晰度 |
| season | INTEGER | 季数 |
| episode | INTEGER | 集数 |
| url | TEXT UNIQUE | 剧集详情页URL |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 五、爬取策略

### 电影爬取
1. 从最新年份开始倒序爬取（2026 → 2025 → 2024...）
2. 每个年份遍历所有分页
3. 进入每部电影的详情页提取完整元数据
4. 存入 movies 表

### 电视剧爬取
1. 从 `/serie` 页面开始
2. 遍历所有分页获取电视剧列表
3. 进入每个电视剧页面，获取所有季和集的列表
4. 进入每个剧集详情页提取完整元数据
5. 存入 tv_series 表

### 更新逻辑
1. 每天定时执行
2. 检查最新的电影和电视剧
3. 对比数据库，只插入新记录或更新变化的记录
4. 使用 URL 作为唯一标识避免重复

## 六、定时任务
- 使用 cron 或系统定时任务
- 建议每天凌晨执行（如 02:00）
- 日志记录每次爬取结果
