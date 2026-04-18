"""
数据模型定义
使用SQLAlchemy ORM
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
import json

Base = declarative_base()

class AudioFile(Base):
    """音频/视频文件"""
    __tablename__ = 'audio_files'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(500), nullable=False)
    filepath = Column(String(1000), nullable=False)
    duration = Column(Float, nullable=False)  # 秒
    filesize = Column(Integer, nullable=False)  # 字节
    format = Column(String(50), nullable=False)  # mp3, mp4, wav等
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    transcriptions = relationship("Transcription", back_populates="audio_file", cascade="all, delete-orphan")
    segments = relationship("AudioSegment", back_populates="audio_file", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'filepath': self.filepath,
            'duration': self.duration,
            'filesize': self.filesize,
            'format': self.format,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Transcription(Base):
    """语音转写结果"""
    __tablename__ = 'transcriptions'
    
    id = Column(Integer, primary_key=True)
    audio_file_id = Column(Integer, ForeignKey('audio_files.id'), nullable=False)
    language = Column(String(10), default='de')  # 语言代码，默认为德语
    model_used = Column(String(100), nullable=False)  # 使用的转写模型
    confidence = Column(Float, default=0.0)  # 整体置信度
    raw_text = Column(Text, nullable=False)  # 原始转写文本
    processed_text = Column(Text, nullable=True)  # 处理后的文本（标点修正等）
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    audio_file = relationship("AudioFile", back_populates="transcriptions")
    segments = relationship("TranscriptionSegment", back_populates="transcription", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'audio_file_id': self.audio_file_id,
            'language': self.language,
            'model_used': self.model_used,
            'confidence': self.confidence,
            'raw_text': self.raw_text,
            'processed_text': self.processed_text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TranscriptionSegment(Base):
    """转写分段（句子级别）"""
    __tablename__ = 'transcription_segments'
    
    id = Column(Integer, primary_key=True)
    transcription_id = Column(Integer, ForeignKey('transcriptions.id'), nullable=False)
    segment_index = Column(Integer, nullable=False)  # 分段序号
    start_time = Column(Float, nullable=False)  # 开始时间（秒）
    end_time = Column(Float, nullable=False)  # 结束时间（秒）
    german_text = Column(Text, nullable=False)  # 德语原文
    confidence = Column(Float, default=0.0)  # 分段置信度
    
    # 关联关系
    transcription = relationship("Transcription", back_populates="segments")
    translation = relationship("Translation", uselist=False, back_populates="segment", cascade="all, delete-orphan")
    audio_segment = relationship("AudioSegment", uselist=False, back_populates="transcription_segment", cascade="all, delete-orphan")
    collected_sentences = relationship("CollectedSentence", back_populates="segment", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'transcription_id': self.transcription_id,
            'segment_index': self.segment_index,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'german_text': self.german_text,
            'confidence': self.confidence
        }

class Translation(Base):
    """翻译结果"""
    __tablename__ = 'translations'
    
    id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('transcription_segments.id'), nullable=False, unique=True)
    chinese_text = Column(Text, nullable=False)  # 中文翻译
    model_used = Column(String(100), nullable=False)  # 使用的翻译模型
    confidence = Column(Float, default=0.0)  # 翻译置信度
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    segment = relationship("TranscriptionSegment", back_populates="translation")
    
    def to_dict(self):
        return {
            'id': self.id,
            'segment_id': self.segment_id,
            'chinese_text': self.chinese_text,
            'model_used': self.model_used,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AudioSegment(Base):
    """音频分段（对应转写分段）"""
    __tablename__ = 'audio_segments'
    
    id = Column(Integer, primary_key=True)
    audio_file_id = Column(Integer, ForeignKey('audio_files.id'), nullable=False)
    segment_id = Column(Integer, ForeignKey('transcription_segments.id'), nullable=True, unique=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    filepath = Column(String(1000), nullable=True)  # 分段音频文件路径（如已导出）
    duration = Column(Float, nullable=False)
    
    # 关联关系
    audio_file = relationship("AudioFile", back_populates="segments")
    transcription_segment = relationship("TranscriptionSegment", back_populates="audio_segment")
    
    def to_dict(self):
        return {
            'id': self.id,
            'audio_file_id': self.audio_file_id,
            'segment_id': self.segment_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'filepath': self.filepath,
            'duration': self.duration
        }

class WordEntry(Base):
    """单词词典条目"""
    __tablename__ = 'word_entries'
    
    id = Column(Integer, primary_key=True)
    word = Column(String(200), nullable=False, index=True)  # 单词原文
    normalized_word = Column(String(200), nullable=False, index=True)  # 标准化（小写、去除变音符号）
    part_of_speech = Column(String(50), nullable=True)  # 词性
    german_definition = Column(Text, nullable=True)  # 德语释义
    chinese_definition = Column(Text, nullable=True)  # 中文释义
    english_definition = Column(Text, nullable=True)  # 英语释义
    examples = Column(JSON, nullable=True)  # 例句列表 [{german: ..., chinese: ...}]
    difficulty_level = Column(Integer, default=1)  # 难度等级 1-5
    frequency_rank = Column(Integer, nullable=True)  # 词频排名
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    collected_words = relationship("CollectedWord", back_populates="word_entry")
    
    def to_dict(self):
        return {
            'id': self.id,
            'word': self.word,
            'normalized_word': self.normalized_word,
            'part_of_speech': self.part_of_speech,
            'german_definition': self.german_definition,
            'chinese_definition': self.chinese_definition,
            'english_definition': self.english_definition,
            'examples': self.examples,
            'difficulty_level': self.difficulty_level,
            'frequency_rank': self.frequency_rank,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CollectedSentence(Base):
    """用户收藏的句子"""
    __tablename__ = 'collected_sentences'
    
    id = Column(Integer, primary_key=True)
    segment_id = Column(Integer, ForeignKey('transcription_segments.id'), nullable=False)
    user_notes = Column(Text, nullable=True)  # 用户笔记
    tags = Column(JSON, nullable=True)  # 标签列表
    difficulty_rating = Column(Integer, nullable=True)  # 用户自评难度 1-5
    review_count = Column(Integer, default=0)  # 复习次数
    last_reviewed = Column(DateTime, nullable=True)
    next_review = Column(DateTime, nullable=True)  # 下次复习时间
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    segment = relationship("TranscriptionSegment", back_populates="collected_sentences")
    
    def to_dict(self):
        return {
            'id': self.id,
            'segment_id': self.segment_id,
            'user_notes': self.user_notes,
            'tags': self.tags,
            'difficulty_rating': self.difficulty_rating,
            'review_count': self.review_count,
            'last_reviewed': self.last_reviewed.isoformat() if self.last_reviewed else None,
            'next_review': self.next_review.isoformat() if self.next_review else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class CollectedWord(Base):
    """用户收藏的单词（从收藏句子中提取）"""
    __tablename__ = 'collected_words'
    
    id = Column(Integer, primary_key=True)
    word_entry_id = Column(Integer, ForeignKey('word_entries.id'), nullable=False)
    sentence_id = Column(Integer, ForeignKey('collected_sentences.id'), nullable=False)
    context = Column(Text, nullable=True)  # 单词在句子中的上下文
    user_definition = Column(Text, nullable=True)  # 用户自定义释义
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    word_entry = relationship("WordEntry", back_populates="collected_words")
    
    def to_dict(self):
        return {
            'id': self.id,
            'word_entry_id': self.word_entry_id,
            'sentence_id': self.sentence_id,
            'context': self.context,
            'user_definition': self.user_definition,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# 数据库管理器
class DatabaseManager:
    def __init__(self, db_path: str = "data/deutsch_lernen.db"):
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def init_db(self):
        """初始化数据库，创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        
    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

# 默认数据库管理器
db_manager = DatabaseManager()

if __name__ == "__main__":
    # 测试数据库初始化
    db_manager.init_db()
    print("数据库初始化完成！")