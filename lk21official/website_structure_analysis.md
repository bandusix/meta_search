# LK21 (tv8.lk21official.cc) 网站结构分析

**分析日期**: 2026-02-11  
**目标网站**: tv8.lk21official.cc  
**网站类型**: 印尼电影流媒体网站（Layarkaca21）

---

## 1. 网站基本信息

### 1.1 域名结构

- **主域名**: tv8.lk21official.cc
- **电视剧域名**: tv3.nontondrama.my（电视剧内容被重定向到独立域名）
- **图片CDN**: poster.lk21.party

### 1.2 内容分类

| 类型 | 域名 | 说明 |
|------|------|------|
| 电影 | tv8.lk21official.cc | 主站，包含所有电影内容 |
| 电视剧 | tv3.nontondrama.my | 独立站点，专门提供电视剧内容 |

**重要发现**: 电视剧内容完全独立于主站，使用不同的域名和系统。

---

## 2. 电影列表页面结构

### 2.1 URL 格式

#### 按年份浏览
```
https://tv8.lk21official.cc/year/{year}/page/{page}/
```

**示例**:
- 2015年第46页: `https://tv8.lk21official.cc/year/2015/page/46/`
- 2025年第1页: `https://tv8.lk21official.cc/year/2025/page/1/`

#### 年份范围
根据网站内容，支持的年份范围：**1917 - 2026**（及未来年份）

### 2.2 HTML 结构

#### 电影卡片选择器

```html
<article itemscope itemtype="https://schema.org/Movie">
    <meta itemprop="genre" content="Wrestling">
    <figure>
        <a href="/wwe-night-champions-20th-september-2015" itemprop="url">
            <div class="poster">
                <span class="year" itemprop="datePublished">2015</span>
                <span class="label label-SD">SD</span>
                <span class="duration" itemprop="duration" content="PT2H7M">02:50</span>
                <picture>
                    <source type="image/webp" srcset="https://poster.lk21.party/wp-content/uploads/wwe.jpg.webp">
                    <source type="image/jpeg" srcset="https://poster.lk21.party/wp-content/uploads/wwe.jpg">
                    <img alt="WWE Night Of Champions 20th September (2015)" 
                         src="https://poster.lk21.party/wp-content/uploads/wwe.jpg" 
                         itemprop="image" 
                         title="WWE Night Of Champions 20th September (2015)">
                </picture>
                <div class="poster-overlay"></div>
            </div>
            <figcaption>
                <div class="genre"> Wrestling </div>
                <h3 class="poster-title" itemprop="name">WWE Night Of Champions 20th September</h3>
            </figcaption>
        </a>
    </figure>
</article>
```

#### CSS 选择器速查表

| 数据字段 | CSS 选择器 | 属性 |
|---------|-----------|------|
| 电影卡片 | `article[itemtype*="Movie"]` | - |
| 详情页URL | `article a[itemprop="url"]` | `href` |
| 标题 | `h3.poster-title[itemprop="name"]` | `textContent` |
| 年份 | `span.year[itemprop="datePublished"]` | `textContent` |
| 清晰度 | `span.label` | `textContent` (SD/HD/CAM/BLURAY) |
| 时长 | `span.duration[itemprop="duration"]` | `textContent` |
| 图片URL | `img[itemprop="image"]` | `src` |
| 类型 | `div.genre` | `textContent` |

### 2.3 分页结构

```html
<ul class="pagination">
    <li><a href="https://tv8.lk21official.cc/year/2015/page/1" aria-label="first">«</a></li>
    <li><a href="https://tv8.lk21official.cc/year/2015/page/44">44</a></li>
    <li><a href="https://tv8.lk21official.cc/year/2015/page/45">45</a></li>
    <li class="active"><a href="https://tv8.lk21official.cc/year/2015/page/46">46</a></li>
</ul>
```

**分页逻辑**:
- 当前页: `li.active a`
- 下一页: 当前页码 + 1
- 最后一页: 当 `li.active` 是最后一个 `li` 时停止

---

