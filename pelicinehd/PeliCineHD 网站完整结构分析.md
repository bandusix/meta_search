# PeliCineHD 网站完整结构分析

## 1. 电影数据爬取

### 1.1 电影列表页面

**URL 格式：**
```
https://pelicinehd.com/release/{year}/page/{page_number}/
```

**示例：**
- 第1页：`https://pelicinehd.com/release/2025/` 或 `https://pelicinehd.com/release/2025/page/1/`
- 第22页：`https://pelicinehd.com/release/2025/page/22/`

**可用年份：**
1932, 1959, 1966, 1968, 1970, 1971, 1973, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026

### 1.2 电影卡片HTML结构

```html
<article class="post dfx fcl movies">
    <header class="entry-header">
        <h2 class="entry-title">El retorno</h2>
        <div class="entry-meta">
            <span class="vote"><span>TMDB</span> 0</span>
        </div>
    </header>
    <div class="post-thumbnail or-1">
        <figure>
            <img loading="lazy" src="//image.tmdb.org/t/p/w500/mZhOvUZdlIiJ4sXGEsFTJ8XvwCP.jpg" alt="Image El retorno">
        </figure>
        <span class="post-ql">
            <span class="Qlty">FHD 1080P</span>
            <span class="lang"><img loading="lazy" src="https://pelicinehd.com/wp-content/uploads/2023/09/espana.png"></span>
        </span>
        <span class="year">2025</span>
        <span class="watch btn sm">Ver pelicula</span>
        <span class="play fa-play"></span>
    </div>
    <a href="https://pelicinehd.com/movies/el-retorno/" class="lnk-blk"></a>
</article>
```

### 1.3 电影列表数据提取

**CSS 选择器：**
- 电影卡片：`article.movies`
- 西语标题：`.entry-title`
- TMDB评分：`.vote` (格式: "TMDB 0")
- 清晰度：`.Qlty` (例如: "FHD 1080P", "CAM")
- 年份：`.year`
- 详情页链接：`a.lnk-blk[href]`
- 海报图片：`img[src]`

**提取逻辑：**
```python
soup = BeautifulSoup(html, 'html.parser')
movies = soup.select('article.movies')

for movie in movies:
    title_spanish = movie.select_one('.entry-title').text.strip()
    rating_text = movie.select_one('.vote').text.strip()  # "TMDB 4.5"
    rating = float(rating_text.replace('TMDB', '').strip())
    quality = movie.select_one('.Qlty').text.strip() if movie.select_one('.Qlty') else None
    year = movie.select_one('.year').text.strip()
    url = movie.select_one('a.lnk-blk')['href']
    poster = movie.select_one('img')['src']
```

### 1.4 电影详情页面

**URL 格式：**
```
https://pelicinehd.com/movies/{slug}/
```

**示例：**
```
https://pelicinehd.com/movies/el-retorno/
```

### 1.5 电影详情数据提取

**可提取字段：**
- 西语标题：`h1.entry-title`
- 原标题：可能不存在，需要从其他元素提取
- 年份：`.year`
- 评分：`.vote` 或 `.rating`
- 清晰度：`.Qlty`
- 时长：`.duration` (格式: "1h 35m")
- 类型：`a[rel="category tag"]`
- 演员：`a[rel="tag"]`
- 简介：`.description` 或 `p`
- 海报：`.poster img`

**注意：** 原标题可能不在详情页，可能需要从列表页或其他来源获取。

---

## 2. 电视剧数据爬取

### 2.1 电视剧列表页面

**URL 格式：**
```
https://pelicinehd.com/series/page/{page_number}/
```

**示例：**
- 第1页：`https://pelicinehd.com/series/` 或 `https://pelicinehd.com/series/page/1/`
- 第9页：`https://pelicinehd.com/series/page/9/`

### 2.2 电视剧卡片HTML结构

