"""
德语学习应用 - 主包
提供音频转写、翻译、单词学习和Anki导出功能
"""

__version__ = "0.1.0"
__author__ = "Deutsch Lernen Team"

# 导入核心模块
from .core.audio_processor import AudioProcessor
from .core.transcriber import WhisperTranscriber
from .core.translator import LocalTranslator

# 导入数据模型
from .data.models import AudioFile, Transcription, TranscriptionSegment, Translation, WordEntry, CollectedSentence

# 导入导出模块
from .export.anki_exporter import AnkiExporter

__all__ = [
    # 核心模块
    'AudioProcessor',
    'WhisperTranscriber',
    'LocalTranslator',
    
    # 数据模型
    'AudioFile',
    'Transcription',
    'TranscriptionSegment',
    'Translation',
    'WordEntry',
    'CollectedSentence',
    
    # 导出模块
    'AnkiExporter',
]