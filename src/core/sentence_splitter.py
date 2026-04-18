"""
句子分段器
将转写文本分割为句子
支持德语和中文的句子分割规则
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..utils.logger import get_logger
from ..utils.helpers import normalize_text

logger = get_logger(__name__)

class SentenceBoundary(Enum):
    """句子边界类型"""
    PERIOD = "period"  # 句号
    EXCLAMATION = "exclamation"  # 感叹号
    QUESTION = "question"  # 问号
    ELLIPSIS = "ellipsis"  # 省略号
    NEWLINE = "newline"  # 换行
    SEMICOLON = "semicolon"  # 分号
    COLON = "colon"  # 冒号

@dataclass
class Sentence:
    """句子数据类"""
    text: str  # 句子文本
    start_pos: int  # 起始位置
    end_pos: int  # 结束位置
    boundary_type: SentenceBoundary  # 边界类型
    confidence: float = 1.0  # 分割置信度
    language: str = "de"  # 语言代码
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'text': self.text,
            'start_pos': self.start_pos,
            'end_pos': self.end_pos,
            'boundary_type': self.boundary_type.value,
            'confidence': self.confidence,
            'language': self.language
        }

class GermanSentenceSplitter:
    """德语句子分段器"""
    
    # 德语缩写词列表（避免误分割）
    GERMAN_ABBREVIATIONS = [
        "z.B.", "z. B.", "d.h.", "d. h.", "u.a.", "u. a.", "usw.", "etc.",
        "bzw.", "ca.", "evtl.", "ggf.", "inkl.", "max.", "min.", "Mio.",
        "Mrd.", "Nr.", "o.ä.", "o. Ä.", "s.o.", "s. o.", "s.u.", "s. u.",
        "Tab.", "Taf.", "Tel.", "u.ä.", "u. Ä.", "vgl.", "v. Chr.",
        "n. Chr.", "v.u.Z.", "n.u.Z.", "Abs.", "Art.", "Bd.", "bzw.",
        "Dr.", "Dipl.", "Ing.", "Prof.", "Fr.", "Hr.", "Str.", "Tel.",
        "geb.", "gest.", "hrsg.", "incl.", "jew.", "kath.", "led.",
        "mind.", "mtl.", "östl.", "röm.", "sog.", "tägl.", "westl.",
        "zit.", "zust.", "Übers.", "Verf.", "Hrsg.", "Aufl.", "Bd.",
        "ff.", "Jg.", "Nr.", "S.", "s.", "f.", "ff.", "Vgl.", "vgl.",
        "Anm.", "d.Ä.", "d.J.", "d.M.", "d.W.", "Hg.", "Jh.", "Jhd.",
        "n.Chr.", "o.Ä.", "röm.-kath.", "v.Chr.", "z.Bsp.", "z.T.",
        "z.Z.", "z.Zt.", "dgl.", "erg.", "ev.", "e.v.", "geb.", "gest.",
        "i.A.", "i.d.R.", "i.S.", "i.S.v.", "o.a.", "o.g.", "s.a.",
        "s.o.", "s.u.", "u.E.", "u.U.", "v.a.", "vgl.", "w.o.", "z.B.",
        "z.Hd.", "z.T.", "z.Z.", "zzt.", "u.v.a.m.", "u.ä.", "usf."
    ]
    
    # 德语句子结束标点
    SENTENCE_ENDINGS = r'[.!?]+'
    
    # 德语句子开始模式（大写字母开头）
    SENTENCE_START_PATTERN = r'^[A-ZÄÖÜ]'
    
    def __init__(self, min_sentence_length: int = 5, max_sentence_length: int = 500):
        """
        初始化德语句子分段器
        
        Args:
            min_sentence_length: 最小句子长度（字符数）
            max_sentence_length: 最大句子长度（字符数）
        """
        self.min_sentence_length = min_sentence_length
        self.max_sentence_length = max_sentence_length
        
        # 编译正则表达式
        self._compile_patterns()
        
        logger.info("德语句子分段器初始化完成")
    
    def _compile_patterns(self):
        """编译正则表达式模式"""
        # 转义缩写词
        escaped_abbreviations = []
        for abbr in self.GERMAN_ABBREVIATIONS:
            escaped = re.escape(abbr)
            escaped_abbreviations.append(escaped)
        
        # 缩写词模式
        self.abbreviation_pattern = re.compile(
            r'\b(' + '|'.join(escaped_abbreviations) + r')\b',
            re.IGNORECASE
        )
        
        # 句子结束模式
        self.sentence_ending_pattern = re.compile(self.SENTENCE_ENDINGS)
        
        # 数字模式（避免数字中的句号误分割）
        self.number_pattern = re.compile(r'\d+[.,]\d+')
        
        # 德语特殊字符模式
        self.german_char_pattern = re.compile(r'[äöüßÄÖÜ]')
        
        # 句子开始模式
        self.sentence_start_pattern = re.compile(self.SENTENCE_START_PATTERN)
    
    def split(self, text: str, language: str = "de") -> List[Sentence]:
        """
        分割文本为句子
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            Sentence对象列表
        """
        if not text or not text.strip():
            return []
        
        # 预处理文本
        processed_text = self._preprocess_text(text)
        
        # 分割句子
        sentences = self._split_into_sentences(processed_text, language)
        
        # 后处理
        sentences = self._postprocess_sentences(sentences)
        
        logger.debug(f"文本分割完成: {len(sentences)} 个句子")
        return sentences
    
    def _preprocess_text(self, text: str) -> str:
        """
        预处理文本
        
        Args:
            text: 原始文本
            
        Returns:
            处理后的文本
        """
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除首尾空白
        text = text.strip()
        
        return text
    
    def _split_into_sentences(self, text: str, language: str) -> List[Sentence]:
        """
        将文本分割为句子
        
        Args:
            text: 处理后的文本
            language: 语言代码
            
        Returns:
            Sentence列表
        """
        sentences = []
        current_pos = 0
        sentence_start = 0
        
        # 逐字符处理
        i = 0
        while i < len(text):
            char = text[i]
            
            # 检查是否为句子结束标点
            if char in '.!?':
                # 检查是否为缩写词的一部分
                if self._is_abbreviation(text, i):
                    i += 1
                    continue
                
                # 检查是否为数字中的标点
                if self._is_in_number(text, i):
                    i += 1
                    continue
                
                # 确定边界类型
                boundary_type = self._get_boundary_type(char)
                
                # 提取句子
                sentence_text = text[sentence_start:i+1].strip()
                
                # 检查句子长度
                if len(sentence_text) >= self.min_sentence_length:
                    sentence = Sentence(
                        text=sentence_text,
                        start_pos=sentence_start,
                        end_pos=i+1,
                        boundary_type=boundary_type,
                        language=language
                    )
                    sentences.append(sentence)
                    
                    # 更新下一句的起始位置
                    sentence_start = i + 1
            
            i += 1
        
        # 处理最后一个句子（如果没有以标点结束）
        if sentence_start < len(text):
            remaining_text = text[sentence_start:].strip()
            if remaining_text and len(remaining_text) >= self.min_sentence_length:
                sentence = Sentence(
                    text=remaining_text,
                    start_pos=sentence_start,
                    end_pos=len(text),
                    boundary_type=SentenceBoundary.NEWLINE,  # 假设以换行结束
                    language=language
                )
                sentences.append(sentence)
        
        return sentences
    
    def _is_abbreviation(self, text: str, pos: int) -> bool:
        """
        检查位置是否为缩写词的一部分
        
        Args:
            text: 文本
            pos: 位置
            
        Returns:
            是否为缩写词
        """
        # 获取上下文
        start = max(0, pos - 10)
        end = min(len(text), pos + 2)
        context = text[start:end]
        
        # 检查是否匹配缩写词模式
        return bool(self.abbreviation_pattern.search(context))
    
    def _is_in_number(self, text: str, pos: int) -> bool:
        """
        检查位置是否在数字中
        
        Args:
            text: 文本
            pos: 位置
            
        Returns:
            是否在数字中
        """
        # 获取上下文
        start = max(0, pos - 5)
        end = min(len(text), pos + 5)
        context = text[start:end]
        
        # 检查是否匹配数字模式
        match = self.number_pattern.search(context)
        if match:
            # 检查位置是否在数字范围内
            match_start = start + match.start()
            match_end = start + match.end()
            return match_start <= pos < match_end
        
        return False
    
    def _get_boundary_type(self, char: str) -> SentenceBoundary:
        """
        获取边界类型
        
        Args:
            char: 标点字符
            
        Returns:
            边界类型
        """
        if char == '.':
            return SentenceBoundary.PERIOD
        elif char == '!':
            return SentenceBoundary.EXCLAMATION
        elif char == '?':
            return SentenceBoundary.QUESTION
        elif char == '…':
            return SentenceBoundary.ELLIPSIS
        else:
            return SentenceBoundary.PERIOD
    
    def _postprocess_sentences(self, sentences: List[Sentence]) -> List[Sentence]:
        """
        后处理句子列表
        
        Args:
            sentences: 原始句子列表
            
        Returns:
            处理后的句子列表
        """
        processed = []
        
        for sentence in sentences:
            # 清理句子文本
            text = sentence.text.strip()
            
            # 跳过空句子
            if not text:
                continue
            
            # 检查句子长度
            if len(text) < self.min_sentence_length:
                # 如果太短，尝试与前一个句子合并
                if processed:
                    last_sentence = processed[-1]
                    merged_text = last_sentence.text + " " + text
                    if len(merged_text) <= self.max_sentence_length:
                        processed[-1] = Sentence(
                            text=merged_text,
                            start_pos=last_sentence.start_pos,
                            end_pos=sentence.end_pos,
                            boundary_type=sentence.boundary_type,
                            language=sentence.language
                        )
                        continue
            
            # 检查句子是否以大写字母开头（德语规则）
            if text and not self.sentence_start_pattern.match(text[0]):
                # 如果不是大写开头，可能需要与前一个句子合并
                if processed:
                    last_sentence = processed[-1]
                    merged_text = last_sentence.text + " " + text
                    if len(merged_text) <= self.max_sentence_length:
                        processed[-1] = Sentence(
                            text=merged_text,
                            start_pos=last_sentence.start_pos,
                            end_pos=sentence.end_pos,
                            boundary_type=sentence.boundary_type,
                            language=sentence.language
                        )
                        continue
            
            processed.append(sentence)
        
        return processed
    
    def split_with_timestamps(self, text: str, timestamps: List[Tuple[float, float]], language: str = "de") -> List[Sentence]:
        """
        使用时间戳信息分割句子
        
        Args:
            text: 输入文本
            timestamps: 时间戳列表 [(start, end), ...]
            language: 语言代码
            
        Returns:
            Sentence列表
        """
        # 首先按标点分割
        sentences = self.split(text, language)
        
        # 如果有时间戳，尝试将时间戳与句子对齐
        if timestamps and len(timestamps) == len(sentences):
            for i, sentence in enumerate(sentences):
                start_time, end_time = timestamps[i]
                # 可以在这里添加时间戳信息到句子对象
                # sentence.start_time = start_time
                # sentence.end_time = end_time
        
        return sentences

class ChineseSentenceSplitter:
    """中文句子分段器"""
    
    # 中文句子结束标点
    CHINESE_SENTENCE_ENDINGS = r'[。！？；…]+'
    
    def __init__(self, min_sentence_length: int = 2, max_sentence_length: int = 200):
        """
        初始化中文句子分段器
        
        Args:
            min_sentence_length: 最小句子长度（字符数）
            max_sentence_length: 最大句子长度（字符数）
        """
        self.min_sentence_length = min_sentence_length
        self.max_sentence_length = max_sentence_length
        
        # 编译正则表达式
        self.sentence_ending_pattern = re.compile(self.CHINESE_SENTENCE_ENDINGS)
        
        logger.info("中文句子分段器初始化完成")
    
    def split(self, text: str, language: str = "zh") -> List[Sentence]:
        """
        分割中文文本为句子
        
        Args:
            text: 输入文本
            language: 语言代码
            
        Returns:
            Sentence对象列表
        """
        if not text or not text.strip():
            return []
        
        sentences = []
        current_pos = 0
        sentence_start = 0
        
        # 逐字符处理
        for i, char in enumerate(text):
            if self.sentence_ending_pattern.match(char):
                # 提取句子
                sentence_text = text[sentence_start:i+1].strip()
                
                if len(sentence_text) >= self.min_sentence_length:
                    # 确定边界类型
                    if char in '。':
                        boundary_type = SentenceBoundary.PERIOD
                    elif char in '！':
                        boundary_type = SentenceBoundary.EXCLAMATION
                    elif char in '？':
                        boundary_type = SentenceBoundary.QUESTION
                    elif char in '…':
                        boundary_type = SentenceBoundary.ELLIPSIS
                    elif char in '；':
                        boundary_type = SentenceBoundary.SEMICOLON
                    else:
                        boundary_type = SentenceBoundary.PERIOD
                    
                    sentence = Sentence(
                        text=sentence_text,
                        start_pos=sentence_start,
                        end_pos=i+1,
                        boundary_type=boundary_type,
                        language=language
                    )
                    sentences.append(sentence)
                    
                    sentence_start = i + 1
        
        # 处理最后一个句子
        if sentence_start < len(text):
            remaining_text = text[sentence_start:].strip()
            if remaining_text and len(remaining_text) >= self.min_sentence_length:
                sentence = Sentence(
                    text=remaining_text,
                    start_pos=sentence_start,
                    end_pos=len(text),
                    boundary_type=SentenceBoundary.NEWLINE,
                    language=language
                )
                sentences.append(sentence)
        
        return sentences

class SentenceSplitterFactory:
    """句子分段器工厂"""
    
    @staticmethod
    def create_splitter(language: str = "de", **kwargs):
        """
        创建句子分段器
        
        Args:
            language: 语言代码
            **kwargs: 其他参数
            
        Returns:
            句子分段器实例
        """
        if language.lower() == "de":
            return GermanSentenceSplitter(**kwargs)
        elif language.lower() in ["zh", "cn", "chinese"]:
            return ChineseSentenceSplitter(**kwargs)
        else:
            # 默认使用德语分段器
            logger.warning(f"不支持的语言 {language}，使用德语分段器")
            return GermanSentenceSplitter(**kwargs)

# 全局句子分段器实例
_sentence_splitters: Dict[str, Any] = {}

def get_sentence_splitter(language: str = "de", **kwargs):
    """
    获取句子分段器实例
    
    Args:
        language: 语言代码
        **kwargs: 其他参数
        
    Returns:
        句子分段器实例
    """
    if language not in _sentence_splitters:
        _sentence_splitters[language] = SentenceSplitterFactory.create_splitter(language, **kwargs)
    
    return _sentence_splitters[language]

def split_text_into_sentences(text: str, language: str = "de", **kwargs) -> List[Sentence]:
    """
    将文本分割为句子（便捷函数）
    
    Args:
        text: 输入文本
        language: 语言代码
        **kwargs: 其他参数
        
    Returns:
        Sentence列表
    """
    splitter = get_sentence_splitter(language, **kwargs)
    return splitter.split(text, language)

def split_german_text(text: str, **kwargs) -> List[Sentence]:
    """
    分割德语文本为句子（便捷函数）
    
    Args:
        text: 输入文本
        **kwargs: 其他参数
        
    Returns:
        Sentence列表
    """
    return split_text_into_sentences(text, "de", **kwargs)

def split_chinese_text(text: str, **kwargs) -> List[Sentence]:
    """
    分割中文文本为句子（便捷函数）
    
    Args:
        text: 输入文本
        **kwargs: 其他参数
        
    Returns:
        Sentence列表
    """
    return split_text_into_sentences(text, "zh", **kwargs)