```html
<article class="post dfx fcl movies">
    <header class="entry-header">
        <h2 class="entry-title">Spartacus: House of Ashur</h2>
        <div class="entry-meta">
            <span class="vote"><span>TMDB</span> 4.462</span>
        </div>
    </header>
    <div class="post-thumbnail or-1">
        <figure>
            <img loading="lazy" src="//image.tmdb.org/t/p/w500/vNByuzy60v31nmUVPMA8oAtneUK.jpg" alt="Image Spartacus: House of Ashur">
        </figure>
        <span class="post-ql"></span>
        <span class="year">2025</span>
        <span class="watch btn sm">Ver Serie</span>
        <span class="play fa-play"></span>
    </div>
    <a href="https://pelicinehd.com/series/spartacus-house-of-ashur/" class="lnk-blk"></a>
</article>
```

**注意：** 电视剧卡片的HTML结构与电影卡片相同，区别在于：
- 按钮文本：`Ver Serie` vs `Ver pelicula`
- URL路径：`/series/` vs `/movies/`

### 2.3 电视剧列表数据提取

**CSS 选择器：**
- 电视剧卡片：`article.movies` (与电影相同)
- 西语标题：`.entry-title`
- TMDB评分：`.vote`
- 年份：`.year`
- 详情页链接：`a.lnk-blk[href]` (包含 `/series/`)

**区分电影和电视剧：**
```python
url = movie.select_one('a.lnk-blk')['href']
if '/series/' in url:
    # 这是电视剧
    media_type = 'TV Series'
elif '/movies/' in url:
    # 这是电影
    media_type = 'Movie'
```

### 2.4 电视剧详情页面

**URL 格式：**
```
https://pelicinehd.com/series/{slug}/
```

**示例：**
```
https://pelicinehd.com/series/spartacus-house-of-ashur/
```

### 2.5 电视剧详情数据提取

**可提取字段：**
- 西语标题：`h1.entry-title`
- 原标题：可能不存在
- 年份：`.year`
- 评分：`.vote`
- 季数信息：`.seasons` (格式: "1 Temporadas")
- 类型：`a[rel="category tag"]`
- 演员：`a[rel="tag"]`
- 简介：`.description`

### 2.6 剧集列表提取

**剧集链接格式：**
```
https://pelicinehd.com/episode/{series-slug}-{season}x{episode}/
```

**示例：**
```
https://pelicinehd.com/episode/spartacus-house-of-ashur-1x1/
https://pelicinehd.com/episode/spartacus-house-of-ashur-1x2/
https://pelicinehd.com/episode/spartacus-house-of-ashur-1x10/
```

**提取逻辑：**
```python
# 在电视剧详情页
episode_links = soup.select('a[href*="/episode/"]')

for link in episode_links:
    url = link['href']
    # 从URL提取季和集信息
    match = re.search(r'-(\d+)x(\d+)', url)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
```

### 2.7 剧集详情页面

**URL 格式：**
```
https://pelicinehd.com/episode/{series-slug}-{season}x{episode}/
```

### 2.8 剧集详情数据提取

**可提取字段：**
- 标题：`h1.entry-title` (格式: "Spartacus: House of Ashur 1x1")
- 季数：从URL提取 (正则: `(\d+)x\d+`)
- 集数：从URL提取 (正则: `\d+x(\d+)`)
- 年份：`.year`
- 评分：`.vote`
- 播放选项：`.option` 或 `a[href*="option"]`

---

## 3. 分页处理

### 3.1 电影分页

**分页链接格式：**
```html
<a href="https://pelicinehd.com/release/2025/page/2/">2</a>
<a href="https://pelicinehd.com/release/2025/page/3/">3</a>
...
<a href="https://pelicinehd.com/release/2025/page/22/">22</a>
```

**分页检测：**
- 查找分页链接：`a[href*="/page/"]`
- 提取最大页码：从所有分页链接中找到最大数字
- 检测"下一页"按钮：`a:contains("SIGUIENTE")`

**爬取逻辑：**
```python
page = 1
while True:
    url = f"https://pelicinehd.com/release/{year}/page/{page}/"
    soup = fetch_page(url)
    
    movies = extract_movies(soup)
    if not movies:
        break  # 没有更多电影
    
    # 处理电影数据
    save_movies(movies)
    
    # 检查是否有下一页
    next_page = soup.select_one('a:contains("SIGUIENTE")')
    if not next_page:
        break
    
    page += 1
```

