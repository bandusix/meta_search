import re
from base_scraper import BaseScraper

from concurrent.futures import ThreadPoolExecutor, as_completed

class MovieScraper(BaseScraper):
    """电影爬虫"""
    
    def _parse_movie_card(self, article):
        """解析电影卡片，提取基本信息"""
        try:
            # 检查是否为电视剧（跳过）
            quality_el = article.select_one('.quality')
            quality_text = quality_el.get_text(strip=True) if quality_el else ''
            if re.match(r's\d+-e\d+', quality_text):
                return None  # 这是电视剧，跳过
            
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
                # 去除可能的非数字字符
                rating_val = re.search(r'[\d\.]+', rating_text)
                rating = float(rating_val.group()) if rating_val else None
            except ValueError:
                rating = None
            
            # 清晰度
            quality = quality_text if quality_text else None
            
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
            
            # 音频语言
            audio_langs = []
            if article.select_one('.audio .latino'):
                audio_langs.append('Latino')
            if article.select_one('.audio .castellano'):
                audio_langs.append('Castellano')
            if article.select_one('.audio .subtitulado'):
                audio_langs.append('Subtitulado')
            audio = ', '.join(audio_langs) if audio_langs else None
            
            return {
                'title_spanish': title,
                'year': year,
                'rating': rating,
                'quality': quality,
                'image_url': image_url,
                'detail_url': detail_url,
                'audio': audio,
            }
            
        except Exception as e:
            print(f"  ⚠️ 解析卡片失败: {e}")
            return None
    
    def _parse_movie_detail(self, url):
        """访问详情页，提取额外信息"""
        soup = self._fetch_page(url)
        if not soup:
            return {}
        
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
                # 通常类型在第4个位置，但也可能变动，简单遍历查找非特定格式的span
                # 或者直接取所有非特定class的span作为genre候选
                genres = []
                for span in spans:
                    text = span.get_text(strip=True)
                    # 排除年份、时长、国家、清晰度等特征文本
                    if (not re.match(r'^\d{4}$', text) and 
                        'Min.' not in text and 
                        'HD' not in text and 
                        text != detail.get('country', '')):
                        genres.append(text)
                if genres:
                    detail['genre'] = ', '.join(genres)
            
            # 清晰度（从详情页获取更准确的信息）
            if extra:
                spans = extra.select('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if 'HD' in text or 'CAM' in text:
                        detail['quality'] = text
                        break
            
            # 站内评分
            rating_el = soup.select_one('.dt_rating_vgs')
            if rating_el:
                try:
                    detail['rating'] = float(rating_el.get_text(strip=True))
                except ValueError:
                    pass
            
            # 网页标题
            if soup.title:
                detail['web_url_title'] = soup.title.get_text(strip=True)
            
            # 海报（高清版）
            poster_el = soup.select_one('.sheader .poster img')
            if poster_el:
                src = poster_el.get('src', '')
                if src and not src.startswith('http'):
                    src = self.BASE_URL + src
                detail['image_url'] = src
            
        except Exception as e:
            print(f"  ⚠️ 解析详情页失败: {e}")
        
        return detail

    def scrape_latest_movies(self, limit=2000, fetch_details=True, existing_urls=None):
        """爬取最新电影"""
        movies = []
        page = 1
        count = 0
        if existing_urls is None:
            existing_urls = set()
        
        print(f"\n{'='*60}")
        print(f"🎬 开始爬取最新电影 (目标: {limit} 部) [线程数: {self.max_workers}]...")
        print(f"{'='*60}")
        
        while count < limit:
            # 构建URL
            if page == 1:
                url = f"{self.BASE_URL}/pelicula/"
            else:
                url = f"{self.BASE_URL}/pelicula/page/{page}/"
            
            print(f"\n📄 正在爬取第 {page} 页: {url}")
            
            soup = self._fetch_page(url)
            if not soup:
                print(f"  ❌ 获取页面失败，停止爬取")
                break
            
            # 解析所有卡片
            articles = soup.select('article.item.movies')
            if not articles:
                # 尝试备选选择器
                articles = soup.select('article.item')
            
            if not articles:
                print(f"  ✅ 没有更多内容，结束爬取")
                break
            
            page_movies = []
            for article in articles:
                if count >= limit:
                    break
                movie = self._parse_movie_card(article)
                if movie:  # None 表示是电视剧，已跳过
                    page_movies.append(movie)
                    count += 1
            
            print(f"  找到 {len(page_movies)} 部电影")
            
            # 可选：访问详情页获取更多信息
            if fetch_details:
                # 准备任务列表
                tasks = []
                for i, movie in enumerate(page_movies):
                    url = movie['detail_url']
                    
                    # 检查是否已存在
                    is_existing = False
                    need_update = True
                    
                    if isinstance(existing_urls, dict):
                        if url in existing_urls:
                            is_existing = True
                            if existing_urls[url]: 
                                need_update = False
                    elif url in existing_urls:
                        is_existing = True
                        need_update = False 
                        
                    if is_existing and not need_update:
                        print(f"  📖 [{count-len(page_movies)+i+1}/{limit}] 已存在且完整，跳过: {movie['title_spanish']}")
                        continue

                    if is_existing and need_update:
                        print(f"  🔄 [{count-len(page_movies)+i+1}/{limit}] 需补全: {movie['title_spanish']}")
                    else:
                        print(f"  📖 [{count-len(page_movies)+i+1}/{limit}] 获取详情: {movie['title_spanish']}")
                    
                    tasks.append(movie)

                # 并发执行详情页抓取
                if tasks:
                    with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                        future_to_movie = {executor.submit(self._parse_movie_detail, m['detail_url']): m for m in tasks}
                        
                        for future in as_completed(future_to_movie):
                            movie = future_to_movie[future]
                            try:
                                detail = future.result()
                                movie.update(detail)
                            except Exception as exc:
                                print(f"  ❌ {movie['title_spanish']} generated an exception: {exc}")
            
            movies.extend(page_movies)
            
            # 检查是否有下一页
            pagination = soup.select_one('.pagination')
            if not pagination or not pagination.select_one('#nextpagination'):
                print(f"  ✅ 已到最后一页")
                break
            
            page += 1
            # self._random_delay() # 并发模式下，延迟由各个线程控制，主循环不需要延迟
        
        print(f"\n✨ 最新电影爬取完成！共 {len(movies)} 部电影")
        return movies
