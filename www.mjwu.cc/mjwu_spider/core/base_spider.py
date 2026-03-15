#!/usr/bin/env python3
"""爬虫基类"""

import re
import time
import random
import logging
import sqlite3
import requests
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin

class BaseSpider(ABC):
    """爬虫基类"""
    
    # iPhone 17 UA (iOS 18)
    IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1"
    
    # PC UA
    PC_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    def __init__(self, config_path=None):
        if config_path is None:
            # Default to config/settings.yaml relative to the script location
            base_dir = Path(__file__).resolve().parent.parent
            config_path = base_dir / 'config' / 'settings.yaml'
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.base_url = self.config['spider']['base_url']
        self.delay_range = tuple(self.config['spider']['delay_range'])
        self.max_retries = self.config['spider']['max_retries']
        self.timeout = self.config['spider']['timeout']
        
        # 初始化日志
        self.logger = self._init_logger()
        
        # 初始化Session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.IPHONE_UA,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        
        # 初始化数据库
        self.db_path = self.config['database']['path']
        self.logger.info(f"Using database: {self.db_path}")
        self._init_database()
    
    def _init_logger(self):
        """初始化日志"""
        log_config = self.config['logging']
        logger = logging.getLogger(self.__class__.__name__)
        logger.setLevel(getattr(logging, log_config['level']))
        
        # 控制台处理器
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(log_config['format']))
        logger.addHandler(console)
        
        # 文件处理器（带轮转）
        from logging.handlers import RotatingFileHandler
        Path(log_config['file']).parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_config['file'],
            maxBytes=log_config['max_bytes'],
            backupCount=log_config['backup_count'],
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_config['format']))
        logger.addHandler(file_handler)
        
        return logger
    
    def _get_random_ua(self):
        """获取随机User-Agent（iPhone/PC轮换）"""
        return random.choice([self.IPHONE_UA, self.PC_UA])
    
    def _init_database(self):
        """初始化数据库（子类实现具体表结构）"""
        pass
    
    def request(self, url, max_retries=None):
        """发送HTTP请求，带重试和随机延迟"""
        max_retries = max_retries or self.max_retries
        full_url = url if url.startswith('http') else urljoin(self.base_url, url)
        
        for attempt in range(max_retries):
            try:
                # 轮换UA
                self.session.headers['User-Agent'] = self._get_random_ua()
                response = self.session.get(full_url, timeout=self.timeout)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    time.sleep(random.uniform(*self.delay_range))
                    return response
                elif response.status_code == 404:
                    self.logger.warning(f"页面不存在: {full_url}")
                    return None
                else:
                    self.logger.warning(f"HTTP {response.status_code}: {full_url}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"请求超时 ({attempt+1}/{max_retries}): {full_url}")
            except requests.exceptions.RequestException as e:
                self.logger.error(f"请求错误 ({attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def build_list_url(self, content_type, page=1, year=None):
        """构造列表页URL"""
        base = f"/type/{content_type}"
        if year and page > 1:
            return f"{base}/year/{year}/page/{page}/"
        elif year:
            return f"{base}/year/{year}/"
        elif page > 1:
            return f"{base}/page/{page}/"
        else:
            return f"{base}/"
    
    @staticmethod
    def extract_vod_id(url):
        """从URL中提取视频ID"""
        match = re.search(r'/(?:vod|play)/(\d+)', url)
        return int(match.group(1)) if match else None
    
    @staticmethod
    def extract_year_from_url(url):
        """从URL中提取年份"""
        match = re.search(r'/year/(\d{4})', url)
        return int(match.group(1)) if match else None
    
    @abstractmethod
    def run(self):
        """运行爬虫（子类实现）"""
        pass
