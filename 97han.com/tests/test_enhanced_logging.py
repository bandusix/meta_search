#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志系统单元测试
覆盖率≥90%
"""

import unittest
import tempfile
import os
import json
import time
import sqlite3
from datetime import datetime
from unittest.mock import patch, MagicMock

# 导入测试模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_logger import EnhancedLogger
from utils.data_validator import DataValidator, SimpleBloomFilter
from utils.auto_optimizer import AutoOptimizer

class TestEnhancedLogger(unittest.TestCase):
    """测试增强型日志器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'test_crawl_progress.log')
        self.logger = EnhancedLogger(log_file=self.log_file)
    
    def tearDown(self):
        """测试后清理"""
        self.logger.close()
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        os.rmdir(self.temp_dir)
    
    def test_log_initialization(self):
        """测试日志器初始化"""
        self.assertIsNotNone(self.logger)
        self.assertEqual(self.logger.log_file, self.log_file)
        self.assertTrue(os.path.exists(self.log_file))
    
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
            self.assertIn(request_url, args)
            self.assertIn("START", args)
    
    def test_log_request_complete(self):
        """测试请求完成记录"""
        spider_name = "test_spider"
        request_url = "http://example.com/test"
        response_status = 200
        saved_data_fields = ["title", "url", "year"]
        saved_id = 12345
        item_count = 1
        elapsed_ms = 1500.5
        
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
            self.assertIn(str(response_status), args)
            self.assertIn(str(saved_id), args)
            self.assertIn(str(item_count), args)
            self.assertIn(str(int(elapsed_ms)), args)
    
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
            self.assertIn(request_url, args)
            self.assertIn(error_type, args)
            self.assertIn(error_message, args)
    
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
            self.assertIn("VALIDATION", args)
            self.assertIn(str(total_records), args)
    
    def test_log_buffer_flush(self):
        """测试日志缓冲区刷新"""
        # 添加多条日志
        for i in range(15):  # 超过缓冲区大小
            self.logger.log_request_complete(
                "test_spider", f"http://example.com/{i}", 200,
                ["field1", "field2"], i, 1, 100.0
            )
        
        # 等待刷新
        time.sleep(2)
        
        # 验证日志文件内容
        with open(self.log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("test_spider", content)
            self.assertIn("http://example.com", content)
    
    def test_get_stats(self):
        """测试获取统计信息"""
        # 添加一些测试数据
        self.logger.add_performance_data(1.5, False, False, 1)
        self.logger.add_performance_data(2.0, True, False, 0)
        self.logger.add_performance_data(1.0, False, True, 1)
        
        stats = self.logger.get_stats()
        
        self.assertIn('total_requests', stats)
        self.assertIn('failed_requests', stats)
        self.assertIn('duplicate_ids', stats)
        self.assertIn('avg_response_time', stats)
        self.assertGreater(stats['total_requests'], 0)
    
    def test_get_config(self):
        """测试获取配置"""
        config = self.logger.get_config()
        
        self.assertIn('concurrency', config)
        self.assertIn('retry_enabled', config)
        self.assertIn('bloom_filter_enabled', config)
        self.assertIn('response_time_threshold', config)
        self.assertIn('failure_threshold', config)
    
    def test_parse_log_line(self):
        """测试日志行解析"""
        # 创建测试日志行
        test_line = "2024-01-15 14:30:45.123|test_spider|http://example.com|200|[\"title\",\"url\"]|12345|1|1500"
        
        parsed = self.logger.parse_log_line(test_line)
        
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['timestamp'], "2024-01-15 14:30:45.123")
        self.assertEqual(parsed['spider_name'], "test_spider")
        self.assertEqual(parsed['request_url'], "http://example.com")
        self.assertEqual(parsed['response_status'], 200)
        self.assertEqual(parsed['saved_id'], 12345)
        self.assertEqual(parsed['item_count'], 1)
        self.assertEqual(parsed['elapsed_ms'], 1500)


