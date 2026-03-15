# -*- coding: utf-8 -*-
"""
utils/logger.py

Sets up the global logger for the application.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 使用一个模块级变量来防止重复初始化
_LOGGER_INITIALIZED = False

def setup_logger(config):
    """
    Configures the root logger based on the settings file.
    Includes safeguards against recursion and file locking issues.
    
    Args:
        config (dict): The logging configuration dictionary.
    """
    global _LOGGER_INITIALIZED
    
    # 1. 防止重复初始化 (Idempotency Check)
    # 如果已经初始化过,直接返回,避免反复关闭/打开文件句柄
    if _LOGGER_INITIALIZED:
        return
    
    log_config = config["logging"]
    log_file_path = Path(log_config["file"])
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(log_config["level"].upper())
    
    # Create formatter
    formatter = logging.Formatter(log_config["format"])
    
    # Clear existing handlers carefully
    # 只有在确实有 Handler 时才清理,且通常只在程序启动时清理一次
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 2. 优先添加 Console Handler
    # 这样即使文件写入失败,我们至少还能在控制台看到日志,避免完全静默失败
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 3. 安全地添加 File Handler
    try:
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=log_config["max_bytes"],
            backupCount=log_config["backup_count"],
            encoding='utf-8',
            delay=True  # <--- 关键优化：延迟打开文件
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    except (OSError, PermissionError) as e:
        # 4. 容错处理
        # 如果文件无法打开（权限或占用）,仅输出错误到控制台,不让程序崩溃,也不尝试记录日志（防止死循环）
        sys.stderr.write(f"ERROR: Could not create log file handler: {e}\n")
        sys.stderr.write("Logging will continue to console only.\n")
    
    # 标记为已初始化
    _LOGGER_INITIALIZED = True
    
    logger.info("Logger initialized successfully.")
