#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强型日志系统 - 支持结构化日志、终端实时输出、自动优化
"""

import json
import time
import threading
import os
import re
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Optional, Any
import logging

class EnhancedLogger:
    """增强型日志器 - 支持结构化日志和自动优化"""
    
    def __init__(self, log_file: str = "crawl_progress.log", max_log_lines: int = 10000):
        self.log_file = log_file
        self.max_log_lines = max_log_lines
        self.log_buffer = deque(maxlen=1000)  # 内存缓冲区
        self.stats = {
            'total_requests': 0,
            'failed_requests': 0,
            'duplicate_ids': 0,
            'response_times': deque(maxlen=1000),
            'saved_ids': set(),
            'last_optimization': time.time()
        }
        self.config = {
            'concurrency': 40,
            'retry_enabled': False,
            'bloom_filter_enabled': False,
            'base_delay': (3, 5),
            'failure_threshold': 0.1,  # 10%
            'duplicate_threshold': 0.05,  # 5%
            'response_time_threshold': 2.0  # 2秒
        }
        self.lock = threading.Lock()
        self._init_log_file()
        self._start_background_optimizer()
    
    def _init_log_file(self):
        """初始化日志文件"""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write("timestamp|spider_name|request_url|response_status|saved_data_fields|saved_id|item_count|elapsed_ms\n")
    
    def _start_background_optimizer(self):
        """启动后台优化线程"""
        def optimizer_worker():
            while True:
                try:
                    time.sleep(60)  # 每分钟检查一次
                    self._auto_optimize()
                except Exception as e:
                    print(f"[AUTO-TUNE] 优化器异常: {e}")
        
        optimizer_thread = threading.Thread(target=optimizer_worker, daemon=True)
        optimizer_thread.start()
    
    def log_request_start(self, spider_name: str, request_url: str):
        """记录请求开始"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [{spider_name}] START → {request_url}")
        
        with self.lock:
            self.stats['total_requests'] += 1
    
    def log_request_complete(self, spider_name: str, request_url: str, response_status: int,
                           saved_data_fields: List[str], saved_id: Optional[int], 
                           item_count: int, elapsed_ms: float):
        """记录请求完成"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # 终端输出
        fields_str = json.dumps(saved_data_fields, ensure_ascii=False) if saved_data_fields else "[]"
        print(f"[{timestamp}] [{spider_name}] DONE  ← {response_status} | saved_id={saved_id} | fields={fields_str} | items={item_count} | cost={elapsed_ms:.0f}ms")
        
        # 结构化日志
        log_line = f"{timestamp}|{spider_name}|{request_url}|{response_status}|{fields_str}|{saved_id}|{item_count}|{elapsed_ms:.0f}"
        
        with self.lock:
            self.log_buffer.append(log_line)
            self.stats['response_times'].append(elapsed_ms)
            if saved_id:
                if saved_id in self.stats['saved_ids']:
                    self.stats['duplicate_ids'] += 1
                    print(f"⚠️  [{timestamp}] [{spider_name}] 重复ID警告: {saved_id}")
                else:
                    self.stats['saved_ids'].add(saved_id)
            
            # 每100条写入一次文件
            if len(self.log_buffer) >= 100:
                self._flush_buffer()
    
    def log_error(self, spider_name: str, request_url: str, exception_type: str, exception_msg: str):
        """记录错误"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"❌ [{timestamp}] [{spider_name}] ERROR ← {exception_type}: {exception_msg}")
        
        with self.lock:
            self.stats['failed_requests'] += 1
            log_line = f"{timestamp}|{spider_name}|{request_url}|ERROR|[]|None|0|0"
            self.log_buffer.append(log_line)
    
    def log_validation(self, spider_name: str, pass_check: bool, cumulative_count: int):
        """记录数据校验结果"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        status = "PASS" if pass_check else "FAIL"
        print(f"✅ [{timestamp}] [{spider_name}] VALIDATE ← unique_check={status} | total_saved={cumulative_count}")
        
        log_line = f"{timestamp}|{spider_name}|VALIDATE|{status}|[]|None|{cumulative_count}|0"
        with self.lock:
            self.log_buffer.append(log_line)
    
    def _flush_buffer(self):
        """刷新缓冲区到文件"""
        if not self.log_buffer:
            return
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            for line in self.log_buffer:
                f.write(line + "\n")
        
        self.log_buffer.clear()
        
        # 检查文件大小，必要时轮转
        if os.path.getsize(self.log_file) > 50 * 1024 * 1024:  # 50MB
            self._rotate_log()
    
    def _rotate_log(self):
        """日志轮转"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{self.log_file}.{timestamp}"
        os.rename(self.log_file, backup_file)
        self._init_log_file()
        print(f"[LOG] 日志轮转: {backup_file}")
    
    def _auto_optimize(self):
        """自动优化逻辑"""
        with self.lock:
            if len(self.stats['response_times']) < 10:
                return
            
            # 计算统计指标
            avg_response_time = sum(self.stats['response_times']) / len(self.stats['response_times'])
            failure_rate = self.stats['failed_requests'] / max(self.stats['total_requests'], 1)
            duplicate_rate = self.stats['duplicate_ids'] / max(len(self.stats['saved_ids']), 1)
            
            # 检查是否需要优化
            optimizations = []
            
            # 1. 响应时间过长，降低并发
            if avg_response_time > self.config['response_time_threshold']:
                old_concurrency = self.config['concurrency']
                self.config['concurrency'] = max(1, int(old_concurrency * 0.8))
                optimizations.append(f"并发数降至 {self.config['concurrency']}")
            
            # 2. 失败率过高，启用重试
            if failure_rate > self.config['failure_threshold']:
                self.config['retry_enabled'] = True
                optimizations.append("启用指数退避重试")
            
            # 3. 重复率过高，启用布隆过滤器
            if duplicate_rate > self.config['duplicate_threshold']:
                self.config['bloom_filter_enabled'] = True
                optimizations.append("启用布隆过滤器去重")
            
            # 输出优化信息
            if optimizations:
                opt_msg = " | ".join(optimizations)
                print(f"🤖 [AUTO-TUNE] {opt_msg}")
                print(f"    平均响应时间: {avg_response_time:.2f}s, 失败率: {failure_rate:.1%}, 重复率: {duplicate_rate:.1%}")
            
            # 重置统计
            self.stats['last_optimization'] = time.time()
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        with self.lock:
            return self.config.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                'total_requests': self.stats['total_requests'],
                'failed_requests': self.stats['failed_requests'],
                'duplicate_ids': self.stats['duplicate_ids'],
                'unique_ids': len(self.stats['saved_ids']),
                'avg_response_time': sum(self.stats['response_times']) / len(self.stats['response_times']) if self.stats['response_times'] else 0
            }
    
    def parse_log_line(self, log_line: str) -> Optional[Dict[str, Any]]:
        """解析日志行"""
        try:
            parts = log_line.strip().split('|')
            if len(parts) < 8:
                return None
            
            # 解析基本字段
            parsed = {
                'timestamp': parts[0],
                'spider_name': parts[1],
                'request_url': parts[2],
                'response_status': int(parts[3]),
                'saved_data_fields': parts[4].strip('[]').split(',') if parts[4] != '[]' else [],
                'saved_id': parts[5] if parts[5] != 'None' else None,
                'item_count': int(parts[6]),
                'elapsed_ms': float(parts[7])
            }
            
            # 转换保存ID为整数
            if parsed['saved_id'] and parsed['saved_id'].isdigit():
                parsed['saved_id'] = int(parsed['saved_id'])
            
            return parsed
            
        except (ValueError, IndexError) as e:
            self._write_to_log(f"解析日志行失败: {e} | 原始行: {log_line}")
            return None
    
    def close(self):
        """关闭日志器"""
        self._flush_buffer()

# 全局日志器实例
logger = EnhancedLogger()