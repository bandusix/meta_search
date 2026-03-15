import requests
import random
import time
from bs4 import BeautifulSoup
import urllib3
import threading

# 禁用不安全请求警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class BaseScraper:
    """基础爬虫类"""
    
    BASE_URL = "https://repelishd.city"
    
    # 代理配置
    PROXIES = {
        "http": "http://hstxytwd:t42hc6faklwd@193.160.79.117:6079/",
        "https": "http://hstxytwd:t42hc6faklwd@193.160.79.117:6079/"
    }
    
    # 200+ User-Agents (涵盖 PC, Mobile, Tablet, Search Bots)
    USER_AGENTS = [
        # --- PC Windows ---
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0 Safari/537.36",
        # ... (此处省略部分以节省空间，实际部署时会包含完整列表) ...
        # --- PC Mac ---
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        # --- PC Linux ---
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0",
        # --- Mobile Android ---
        "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.101 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
        # --- Mobile iOS ---
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
        # --- Search Bots ---
        "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
        "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
        "Mozilla/5.0 (compatible; Yahoo! Slurp; +http://help.yahoo.com/help/us/ysearch/slurp)",
        "Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)",
    ] + [f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{i}.0.0.0 Safari/537.36" for i in range(100, 120)] # 动态生成更多
    
    def __init__(self, delay_min=0.1, delay_max=0.5, max_workers=10):
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.max_workers = max_workers
        self.local = threading.local() # 线程本地存储
    
    def _get_session(self):
        """获取当前线程的 Session，如果不存在则创建"""
        if not hasattr(self.local, 'session'):
            self.local.session = self._create_session()
        return self.local.session

    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-MX,es;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': self.BASE_URL,
        })
        session.proxies.update(self.PROXIES)
        session.verify = False  # 忽略 SSL 证书验证
        return session
    
    def _random_delay(self):
        # 高并发模式下，延迟可以适当降低
        delay = random.uniform(self.delay_min, self.delay_max)
        time.sleep(delay)
    
    def _rotate_user_agent(self, session):
        session.headers['User-Agent'] = random.choice(self.USER_AGENTS)
    
    def _fetch_page(self, url, max_retries=3):
        session = self._get_session()
        for attempt in range(max_retries):
            try:
                self._rotate_user_agent(session)
                # print(f"  🕸️ Fetching: {url}")
                response = session.get(url, timeout=20) # 缩短超时时间
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'html.parser')
                elif response.status_code == 404:
                    print(f"  ⚠️ 页面不存在 (404): {url}")
                    return None
                else:
                    print(f"  ⚠️ HTTP {response.status_code}: {url}")
                    
            except requests.exceptions.Timeout:
                print(f"  ⚠️ 请求超时 (尝试 {attempt+1}/{max_retries}): {url}")
            except requests.exceptions.ConnectionError:
                print(f"  ⚠️ 连接错误 (尝试 {attempt+1}/{max_retries}): {url}")
            except Exception as e:
                print(f"  ⚠️ 请求异常 (尝试 {attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 1 # 减少重试等待时间
                time.sleep(wait)
        
        return None
