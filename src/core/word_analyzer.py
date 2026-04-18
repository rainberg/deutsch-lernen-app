"""
单词分析器
提供单词查询、词性、释义功能
支持本地词典和在线查询
"""

import os
import json
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..utils.config import get_config
from ..utils.logger import get_logger
from ..utils.helpers import normalize_text, extract_words_from_text

logger = get_logger(__name__)

@dataclass
class WordInfo:
    """单词信息数据类"""
    word: str  # 原始单词
    normalized_word: str  # 标准化单词
    part_of_speech: str  # 词性
    german_definition: str  # 德语释义
    chinese_definition: str  # 中文释义
    english_definition: str  # 英语释义
    examples: List[Dict[str, str]]  # 例句列表
    difficulty_level: int  # 难度等级 1-5
    frequency_rank: Optional[int] = None  # 词频排名
    synonyms: List[str] = None  # 同义词
    antonyms: List[str] = None  # 反义词
    related_words: List[str] = None  # 相关词
    
    def __post_init__(self):
        if self.synonyms is None:
            self.synonyms = []
        if self.antonyms is None:
            self.antonyms = []
        if self.related_words is None:
            self.related_words = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'word': self.word,
            'normalized_word': self.normalized_word,
            'part_of_speech': self.part_of_speech,
            'german_definition': self.german_definition,
            'chinese_definition': self.chinese_definition,
            'english_definition': self.english_definition,
            'examples': self.examples,
            'difficulty_level': self.difficulty_level,
            'frequency_rank': self.frequency_rank,
            'synonyms': self.synonyms,
            'antonyms': self.antonyms,
            'related_words': self.related_words
        }

