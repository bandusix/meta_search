# Cuevana3.top 网站结构分析

## URL 结构
- 基础 URL: `https://cuevana3.top/estreno/{year}/`
- 分页 URL: `https://cuevana3.top/estreno/{year}/page/{page_number}/`
- 示例: `https://cuevana3.top/estreno/2024/` (第1页)
- 示例: `https://cuevana3.top/estreno/2024/page/2/` (第2页)

## 分页机制
- 在页面底部有分页导航
- 显示当前页码（例如：1 de 16，表示第1页共16页）
- 有前一页和后一页的箭头按钮
- 可以直接点击页码跳转

## HTML 结构分析

### 电影条目容器
每个电影条目都包含在一个 `<article>` 标签中，具有以下特征：
- 类名: `TPost C`
- ID: `post-{数字}` (例如: `post-12345`)

### 电影链接和标题提取
根据需求文档：
1. **URL 提取**:
   - XPath: `//div[contains(@id, "post-")]/div/a/@href`
   - 实际结构: 电影链接在 `<article id="post-xxx">` 内的 `<a>` 标签中
   
2. **标题提取**:
   - 定位: `<h2 class="Title">` 标签内的文本
   - 位置: 在同一个 `<a>` 标签内或临近结构中

### 实际 HTML 结构示例
```html
<article id="post-xxxxx" class="TPost C">
    <a href="https://cuevana3.top/pelicula/nombre-pelicula/">
        <div class="Image">
            <figure class="Objf TpMvPlay AAIco-play_arrow">
                <img src="...">
            </figure>
        </div>
        <div class="TPMvCn">
            <h2 class="Title">Nombre de la Película</h2>
            <span class="Year">2024</span>
        </div>
    </a>
</article>
```

## 数据提取策略
1. 使用 `lxml` 或 `BeautifulSoup` 解析 HTML
2. 查找所有 `<article>` 标签，其 `id` 属性以 "post-" 开头
3. 在每个 article 中：
   - 提取 `<a>` 标签的 `href` 属性作为 URL
   - 提取 `<h2 class="Title">` 的文本内容作为标题
4. 检查分页信息，确定总页数
5. 遍历所有页面直到完成

## 反爬虫策略
- 需要设置 User-Agent
- 添加随机延迟（1-3秒）
- 可能需要处理 JavaScript 渲染（如果内容是动态加载的）