## 3. 电影详情页面结构

### 3.1 URL 格式

```
https://tv8.lk21official.cc/{slug}
```

**示例**:
- `https://tv8.lk21official.cc/lagenda-budak-setan-2010`
- `https://tv8.lk21official.cc/wwe-night-champions-20th-september-2015`

**特点**: URL 中的 slug 通常包含标题和年份

### 3.2 HTML 结构

#### 页面标题
```html
<h1>Nonton Lagenda Budak Setan (2010) Sub Indo di Lk21</h1>
```

#### 元数据区域
```html
<div class="meta-info">
    <span class="rating">6.2</span>
    <span class="quality">WEBDL</span>
    <span class="resolution">1080p</span>
    <span class="duration">1h 40m</span>
</div>
```

#### 简介
```html
<div class="synopsis">
    Dalam "Lagenda Budak Setan", Kasyah, seorang remaja nakal, menghadapi perubahan besar saat bertemu Ayu. Cinta mereka berkembang, tapi Kasyah harus meninggalkan Ayu untuk menyelesaikan tesisnya di sebu...
</div>
```

#### 类型标签
```html
<div class="genre">
    <a href="/genre/malaysia">Malaysia</a>
    <a href="/genre/drama">Drama</a>
    <a href="/genre/romance">Romance</a>
</div>
```

### 3.3 CSS 选择器速查表

| 数据字段 | CSS 选择器 | 属性 |
|---------|-----------|------|
| 标题 | `h1, [itemprop="name"]` | `textContent` |
| 评分 | `.rating, [itemprop="ratingValue"]` | `textContent` |
| 清晰度 | `.quality, .label` | `textContent` |
| 时长 | `.duration, [itemprop="duration"]` | `textContent` |
| 年份 | `.year, [itemprop="datePublished"]` | `textContent` |
| 图片 | `[itemprop="image"], .poster img` | `src` |
| 简介 | `[itemprop="description"], .synopsis` | `textContent` |
| 类型 | `.genre a, [itemprop="genre"]` | `textContent` |
| 国家 | `.country, [itemprop="countryOfOrigin"]` | `textContent` |

---

## 4. 电视剧结构（独立域名）

### 4.1 重要发现

**电视剧内容被重定向到独立域名**: `tv3.nontondrama.my`

当用户点击主站的"Series"菜单时，会自动跳转到 nontondrama.my。

### 4.2 电视剧列表页面

**URL**: `https://tv3.nontondrama.my/`

**特点**:
- 使用独立的域名和系统
- 与主站（lk21official.cc）的结构不同
- 需要单独分析和爬取

### 4.3 电视剧卡片结构

从首页可以看到电视剧卡片包含：
- 评分
- 年份
- 季数（S.1, S.3, S.5 等）
- 集数（EPS 12, EPS 16 等）
- 类型标签

**示例**:
```
8.1 2021 EPS 16 S.3 Taxi Driver (Mobeomtaeksi)
9.5 2008 EPS 16 S.5 Breaking Bad
```

### 4.4 建议

由于电视剧内容在独立域名，建议：
1. **主要爬取电影内容**（tv8.lk21official.cc）
2. **电视剧内容作为可选功能**（需要额外分析 nontondrama.my）

---

## 5. 数据提取要点

### 5.1 电影数据字段

| 字段名 | 数据来源 | 说明 |
|--------|---------|------|
| title | 列表页 + 详情页 | 电影标题 |
| title_original | 详情页 | 原标题（如果有） |
| year | 列表页 + 详情页 | 年份 |
| rating | 详情页 | 评分 |
| quality | 列表页 + 详情页 | 清晰度（SD/HD/CAM/BLURAY/WEBDL） |
| resolution | 详情页 | 分辨率（1080p/720p等） |
| duration | 列表页 + 详情页 | 时长 |
| image_url | 列表页 + 详情页 | 海报图片URL |
| movie_url | 列表页 | 详情页URL |
| genre | 列表页 + 详情页 | 类型/类别 |
| country | 详情页 | 国家 |
| description | 详情页 | 简介 |

