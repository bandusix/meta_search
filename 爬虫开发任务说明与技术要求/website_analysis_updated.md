# Cuevana3.top 网站结构分析（更新版）

## 关键发现

### 1. 电影条目结构
- **容器**: `<div class="TPostMv item" id="post-{数字}">`
- **每页条目数**: 50个电影条目
- **总页数**: 从分页信息可以看到（例如：16页）

### 2. 实际 HTML 结构
```html
<div class="TPostMv item" id="post-66596">
    <div class="TPost D">
        <div class="Image">
            <figure class="Objf">
                <img src="..." alt="Papá x dos">
            </figure>
        </div>
        <div class="TPMvCn">
            <a href="https://cuevana3.top/pelicula/papa-x-dos/">
                <div class="Title">
                    Papá x dos 
                    <span class="TpTv BgA">PELÍCULA</span>
                </div>
            </a>
            <p class="Info">...</p>
            <p class="the_excerpt">...</p>
        </div>
    </div>
</div>
```

### 3. 数据提取方法

**方法 1: 使用 CSS 选择器**
```python
# 获取所有电影条目
posts = soup.select('div[id^="post-"]')

for post in posts:
    # 提取 URL
    link = post.select_one('a[href*="/pelicula/"]')
    url = link['href'] if link else None
    
    # 提取标题
    title_div = post.select_one('div.Title')
    if title_div:
        # 移除 span 标签，只保留文本
        for span in title_div.find_all('span'):
            span.decompose()
        title = title_div.get_text(strip=True)
```

**方法 2: 使用 XPath (lxml)**
```python
# 获取所有电影条目
posts = tree.xpath('//div[contains(@id, "post-")]')

for post in posts:
    # 提取 URL
    url = post.xpath('.//a[contains(@href, "/pelicula/")]/@href')
    url = url[0] if url else None
    
    # 提取标题
    title = post.xpath('.//div[@class="Title"]/text()')
    title = title[0].strip() if title else None
```

### 4. 分页机制
- **分页容器**: `<nav class="navigation pagination">`
- **分页链接**: `<div class="nav-links">`
- **URL 格式**: 
  - 第1页: `https://cuevana3.top/estreno/2024/`
  - 第2页及以后: `https://cuevana3.top/estreno/2024/page/{页码}/`
- **总页数提取**: 可以从最后一个页码链接获取

### 5. 分页信息提取
```python
# 获取最后一个页码
last_page_link = soup.select_one('nav.pagination a.page-link:last-of-type')
if last_page_link:
    last_page_text = last_page_link.get_text(strip=True)
    total_pages = int(last_page_text)
```

## 爬虫实现策略

1. **初始化**: 从第1页开始
2. **提取数据**: 解析每页的50个电影条目
3. **获取总页数**: 从分页导航中提取
4. **遍历所有页**: 循环访问所有页面
5. **保存数据**: 将结果保存为 CSV 文件

## 注意事项
- 标题中包含 `<span class="TpTv BgA">PELÍCULA</span>`，需要去除
- URL 都是完整的绝对路径
- 每页固定50个条目
- 需要添加延迟和 User-Agent 以避免被封禁
