#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版日志系统集成测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.enhanced_logger import logger as enhanced_logger
from utils.data_validator import DataValidator
from utils.auto_optimizer import AutoOptimizer
import time
import random

def test_enhanced_logging():
    """测试增强版日志系统"""
    print("🚀 开始测试增强版日志系统...")
    
    # 初始化组件
    validator = DataValidator()
    optimizer = AutoOptimizer()
    optimizer.start_monitoring()
    
    print("✅ 组件初始化完成")
    
    # 模拟爬虫操作
    spider_name = "test_spider"
    test_urls = [
        "http://www.97han.com/type/1.html",
        "http://www.97han.com/show/1-123-----------.html",
        "http://www.97han.com/vod/12345.html",
        "http://www.97han.com/vod/67890.html"
    ]
    
    print(f"📝 模拟爬取 {len(test_urls)} 个页面...")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n📄 处理第 {i}/{len(test_urls)} 个页面: {url}")
        
        # 记录请求开始
        enhanced_logger.log_request_start(spider_name, url)
        
        # 模拟网络延迟
        delay = random.uniform(0.5, 2.0)
        time.sleep(delay)
        
        # 模拟响应状态
        response_status = random.choice([200, 200, 200, 404, 500])  # 75%成功率
        elapsed_ms = delay * 1000
        
        if response_status == 200:
            # 模拟成功保存数据
            saved_id = random.randint(10000, 99999)
            saved_fields = ["title", "year", "category", "play_line_name", "player_page_url"]
            item_count = random.randint(1, 5)
            
            enhanced_logger.log_request_complete(
                spider_name, url, response_status,
                saved_fields, saved_id, item_count, elapsed_ms
            )
            
            # 添加性能数据
            optimizer.add_performance_data(delay, False, False, item_count)
            
            print(f"✅ 成功保存: ID={saved_id}, 字段={len(saved_fields)}, 耗时={elapsed_ms:.0f}ms")
            
        else:
            # 模拟错误
            error_type = "HTTPError" if response_status == 404 else "ServerError"
            error_message = f"HTTP {response_status}"
            
            enhanced_logger.log_error(spider_name, url, error_type, error_message)
            optimizer.add_performance_data(delay, True, False, 0)
            
            print(f"❌ 请求失败: {error_type} - {error_message}")
        
        # 每2个请求进行一次数据验证
        if i % 2 == 0:
            total_records = i * random.randint(10, 20)
            enhanced_logger.log_validation(spider_name, True, total_records)
            print(f"🔍 数据验证: 总计 {total_records} 条记录")
    
    print("\n📊 生成最终统计...")
    
    # 获取统计信息
    stats = enhanced_logger.get_stats()
    print(f"📈 爬取统计:")
    print(f"   总请求: {stats['total_requests']}")
    print(f"   失败请求: {stats['failed_requests']}")
    print(f"   重复ID: {stats['duplicate_ids']}")
    print(f"   平均响应时间: {stats['avg_response_time']:.2f}s")
    
    # 获取优化配置
    config = enhanced_logger.get_config()
    print(f"\n⚙️  当前优化配置:")
    print(f"   并发数: {config['concurrency']}")
    print(f"   重试启用: {config['retry_enabled']}")
    print(f"   布隆过滤器: {config['bloom_filter_enabled']}")
    
    # 分析性能
    analysis = optimizer.analyze_performance()
    print(f"\n📋 性能分析:")
    if 'avg_response_time' in analysis:
        print(f"   平均响应时间: {analysis['avg_response_time']:.2f}s")
    if 'error_rate' in analysis:
        print(f"   失败率: {analysis['error_rate']:.1%}")
    if 'duplicate_rate' in analysis:
        print(f"   重复率: {analysis['duplicate_rate']:.1%}")
    if 'total_requests' in analysis:
        print(f"   总请求数: {analysis['total_requests']}")
    if 'status' in analysis:
        print(f"   状态: {analysis['status']}")
    
    # 生成优化建议
    plan = optimizer.generate_optimization_plan()
    print(f"\n🔧 优化建议:")
    if plan.get('should_optimize', False):
        print(f"   需要优化: 是")
        if 'actions' in plan:
            for action in plan['actions']:
                print(f"   {action['type']}: {action['reason']}")
    else:
        print(f"   需要优化: 否")
    
    # 停止监控
    optimizer.stop_monitoring()
    enhanced_logger.close()
    
    print("\n✅ 测试完成!")
    print(f"📁 日志文件: {enhanced_logger.log_file}")
    print(f"📁 配置文件: {optimizer.config_file}")

def test_log_parsing():
    """测试日志解析"""
    print("\n🔍 测试日志解析功能...")
    
    # 创建测试日志行
    test_logs = [
        "2024-01-15 14:30:45.123|movie|http://www.97han.com/type/1.html|200|[\"title\",\"year\"]|12345|1|1500",
        "2024-01-15 14:30:46.823|movie|http://www.97han.com/vod/67890.html|404|[]|None|0|800",
        "2024-01-15 14:30:47.623|tv|http://www.97han.com/type/2-123.html|200|[\"title\",\"episodes\"]|54321|25|1200"
    ]
    
    print("📋 解析测试日志:")
    for log_line in test_logs:
        parsed = enhanced_logger.parse_log_line(log_line)
        if parsed:
            print(f"\n📝 原始日志: {log_line}")
            print(f"   时间戳: {parsed['timestamp']}")
            print(f"   爬虫: {parsed['spider_name']}")
            print(f"   URL: {parsed['request_url']}")
            print(f"   状态: {parsed['response_status']}")
            print(f"   保存ID: {parsed['saved_id']}")
            print(f"   项目数: {parsed['item_count']}")
            print(f"   耗时: {parsed['elapsed_ms']}ms")
        else:
            print(f"❌ 解析失败: {log_line}")

def main():
    """主函数"""
    print("🎯 增强版日志系统测试")
    print("=" * 60)
    
    try:
        # 测试增强版日志系统
        test_enhanced_logging()
        
        # 测试日志解析
        test_log_parsing()
        
        print("\n🎉 所有测试完成!")
        print("\n📚 使用说明:")
        print("   1. 查看生成的日志文件: crawl_progress.log")
        print("   2. 使用Pandas分析日志数据")
        print("   3. 运行单元测试: python -m pytest tests/test_enhanced_logging.py")
        print("   4. 查看README_ENHANCED.md获取详细文档")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()