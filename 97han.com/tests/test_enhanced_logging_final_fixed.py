#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志系统单元测试 - 最终修正版
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import time
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_logger import EnhancedLogger
from utils.data_validator import DataValidator
from utils.auto_optimizer import AutoOptimizer


class TestEnhancedLogger(unittest.TestCase):
    """测试增强版日志器"""
    
    def setUp(self):
        """测试前设置"""
        self.logger = EnhancedLogger(log_file="test_crawl.log")
        # 清空之前的测试数据
        if os.path.exists("test_crawl.log"):
            os.remove("test_crawl.log")
    
    def tearDown(self):
        """测试后清理"""
        self.logger.close()
        if os.path.exists("test_crawl.log"):
            os.remove("test_crawl.log")
    
    def test_initialization(self):
        """测试日志器初始化"""
        self.assertIsNotNone(self.logger)
        self.assertEqual(self.logger.log_file, "test_crawl.log")
        self.assertEqual(self.logger.max_log_lines, 10000)
        self.assertIsNotNone(self.logger.log_buffer)
        self.assertIsNotNone(self.logger.lock)
    
    def test_log_request_start(self):
        """测试请求开始记录"""
        spider_name = "test_spider"
        request_url = "http://example.com/test"
        
        # 捕获输出
        with patch('builtins.print') as mock_print:
            self.logger.log_request_start(spider_name, request_url)
            
            # 验证打印输出
            mock_print.assert_called()
            args = mock_print.call_args[0][0]
            self.assertIn(spider_name, args)
            self.assertIn("START", args)
    
    def test_log_request_complete(self):
        """测试请求完成记录"""
        spider_name = "test_spider"
        request_url = "http://example.com/test"
        response_status = 200
        saved_data_fields = ["title", "year", "category"]
        saved_id = 12345
        item_count = 1
        elapsed_ms = 1500.0
        
        # 捕获输出
        with patch('builtins.print') as mock_print:
            self.logger.log_request_complete(
                spider_name, request_url, response_status,
                saved_data_fields, saved_id, item_count, elapsed_ms
            )
            
            # 验证打印输出
            mock_print.assert_called()
            args = mock_print.call_args[0][0]
            self.assertIn(spider_name, args)
            self.assertIn("DONE", args)
            self.assertIn(str(saved_id), args)
            self.assertIn(str(item_count), args)
    
    def test_log_error(self):
        """测试错误记录"""
        spider_name = "test_spider"
        request_url = "http://example.com/test"
        error_type = "ConnectionError"
        error_message = "连接超时"
        
        # 捕获输出
        with patch('builtins.print') as mock_print:
            self.logger.log_error(spider_name, request_url, error_type, error_message)
            
            # 验证打印输出
            mock_print.assert_called()
            args = mock_print.call_args[0][0]
            self.assertIn(spider_name, args)
            self.assertIn("ERROR", args)
            self.assertIn(error_type, args)
    
    def test_log_validation(self):
        """测试验证记录"""
        spider_name = "test_spider"
        is_valid = True
        total_records = 1000
        
        # 捕获输出
        with patch('builtins.print') as mock_print:
            self.logger.log_validation(spider_name, is_valid, total_records)
            
            # 验证打印输出
            mock_print.assert_called()
            args = mock_print.call_args[0][0]
            self.assertIn(spider_name, args)
            self.assertIn("VALIDATE", args)
            self.assertIn(str(total_records), args)
    
    def test_log_buffer_flush(self):
        """测试日志缓冲区刷新"""
        # 添加多条日志（超过缓冲区大小）
        for i in range(150):  # 超过缓冲区大小
            self.logger.log_request_complete(
                "test_spider", f"http://example.com/{i}", 200,
                ["field1", "field2"], i, 1, 100.0
            )
        
        # 手动刷新缓冲区
        self.logger._flush_buffer()
        
        # 验证日志文件存在且有内容
        self.assertTrue(os.path.exists("test_crawl.log"))
        with open("test_crawl.log", 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("test_spider", content)
            self.assertIn("http://example.com", content)
    
    def test_parse_log_line(self):
        """测试日志行解析"""
        # 创建测试日志行
        log_line = "2024-01-15 14:30:45.123|movie|http://www.97han.com/type/1.html|200|[\"title\",\"year\"]|12345|1|1500"
        
        parsed = self.logger.parse_log_line(log_line)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['timestamp'], "2024-01-15 14:30:45.123")
        self.assertEqual(parsed['spider_name'], "movie")
        self.assertEqual(parsed['request_url'], "http://www.97han.com/type/1.html")
        self.assertEqual(parsed['response_status'], 200)
        self.assertEqual(parsed['saved_data_fields'], ['"title"', '"year"'])
        self.assertEqual(parsed['saved_id'], 12345)
        self.assertEqual(parsed['item_count'], 1)
        self.assertEqual(parsed['elapsed_ms'], 1500.0)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        # 先记录请求开始，增加总请求数
        self.logger.log_request_start("test_spider", "http://example.com/1")
        self.logger.log_request_start("test_spider", "http://example.com/2")
        
        # 然后记录请求完成
        self.logger.log_request_complete(
            "test_spider", "http://example.com/1", 200,
            ["field1"], 1, 1, 1000.0
        )
        self.logger.log_request_complete(
            "test_spider", "http://example.com/2", 404,
            [], None, 0, 500.0
        )
        
        stats = self.logger.get_stats()
        
        self.assertEqual(stats['total_requests'], 2)
        self.assertEqual(stats['failed_requests'], 1)
        self.assertEqual(stats['duplicate_ids'], 0)
        self.assertEqual(stats['unique_ids'], 1)
        self.assertGreater(stats['avg_response_time'], 0)
    
    def test_get_config(self):
        """测试获取配置"""
        config = self.logger.get_config()
        
        self.assertIn('concurrency', config)
        self.assertIn('retry_enabled', config)
        self.assertIn('bloom_filter_enabled', config)


