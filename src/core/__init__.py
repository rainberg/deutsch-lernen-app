"""
核心模块包
包含音频处理、语音转写、翻译、单词分析、句子分段和语音转中文功能
"""

from .audio_processor import AudioProcessor, AudioInfo, AudioSegment
from .transcriber import WhisperTranscriber, TranscriptionResult, TranscriptionSegment
from .translator import LocalTranslator, TranslationResult
from .word_analyzer import WordAnalyzer, WordInfo, LocalDictionary, get_word_analyzer, analyze_word, get_word_definition
from .sentence_splitter import (
    Sentence, SentenceBoundary, GermanSentenceSplitter, ChineseSentenceSplitter,
    SentenceSplitterFactory, get_sentence_splitter, split_text_into_sentences,
    split_german_text, split_chinese_text
)
from .speech_to_chinese import GermanSpeechToChinese, SpeechToTextResult, german_speech_to_chinese

__all__ = [
    # 音频处理
    'AudioProcessor',
    'AudioInfo',
    'AudioSegment',
    
    # 语音转写
    'WhisperTranscriber',
    'TranscriptionResult',
    'TranscriptionSegment',
    
    # 翻译
    'LocalTranslator',
    'TranslationResult',
    
    # 单词分析
    'WordAnalyzer',
    'WordInfo',
    'LocalDictionary',
    'get_word_analyzer',
    'analyze_word',
    'get_word_definition',
    
    # 句子分段
    'Sentence',
    'SentenceBoundary',
    'GermanSentenceSplitter',
    'ChineseSentenceSplitter',
    'SentenceSplitterFactory',
    'get_sentence_splitter',
    'split_text_into_sentences',
    'split_german_text',
    'split_chinese_text',
    
    # 语音转中文
    'GermanSpeechToChinese',
    'SpeechToTextResult',
    'german_speech_to_chinese'
]