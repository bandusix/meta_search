# RepelisHD 电影详情页结构分析

## URL格式
- 电影详情: `https://repelishd.city/ver-pelicula/{id}-{slug}-online-espanol.html`
- 示例: `https://repelishd.city/ver-pelicula/38-dont-fuck-in-the-woods-2-online-espanol.html`

## 详情页 HTML 结构

### 头部区域 (.sheader)
```html
<div class="sheader">
  <div class="poster">
    <img itemprop="image" src="/uploads/mini/cuimage/24/xxx.jpg" alt="..." title="...">
  </div>
  <div class="data">
    <h1>Don't Fuck in the Woods 2 online HD</h1>
    <div class="extra">
      <span>2022</span>
      <span class="country">Estados Unidos</span>
      <span itemprop="duration" class="runtime">81 Min.</span>
      <span>Terror</span>
      <span>HD/latino, sub</span>
    </div>
    <div class="starstruck-ptype">
      <!-- 评分系统 -->
      <div class="dt_rating_data">
        <div class="rating" itemprop="aggregateRating">
          <!-- 星级评分 -->
        </div>
      </div>
      <span class="dt_rating_vgs">3.5</span>
    </div>
    <div class="wp-content">
      <!-- 电影简介 -->
    </div>
  </div>
</div>
```

### 原标题和评分区域 (.custom_fields)
```html
<div class="custom_fields">
  <b class="variante">Título original</b>
  <span class="valor">Don't Fuck in the Woods 2</span>
</div>
```

### IMDb和TMDb评分
页面底部显示:
- Título original: Don't Fuck in the Woods 2
- IMDb Rating: 3.7 (560 votos)
- TMDb Rating: 3.5

## CSS 选择器

| 数据 | CSS 选择器 | 备注 |
|------|-----------|------|
| 标题(含"online HD") | `.sheader .data h1` | 需要清理后缀 |
| 年份 | `.sheader .extra span:first-child` | |
| 国家 | `.sheader .extra .country` | |
| 时长 | `.sheader .extra .runtime` | |
| 清晰度/音频 | `.sheader .extra span:last-child` | 如 "HD/latino, sub" |
| 评分 | `.dt_rating_vgs` | 如 "3.5" |
| 海报 | `.sheader .poster img[src]` | 相对路径 |
| 原标题 | `.custom_fields .valor` | |
| 原标题标签 | `.custom_fields .variante` | "Título original" |
| IMDb评分 | 文本匹配 "IMDb Rating" | |
| TMDb评分 | 文本匹配 "TMDb Rating" | |
