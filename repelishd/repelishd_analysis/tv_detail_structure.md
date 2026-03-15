# RepelisHD 电视剧详情页结构分析

## URL格式
- 电视剧详情: `https://repelishd.city/ver-pelicula/{id}-{slug}-online-espanol.html`
- 注意: 电视剧和电影使用相同的URL前缀 `/ver-pelicula/`

## 详情页 HTML 结构

### 头部区域 (.sheader)
```html
<div class="sheader">
  <div class="poster">
    <img itemprop="image" src="/uploads/mini/cuimage/ad/xxx.jpg" alt="...">
  </div>
  <div class="data">
    <h1>ver serie Tracker online</h1>
    <div class="extra">
      <span>2024</span>
      <span class="country">Estados Unidos</span>
      <span itemprop="duration" class="runtime">43 Min.</span>
      <span>Series   Drama   Crimen</span>
      <span>HD/sub</span>
    </div>
    <!-- 评分系统 -->
    <div class="dt_rating_vgs">6.8</div>
  </div>
</div>
```

### 原标题区域
```html
<div class="custom_fields">
  <b class="variante">Título original</b>
  <span class="valor">Tracker</span>
</div>
```

### 季选择器
- 季通过 `div[id^="season-"]` 组织
- 季数: 3 (season-1, season-2, season-3)
- 季标签通过 Tab 导航切换

### 剧集链接结构 (关键!)
```html
<div class="tab-pane fade active show" id="season-1">
  <ul>
    <li class="active">
      <a href="#" 
         id="serie-1_1" 
         data-num="1x1" 
         data-title="Episode 1"
         data-link="https://supervideo.cc/embed-xxx.html">1</a>
      <div class="mirrors">
        <a href="#" data-m="sup" data-link="https://supervideo.cc/embed-xxx.html">
          <img src="/templates/RePelisHD/images/super.png">Supervideo
        </a>
        <a href="#" data-m="dropload" data-link="https://dropload.tv/embed-xxx.html">
          <img src="/templates/RePelisHD/images/dropload.png">Dropload
        </a>
      </div>
    </li>
    <li>
      <a href="#" id="serie-1_2" data-num="1x2" data-title="Episode 2" ...>2</a>
      ...
    </li>
  </ul>
</div>
```

## 关键数据属性

### 剧集链接 `a[id^="serie-"]`
| 属性 | 说明 | 示例 |
|------|------|------|
| `id` | 格式: `serie-{season}_{episode}` | `serie-1_1`, `serie-2_3` |
| `data-num` | 格式: `{season}x{episode}` | `1x1`, `2x3` |
| `data-title` | 剧集标题 | `Episode 1` |
| `data-link` | 播放链接 | `https://supervideo.cc/embed-xxx.html` |

### 提取季集信息的方法
1. **从 id 解析**: `serie-{season}_{episode}` → season=1, episode=1
2. **从 data-num 解析**: `1x1` → season=1, episode=1
3. **从 season div id 解析**: `season-{n}` → season=n

### 所有剧集ID (Tracker 示例)
- Season 1: serie-1_1 到 serie-1_13 (13集)
- Season 2: serie-2_1 到 serie-2_20 (20集)
- Season 3: serie-3_1 到 serie-3_9 (9集)
- 总计: 42集

## 区分电影和电视剧的方法
1. **标题**: 电视剧标题以 "ver serie" 开头，电影不是
2. **extra span**: 电视剧包含 "Series" 关键词
3. **季集区域**: 电视剧有 `div[id^="season-"]` 元素
4. **列表页 .quality**: 电视剧显示 `s3-e9` 格式，电影显示 `HD`

## 按年份搜索电视剧
- URL: `https://repelishd.city/xfsearch/year/{year}`
- 该URL同时包含电影和电视剧，需要通过 .quality 标签区分
