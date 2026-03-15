#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
管理爬虫系统的配置文件
"""

import os
import configparser
import argparse
import sys


class ConfigManager:
    """配置管理类"""
    
    DEFAULT_CONFIG = {
        'Database': {
            'database_path': 'cuevana3.db',
        },
        'Export': {
            'export_directory': '.',
            'movies_filename': 'movies.csv',
            'tv_series_filename': 'tv_series.csv',
        },
        'Scraper': {
            'delay_min': '1.0',
            'delay_max': '3.0',
            'max_retries': '3',
        }
    }
    
    def __init__(self, config_file='config.ini'):
        """
        初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        
        # 如果配置文件不存在，创建默认配置
        if not os.path.exists(config_file):
            self.create_default_config()
        else:
            self.load_config()
    
    def create_default_config(self):
        """创建默认配置文件"""
        for section, options in self.DEFAULT_CONFIG.items():
            self.config[section] = options
        
        self.save_config()
    
    def load_config(self):
        """加载配置文件"""
        self.config.read(self.config_file, encoding='utf-8')
        
        # 确保所有必需的section和option都存在
        for section, options in self.DEFAULT_CONFIG.items():
            if not self.config.has_section(section):
                self.config[section] = {}
            
            for option, default_value in options.items():
                if not self.config.has_option(section, option):
                    self.config[section][option] = default_value
        
        self.save_config()
    
    def save_config(self):
        """保存配置文件"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            self.config.write(f)
    
    def get(self, section, option):
        """
        获取配置值
        
        Args:
            section: 配置节
            option: 配置项
            
        Returns:
            配置值
        """
        return self.config.get(section, option)
    
    def set(self, section, option, value):
        """
        设置配置值
        
        Args:
            section: 配置节
            option: 配置项
            value: 配置值
        """
        if not self.config.has_section(section):
            self.config[section] = {}
        
        self.config[section][option] = str(value)
        self.save_config()
    
    def get_database_path(self):
        """获取数据库路径"""
        return self.get('Database', 'database_path')
    
    def set_database_path(self, path):
        """设置数据库路径"""
        self.set('Database', 'database_path', path)
    
    def get_export_directory(self):
        """获取导出目录"""
        return self.get('Export', 'export_directory')
    
    def set_export_directory(self, directory):
        """设置导出目录"""
        # 确保目录存在
        if not os.path.exists(directory):
            os.makedirs(directory)
        self.set('Export', 'export_directory', directory)
    
    def get_export_path(self, file_type='movies'):
        """
        获取导出文件的完整路径
        
        Args:
            file_type: 文件类型 ('movies' 或 'tv_series')
            
        Returns:
            完整的导出文件路径
        """
        directory = self.get_export_directory()
        
        if file_type == 'movies':
            filename = self.get('Export', 'movies_filename')
        elif file_type == 'tv_series':
            filename = self.get('Export', 'tv_series_filename')
        else:
            filename = f'{file_type}.csv'
        
        return os.path.join(directory, filename)
    
    def get_delay_range(self):
        """获取延迟时间范围"""
        delay_min = float(self.get('Scraper', 'delay_min'))
        delay_max = float(self.get('Scraper', 'delay_max'))
        return (delay_min, delay_max)
    
    def set_delay_range(self, delay_min, delay_max):
        """设置延迟时间范围"""
        self.set('Scraper', 'delay_min', str(delay_min))
        self.set('Scraper', 'delay_max', str(delay_max))
    
    def get_max_retries(self):
        """获取最大重试次数"""
        return int(self.get('Scraper', 'max_retries'))
    
    def reset_to_default(self):
        """重置为默认配置"""
        self.config.clear()
        self.create_default_config()
    
    def show_config(self, brief=False):
        """
        显示当前配置
        
        Args:
            brief: 是否显示简要信息
        """
        if brief:
            # 简要显示
            db_path = self.get_database_path()
            export_dir = self.get_export_directory()
            delay_min, delay_max = self.get_delay_range()
            
            print(f"  数据库: {db_path}")
            print(f"  导出目录: {export_dir}")
            print(f"  延迟时间: {delay_min}-{delay_max}秒")
        else:
            # 详细显示
            print("【数据库配置】")
            print(f"  数据库路径: {self.get_database_path()}")
            print()
            
            print("【导出配置】")
            print(f"  导出目录: {self.get_export_directory()}")
            print(f"  电影文件名: {self.get('Export', 'movies_filename')}")
            print(f"  电视剧文件名: {self.get('Export', 'tv_series_filename')}")
            print()
            
            print("【爬虫配置】")
            delay_min, delay_max = self.get_delay_range()
            print(f"  延迟时间: {delay_min}-{delay_max}秒")
            print(f"  最大重试次数: {self.get_max_retries()}")


def main():
    parser = argparse.ArgumentParser(description='配置管理工具')
    
    parser.add_argument('--show', action='store_true',
                        help='显示当前配置')
    parser.add_argument('--show-brief', action='store_true',
                        help='显示简要配置信息')
    parser.add_argument('--get', metavar='KEY',
                        help='获取配置值（格式: section.option 或 option）')
    parser.add_argument('--set', nargs=2, metavar=('KEY', 'VALUE'),
                        help='设置配置值（格式: section.option value）')
    parser.add_argument('--reset', action='store_true',
                        help='重置为默认配置')
    parser.add_argument('--config-file', default='config.ini',
                        help='配置文件路径')
    
    args = parser.parse_args()
    
    config = ConfigManager(args.config_file)
    
    if args.show:
        config.show_config(brief=False)
    
    elif args.show_brief:
        config.show_config(brief=True)
    
    elif args.get:
        key = args.get
        
        # 支持简写（直接使用 option 名称）
        key_mapping = {
            'database_path': ('Database', 'database_path'),
            'export_directory': ('Export', 'export_directory'),
            'delay_min': ('Scraper', 'delay_min'),
            'delay_max': ('Scraper', 'delay_max'),
        }
        
        if key in key_mapping:
            section, option = key_mapping[key]
        elif '.' in key:
            section, option = key.split('.', 1)
        else:
            print(f"错误: 无效的配置键: {key}")
            sys.exit(1)
        
        try:
            value = config.get(section, option)
            print(value)
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)
    
    elif args.set:
        key, value = args.set
        
        # 支持简写
        key_mapping = {
            'database_path': ('Database', 'database_path'),
            'export_directory': ('Export', 'export_directory'),
            'delay_min': ('Scraper', 'delay_min'),
            'delay_max': ('Scraper', 'delay_max'),
        }
        
        if key in key_mapping:
            section, option = key_mapping[key]
        elif '.' in key:
            section, option = key.split('.', 1)
        else:
            print(f"错误: 无效的配置键: {key}")
            sys.exit(1)
        
        try:
            config.set(section, option, value)
            print(f"✅ 配置已更新: {section}.{option} = {value}")
        except Exception as e:
            print(f"错误: {e}")
            sys.exit(1)
    
    elif args.reset:
        config.reset_to_default()
        print("✅ 配置已重置为默认值")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
