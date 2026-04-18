"""
日志系统模块
提供统一的日志配置和管理
"""

import os
import sys
import logging
import logging.handlers
from typing import Optional, Dict, Any
from pathlib import Path

from .config import get_config

# 默认日志配置
DEFAULT_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": "logs/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["console", "file", "error_file"],
            "level": "INFO",
            "propagate": True
        },
        "deutsch_lernen": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 全局日志配置
_logging_configured = False

def setup_logger(name: Optional[str] = None, log_level: str = "INFO", log_file: Optional[str] = None) -> logging.Logger:
    """
    设置并返回日志记录器
    
    Args:
        name: 日志记录器名称，如为None则返回根日志记录器
        log_level: 日志级别
        log_file: 日志文件路径，如为None则使用配置中的路径
        
    Returns:
        配置好的日志记录器
    """
    global _logging_configured
    
    # 获取配置
    config = get_config()
    
    # 确保日志目录存在
    log_dir = config.get("paths.logs_dir", "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 如果未指定日志文件，使用配置中的路径
    if log_file is None:
        log_file = os.path.join(log_dir, "app.log")
    
    # 获取日志级别
    level = LOG_LEVELS.get(log_level.upper(), logging.INFO)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复配置
    if _logging_configured:
        return logger
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"警告: 无法创建日志文件处理器: {e}")
    
    # 错误日志文件处理器
    try:
        error_log_file = os.path.join(log_dir, "error.log")
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
    except Exception as e:
        print(f"警告: 无法创建错误日志文件处理器: {e}")
    
    # 防止日志传播到根日志记录器
    logger.propagate = False
    
    _logging_configured = True
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器
    """
    return logging.getLogger(name)

def set_log_level(level: str):
    """
    设置全局日志级别
    
    Args:
        level: 日志级别字符串
    """
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
    
    # 设置根日志记录器级别
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 设置所有处理器的级别
    for handler in root_logger.handlers:
        handler.setLevel(log_level)
    
    # 设置应用日志记录器级别
    app_logger = logging.getLogger("deutsch_lernen")
    app_logger.setLevel(log_level)
    
    for handler in app_logger.handlers:
        handler.setLevel(log_level)

def log_exception(logger: logging.Logger, message: str, exc_info=True):
    """
    记录异常信息
    
    Args:
        logger: 日志记录器
        message: 日志消息
        exc_info: 是否包含异常信息
    """
    logger.error(message, exc_info=exc_info)

def create_child_logger(parent_name: str, child_name: str) -> logging.Logger:
    """
    创建子日志记录器
    
    Args:
        parent_name: 父日志记录器名称
        child_name: 子日志记录器名称
        
    Returns:
        子日志记录器
    """
    return logging.getLogger(f"{parent_name}.{child_name}")

# 初始化日志系统
def init_logging():
    """初始化日志系统"""
    try:
        # 获取配置
        config = get_config()
        
        # 获取日志配置
        log_level = config.get("logging.level", "INFO")
        log_file = config.get("logging.file", "logs/app.log")
        
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 设置根日志记录器
        setup_logger(None, log_level, log_file)
        
        # 设置应用日志记录器
        app_logger = setup_logger("deutsch_lernen", log_level, log_file)
        
        app_logger.info("日志系统初始化完成")
        
        return True
        
    except Exception as e:
        print(f"日志系统初始化失败: {e}")
        return False

# 创建默认日志记录器
logger = setup_logger("deutsch_lernen")