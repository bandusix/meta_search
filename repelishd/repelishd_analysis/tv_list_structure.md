# RepelisHD 电视剧列表页面结构分析

## URL格式
- 电视剧列表: `https://repelishd.city/series/page/{page}/`
- 第一页: `https://repelishd.city/series/`
- 总页数: 107页

## 关键发现
- 电视剧和电影使用**相同的卡片结构** `article.item.movies`
- 电视剧的 `.quality` 标签显示的是 **季集信息**（如 `s3-e9`），而不是清晰度
- 电视剧详情页URL格式与电影相同: `/ver-pelicula/{id}-{slug}-online-espanol.html`

## 电视剧卡片 HTML 结构
```html
<article class="item movies">
    <div class="poster">
        <img src="/uploads/mini/cuimage/ad/xxx.jpg" alt="Tracker">
        <div class="rating"><span class="icon-star2"></span>6.8</div>
        <div class="mepo">
            <span class="quality" style="background-color: #2944D5;">s3-e9</span>
        </div>
        <a href="https://repelishd.city/ver-pelicula/13303-tracker-online-espanol.html">
            <div class="see play1"></div>
        </a>
        <div class="audio">
            <div class="subtitulado"></div>
        </div>
    </div>
    <div class="data">
        <h3><a href="https://repelishd.city/ver-pelicula/13303-tracker-online-espanol.html">Tracker</a></h3>
        <span>2024</span>
    </div>
</article>
```

## 电视剧 vs 电影卡片区别
| 特征 | 电影 | 电视剧 |
|------|------|--------|
| .quality 内容 | `HD` | `s3-e9` (季集格式) |
| .quality 背景色 | 默认 | `#2944D5` (蓝色) |
| 区分方式 | quality不含 "s" 和 "e" | quality 匹配 `s\d+-e\d+` |

## 分页结构
- 与电影列表分页结构相同
- 当前页为 `<span>9</span>`
- 有 prevpagination 和 nextpagination 按钮
- 最后一页: 107