class LocalDictionary:
    """本地词典管理器"""
    
    def __init__(self, dict_path: Optional[str] = None):
        """
        初始化本地词典
        
        Args:
            dict_path: 词典文件路径，如为None则使用默认路径
        """
        config = get_config()
        
        if dict_path is None:
            dict_path = config.get("paths.models_dir", "models") + "/german_dictionary.json"
        
        self.dict_path = dict_path
        self.dictionary: Dict[str, WordInfo] = {}
        self.is_loaded = False
        
        # 加载词典
        self._load_dictionary()
    
    def _load_dictionary(self):
        """加载词典文件"""
        try:
            if os.path.exists(self.dict_path):
                with open(self.dict_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 转换为WordInfo对象
                for word, info in data.items():
                    self.dictionary[word] = WordInfo(**info)
                
                self.is_loaded = True
                logger.info(f"本地词典加载完成: {len(self.dictionary)} 个词条")
            else:
                logger.warning(f"词典文件不存在: {self.dict_path}")
                self._create_sample_dictionary()
                
        except Exception as e:
            logger.error(f"加载词典失败: {e}")
            self._create_sample_dictionary()
    
    def _create_sample_dictionary(self):
        """创建示例词典"""
        sample_entries = {
            "Hallo": {
                "word": "Hallo",
                "normalized_word": "hallo",
                "part_of_speech": "interj",
                "german_definition": "Begrüßungswort",
                "chinese_definition": "你好",
                "english_definition": "hello",
                "examples": [
                    {"german": "Hallo, wie geht es dir?", "chinese": "你好，你好吗？"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 100,
                "synonyms": ["Guten Tag", "Hi"],
                "antonyms": ["Tschüss"],
                "related_words": ["Guten Morgen", "Guten Abend"]
            },
            "danke": {
                "word": "danke",
                "normalized_word": "danke",
                "part_of_speech": "interj",
                "german_definition": "Dank ausdrücken",
                "chinese_definition": "谢谢",
                "english_definition": "thank you",
                "examples": [
                    {"german": "Danke für deine Hilfe.", "chinese": "谢谢你的帮助。"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 50,
                "synonyms": ["vielen Dank", "Dankeschön"],
                "antonyms": [],
                "related_words": ["bitte", "Bitte"]
            },
            "bitte": {
                "word": "bitte",
                "normalized_word": "bitte",
                "part_of_speech": "adv",
                "german_definition": "Höflichkeitsformel",
                "chinese_definition": "请；不客气",
                "english_definition": "please; you're welcome",
                "examples": [
                    {"german": "Könnten Sie mir bitte helfen?", "chinese": "请您帮帮我好吗？"},
                    {"german": "Danke! - Bitte!", "chinese": "谢谢！- 不客气！"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 30,
                "synonyms": ["gefälligst"],
                "antonyms": [],
                "related_words": ["danke", "Bitte"]
            },
            "ich": {
                "word": "ich",
                "normalized_word": "ich",
                "part_of_speech": "pron",
                "german_definition": "1. Person Singular",
                "chinese_definition": "我",
                "english_definition": "I",
                "examples": [
                    {"german": "Ich bin Student.", "chinese": "我是学生。"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 5,
                "synonyms": [],
                "antonyms": ["du", "er", "sie", "es"],
                "related_words": ["mein", "meine", "mich", "mir"]
            },
            "du": {
                "word": "du",
                "normalized_word": "du",
                "part_of_speech": "pron",
                "german_definition": "2. Person Singular (informell)",
                "chinese_definition": "你",
                "english_definition": "you (informal)",
                "examples": [
                    {"german": "Wie heißt du?", "chinese": "你叫什么名字？"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 10,
                "synonyms": [],
                "antonyms": ["ich", "er", "sie", "es"],
                "related_words": ["dein", "deine", "dich", "dir"]
            },
            "ist": {
                "word": "ist",
                "normalized_word": "ist",
                "part_of_speech": "verb",
                "german_definition": "3. Person Singular von 'sein'",
                "chinese_definition": "是（第三人称单数）",
                "english_definition": "is (third person singular of 'to be')",
                "examples": [
                    {"german": "Das ist gut.", "chinese": "这很好。"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 2,
                "synonyms": ["befindet sich"],
                "antonyms": ["ist nicht"],
                "related_words": ["bin", "bist", "sind", "seid"]
            },
            "gut": {
                "word": "gut",
                "normalized_word": "gut",
                "part_of_speech": "adj",
                "german_definition": "positiv, von hoher Qualität",
                "chinese_definition": "好的",
                "english_definition": "good",
                "examples": [
                    {"german": "Das ist ein gutes Buch.", "chinese": "这是一本好书。"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 15,
                "synonyms": ["prima", "ausgezeichnet", "hervorragend"],
                "antonyms": ["schlecht"],
                "related_words": ["besser", "am besten", "Güte"]
            },
            "schlecht": {
                "word": "schlecht",
                "normalized_word": "schlecht",
                "part_of_speech": "adj",
                "german_definition": "negativ, von niedriger Qualität",
                "chinese_definition": "坏的",
                "english_definition": "bad",
                "examples": [
                    {"german": "Das Wetter ist schlecht.", "chinese": "天气不好。"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 20,
                "synonyms": ["schlimm", "übel"],
                "antonyms": ["gut"],
                "related_words": ["schlechter", "am schlechtesten", "Schlechtigkeit"]
            },
            "Wasser": {
                "word": "Wasser",
                "normalized_word": "wasser",
                "part_of_speech": "noun",
                "german_definition": "H₂O, transparente Flüssigkeit",
                "chinese_definition": "水",
                "english_definition": "water",
                "examples": [
                    {"german": "Ich möchte ein Glas Wasser.", "chinese": "我想要一杯水。"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 25,
                "synonyms": ["H₂O"],
                "antonyms": [],
                "related_words": ["wasserreich", "Wasserfall", "Wasserglas"]
            },
            "essen": {
                "word": "essen",
                "normalized_word": "essen",
                "part_of_speech": "verb",
                "german_definition": "Nahrung zu sich nehmen",
                "chinese_definition": "吃",
                "english_definition": "to eat",
                "examples": [
                    {"german": "Ich esse gern Pizza.", "chinese": "我喜欢吃披萨。"}
                ],
                "difficulty_level": 1,
                "frequency_rank": 35,
                "synonyms": ["speisen", "verzehren"],
                "antonyms": ["fasten"],
                "related_words": ["Essen", "Essenszeit", "餐厅"]
            }
        }
        
        # 保存示例词典
        try:
            # 确保目录存在
            dict_dir = os.path.dirname(self.dict_path)
            if dict_dir and not os.path.exists(dict_dir):
                os.makedirs(dict_dir, exist_ok=True)
            
            with open(self.dict_path, 'w', encoding='utf-8') as f:
                json.dump(sample_entries, f, indent=2, ensure_ascii=False)
            
            # 重新加载词典
            self._load_dictionary()
            
            logger.info(f"创建示例词典: {self.dict_path}")
            
        except Exception as e:
            logger.error(f"创建示例词典失败: {e}")
    
    def lookup(self, word: str) -> Optional[WordInfo]:
        """
        查询单词
        
        Args:
            word: 要查询的单词
            
        Returns:
            WordInfo对象或None
        """
        if not self.is_loaded:
            logger.warning("词典未加载")
            return None
        
        # 标准化单词
        normalized = self._normalize_german_word(word)
        
        # 尝试精确匹配
        if word in self.dictionary:
            return self.dictionary[word]
        
        if normalized in self.dictionary:
            return self.dictionary[normalized]
        
        # 尝试大小写不敏感匹配
        word_lower = word.lower()
        normalized_lower = normalized.lower()
        
        for entry in self.dictionary.values():
            if entry.word.lower() == word_lower or entry.normalized_word == normalized_lower:
                return entry
        
        return None
    
    def search(self, query: str, limit: int = 50) -> List[WordInfo]:
        """
        搜索单词
        
        Args:
            query: 搜索查询
            limit: 最大结果数
            
        Returns:
            WordInfo列表
        """
        if not self.is_loaded:
            return []
        
        results = []
        query_lower = query.lower()
        
        for entry in self.dictionary.values():
            # 在单词、释义中搜索
            if (query_lower in entry.word.lower() or
                query_lower in entry.normalized_word.lower() or
                query_lower in entry.chinese_definition.lower() or
                query_lower in entry.german_definition.lower()):
                results.append(entry)
                
                if len(results) >= limit:
                    break
        
        return results
    
    def get_words_by_difficulty(self, level: int) -> List[WordInfo]:
        """
        根据难度等级获取单词
        
        Args:
            level: 难度等级 (1-5)
            
        Returns:
            WordInfo列表
        """
        if not self.is_loaded:
            return []
        
        return [entry for entry in self.dictionary.values() if entry.difficulty_level == level]
    
    def get_random_words(self, count: int = 10) -> List[WordInfo]:
        """
        获取随机单词
        
        Args:
            count: 单词数量
            
        Returns:
            WordInfo列表
        """
        import random
        
        if not self.is_loaded:
            return []
        
        all_words = list(self.dictionary.values())
        return random.sample(all_words, min(count, len(all_words)))
    
    def _normalize_german_word(self, word: str) -> str:
        """
        标准化德语单词
        
        Args:
            word: 原始单词
            
        Returns:
            标准化后的单词
        """
        # 转换为小写
        word = word.lower()
        
        # 移除变音符号（用于匹配）
        replacements = {
            'ä': 'ae',
            'ö': 'oe',
            'ü': 'ue',
            'ß': 'ss'
        }
        
        for old, new in replacements.items():
            word = word.replace(old, new)
        
        return word

class WordAnalyzer:
    """单词分析器主类"""
    
    def __init__(self, use_local_dict: bool = True, use_api: bool = False):
        """
        初始化单词分析器
        
        Args:
            use_local_dict: 是否使用本地词典
            use_api: 是否使用在线API
        """
        self.use_local_dict = use_local_dict
        self.use_api = use_api
        
        # 初始化本地词典
        if use_local_dict:
            self.local_dict = LocalDictionary()
        else:
            self.local_dict = None
        
        # 缓存
        self.cache: Dict[str, WordInfo] = {}
        
        logger.info("单词分析器初始化完成")
    
    def analyze_word(self, word: str) -> Optional[WordInfo]:
        """
        分析单词
        
        Args:
            word: 要分析的单词
            
        Returns:
            WordInfo对象或None
        """
        # 检查缓存
        if word in self.cache:
            return self.cache[word]
        
        # 标准化单词
        normalized = self._normalize_word(word)
        
        # 尝试本地词典
        if self.use_local_dict and self.local_dict:
            word_info = self.local_dict.lookup(word)
            if word_info:
                self.cache[word] = word_info
                return word_info
        
        # 如果需要，可以在这里添加在线API查询
        # if self.use_api:
        #     word_info = self._query_online_api(word)
        #     if word_info:
        #         self.cache[word] = word_info
        #         return word_info
        
        # 如果都没有找到，返回基本的单词信息
        basic_info = WordInfo(
            word=word,
            normalized_word=normalized,
            part_of_speech="unknown",
            german_definition="",
            chinese_definition="",
            english_definition="",
            examples=[],
            difficulty_level=3
        )
        
        self.cache[word] = basic_info
        return basic_info
    
    def analyze_text(self, text: str, language: str = "de") -> Dict[str, WordInfo]:
        """
        分析文本中的所有单词
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            单词到WordInfo的映射
        """
        # 提取单词
        words = extract_words_from_text(text, language)
        
        # 分析每个单词
        results = {}
        for word in set(words):  # 去重
            word_info = self.analyze_word(word)
            if word_info:
                results[word] = word_info
        
        return results
    
    def get_word_definition(self, word: str, definition_type: str = "chinese") -> str:
        """
        获取单词释义
        
        Args:
            word: 单词
            definition_type: 释义类型 (chinese, german, english)
            
        Returns:
            释义文本
        """
        word_info = self.analyze_word(word)
        if not word_info:
            return ""
        
        if definition_type == "chinese":
            return word_info.chinese_definition
        elif definition_type == "german":
            return word_info.german_definition
        elif definition_type == "english":
            return word_info.english_definition
        else:
            return word_info.chinese_definition
    
    def get_examples(self, word: str) -> List[Dict[str, str]]:
        """
        获取单词例句
        
        Args:
            word: 单词
            
        Returns:
            例句列表
        """
        word_info = self.analyze_word(word)
        if not word_info:
            return []
        
        return word_info.examples
    
    def get_synonyms(self, word: str) -> List[str]:
        """
        获取同义词
        
        Args:
            word: 单词
            
        Returns:
            同义词列表
        """
        word_info = self.analyze_word(word)
        if not word_info:
            return []
        
        return word_info.synonyms
    
    def get_antonyms(self, word: str) -> List[str]:
        """
        获取反义词
        
        Args:
            word: 单词
            
        Returns:
            反义词列表
        """
        word_info = self.analyze_word(word)
        if not word_info:
            return []
        
        return word_info.antonyms
    
    def get_related_words(self, word: str) -> List[str]:
        """
        获取相关词
        
        Args:
            word: 单词
            
        Returns:
            相关词列表
        """
        word_info = self.analyze_word(word)
        if not word_info:
            return []
        
        return word_info.related_words
    
    def get_difficulty_level(self, word: str) -> int:
        """
        获取单词难度等级
        
        Args:
            word: 单词
            
        Returns:
            难度等级 (1-5)
        """
        word_info = self.analyze_word(word)
        if not word_info:
            return 3  # 默认中等难度
        
        return word_info.difficulty_level
    
    def is_german_word(self, word: str) -> bool:
        """
        检查是否为德语单词
        
        Args:
            word: 单词
            
        Returns:
            是否为德语单词
        """
        # 简单的德语单词检测
        # 检查是否包含德语特殊字符
        german_chars = set('äöüßÄÖÜ')
        if any(char in word for char in german_chars):
            return True
        
        # 检查常见德语词缀
        german_prefixes = ['ge', 'be', 'ver', 'zer', 'ent', 'er', 'un', 'über', 'unter', 'vor', 'nach', 'mit', 'aus', 'ein']
        german_suffixes = ['ung', 'heit', 'keit', 'lich', 'isch', 'bar', 'sam', 'los', 'voll', 'chen', 'lein']
        
        word_lower = word.lower()
        
        for prefix in german_prefixes:
            if word_lower.startswith(prefix):
                return True
        
        for suffix in german_suffixes:
            if word_lower.endswith(suffix):
                return True
        
        return False
    
    def _normalize_word(self, word: str) -> str:
        """
        标准化单词
        
        Args:
            word: 原始单词
            
        Returns:
            标准化后的单词
        """
        # 移除标点符号
        word = re.sub(r'[^\w\s]', '', word)
        
        # 转换为小写
        word = word.lower()
        
        # 移除多余空格
        word = word.strip()
        
        return word
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("单词分析器缓存已清空")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计字典
        """
        return {
            'cache_size': len(self.cache),
            'is_local_dict_loaded': self.local_dict.is_loaded if self.local_dict else False,
            'local_dict_size': len(self.local_dict.dictionary) if self.local_dict else 0
        }

# 全局单词分析器实例
_word_analyzer_instance = None

def get_word_analyzer(use_local_dict: bool = True, use_api: bool = False) -> WordAnalyzer:
    """
    获取单词分析器实例（单例模式）
    
    Args:
        use_local_dict: 是否使用本地词典
        use_api: 是否使用在线API
        
    Returns:
        WordAnalyzer实例
    """
    global _word_analyzer_instance
    
    if _word_analyzer_instance is None:
        _word_analyzer_instance = WordAnalyzer(use_local_dict, use_api)
    
    return _word_analyzer_instance

def analyze_word(word: str) -> Optional[WordInfo]:
    """
    分析单词（便捷函数）
    
    Args:
        word: 要分析的单词
        
    Returns:
        WordInfo对象或None
    """
    analyzer = get_word_analyzer()
    return analyzer.analyze_word(word)

def get_word_definition(word: str, definition_type: str = "chinese") -> str:
    """
    获取单词释义（便捷函数）
    
    Args:
        word: 单词
        definition_type: 释义类型
        
    Returns:
        释义文本
    """
    analyzer = get_word_analyzer()
    return analyzer.get_word_definition(word, definition_type)