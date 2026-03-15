# RepelisHD 电影列表页面结构分析

## URL格式
- 电影列表: `https://repelishd.city/pelicula/page/{page}/`
- 按年份: `https://repelishd.city/xfsearch/year/{year}`
- 总页数: 至少 775 页

## 电影卡片 HTML 结构

选择器: `article.item.movies`

```html
<article class="item movies">
    <div class="poster">
        <img src="/uploads/mini/cuimage/24/3488b10599a7ce872c451974873788.jpg" alt="Don't Fuck in the Woods 2">
        <div class="rating"><span class="icon-star2"></span>3.5</div>
        <div class="mepo">
            <span class="quality">HD</span>
        </div>
        <a href="https://repelishd.city/ver-pelicula/38-dont-fuck-in-the-woods-2-online-espanol.html">
            <div class="see play1"></div>
        </a>
        <div class="audio">
            <div class="latino"></div>
            <div class="subtitulado"></div>
        </div>
    </div>
    <div class="data">
        <h3><a href="https://repelishd.city/ver-pelicula/38-dont-fuck-in-the-woods-2-online-espanol.html">Don't Fuck in the Woods 2</a></h3>
        <span>2022</span>
    </div>
</article>
```

## CSS 选择器

| 数据 | CSS 选择器 | 备注 |
|------|-----------|------|
| 卡片容器 | `article.item.movies` | 每页约19个 |
| 标题 | `.data h3 a` | 文本内容 |
| 详情链接 | `.data h3 a[href]` 或 `.poster > a[href]` | |
| 评分 | `.rating` | 格式: "3.5" (前面有icon) |
| 清晰度 | `.quality` | 如 "HD" |
| 年份 | `.data span` | 如 "2022" |
| 海报 | `.poster img[src]` | 相对路径 |
| 音频 | `.audio > div` | .latino / .subtitulado / .castellano |

## 分页结构

```html
<div class="pagination">
    <a href="/pelicula/page/774/"><i id="prevpagination" class="fas fa-caret-left"></i></a>
    <a href="/pelicula/">1</a>
    <span class="nav_ext">...</span>
    <a href="/pelicula/page/766/">766</a>
    ...
    <a href="/pelicula/page/774/">774</a>
    <span>775</span>  <!-- 当前页无链接 -->
</div>
```

分页检测: 当前页为 `<span>` 而非 `<a>`，检查是否有下一页链接