### 3.2 电视剧分页

**分页链接格式：**
```html
<a href="https://pelicinehd.com/series/page/2/">2</a>
<a href="https://pelicinehd.com/series/page/3/">3</a>
...
<a href="https://pelicinehd.com/series/page/9/">9</a>
```

**爬取逻辑：** 与电影分页相同

---

## 4. 数据库设计

### 4.1 电影表 (movies)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自动递增 |
| title_spanish | TEXT | 西语标题 |
| title_original | TEXT | 原标题（可能为空） |
| year | INTEGER | 年份 |
| rating | REAL | TMDB评分 |
| quality | TEXT | 清晰度 (FHD 1080P, CAM等) |
| duration | TEXT | 时长 (1h 35m) |
| url | TEXT | 详情页URL（唯一） |
| poster_url | TEXT | 海报URL |
| media_type | TEXT | 固定为 "Movie" |
| created_at | TIMESTAMP | 创建时间 |

### 4.2 电视剧剧集表 (tv_episodes)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自动递增 |
| series_title_spanish | TEXT | 剧集西语标题 |
| series_title_original | TEXT | 剧集原标题（可能为空） |
| year | INTEGER | 年份 |
| rating | REAL | TMDB评分 |
| quality | TEXT | 清晰度 |
| season | INTEGER | 季数 |
| episode | INTEGER | 集数 |
| episode_title | TEXT | 单集标题 |
| url | TEXT | 剧集详情页URL（唯一） |
| series_url | TEXT | 电视剧主页URL |
| poster_url | TEXT | 海报URL |
| media_type | TEXT | 固定为 "TV Series" |
| created_at | TIMESTAMP | 创建时间 |

---

## 5. 爬虫实现要点

### 5.1 编码处理

**重要：** 必须设置正确的编码，避免乱码问题

```python
response = requests.get(url, headers=headers)
response.encoding = 'utf-8'  # 关键！
soup = BeautifulSoup(response.text, 'html.parser')
```

### 5.2 反爬虫策略

1. **随机 User-Agent**
```python
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    # 更多...
]
headers = {'User-Agent': random.choice(USER_AGENTS)}
```

2. **随机延迟**
```python
time.sleep(random.uniform(1, 3))
```

3. **会话保持**
```python
session = requests.Session()
response = session.get(url, headers=headers)
```

### 5.3 错误处理

```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
except requests.RequestException as e:
    print(f"请求失败: {e}")
    return None
```

### 5.4 数据去重

```python
# 使用URL作为唯一标识
cursor.execute('''
    INSERT OR IGNORE INTO movies (url, title_spanish, ...)
    VALUES (?, ?, ...)
''', (url, title, ...))
```

---

## 6. 爬取流程

### 6.1 电影爬取流程

```
1. 遍历年份列表（倒序：2026 → 2025 → ... → 1932）
   ↓
2. 对每个年份，从第1页开始爬取
   ↓
3. 提取当前页的所有电影卡片
   ↓
4. 对每个电影：
   - 提取列表页数据（标题、评分、年份、清晰度、URL）
   - 可选：访问详情页获取更多信息（时长、演员、简介）
   ↓
5. 保存到数据库
   ↓
6. 检查是否有下一页
   - 有：page += 1，跳转到步骤2
   - 无：进入下一个年份
```

### 6.2 电视剧爬取流程

```
1. 从第1页开始爬取电视剧列表
   ↓
2. 提取当前页的所有电视剧卡片
   ↓
3. 对每个电视剧：
   - 提取列表页数据（标题、评分、年份、URL）
   - 访问电视剧详情页
   ↓
4. 在详情页提取所有剧集链接
   ↓
5. 对每个剧集：
   - 从URL提取季数和集数
   - 可选：访问剧集详情页获取更多信息
   ↓
6. 保存到数据库
   ↓
7. 检查是否有下一页
   - 有：page += 1，跳转到步骤1
   - 无：结束
```

