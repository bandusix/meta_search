# Cuevana3 网站 URL 结构（已验证）

## 域名
`https://ww9.cuevana3.to`

## 电影（Movies）

### 1. 按年份浏览
- **URL格式**: `https://ww9.cuevana3.to/year/{year}`
- **示例**: 
  - 2025年: `https://ww9.cuevana3.to/year/2025`
  - 2024年: `https://ww9.cuevana3.to/year/2024`

### 2. 分页
- **URL格式**: `https://ww9.cuevana3.to/year/{year}/page/{page_number}`
- **示例**: `https://ww9.cuevana3.to/year/2025/page/2`

### 3. 所有电影（Estrenos）
- **URL**: `https://ww9.cuevana3.to/estrenos`
- **分页**: `https://ww9.cuevana3.to/estrenos/page/{page_number}`

### 4. 电影详情页
- **URL格式**: `https://ww9.cuevana3.to/{id}/{slug}`
- **示例**: `https://ww9.cuevana3.to/22750/un-monde-merveilleux`

## 电视剧（TV Series）

### 1. 所有电视剧
- **URL**: `https://ww9.cuevana3.to/serie`
- **分页**: `https://ww9.cuevana3.to/serie/page/{page_number}`

### 2. 电视剧详情页
- **URL格式**: `https://ww9.cuevana3.to/serie/{slug}`
- **示例**: `https://ww9.cuevana3.to/serie/teheran`

### 3. 剧集详情页
- **URL格式**: `https://ww9.cuevana3.to/episodio/{slug}-{season}x{episode}`
- **示例**: `https://ww9.cuevana3.to/episodio/teheran-1x1`

## 重要发现

1. **电影按年份URL**: 使用 `/year/{year}` 而不是 `/estreno/{year}/`
2. **电影列表页**: 主要使用 `/estrenos` 和 `/year/{year}`
3. **电视剧**: 使用 `/serie` 作为主列表页
4. **分页**: 所有列表页都支持 `/page/{page_number}` 分页

## HTML 结构

### 电影卡片
- 通常在 `<a>` 标签中
- 年份显示在卡片上
- 链接格式: `/{id}/{slug}`

### 电视剧卡片
- 链接格式: `/serie/{slug}` 或 `/episodio/{slug}-{season}x{episode}`
- 包含季和集信息
