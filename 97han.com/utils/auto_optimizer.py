#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动优化器 - 监控爬取性能并自动调整参数
"""

import time
import json
import threading
import statistics
from typing import Dict, List, Any, Optional
from pathlib import Path

class AutoOptimizer:
    """自动性能优化器"""
    
    def __init__(self, config_file: str = "config/optimizer_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.performance_data = {
            'response_times': [],
            'error_rates': [],
            'duplicate_rates': [],
            'throughput': [],
            'timestamps': []
        }
        self.is_running = False
        self.optimizer_thread = None
        self.callbacks = {}
        
    def _load_config(self) -> Dict[str, Any]:
        """加载优化器配置"""
        default_config = {
            "check_interval": 300,  # 5分钟
            "log_lines_threshold": 100,  # 100条日志
            "response_time_threshold": 2.0,  # 2秒
            "error_rate_threshold": 0.1,  # 10%
            "duplicate_rate_threshold": 0.05,  # 5%
            "min_concurrency": 1,
            "max_concurrency": 100,
            "retry_backoff_base": 1.0,
            "retry_max_attempts": 3,
            "auto_tune_enabled": True
        }
        
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                print(f"[AUTO-TUNE] 配置加载失败，使用默认配置: {e}")
        
        return default_config
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            config_dir = Path(self.config_file).parent
            config_dir.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[AUTO-TUNE] 配置保存失败: {e}")
    
    def register_callback(self, event: str, callback):
        """注册事件回调"""
        self.callbacks[event] = callback
    
    def trigger_event(self, event: str, data: Dict[str, Any]):
        """触发事件"""
        if event in self.callbacks:
            try:
                self.callbacks[event](data)
            except Exception as e:
                print(f"[AUTO-TUNE] 事件回调失败 {event}: {e}")
    
    def add_performance_data(self, response_time: float, has_error: bool, 
                             is_duplicate: bool, items_count: int):
        """添加性能数据"""
        current_time = time.time()
        
        self.performance_data['response_times'].append(response_time)
        self.performance_data['error_rates'].append(1.0 if has_error else 0.0)
        self.performance_data['duplicate_rates'].append(1.0 if is_duplicate else 0.0)
        self.performance_data['throughput'].append(items_count)
        self.performance_data['timestamps'].append(current_time)
        
        # 保持数据在合理范围内
        max_data_points = 1000
        for key in self.performance_data:
            if len(self.performance_data[key]) > max_data_points:
                self.performance_data[key] = self.performance_data[key][-max_data_points:]
    
    def analyze_performance(self) -> Dict[str, Any]:
        """分析当前性能"""
        if not self.performance_data['response_times']:
            return {'status': 'no_data'}
        
        recent_data = self._get_recent_data(hours=1)  # 最近1小时
        if not recent_data['response_times']:
            return {'status': 'insufficient_data'}
        
        analysis = {
            'status': 'ok',
            'avg_response_time': statistics.mean(recent_data['response_times']),
            'median_response_time': statistics.median(recent_data['response_times']),
            'p95_response_time': self._percentile(recent_data['response_times'], 95),
            'error_rate': statistics.mean(recent_data['error_rates']),
            'duplicate_rate': statistics.mean(recent_data['duplicate_rates']),
            'avg_throughput': statistics.mean(recent_data['throughput']),
            'total_requests': len(recent_data['response_times'])
        }
        
        return analysis
    
    def _get_recent_data(self, hours: int = 1) -> Dict[str, List]:
        """获取最近时间窗口的数据"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        
        recent_indices = [i for i, ts in enumerate(self.performance_data['timestamps']) 
                         if ts >= cutoff_time]
        
        return {
            'response_times': [self.performance_data['response_times'][i] for i in recent_indices],
            'error_rates': [self.performance_data['error_rates'][i] for i in recent_indices],
            'duplicate_rates': [self.performance_data['duplicate_rates'][i] for i in recent_indices],
            'throughput': [self.performance_data['throughput'][i] for i in recent_indices]
        }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def should_optimize(self) -> tuple[bool, List[str]]:
        """判断是否需要优化"""
        if not self.config['auto_tune_enabled']:
            return False, []
        
        analysis = self.analyze_performance()
        if analysis['status'] != 'ok':
            return False, []
        
        reasons = []
        
        # 检查响应时间
        if analysis['avg_response_time'] > self.config['response_time_threshold']:
            reasons.append(f"响应时间过长: {analysis['avg_response_time']:.2f}s")
        
        # 检查错误率
        if analysis['error_rate'] > self.config['error_rate_threshold']:
            reasons.append(f"错误率过高: {analysis['error_rate']:.1%}")
        
        # 检查重复率
        if analysis['duplicate_rate'] > self.config['duplicate_rate_threshold']:
            reasons.append(f"重复率过高: {analysis['duplicate_rate']:.1%}")
        
        return len(reasons) > 0, reasons
    
    def generate_optimization_plan(self) -> Dict[str, Any]:
        """生成优化计划"""
        should_opt, reasons = self.should_optimize()
        if not should_opt:
            return {'should_optimize': False}
        
        analysis = self.analyze_performance()
        plan = {
            'should_optimize': True,
            'reasons': reasons,
            'analysis': analysis,
            'actions': []
        }
        
        # 响应时间过长 - 降低并发
        if analysis['avg_response_time'] > self.config['response_time_threshold']:
            current_concurrency = self.config.get('current_concurrency', 40)
            new_concurrency = max(self.config['min_concurrency'], 
                                int(current_concurrency * 0.8))
            plan['actions'].append({
                'type': 'reduce_concurrency',
                'from': current_concurrency,
                'to': new_concurrency,
                'reason': '响应时间过长'
            })
        
        # 错误率过高 - 启用重试
        if analysis['error_rate'] > self.config['error_rate_threshold']:
            plan['actions'].append({
                'type': 'enable_retry',
                'backoff_base': self.config['retry_backoff_base'],
                'max_attempts': self.config['retry_max_attempts'],
                'reason': '错误率过高'
            })
        
        # 重复率过高 - 启用布隆过滤器
        if analysis['duplicate_rate'] > self.config['duplicate_rate_threshold']:
            plan['actions'].append({
                'type': 'enable_bloom_filter',
                'reason': '重复率过高'
            })
        
        return plan
    
    def apply_optimization_plan(self, plan: Dict[str, Any]) -> bool:
        """应用优化计划"""
        if not plan.get('should_optimize', False):
            return False
        
        success = True
        applied_actions = []
        
        for action in plan.get('actions', []):
            try:
                if action['type'] == 'reduce_concurrency':
                    self.config['current_concurrency'] = action['to']
                    applied_actions.append(f"并发数降至 {action['to']}")
                
                elif action['type'] == 'enable_retry':
                    self.config['retry_enabled'] = True
                    self.config['retry_backoff_base'] = action['backoff_base']
                    self.config['retry_max_attempts'] = action['max_attempts']
                    applied_actions.append("启用指数退避重试")
                
                elif action['type'] == 'enable_bloom_filter':
                    self.config['bloom_filter_enabled'] = True
                    applied_actions.append("启用布隆过滤器去重")
                
            except Exception as e:
                print(f"[AUTO-TUNE] 应用优化失败 {action['type']}: {e}")
                success = False
        
        if applied_actions:
            self._save_config()
            actions_str = " | ".join(applied_actions)
            print(f"🤖 [AUTO-TUNE] {actions_str}")
            
            # 触发事件
            self.trigger_event('optimization_applied', {
                'actions': applied_actions,
                'plan': plan
            })
        
        return success
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_running:
            return
        
        self.is_running = True
        self.optimizer_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.optimizer_thread.start()
        print("[AUTO-TUNE] 自动优化监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        if self.optimizer_thread:
            self.optimizer_thread.join(timeout=5)
        print("[AUTO-TUNE] 自动优化监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                plan = self.generate_optimization_plan()
                if plan.get('should_optimize', False):
                    self.apply_optimization_plan(plan)
                
                time.sleep(self.config['check_interval'])
            except Exception as e:
                print(f"[AUTO-TUNE] 监控循环异常: {e}")
                time.sleep(60)  # 异常时等待1分钟
    
    def get_status(self) -> Dict[str, Any]:
        """获取优化器状态"""
        analysis = self.analyze_performance()
        return {
            'is_running': self.is_running,
            'config': self.config,
            'analysis': analysis,
            'data_points': len(self.performance_data['response_times']),
            'optimization_stats': {
                'total_plans_generated': 0,  # TODO: 统计生成的优化计划数
                'total_plans_applied': 0     # TODO: 统计应用的优化计划数
            }
        }