import re
from base_scraper import BaseScraper

from concurrent.futures import ThreadPoolExecutor, as_completed

class TVScraper(BaseScraper):
    """电视剧爬虫"""
    
    def _parse_series_card(self, article):
        """解析电视剧卡片"""
        try:
            # 检查是否为电视剧
            quality_el = article.select_one('.quality')
            quality_text = quality_el.get_text(strip=True) if quality_el else ''
            
            if not re.match(r's\d+-e\d+', quality_text):
                return None  # 这是电影，跳过
            
            # 解析季集信息 (如 "s3-e9")
            se_match = re.match(r's(\d+)-e(\d+)', quality_text)
            latest_season = int(se_match.group(1)) if se_match else None
            latest_episode = int(se_match.group(2)) if se_match else None
            
            # 标题和URL
            title_el = article.select_one('.data h3 a')
            if not title_el:
                return None
            
            title = title_el.get_text(strip=True)
            detail_url = title_el.get('href', '')
            if not detail_url.startswith('http'):
                detail_url = self.BASE_URL + detail_url
            
            # 评分
            rating_el = article.select_one('.rating')
            rating_text = rating_el.get_text(strip=True) if rating_el else ''
            try:
                rating_val = re.search(r'[\d\.]+', rating_text)
                rating = float(rating_val.group()) if rating_val else None
            except ValueError:
                rating = None
            
            # 年份
            year_el = article.select_one('.data span')
            year_text = year_el.get_text(strip=True) if year_el else ''
            try:
                year = int(year_text) if year_text else None
            except ValueError:
                year = None
            
            # 海报URL
            img_el = article.select_one('.poster img')
            image_url = img_el.get('src', '') if img_el else ''
            if image_url and not image_url.startswith('http'):
                image_url = self.BASE_URL + image_url
            
            # 音频
            audio_langs = []
            if article.select_one('.audio .latino'):
                audio_langs.append('Latino')
            if article.select_one('.audio .castellano'):
                audio_langs.append('Castellano')
            if article.select_one('.audio .subtitulado'):
                audio_langs.append('Subtitulado')
            
            return {
                'title_spanish': title,
                'year': year,
                'rating': rating,
                'latest_season': latest_season,
                'latest_episode': latest_episode,
                'image_url': image_url,
                'detail_url': detail_url,
                'audio': ', '.join(audio_langs) if audio_langs else None,
            }
            
        except Exception as e:
            print(f"  ⚠️ 解析电视剧卡片失败: {e}")
            return None
    
    def _parse_episodes(self, soup):
        """从详情页解析所有季集信息"""
        episodes = []
        
        # 获取所有季
        season_divs = soup.select('div[id^="season-"]')
        
        for season_div in season_divs:
            # 从 id 获取季数
            season_id = season_div.get('id', '')
            season_match = re.match(r'season-(\d+)', season_id)
            if not season_match:
                continue
            season_num = int(season_match.group(1))
            
            # 获取该季的所有剧集
            episode_links = season_div.select('a[id^="serie-"]')
            
            for ep_link in episode_links:
                ep_id = ep_link.get('id', '')
                data_num = ep_link.get('data-num', '')
                data_title = ep_link.get('data-title', '')
                
                # 提取多个播放源
                embed_urls = []
                # 1. 直接获取当前链接的 (通常是默认第一个)
                default_link = ep_link.get('data-link', '')
                if default_link:
                    embed_urls.append(default_link)
                
                # 2. 查找同级下的 mirrors 列表
                parent_li = ep_link.find_parent('li')
                if parent_li:
                    mirrors_div = parent_li.select_one('.mirrors')
                    if mirrors_div:
                        mirror_links = mirrors_div.select('a[data-link]')
                        for m_link in mirror_links:
                            link = m_link.get('data-link')
                            if link and link not in embed_urls:
                                embed_urls.append(link)
                
                embed_url_str = ','.join(embed_urls) # 用逗号分隔多个链接
                
                # 从 id 解析集数
                ep_match = re.match(r'serie-\d+_(\d+)', ep_id)
                episode_num = int(ep_match.group(1)) if ep_match else None
                
                episodes.append({
                    'season': season_num,
                    'episode': episode_num,
                    'episode_title': data_title,
                    'episode_data_num': data_num,
                    'embed_url': embed_url_str, # 保存所有 embed_url
                })
        
        return episodes
    
    def _parse_series_detail(self, url):
        """访问电视剧详情页，提取元数据和所有剧集"""
        soup = self._fetch_page(url)
        if not soup:
            return {}, []
        
        detail = {}
        
        try:
            # 原标题
            custom_fields = soup.select_one('.custom_fields')
            if custom_fields:
                valor = custom_fields.select_one('.valor')
                if valor:
                    detail['title_original'] = valor.get_text(strip=True)
            
            # 国家
            country_el = soup.select_one('.sheader .extra .country')
            if country_el:
                detail['country'] = country_el.get_text(strip=True)
            
            # 时长
            runtime_el = soup.select_one('.sheader .extra .runtime')
            if runtime_el:
                detail['duration'] = runtime_el.get_text(strip=True)
            
            # 类型
            extra = soup.select_one('.sheader .extra')
            if extra:
                spans = extra.select('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if 'Series' in text:
                        # 去除 "Series" 前缀，保留类型
                        genre = text.replace('Series', '').strip()
                        if genre:
                            detail['genre'] = genre
                        break
            
            # 清晰度
            if extra:
                spans = extra.select('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if 'HD' in text or '/' in text:
                        detail['quality'] = text
                        break
            
            # 评分
            rating_el = soup.select_one('.dt_rating_vgs')
            if rating_el:
                try:
                    detail['rating'] = float(rating_el.get_text(strip=True))
                except ValueError:
                    pass
            
            # 网页标题
            if soup.title:
                detail['web_url_title'] = soup.title.get_text(strip=True)
            
            # 海报
            poster_el = soup.select_one('.sheader .poster img')
            if poster_el:
                src = poster_el.get('src', '')
                if src and not src.startswith('http'):
                    src = self.BASE_URL + src
                detail['image_url'] = src
            
        except Exception as e:
            print(f"  ⚠️ 解析电视剧详情失败: {e}")
        
        # 解析所有剧集
        episodes = self._parse_episodes(soup)
        
        return detail, episodes
    
    def scrape_latest_series(self, limit=2000, existing_urls=None):
        """爬取最新电视剧及其剧集"""
        series_list = []
        page = 1
        count = 0
        if existing_urls is None:
            existing_urls = set()
        
        # 获取需要补全 web_url_title 的 URL 集合
        
        print(f"\n{'='*60}")
        print(f"📺 开始爬取电视剧列表 (目标: {limit} 部) [线程数: {self.max_workers}]...")
        print(f"{'='*60}")
        
        # 第一阶段：获取电视剧列表 (顺序执行)
        while count < limit:
            if page == 1:
                url = f"{self.BASE_URL}/series/"
            else:
                url = f"{self.BASE_URL}/series/page/{page}/"
            
            print(f"\n📄 正在爬取列表第 {page} 页: {url}")
            
            soup = self._fetch_page(url)
            if not soup:
                break
            
            articles = soup.select('article.item.movies')
            if not articles:
                articles = soup.select('article.item')
            
            if not articles:
                print(f"  ✅ 没有更多内容")
                break
            
            page_series = []
            for article in articles:
                if count >= limit:
                    break
                series = self._parse_series_card(article)
                if series:
                    page_series.append(series)
                    count += 1
            
            print(f"  找到 {len(page_series)} 部电视剧")
            series_list.extend(page_series)
            
            # 检查下一页
            pagination = soup.select_one('.pagination')
            if not pagination or not pagination.select_one('#nextpagination'):
                print(f"  ✅ 已到最后一页")
                break
            
            page += 1
            # self._random_delay()
            
        print(f"\n✨ 电视剧列表爬取完成！共 {len(series_list)} 部电视剧")
        
        # 第二阶段：并发获取剧集详情
        print(f"\n{'#'*60}")
        print(f"# 开始并发爬取 {len(series_list)} 部电视剧的所有剧集")
        print(f"{'#'*60}")
        
        all_episodes = []
        
        # 准备任务
        tasks = []
        for i, series in enumerate(series_list):
            url = series['detail_url']
            
            # 检查是否已存在
            is_existing = False
            need_update = True
            
            if isinstance(existing_urls, dict):
                if url in existing_urls:
                    is_existing = True
                    # 如果已存在且有标题，则不需要更新
                    if existing_urls[url]: 
                        need_update = False
            elif url in existing_urls:
                is_existing = True
                need_update = False
                
            if is_existing and not need_update:
                print(f"[{i+1}/{len(series_list)}] 📺 已存在且完整，跳过: {series['title_spanish']}")
                continue

            if is_existing and need_update:
                print(f"[{i+1}/{len(series_list)}] 🔄 需补全: {series['title_spanish']}")
            else:
                print(f"[{i+1}/{len(series_list)}] 📺 准备获取: {series['title_spanish']}")
            
            tasks.append(series)
        
        # 定义处理函数
        def process_series(series):
            try:
                detail, episodes = self._parse_series_detail(series['detail_url'])
                
                # 合并信息
                current_series_episodes = []
                for ep in episodes:
                    ep_data = {
                        'title_spanish': series['title_spanish'],
                        'title_original': detail.get('title_original', ''),
                        'year': series['year'],
                        'rating': detail.get('rating', series['rating']),
                        'quality': detail.get('quality', ''),
                        'image_url': detail.get('image_url', series['image_url']),
                        'detail_url': series['detail_url'],
                        'web_url_title': detail.get('web_url_title', ''),
                        'season': ep['season'],
                        'episode': ep['episode'],
                        'episode_title': ep['episode_title'],
                        'episode_data_num': ep['episode_data_num'],
                        'embed_url': ep.get('embed_url', ''), # 新增
                        'country': detail.get('country', ''),
                        'duration': detail.get('duration', ''),
                        'genre': detail.get('genre', ''),
                        'audio': series.get('audio', ''),
                    }
                    current_series_episodes.append(ep_data)
                return current_series_episodes
            except Exception as e:
                print(f"❌ Error processing {series['title_spanish']}: {e}")
                return []

        # 并发执行
        if tasks:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_series = {executor.submit(process_series, s): s for s in tasks}
                
                for i, future in enumerate(as_completed(future_to_series)):
                    series = future_to_series[future]
                    try:
                        result_episodes = future.result()
                        all_episodes.extend(result_episodes)
                        if result_episodes:
                            print(f"  ✅ [{i+1}/{len(tasks)}] 完成: {series['title_spanish']} ({len(result_episodes)} 集)")
                        else:
                            print(f"  ⚠️ [{i+1}/{len(tasks)}] 无剧集: {series['title_spanish']}")
                    except Exception as exc:
                        print(f"  ❌ {series['title_spanish']} generated an exception: {exc}")
        
        return all_episodes
