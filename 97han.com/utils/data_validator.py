#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据完整性校验器 - 支持重复ID检测、字段验证
"""

import sqlite3
import hashlib
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime

class DataValidator:
    """数据完整性校验器"""
    
    def __init__(self, db_path: str = 'spider.db'):
        self.db_path = db_path
        self.seen_ids: Set[int] = set()
        self.seen_hashes: Set[str] = set()
        self.validation_stats = {
            'total_checks': 0,
            'duplicates_found': 0,
            'validation_failures': 0
        }
    
    def validate_movie_data(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证电影数据完整性"""
        self.validation_stats['total_checks'] += 1
        
        # 检查必需字段
        required_fields = ['vod_id', 'title', 'category']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"缺少必需字段: {field}"
        
        # 检查ID重复
        vod_id = data['vod_id']
        if vod_id in self.seen_ids:
            self.validation_stats['duplicates_found'] += 1
            return False, f"重复ID: {vod_id}"
        
        # 生成数据哈希（用于内容去重）
        data_hash = self._generate_hash(data)
        if data_hash in self.seen_hashes:
            self.validation_stats['duplicates_found'] += 1
            return False, f"重复内容哈希: {data_hash[:16]}..."
        
        # 添加到已见集合
        self.seen_ids.add(vod_id)
        self.seen_hashes.add(data_hash)
        
        return True, None
    
    def validate_tv_data(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """验证电视剧数据完整性"""
        self.validation_stats['total_checks'] += 1
        
        # 检查必需字段
        required_fields = ['vod_id', 'title', 'category', 'episodes']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, f"缺少必需字段: {field}"
        
        # 检查剧集数据
        if not isinstance(data['episodes'], list):
            return False, "episodes 必须是列表"
        
        # 验证每集数据
        for i, episode in enumerate(data['episodes']):
            if not isinstance(episode, dict):
                return False, f"第{i+1}集数据格式错误"
            
            ep_required = ['episode_number', 'play_url']
            for field in ep_required:
                if field not in episode or not episode[field]:
                    return False, f"第{i+1}集缺少必需字段: {field}"
        
        # 检查ID重复
        vod_id = data['vod_id']
        if vod_id in self.seen_ids:
            self.validation_stats['duplicates_found'] += 1
            return False, f"重复ID: {vod_id}"
        
        # 生成数据哈希
        data_hash = self._generate_hash(data)
        if data_hash in self.seen_hashes:
            self.validation_stats['duplicates_found'] += 1
            return False, f"重复内容哈希: {data_hash[:16]}..."
        
        # 添加到已见集合
        self.seen_ids.add(vod_id)
        self.seen_hashes.add(data_hash)
        
        return True, None
    
    def _generate_hash(self, data: Dict[str, Any]) -> str:
        """生成数据哈希"""
        # 移除时间戳等动态字段
        clean_data = {k: v for k, v in data.items() 
                     if k not in ['created_at', 'updated_at', 'id']}
        
        # 排序并序列化
        sorted_str = json.dumps(clean_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(sorted_str.encode('utf-8')).hexdigest()
    
    def check_database_duplicates(self, table_name: str, id_field: str = 'vod_id') -> Dict[str, Any]:
        """检查数据库中的重复记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查找重复ID
                cursor.execute(f"""
                    SELECT {id_field}, COUNT(*) as cnt
                    FROM {table_name}
                    GROUP BY {id_field}
                    HAVING cnt > 1
                """)
                duplicates = cursor.fetchall()
                
                # 统计总数
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                total_count = cursor.fetchone()[0]
                
                # 查找唯一ID数
                cursor.execute(f"SELECT COUNT(DISTINCT {id_field}) FROM {table_name}")
                unique_count = cursor.fetchone()[0]
                
                return {
                    'table': table_name,
                    'total_records': total_count,
                    'unique_ids': unique_count,
                    'duplicate_ids': len(duplicates),
                    'duplicates': duplicates[:10]  # 只返回前10个
                }
        except Exception as e:
            return {
                'table': table_name,
                'error': str(e)
            }
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证统计摘要"""
        return {
            'total_checks': self.validation_stats['total_checks'],
            'duplicates_found': self.validation_stats['duplicates_found'],
            'validation_failures': self.validation_stats['validation_failures'],
            'unique_ids_cached': len(self.seen_ids),
            'unique_hashes_cached': len(self.seen_hashes)
        }
    
    def clear_cache(self):
        """清除验证缓存"""
        self.seen_ids.clear()
        self.seen_hashes.clear()
        self.validation_stats = {
            'total_checks': 0,
            'duplicates_found': 0,
            'validation_failures': 0
        }

# 布隆过滤器实现（简单版）
class SimpleBloomFilter:
    """简单布隆过滤器实现"""
    
    def __init__(self, size: int = 1000000, hash_count: int = 7):
        self.size = size
        self.hash_count = hash_count
        self.bit_array = [False] * size
    
    def _hashes(self, item: str) -> list[int]:
        """生成多个哈希值"""
        hashes = []
        hash_val = hash(item)
        for i in range(self.hash_count):
            hashes.append(abs((hash_val + i) % self.size))
        return hashes
    
    def add(self, item: str):
        """添加元素"""
        for hash_val in self._hashes(item):
            self.bit_array[hash_val] = True
    
    def __contains__(self, item: str) -> bool:
        """检查元素是否存在"""
        return all(self.bit_array[hash_val] for hash_val in self._hashes(item))