### 5.2 特殊处理

#### 图片URL
- 使用 `<picture>` 标签，优先提取 WebP 格式
- 备选 JPEG 格式
- CDN 域名: `poster.lk21.party`

#### 清晰度标签
- SD: 标清
- HD: 高清
- CAM: 枪版
- BLURAY: 蓝光
- WEBDL: 网络下载版

#### 时长格式
- 显示格式: `02:50` (2小时50分钟)
- Schema.org 格式: `PT2H7M`

---

## 6. 爬取策略建议

### 6.1 电影爬取流程

```
1. 生成年份列表（1917-2026，倒序）
2. 对每个年份:
   a. 访问第1页
   b. 提取电影列表
   c. 检查是否有下一页
   d. 重复直到最后一页
3. 对每部电影:
   a. 访问详情页
   b. 提取完整元数据
   c. 保存到数据库
```

### 6.2 增量更新策略

```python
# 只爬取最新年份的新增内容
current_year = 2026
last_scraped_url = get_last_scraped_url(current_year)

# 从第1页开始爬取
for page in range(1, max_pages):
    movies = scrape_page(current_year, page)
    
    for movie in movies:
        if movie['url'] == last_scraped_url:
            # 遇到上次爬取的最后一部电影，停止
            break
        
        # 保存新电影
        save_to_db(movie)
```

### 6.3 反爬虫策略

- **User-Agent 轮换**: 使用多个 User-Agent
- **延迟控制**: 每次请求间隔 1-3 秒
- **会话保持**: 使用 `requests.Session()`
- **错误重试**: 请求失败时重试 3 次

---

## 7. 与其他网站对比

| 特性 | Cuevana3 | PeliCineHD | RepelisHD | **LK21** |
|------|----------|------------|-----------|---------|
| 模板引擎 | WordPress | DLE | DLE | **自定义** |
| 电影URL | `/pelicula/` | `/movies/` | `/ver-pelicula/` | **/{slug}** |
| 电视剧URL | `/serie/` | `/series/` | `/ver-pelicula/` | **独立域名** |
| 按年份URL | `/estreno/{year}/` | `/release/{year}/` | `/xfsearch/year/{year}` | **/year/{year}/page/{page}/** |
| 卡片选择器 | `div.TPost` | `article.item` | `article.item` | **article[itemtype*="Movie"]** |
| Schema.org | ✅ 使用 | ✅ 使用 | ❌ 不使用 | **✅ 使用** |
| 图片格式 | JPEG | JPEG/WebP | JPEG | **WebP优先** |
| 电视剧独立站 | ❌ | ❌ | ❌ | **✅ 是** |

---

## 8. 技术要点总结

### 8.1 优势

1. **Schema.org 支持**: 使用标准的 `itemprop` 属性，易于提取
2. **WebP 图片**: 现代图片格式，文件更小
3. **清晰的HTML结构**: 使用语义化标签
4. **分页明确**: 分页逻辑清晰，易于遍历

### 8.2 挑战

1. **电视剧独立域名**: 需要额外处理 nontondrama.my
2. **动态内容**: 部分内容可能通过 JavaScript 加载
3. **CDN 图片**: 图片在独立CDN，需要额外请求

### 8.3 建议

1. **优先爬取电影**: 电影内容在主站，结构清晰
2. **电视剧作为扩展**: 如需电视剧，单独分析 nontondrama.my
3. **使用 Schema.org 属性**: 优先使用 `itemprop` 选择器
4. **图片处理**: 优先使用 WebP 格式，备选 JPEG

---

## 9. 下一步行动

1. ✅ 完成电影列表页面分析
2. ✅ 完成电影详情页面分析
3. ⏳ 分析电视剧结构（nontondrama.my）
4. ⏳ 编写完整的爬虫技术文档
5. ⏳ 提供代码示例

---

**分析完成时间**: 2026-02-11 06:36  
**分析状态**: 电影部分已完成，电视剧部分需要额外分析