class TestDataValidator(unittest.TestCase):
    """测试数据验证器"""
    
    def setUp(self):
        """测试前设置"""
        self.validator = DataValidator()
    
    def test_validate_movie_data_valid(self):
        """测试有效电影数据验证"""
        movie_data = {
            'vod_id': 12345,
            'title': '测试电影',
            'category': '电影',
            'year': 2023
        }
        
        is_valid, error_msg = self.validator.validate_movie_data(movie_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_movie_data_invalid(self):
        """测试无效电影数据验证"""
        # 缺少必填字段
        movie_data = {
            'title': '测试电影',
            'category': '电影'
        }
        
        is_valid, error_msg = self.validator.validate_movie_data(movie_data)
        
        self.assertFalse(is_valid)
        self.assertIn("缺少必需字段", error_msg)
    
    def test_validate_tv_data_valid(self):
        """测试有效电视剧数据验证"""
        tv_data = {
            'vod_id': 67890,
            'title': '测试电视剧',
            'category': '电视剧',
            'episodes': [
                {'episode_number': 1, 'play_url': 'http://example.com/ep1'},
                {'episode_number': 2, 'play_url': 'http://example.com/ep2'}
            ]
        }
        
        is_valid, error_msg = self.validator.validate_tv_data(tv_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_validate_tv_data_invalid(self):
        """测试无效电视剧数据验证"""
        tv_data = {
            'vod_id': 67890,
            'title': '测试电视剧',
            'category': '电视剧'
            # 缺少episodes字段
        }
        
        is_valid, error_msg = self.validator.validate_tv_data(tv_data)
        
        self.assertFalse(is_valid)
        self.assertIn("缺少必需字段", error_msg)
    
    def test_duplicate_detection(self):
        """测试重复检测"""
        # 第一次添加ID
        movie_data1 = {
            'vod_id': 12345,
            'title': '测试电影1',
            'category': '电影'
        }
        
        is_valid1, error_msg1 = self.validator.validate_movie_data(movie_data1)
        self.assertTrue(is_valid1)
        self.assertIsNone(error_msg1)
        
        # 第二次添加相同ID
        movie_data2 = {
            'vod_id': 12345,
            'title': '测试电影2',
            'category': '电影'
        }
        
        is_valid2, error_msg2 = self.validator.validate_movie_data(movie_data2)
        self.assertFalse(is_valid2)
        self.assertIn("重复ID", error_msg2)
    
    def test_get_validation_summary(self):
        """测试获取验证统计"""
        # 添加一些测试数据
        self.validator.validation_stats['total_checks'] = 10
        self.validator.validation_stats['duplicates_found'] = 2
        self.validator.validation_stats['validation_failures'] = 1
        
        summary = self.validator.get_validation_summary()
        
        self.assertEqual(summary['total_checks'], 10)
        self.assertEqual(summary['duplicates_found'], 2)
        self.assertEqual(summary['validation_failures'], 1)


class TestAutoOptimizer(unittest.TestCase):
    """测试自动优化器"""
    
    def setUp(self):
        """测试前设置"""
        self.config_file = "test_optimizer_config.json"
        self.optimizer = AutoOptimizer(config_file=self.config_file)
        
        # 清理测试文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def tearDown(self):
        """测试后清理"""
        self.optimizer.stop_monitoring()
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def test_initialization(self):
        """测试优化器初始化"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.config_file, self.config_file)
        self.assertIn('response_time_threshold', self.optimizer.config)
        self.assertIn('error_rate_threshold', self.optimizer.config)
    
    def test_add_performance_data(self):
        """测试添加性能数据"""
        # 添加正常数据
        self.optimizer.add_performance_data(1.5, False, False, 1)
        self.optimizer.add_performance_data(2.0, True, False, 0)
        self.optimizer.add_performance_data(0.8, False, True, 1)
        
        # 验证数据被添加
        self.assertEqual(len(self.optimizer.performance_data['response_times']), 3)
        self.assertEqual(len(self.optimizer.performance_data['error_rates']), 3)
        self.assertEqual(len(self.optimizer.performance_data['duplicate_rates']), 3)
    
    def test_analyze_performance(self):
        """测试性能分析"""
        # 添加测试数据
        for i in range(10):
            response_time = 1.0 + (i * 0.2)  # 递增的响应时间
            is_error = i % 3 == 0  # 每3个请求有一个错误
            is_duplicate = i % 5 == 0  # 每5个请求有一个重复
            self.optimizer.add_performance_data(response_time, is_error, is_duplicate, 1)
        
        analysis = self.optimizer.analyze_performance()
        
        self.assertIn('status', analysis)
        self.assertEqual(analysis['status'], 'ok')
        self.assertIn('avg_response_time', analysis)
        self.assertIn('error_rate', analysis)
        self.assertIn('duplicate_rate', analysis)
        self.assertIn('total_requests', analysis)
    
    def test_generate_optimization_plan(self):
        """测试生成优化计划"""
        # 添加导致需要优化的数据
        # 高响应时间
        for i in range(10):
            self.optimizer.add_performance_data(5.0, False, False, 1)  # 5秒响应时间
        
        # 高失败率
        for i in range(10):
            self.optimizer.add_performance_data(1.0, True, False, 0)  # 100%失败率
        
        # 高重复率
        for i in range(10):
            self.optimizer.add_performance_data(1.0, False, True, 1)  # 100%重复率
        
        plan = self.optimizer.generate_optimization_plan()
        
        self.assertIn('should_optimize', plan)
        self.assertTrue(plan['should_optimize'])
        self.assertIn('reasons', plan)
        self.assertIn('actions', plan)
        self.assertGreater(len(plan['actions']), 0)
    
    def test_apply_optimization_plan(self):
        """测试应用优化计划"""
        # 创建实际的优化计划
        plan = self.optimizer.generate_optimization_plan()
        
        # 如果不需要优化，添加一些数据使其需要优化
        if not plan.get('should_optimize', False):
            for i in range(10):
                self.optimizer.add_performance_data(5.0, False, False, 1)
            plan = self.optimizer.generate_optimization_plan()
        
        # 应用优化计划
        result = self.optimizer.apply_optimization_plan(plan)
        
        # 验证优化被应用
        self.assertTrue(result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前设置"""
        self.logger = EnhancedLogger(log_file="integration_test.log")
        self.validator = DataValidator()
        self.optimizer = AutoOptimizer(config_file="integration_optimizer_config.json")
        
        # 清理测试文件
        for file in ["integration_test.log", "integration_optimizer_config.json"]:
            if os.path.exists(file):
                os.remove(file)
    
    def tearDown(self):
        """测试后清理"""
        self.logger.close()
        self.optimizer.stop_monitoring()
        
        # 清理测试文件
        for file in ["integration_test.log", "integration_optimizer_config.json"]:
            if os.path.exists(file):
                os.remove(file)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        spider_name = "integration_test"
        
        # 1. 记录请求开始
        self.logger.log_request_start(spider_name, "http://example.com/movie/12345")
        
        # 2. 验证数据
        movie_data = {
            'vod_id': 12345,
            'title': '测试电影',
            'category': '电影'
        }
        
        is_valid, error_msg = self.validator.validate_movie_data(movie_data)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        
        # 3. 记录请求完成
        self.logger.log_request_complete(
            spider_name, "http://example.com/movie/12345", 200,
            ['title', 'category'], 12345, 1, 1500.0
        )
        
        # 4. 添加性能数据到优化器
        self.optimizer.add_performance_data(1.5, False, False, 1)
        
        # 5. 记录验证结果
        self.logger.log_validation(spider_name, True, 1)
        
        # 6. 分析性能
        analysis = self.optimizer.analyze_performance()
        self.assertGreater(analysis['total_requests'], 0)
        
        # 7. 生成优化计划
        plan = self.optimizer.generate_optimization_plan()
        self.assertIn('should_optimize', plan)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)