class TestDataValidator(unittest.TestCase):
    """测试数据验证器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_spider.db')
        self.validator = DataValidator(db_path=self.db_path)
        
        # 创建测试数据库
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY,
                    vod_id INTEGER UNIQUE,
                    title TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tv_series (
                    id INTEGER PRIMARY KEY,
                    vod_id INTEGER UNIQUE,
                    title TEXT
                )
            """)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)
    
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
    
    def test_validate_movie_data_missing_field(self):
        """测试缺少字段的电影数据验证"""
        movie_data = {
            'title': '测试电影',
            'category': '电影'
            # 缺少 vod_id
        }
        
        is_valid, error_msg = self.validator.validate_movie_data(movie_data)
        
        self.assertFalse(is_valid)
        self.assertIn("缺少必需字段", error_msg)
        self.assertIn("vod_id", error_msg)
    
    def test_validate_movie_data_empty_field(self):
        """测试空字段的电影数据验证"""
        movie_data = {
            'vod_id': '',  # 空字段
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
            'episodes': [{'episode_number': 1, 'title': '第1集'}]
        }
        
        is_valid, error_msg = self.validator.validate_tv_data(tv_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
    
    def test_check_duplicate_id(self):
        """测试重复ID检查"""
        # 添加一个ID到已见集合
        self.validator.seen_ids.add(12345)
        
        movie_data = {
            'vod_id': 12345,
            'title': '重复电影',
            'category': '电影'
        }
        
        is_valid, error_msg = self.validator.validate_movie_data(movie_data)
        
        self.assertFalse(is_valid)
        self.assertIn("重复ID", error_msg)
        self.assertIn("12345", error_msg)
    
    def test_check_database_duplicates(self):
        """测试数据库重复检查"""
        # 插入测试数据
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO movies (vod_id, title) VALUES (?, ?)", (11111, "测试电影1"))
            conn.execute("INSERT INTO movies (vod_id, title) VALUES (?, ?)", (22222, "测试电影2"))
            conn.execute("INSERT INTO tv_series (vod_id, title) VALUES (?, ?)", (33333, "测试电视剧"))
        
        # 检查重复
        movie_result = self.validator.check_database_duplicates('movies', 'vod_id')
        tv_result = self.validator.check_database_duplicates('tv_series', 'vod_id')
        
        self.assertEqual(movie_result['total_records'], 2)
        self.assertEqual(movie_result['duplicate_ids'], 0)
        self.assertEqual(tv_result['total_records'], 1)
        self.assertEqual(tv_result['duplicate_ids'], 0)
    
    def test_get_validation_summary(self):
        """测试获取验证统计"""
        # 添加一些测试数据
        self.validator.validation_stats['total_checks'] = 10
        self.validator.validation_stats['failed_checks'] = 2
        self.validator.validation_stats['duplicates_found'] = 1
        
        summary = self.validator.get_validation_summary()
        
        self.assertEqual(summary['total_checks'], 10)
        self.assertEqual(summary['failed_checks'], 2)
        self.assertEqual(summary['duplicates_found'], 1)
        self.assertEqual(summary['success_rate'], 80.0)


class TestSimpleBloomFilter(unittest.TestCase):
    """测试简单布隆过滤器"""
    
    def setUp(self):
        """测试前准备"""
        self.filter = SimpleBloomFilter(size=1000, hash_count=3)
    
    def test_add_and_contains(self):
        """测试添加和包含检查"""
        test_id = "test_12345"
        
        # 添加前不应包含
        self.assertFalse(self.filter.contains(test_id))
        
        # 添加后应包含
        self.filter.add(test_id)
        self.assertTrue(self.filter.contains(test_id))
    
    def test_false_positive_rate(self):
        """测试误报率"""
        # 添加100个ID
        test_ids = [f"test_{i}" for i in range(100)]
        for test_id in test_ids:
            self.filter.add(test_id)
        
        # 检查已添加的ID
        for test_id in test_ids:
            self.assertTrue(self.filter.contains(test_id))
        
        # 检查未添加的ID（可能产生误报）
        false_positives = 0
        test_count = 1000
        for i in range(test_count):
            test_id = f"nonexistent_{i}"
            if self.filter.contains(test_id):
                false_positives += 1
        
        # 误报率应较低（通常<5%）
        false_positive_rate = false_positives / test_count
        self.assertLess(false_positive_rate, 0.1)  # 误报率<10%
    
    def test_clear(self):
        """测试清空过滤器"""
        test_id = "test_12345"
        self.filter.add(test_id)
        self.assertTrue(self.filter.contains(test_id))
        
        self.filter.clear()
        self.assertFalse(self.filter.contains(test_id))


class TestAutoOptimizer(unittest.TestCase):
    """测试自动优化器"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, 'test_optimizer_config.json')
        self.optimizer = AutoOptimizer(config_file=self.config_file)
    
    def tearDown(self):
        """测试后清理"""
        self.optimizer.stop_monitoring()
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        os.rmdir(self.temp_dir)
    
    def test_initialization(self):
        """测试优化器初始化"""
        self.assertIsNotNone(self.optimizer)
        self.assertEqual(self.optimizer.config_file, self.config_file)
        self.assertIn('concurrency', self.optimizer.config)
        self.assertIn('retry_enabled', self.optimizer.config)
    
    def test_load_config(self):
        """测试配置加载"""
        # 创建测试配置文件
        test_config = {
            'concurrency': 5,
            'retry_enabled': True,
            'bloom_filter_enabled': False,
            'response_time_threshold': 3.0,
            'failure_threshold': 0.1
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(test_config, f, ensure_ascii=False, indent=2)
        
        # 重新初始化以加载配置
        optimizer = AutoOptimizer(config_file=self.config_file)
        
        self.assertEqual(optimizer.config['concurrency'], 5)
        self.assertTrue(optimizer.config['retry_enabled'])
        self.assertFalse(optimizer.config['bloom_filter_enabled'])
    
    def test_save_config(self):
        """测试配置保存"""
        # 修改配置
        self.optimizer.config['concurrency'] = 8
        self.optimizer.config['retry_enabled'] = False
        
        # 保存配置
        self.optimizer._save_config()
        
        # 验证文件存在且内容正确
        self.assertTrue(os.path.exists(self.config_file))
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config['concurrency'], 8)
        self.assertFalse(saved_config['retry_enabled'])
    
    def test_add_performance_data(self):
        """测试添加性能数据"""
        # 添加正常数据
        self.optimizer.add_performance_data(1.5, False, False, 1)
        self.optimizer.add_performance_data(2.0, True, False, 0)
        self.optimizer.add_performance_data(0.8, False, True, 1)
        
        self.assertEqual(len(self.optimizer.stats['response_times']), 3)
        self.assertEqual(self.optimizer.stats['failed_requests'], 1)
        self.assertEqual(self.optimizer.stats['duplicate_ids'], 1)
        self.assertEqual(self.optimizer.stats['total_requests'], 3)
    
    def test_analyze_performance(self):
        """测试性能分析"""
        # 添加测试数据
        for i in range(10):
            response_time = 1.0 + (i * 0.2)  # 递增的响应时间
            is_error = i % 3 == 0  # 每3个请求有一个错误
            is_duplicate = i % 5 == 0  # 每5个请求有一个重复
            self.optimizer.add_performance_data(response_time, is_error, is_duplicate, 1)
        
        analysis = self.optimizer.analyze_performance()
        
        self.assertIn('avg_response_time', analysis)
        self.assertIn('failure_rate', analysis)
        self.assertIn('duplicate_rate', analysis)
        self.assertIn('total_requests', analysis)
        
        self.assertGreater(analysis['avg_response_time'], 0)
        self.assertGreaterEqual(analysis['failure_rate'], 0)
        self.assertGreaterEqual(analysis['duplicate_rate'], 0)
    
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
        
        self.assertIn('adjust_concurrency', plan)
        self.assertIn('enable_retry', plan)
        self.assertIn('enable_bloom_filter', plan)
        
        # 应该触发优化
        self.assertTrue(plan['adjust_concurrency'])
        self.assertTrue(plan['enable_retry'])
        self.assertTrue(plan['enable_bloom_filter'])
    
    def test_apply_optimization_plan(self):
        """测试应用优化计划"""
        plan = {
            'adjust_concurrency': True,
            'enable_retry': True,
            'enable_bloom_filter': False,
            'new_concurrency': 3
        }
        
        old_concurrency = self.optimizer.config['concurrency']
        old_retry = self.optimizer.config['retry_enabled']
        
        self.optimizer.apply_optimization_plan(plan)
        
        self.assertEqual(self.optimizer.config['concurrency'], 3)
        self.assertTrue(self.optimizer.config['retry_enabled'])
        self.assertFalse(self.optimizer.config['bloom_filter_enabled'])
    
    def test_callback_registration(self):
        """测试回调函数注册"""
        callback_called = False
        callback_data = None
        
        def test_callback(data):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = data
        
        self.optimizer.register_callback('optimization_applied', test_callback)
        
        # 触发优化
        plan = {'adjust_concurrency': True, 'new_concurrency': 2}
        self.optimizer.apply_optimization_plan(plan)
        
        # 验证回调被调用
        self.assertTrue(callback_called)
        self.assertIsNotNone(callback_data)
    
    def test_monitoring_start_stop(self):
        """测试监控启动和停止"""
        # 启动监控
        self.optimizer.start_monitoring()
        self.assertTrue(self.optimizer.monitoring)
        
        # 等待一段时间让监控运行
        time.sleep(1)
        
        # 停止监控
        self.optimizer.stop_monitoring()
        self.assertFalse(self.optimizer.monitoring)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test_integration.db')
        self.log_file = os.path.join(self.temp_dir, 'test_integration.log')
        self.config_file = os.path.join(self.temp_dir, 'test_integration_config.json')
        
        # 创建测试数据库
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS movies (
                    id INTEGER PRIMARY KEY,
                    vod_id INTEGER UNIQUE,
                    title TEXT
                )
            """)
        
        # 初始化组件
        self.logger = EnhancedLogger(log_file=self.log_file)
        self.validator = DataValidator(db_path=self.db_path)
        self.optimizer = AutoOptimizer(config_file=self.config_file)
    
    def tearDown(self):
        """测试后清理"""
        self.logger.close()
        self.optimizer.stop_monitoring()
        
        # 清理临时文件
        for file_path in [self.db_path, self.log_file, self.config_file]:
            if os.path.exists(file_path):
                os.remove(file_path)
        os.rmdir(self.temp_dir)
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        spider_name = "integration_test"
        
        # 1. 记录请求开始
        self.logger.log_request_start(spider_name, "http://example.com/movie/12345")
        
        # 2. 验证数据
        movie_data = {
            'vod_id': 12345,
            'title': '测试电影',
            'category': '电影',
            'year': 2023
        }
        
        is_valid, error_msg = self.validator.validate_movie_data(movie_data)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)
        
        # 3. 记录请求完成
        self.logger.log_request_complete(
            spider_name, "http://example.com/movie/12345", 200,
            ['title', 'year', 'category'], 12345, 1, 1500.0
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
        self.assertIn('adjust_concurrency', plan)
        
        # 8. 应用优化
        if plan['adjust_concurrency']:
            self.optimizer.apply_optimization_plan(plan)
        
        # 9. 获取统计信息
        stats = self.logger.get_stats()
        self.assertIn('total_requests', stats)
        
        # 10. 验证日志文件
        time.sleep(2)  # 等待日志刷新
        with open(self.log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
            self.assertIn(spider_name, log_content)
            self.assertIn("http://example.com/movie/12345", log_content)


if __name__ == '__main__':
    # 运行所有测试
    unittest.main(verbosity=2)