---

## 7. 特殊注意事项

### 7.1 原标题问题

**观察：** 在列表页和详情页都没有明显的"原标题"字段。

**可能的解决方案：**
1. 原标题可能就是西语标题（很多电影没有单独的原标题）
2. 可能需要通过TMDB API获取原标题
3. 可以将此字段设为可选（允许为空）

### 7.2 清晰度字段

**观察：** 电视剧列表页的清晰度字段可能为空。

**处理方式：**
- 列表页：`quality = movie.select_one('.Qlty').text.strip() if movie.select_one('.Qlty') else None`
- 详情页：从播放选项中提取（例如："LATÍNO HD", "SUBTITULADO"）

### 7.3 年份范围

**注意：** 网站提供的年份不是连续的，需要使用提供的年份列表：

```python
AVAILABLE_YEARS = [
    1932, 1959, 1966, 1968, 1970, 1971, 1973, 1977, 1978, 1979,
    1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989,
    1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998, 1999,
    2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
    2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019,
    2020, 2021, 2022, 2023, 2024, 2025, 2026
]
```

### 7.4 电影与电视剧的区分

**关键：** 使用URL路径区分

```python
if '/series/' in url:
    media_type = 'TV Series'
elif '/movies/' in url:
    media_type = 'Movie'
```

---

## 8. 性能优化建议

### 8.1 并发爬取

- 使用 `concurrent.futures` 或 `asyncio` 实现并发
- 控制并发数量（建议 3-5 个并发）
- 避免对同一域名发起过多并发请求

### 8.2 缓存机制

- 缓存已访问的页面（避免重复请求）
- 使用 Redis 或本地文件缓存

### 8.3 增量更新

- 记录上次爬取的时间
- 只爬取新增或更新的内容
- 使用URL作为唯一标识进行去重

---

## 9. 总结

### 9.1 关键技术点

1. ✅ **编码处理**：必须设置 `response.encoding = 'utf-8'`
2. ✅ **CSS 选择器**：`article.movies` 用于电影和电视剧
3. ✅ **URL 模式**：
   - 电影列表：`/release/{year}/page/{page}/`
   - 电视剧列表：`/series/page/{page}/`
   - 剧集详情：`/episode/{slug}-{season}x{episode}/`
4. ✅ **数据提取**：使用 BeautifulSoup 的 `select()` 和 `select_one()`
5. ✅ **分页处理**：检测"SIGUIENTE"按钮或分页链接
6. ✅ **反爬虫**：随机 User-Agent + 随机延迟 + 会话保持

### 9.2 实现难度评估

| 功能 | 难度 | 说明 |
|------|------|------|
| 电影列表爬取 | ⭐⭐ | 简单，HTML结构清晰 |
| 电影详情爬取 | ⭐⭐ | 简单，字段明确 |
| 电视剧列表爬取 | ⭐⭐ | 简单，与电影相同 |
| 电视剧剧集爬取 | ⭐⭐⭐ | 中等，需要提取所有剧集链接 |
| 分页处理 | ⭐⭐ | 简单，标准分页 |
| 数据库存储 | ⭐⭐ | 简单，SQLite即可 |
| 反爬虫处理 | ⭐⭐⭐ | 中等，需要合理的延迟和User-Agent |

### 9.3 与 Cuevana3 的对比

| 特性 | PeliCineHD | Cuevana3 |
|------|-----------|----------|
| HTML结构 | 更规范，使用标准的 `<article>` | 使用自定义 `div.TPost` |
| 电影列表 | 按年份分页 | 按年份分页 |
| 电视剧列表 | 统一列表 | 统一列表 |
| 剧集URL格式 | `/episode/{slug}-{season}x{episode}/` | `/episodio/{slug}-{season}x{episode}` |
| 清晰度字段 | 可能为空 | 通常存在 |
| 原标题字段 | 不明显 | 不明显 |
| 爬取难度 | ⭐⭐ | ⭐⭐⭐ |

**结论：** PeliCineHD 的HTML结构更规范，爬取难度略低于 Cuevana3。
