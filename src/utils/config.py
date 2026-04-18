"""
配置管理模块
支持JSON配置文件的读取、保存和验证
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    # 应用设置
    "app": {
        "name": "Deutsch Lernen App",
        "version": "0.1.0",
        "language": "zh-CN",
        "theme": "light",
        "auto_save": True,
        "recent_files": [],
    },
    
    # 音频处理设置
    "audio": {
        "default_sample_rate": 16000,
        "default_format": "wav",
        "silence_threshold": -40,
        "min_silence_len": 500,
        "segment_duration": 10.0,
    },
    
    # 转写设置
    "transcription": {
        "model_size": "base",
        "device": "auto",
        "language": "de",
        "use_api": False,
        "api_key": "",
        "api_base": "https://api.openai.com/v1",
    },
    
    # 翻译设置
    "translation": {
        "model_name": "Helsinki-NLP/opus-mt-de-zh",
        "device": "auto",
        "source_lang": "de",
        "target_lang": "zh",
        "use_api": False,
        "api_key": "",
        "api_base": "https://api.openai.com/v1",
    },
    
    # 数据库设置
    "database": {
        "path": "data/deutsch_lernen.db",
        "echo": False,
    },
    
    # 导出设置
    "export": {
        "anki_deck_name": "Deutsch Lernen",
        "anki_deck_description": "德语学习牌组",
        "anki_model_id": 1607392319,
        "anki_deck_id": 2059400110,
        "include_audio": True,
        "output_dir": "exports",
    },
    
    # 日志设置
    "logging": {
        "level": "INFO",
        "file": "logs/app.log",
        "max_size": 10485760,
    },
    
    # 路径设置
    "paths": {
        "data_dir": "data",
        "audio_dir": "data/audio",
        "exports_dir": "exports",
        "logs_dir": "logs",
    },
}

@dataclass
class Config:
    """配置类，管理应用的所有配置"""
    
    config_path: str = "config.json"
    _data: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG.copy())
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保配置目录存在
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        # 如果配置文件存在则加载
        if os.path.exists(self.config_path):
            self.load()
        else:
            # 使用默认配置并保存
            self.save()
    
    def load(self, config_path: Optional[str] = None):
        """从文件加载配置"""
        path = config_path or self.config_path
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 合并配置，保留默认值
            self._merge_config(data)
            logger.info(f"配置已加载: {path}")
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"加载配置失败，使用默认配置: {e}")
            self._data = DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self, config_path: Optional[str] = None):
        """保存配置到文件"""
        path = config_path or self.config_path
        
        try:
            # 确保目录存在
            config_dir = os.path.dirname(path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已保存: {path}")
            
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            raise
    
    def get(self, key: str, default=None):
        """获取配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        value = self._data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """设置配置值，支持点号分隔的嵌套键"""
        keys = key.split('.')
        data = self._data
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        
        # 设置值
        data[keys[-1]] = value
    
    def _merge_config(self, new_data: Dict[str, Any]):
        """合并配置，保留默认值"""
        def merge_dict(base: Dict, new: Dict):
            for key, value in new.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value
        
        merge_dict(self._data, new_data)
    
    def validate(self) -> bool:
        """验证配置的有效性"""
        try:
            # 检查必要的配置项
            required_keys = [
                "app.name",
                "transcription.model_size",
                "translation.model_name",
                "database.path",
            ]
            
            for key in required_keys:
                if self.get(key) is None:
                    logger.error(f"缺少必要的配置项: {key}")
                    return False
            
            # 检查路径有效性
            db_path = self.get("database.path")
            if db_path:
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    try:
                        os.makedirs(db_dir, exist_ok=True)
                    except Exception as e:
                        logger.error(f"无法创建数据库目录: {e}")
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def reset_to_default(self):
        """重置为默认配置"""
        self._data = DEFAULT_CONFIG.copy()
        self.save()
        logger.info("配置已重置为默认值")
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return self._data.copy()

# 全局配置实例
_config_instance = None

def load_config(config_path: str = "config.json") -> Config:
    """加载配置文件"""
    global _config_instance
    _config_instance = Config(config_path)
    return _config_instance

def get_config() -> Config:
    """获取当前配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance

def save_config(config: Config, config_path: Optional[str] = None):
    """保存配置"""
    config.save(config_path)