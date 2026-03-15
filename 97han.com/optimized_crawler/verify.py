#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证脚本 - 校验爬取结果的有效性
"""

import asyncio
import aiohttp
import sqlite3
import random
import logging
import re
from typing import List, Dict, Tuple
from urllib.parse import urlparse
import json
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/verify.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class DataVerifier:
    """数据验证器"""
    
    def __init__(self, db_path: str = "optimized_crawler.db", sample_rate: float = 0.01):
        self.db_path = db_path
        self.sample_rate = sample_rate  # 1% 抽样率
        self.timeout = 10  # 请求超时时间
        self.session = None
        
        # 验证关键词
        self.valid_keywords = [
            'video', 'player', 'play', '播放', '视频',
            'm3u8', 'mp4', 'flv', 'avi', 'rmvb',
            'iframe', 'embed', 'object', 'videojs'
        ]
        
        # 无效关键词
        self.invalid_keywords = [
            '404', 'not found', 'error', '错误',
            'maintenance', '维护', 'forbidden', '禁止'
        ]
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def get_sample_data(self, category: str = None) -> List[Dict]:
        """从数据库获取抽样数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 构建查询SQL
            if category:
                # 按分类抽样
                cursor.execute("""
                    SELECT * FROM movies 
                    WHERE category = ? 
                    ORDER BY RANDOM() 
                    LIMIT (SELECT COUNT(*) * ? FROM movies WHERE category = ?)
                """, (category, self.sample_rate, category))
            else:
                # 全局抽样
                cursor.execute("""
                    SELECT * FROM movies 
                    ORDER BY RANDOM() 
                    LIMIT (SELECT COUNT(*) * ? FROM movies)
                """, (self.sample_rate,))
            
            rows = cursor.fetchall()
            
            # 转换为字典列表
            sample_data = []
            for row in rows:
                sample_data.append(dict(row))
            
            conn.close()
            
            logger.info(f"📊 获取抽样数据: {len(sample_data)} 条记录")
            return sample_data
            
        except Exception as e:
            logger.error(f"❌ 获取抽样数据失败: {str(e)}")
            return []
    
    async def verify_play_url(self, play_url: str, title: str = "") -> Dict:
        """验证播放URL的有效性"""
        try:
            # 发送HEAD请求检查URL状态
            async with self.session.head(play_url, allow_redirects=True) as response:
                status_code = response.status
                final_url = str(response.url)
                
                if status_code != 200:
                    return {
                        'url': play_url,
                        'status_code': status_code,
                        'valid': False,
                        'reason': f'HTTP状态码: {status_code}',
                        'final_url': final_url
                    }
            
            # 发送GET请求获取内容
            async with self.session.get(play_url) as response:
                if response.status != 200:
                    return {
                        'url': play_url,
                        'status_code': response.status,
                        'valid': False,
                        'reason': f'HTTP状态码: {response.status}',
                        'final_url': str(response.url)
                    }
                
                content = await response.text()
                content_lower = content.lower()
                
                # 检查无效关键词
                for keyword in self.invalid_keywords:
                    if keyword.lower() in content_lower:
                        return {
                            'url': play_url,
                            'status_code': 200,
                            'valid': False,
                            'reason': f'包含无效关键词: {keyword}',
                            'final_url': str(response.url)
                        }
                
                # 检查有效关键词
                valid_keyword_found = False
                for keyword in self.valid_keywords:
                    if keyword.lower() in content_lower:
                        valid_keyword_found = True
                        break
                
                # 检查视频相关标签
                video_tags_found = any([
                    '<video' in content_lower,
                    '<iframe' in content_lower,
                    '<embed' in content_lower,
                    'videojs' in content_lower,
                    'jwplayer' in content_lower,
                    'dplayer' in content_lower
                ])
                
                # 检查视频文件扩展名
                video_extensions = ['.m3u8', '.mp4', '.flv', '.avi', '.rmvb']
                has_video_extension = any(ext in final_url.lower() for ext in video_extensions)
                
                # 综合判断
                is_valid = (valid_keyword_found or video_tags_found or has_video_extension)
                
                return {
                    'url': play_url,
                    'status_code': 200,
                    'valid': is_valid,
                    'reason': '通过综合验证' if is_valid else '未找到视频相关内容',
                    'final_url': final_url,
                    'content_length': len(content),
                    'has_video_tags': video_tags_found,
                    'has_video_extension': has_video_extension
                }
                
        except asyncio.TimeoutError:
            return {
                'url': play_url,
                'status_code': None,
                'valid': False,
                'reason': '请求超时',
                'final_url': play_url
            }
        except Exception as e:
            logger.warning(f"⚠️ 验证URL失败: {play_url} - {str(e)}")
            return {
                'url': play_url,
                'status_code': None,
                'valid': False,
                'reason': f'异常: {str(e)}',
                'final_url': play_url
            }
    
    async def verify_batch(self, sample_data: List[Dict]) -> Dict:
        """批量验证数据"""
        verification_results = {
            'total': len(sample_data),
            'valid': 0,
            'invalid': 0,
            'timeout': 0,
            'error': 0,
            'details': [],
            'start_time': datetime.now(),
            'end_time': None
        }
        
        # 创建验证任务
        tasks = []
        for item in sample_data:
            task = self.verify_play_url(
                item['play_url'], 
                item.get('title', '')
            )
            tasks.append(task)
        
        # 并发执行验证
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        for item, result in zip(sample_data, results):
            if isinstance(result, Exception):
                verification_results['error'] += 1
                detail = {
                    'title': item.get('title', ''),
                    'category': item.get('category', ''),
                    'play_url': item['play_url'],
                    'valid': False,
                    'reason': f'验证异常: {str(result)}'
                }
            else:
                if result['valid']:
                    verification_results['valid'] += 1
                else:
                    verification_results['invalid'] += 1
                
                if result['status_code'] is None:
                    verification_results['timeout'] += 1
                
                detail = {
                    'title': item.get('title', ''),
                    'category': item.get('category', ''),
                    'play_url': item['play_url'],
                    'valid': result['valid'],
                    'reason': result['reason'],
                    'status_code': result['status_code'],
                    'final_url': result['final_url']
                }
            
            verification_results['details'].append(detail)
        
        verification_results['end_time'] = datetime.now()
        return verification_results
    
    def generate_report(self, results: Dict) -> str:
        """生成验证报告"""
        duration = (results['end_time'] - results['start_time']).total_seconds()
        
        report = f"""
📊 数据验证报告
==================

📈 统计概览:
- 总抽样数: {results['total']}
- 有效链接: {results['valid']} ({results['valid']/max(results['total'],1)*100:.1f}%)
- 无效链接: {results['invalid']} ({results['invalid']/max(results['total'],1)*100:.1f}%)
- 超时链接: {results['timeout']}
- 错误链接: {results['error']}

⏱️ 验证耗时: {duration:.1f} 秒

📋 详细结果:
"""
        
        # 按分类统计
        category_stats = {}
        for detail in results['details']:
            category = detail['category']
            if category not in category_stats:
                category_stats[category] = {'total': 0, 'valid': 0}
            category_stats[category]['total'] += 1
            if detail['valid']:
                category_stats[category]['valid'] += 1
        
        report += "\n分类统计:\n"
        for category, stats in category_stats.items():
            valid_rate = stats['valid'] / max(stats['total'], 1) * 100
            report += f"- {category}: {stats['valid']}/{stats['total']} ({valid_rate:.1f}%)\n"
        
        # 无效链接详情
        invalid_details = [d for d in results['details'] if not d['valid']]
        if invalid_details:
            report += f"\n❌ 无效链接详情 (前10个):\n"
            for detail in invalid_details[:10]:
                report += f"- {detail['title']} ({detail['category']})\n"
                report += f"  URL: {detail['play_url']}\n"
                report += f"  原因: {detail['reason']}\n\n"
        
        # 结论
        valid_rate = results['valid'] / max(results['total'], 1) * 100
        if valid_rate >= 98:
            report += f"\n✅ 验证通过! 有效率达到 {valid_rate:.1f}% (要求≥98%)\n"
        else:
            report += f"\n❌ 验证失败! 有效率仅 {valid_rate:.1f}% (要求≥98%)\n"
        
        return report

async def main():
    """主函数"""
    print("🔍 开始数据验证...")
    
    async with DataVerifier(sample_rate=0.01) as verifier:
        # 获取抽样数据
        sample_data = verifier.get_sample_data()
        
        if not sample_data:
            print("❌ 没有获取到抽样数据")
            return
        
        print(f"📊 获取到 {len(sample_data)} 条抽样数据")
        
        # 执行验证
        results = await verifier.verify_batch(sample_data)
        
        # 生成报告
        report = verifier.generate_report(results)
        print(report)
        
        # 保存报告到文件
        with open('logs/verification_report.txt', 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("📄 验证报告已保存到 logs/verification_report.txt")

if __name__ == "__main__":
    asyncio.run(main())