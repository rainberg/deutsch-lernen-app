"""
工具函数模块
提供通用的辅助函数
"""

import os
import re
import sys
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import unicodedata

def format_duration(seconds: float) -> str:
    """
    格式化时间长度（秒）为可读字符串
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化的时间字符串 (HH:MM:SS 或 MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_filesize(size_bytes: int) -> str:
    """
    格式化文件大小（字节）为可读字符串
    
    Args:
        size_bytes: 字节数
        
    Returns:
        格式化的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除或替换非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的文件名
    """
    # 替换非法字符为下划线
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除连续的点号
    filename = re.sub(r'\.{2,}', '.', filename)
    # 移除首尾空格和点号
    filename = filename.strip('. ')
    # 确保文件名不为空
    if not filename:
        filename = "unnamed"
    return filename

def get_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """
    计算文件的哈希值
    
    Args:
        file_path: 文件路径
        algorithm: 哈希算法 (md5, sha1, sha256)
        
    Returns:
        文件哈希值
    """
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def ensure_dir_exists(dir_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
        
    Returns:
        是否成功
    """
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败: {e}")
        return False

def get_temp_dir() -> str:
    """
    获取临时目录路径
    
    Returns:
        临时目录路径
    """
    temp_dir = tempfile.mkdtemp(prefix="deutsch_lernen_")
    return temp_dir

def cleanup_temp_dir(temp_dir: str):
    """
    清理临时目录
    
    Args:
        temp_dir: 临时目录路径
    """
    try:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"清理临时目录失败: {e}")

def split_text_into_sentences(text: str, language: str = "de") -> List[str]:
    """
    将文本分割成句子
    
    Args:
        text: 输入文本
        language: 语言代码
        
    Returns:
        句子列表
    """
    # 简单的句子分割，按标点符号分割
    # 对于德语，主要使用句号、问号、感叹号
    if language == "de":
        # 德语句子结束标点
        sentence_endings = r'[.!?]+'
    else:
        # 默认使用通用标点
        sentence_endings = r'[.!?。！？]+'
    
    # 分割文本
    sentences = re.split(sentence_endings, text)
    
    # 清理空句子
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences

def extract_words_from_text(text: str, language: str = "de") -> List[str]:
    """
    从文本中提取单词
    
    Args:
        text: 输入文本
        language: 语言代码
        
    Returns:
        单词列表
    """
    if language == "de":
        # 德语单词匹配模式
        # 包含德语特殊字符 ä, ö, ü, ß
        pattern = r'\b[A-Za-zÄÖÜäöüß]+\b'
    else:
        # 通用单词匹配
        pattern = r'\b\w+\b'
    
    words = re.findall(pattern, text)
    return words

def normalize_text(text: str, language: str = "de") -> str:
    """
    标准化文本
    
    Args:
        text: 输入文本
        language: 语言代码
        
    Returns:
        标准化后的文本
    """
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 标准化Unicode字符
    text = unicodedata.normalize('NFKC', text)
    
    # 对于德语，处理特殊字符
    if language == "de":
        # 确保德语特殊字符正确编码
        text = text.replace('ae', 'ä').replace('oe', 'ö').replace('ue', 'ü')
    
    return text

def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    解析时间戳字符串
    
    Args:
        timestamp_str: 时间戳字符串
        
    Returns:
        datetime对象或None
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d.%m.%Y %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue
    
    return None

def format_timestamp(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化datetime对象为字符串
    
    Args:
        dt: datetime对象
        fmt: 格式字符串
        
    Returns:
        格式化的时间字符串
    """
    return dt.strftime(fmt)

def get_relative_time(dt: datetime) -> str:
    """
    获取相对时间描述
    
    Args:
        dt: datetime对象
        
    Returns:
        相对时间字符串
    """
    now = datetime.now()
    diff = now - dt
    
    if diff.days > 365:
        years = diff.days // 365
        return f"{years}年前"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months}个月前"
    elif diff.days > 0:
        return f"{diff.days}天前"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours}小时前"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes}分钟前"
    else:
        return "刚刚"

def truncate_string(s: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    截断字符串
    
    Args:
        s: 输入字符串
        max_length: 最大长度
        suffix: 后缀
        
    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix

def remove_duplicates(lst: List[Any]) -> List[Any]:
    """
    移除列表中的重复项，保持顺序
    
    Args:
        lst: 输入列表
        
    Returns:
        去重后的列表
    """
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        lst: 输入列表
        chunk_size: 块大小
        
    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def flatten_list(lst: List[List[Any]]) -> List[Any]:
    """
    展平嵌套列表
    
    Args:
        lst: 嵌套列表
        
    Returns:
        展平后的列表
    """
    return [item for sublist in lst for item in sublist]

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """
    安全除法，避免除以零
    
    Args:
        a: 被除数
        b: 除数
        default: 默认值
        
    Returns:
        除法结果或默认值
    """
    try:
        return a / b
    except ZeroDivisionError:
        return default

def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    将值限制在指定范围内
    
    Args:
        value: 输入值
        min_value: 最小值
        max_value: 最大值
        
    Returns:
        限制后的值
    """
    return max(min_value, min(value, max_value))

def percentage(part: float, whole: float) -> float:
    """
    计算百分比
    
    Args:
        part: 部分值
        whole: 整体值
        
    Returns:
        百分比 (0-100)
    """
    if whole == 0:
        return 0.0
    return (part / whole) * 100.0