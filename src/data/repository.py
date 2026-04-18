"""
数据访问层（Repository模式）
提供对各个数据模型的CRUD操作
"""

import logging
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_, or_, desc, asc

from .models import (
    Base, AudioFile, Transcription, TranscriptionSegment, 
    Translation, AudioSegment, WordEntry, CollectedSentence, CollectedWord
)
from .database import get_db_session
from ..utils.logger import get_logger

logger = get_logger(__name__)

# 泛型类型变量
T = TypeVar('T', bound=Base)

class BaseRepository(Generic[T]):
    """基础仓储类，提供通用CRUD操作"""
    
    def __init__(self, model_class: Type[T]):
        """
        初始化仓储
        
        Args:
            model_class: 模型类
        """
        self.model_class = model_class
    
    def create(self, session: Session, **kwargs) -> T:
        """
        创建新记录
        
        Args:
            session: 数据库会话
            **kwargs: 模型属性
            
        Returns:
            创建的模型实例
        """
        try:
            instance = self.model_class(**kwargs)
            session.add(instance)
            session.flush()  # 获取ID但不提交
            logger.debug(f"创建 {self.model_class.__name__} 记录: {instance.id}")
            return instance
        except SQLAlchemyError as e:
            logger.error(f"创建 {self.model_class.__name__} 失败: {e}")
            raise
    
    def get_by_id(self, session: Session, id: int) -> Optional[T]:
        """
        根据ID获取记录
        
        Args:
            session: 数据库会话
            id: 记录ID
            
        Returns:
            模型实例或None
        """
        return session.query(self.model_class).filter(self.model_class.id == id).first()
    
    def get_all(self, session: Session, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """
        获取所有记录
        
        Args:
            session: 数据库会话
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            模型实例列表
        """
        query = session.query(self.model_class)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def update(self, session: Session, id: int, **kwargs) -> Optional[T]:
        """
        更新记录
        
        Args:
            session: 数据库会话
            id: 记录ID
            **kwargs: 要更新的属性
            
        Returns:
            更新后的模型实例或None
        """
        try:
            instance = self.get_by_id(session, id)
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                session.flush()
                logger.debug(f"更新 {self.model_class.__name__} 记录: {id}")
            return instance
        except SQLAlchemyError as e:
            logger.error(f"更新 {self.model_class.__name__} 失败: {e}")
            raise
    
    def delete(self, session: Session, id: int) -> bool:
        """
        删除记录
        
        Args:
            session: 数据库会话
            id: 记录ID
            
        Returns:
            是否删除成功
        """
        try:
            instance = self.get_by_id(session, id)
            if instance:
                session.delete(instance)
                session.flush()
                logger.debug(f"删除 {self.model_class.__name__} 记录: {id}")
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"删除 {self.model_class.__name__} 失败: {e}")
            raise
    
    def count(self, session: Session) -> int:
        """
        获取记录总数
        
        Args:
            session: 数据库会话
            
        Returns:
            记录总数
        """
        return session.query(self.model_class).count()
    
    def exists(self, session: Session, id: int) -> bool:
        """
        检查记录是否存在
        
        Args:
            session: 数据库会话
            id: 记录ID
            
        Returns:
            记录是否存在
        """
        return session.query(self.model_class).filter(self.model_class.id == id).count() > 0

class AudioFileRepository(BaseRepository[AudioFile]):
    """音频文件仓储"""
    
    def __init__(self):
        super().__init__(AudioFile)
    
    def get_by_filename(self, session: Session, filename: str) -> Optional[AudioFile]:
        """根据文件名获取音频文件"""
        return session.query(AudioFile).filter(AudioFile.filename == filename).first()
    
    def get_by_format(self, session: Session, format: str) -> List[AudioFile]:
        """根据格式获取音频文件列表"""
        return session.query(AudioFile).filter(AudioFile.format == format).all()
    
    def get_recent_files(self, session: Session, limit: int = 10) -> List[AudioFile]:
        """获取最近的文件"""
        return session.query(AudioFile).order_by(desc(AudioFile.created_at)).limit(limit).all()

class TranscriptionRepository(BaseRepository[Transcription]):
    """转写结果仓储"""
    
    def __init__(self):
        super().__init__(Transcription)
    
    def get_by_audio_file(self, session: Session, audio_file_id: int) -> List[Transcription]:
        """根据音频文件ID获取转写结果"""
        return session.query(Transcription).filter(Transcription.audio_file_id == audio_file_id).all()
    
    def get_by_language(self, session: Session, language: str) -> List[Transcription]:
        """根据语言获取转写结果"""
        return session.query(Transcription).filter(Transcription.language == language).all()
    
    def get_high_confidence(self, session: Session, min_confidence: float = 0.8) -> List[Transcription]:
        """获取高置信度的转写结果"""
        return session.query(Transcription).filter(Transcription.confidence >= min_confidence).all()

class TranscriptionSegmentRepository(BaseRepository[TranscriptionSegment]):
    """转写分段仓储"""
    
    def __init__(self):
        super().__init__(TranscriptionSegment)
    
    def get_by_transcription(self, session: Session, transcription_id: int) -> List[TranscriptionSegment]:
        """根据转写ID获取分段列表"""
        return session.query(TranscriptionSegment).filter(
            TranscriptionSegment.transcription_id == transcription_id
        ).order_by(asc(TranscriptionSegment.segment_index)).all()
    
    def get_by_time_range(self, session: Session, transcription_id: int, start_time: float, end_time: float) -> List[TranscriptionSegment]:
        """根据时间范围获取分段"""
        return session.query(TranscriptionSegment).filter(
            and_(
                TranscriptionSegment.transcription_id == transcription_id,
                TranscriptionSegment.start_time >= start_time,
                TranscriptionSegment.end_time <= end_time
            )
        ).order_by(asc(TranscriptionSegment.start_time)).all()
    
    def search_text(self, session: Session, transcription_id: int, search_text: str) -> List[TranscriptionSegment]:
        """搜索文本内容"""
        return session.query(TranscriptionSegment).filter(
            and_(
                TranscriptionSegment.transcription_id == transcription_id,
                TranscriptionSegment.german_text.contains(search_text)
            )
        ).all()

class TranslationRepository(BaseRepository[Translation]):
    """翻译结果仓储"""
    
    def __init__(self):
        super().__init__(Translation)
    
    def get_by_segment(self, session: Session, segment_id: int) -> Optional[Translation]:
        """根据分段ID获取翻译"""
        return session.query(Translation).filter(Translation.segment_id == segment_id).first()
    
    def get_by_model(self, session: Session, model_name: str) -> List[Translation]:
        """根据模型名称获取翻译列表"""
        return session.query(Translation).filter(Translation.model_used == model_name).all()

class AudioSegmentRepository(BaseRepository[AudioSegment]):
    """音频分段仓储"""
    
    def __init__(self):
        super().__init__(AudioSegment)
    
    def get_by_audio_file(self, session: Session, audio_file_id: int) -> List[AudioSegment]:
        """根据音频文件ID获取分段"""
        return session.query(AudioSegment).filter(AudioSegment.audio_file_id == audio_file_id).all()
    
    def get_by_transcription_segment(self, session: Session, segment_id: int) -> Optional[AudioSegment]:
        """根据转写分段ID获取音频分段"""
        return session.query(AudioSegment).filter(AudioSegment.segment_id == segment_id).first()

class WordEntryRepository(BaseRepository[WordEntry]):
    """单词词典仓储"""
    
    def __init__(self):
        super().__init__(WordEntry)
    
    def get_by_word(self, session: Session, word: str) -> Optional[WordEntry]:
        """根据单词获取词典条目"""
        return session.query(WordEntry).filter(WordEntry.word == word).first()
    
    def get_by_normalized_word(self, session: Session, normalized_word: str) -> Optional[WordEntry]:
        """根据标准化单词获取词典条目"""
        return session.query(WordEntry).filter(WordEntry.normalized_word == normalized_word).first()
    
    def search_words(self, session: Session, search_term: str, limit: int = 50) -> List[WordEntry]:
        """搜索单词"""
        return session.query(WordEntry).filter(
            or_(
                WordEntry.word.contains(search_term),
                WordEntry.normalized_word.contains(search_term),
                WordEntry.chinese_definition.contains(search_term)
            )
        ).limit(limit).all()
    
    def get_by_difficulty(self, session: Session, difficulty_level: int) -> List[WordEntry]:
        """根据难度等级获取单词"""
        return session.query(WordEntry).filter(WordEntry.difficulty_level == difficulty_level).all()

class CollectedSentenceRepository(BaseRepository[CollectedSentence]):
    """收藏句子仓储"""
    
    def __init__(self):
        super().__init__(CollectedSentence)
    
    def get_by_segment(self, session: Session, segment_id: int) -> Optional[CollectedSentence]:
        """根据分段ID获取收藏句子"""
        return session.query(CollectedSentence).filter(CollectedSentence.segment_id == segment_id).first()
    
    def get_by_tags(self, session: Session, tags: List[str]) -> List[CollectedSentence]:
        """根据标签获取收藏句子"""
        # 由于SQLite的JSON支持有限，这里使用简单的包含查询
        query = session.query(CollectedSentence)
        for tag in tags:
            query = query.filter(CollectedSentence.tags.contains(tag))
        return query.all()
    
    def get_for_review(self, session: Session, limit: int = 50) -> List[CollectedSentence]:
        """获取需要复习的句子"""
        now = datetime.utcnow()
        return session.query(CollectedSentence).filter(
            or_(
                CollectedSentence.next_review.is_(None),
                CollectedSentence.next_review <= now
            )
        ).order_by(asc(CollectedSentence.next_review)).limit(limit).all()
    
    def get_recently_collected(self, session: Session, limit: int = 20) -> List[CollectedSentence]:
        """获取最近收藏的句子"""
        return session.query(CollectedSentence).order_by(desc(CollectedSentence.created_at)).limit(limit).all()

class CollectedWordRepository(BaseRepository[CollectedWord]):
    """收藏单词仓储"""
    
    def __init__(self):
        super().__init__(CollectedWord)
    
    def get_by_sentence(self, session: Session, sentence_id: int) -> List[CollectedWord]:
        """根据句子ID获取收藏单词"""
        return session.query(CollectedWord).filter(CollectedWord.sentence_id == sentence_id).all()
    
    def get_by_word_entry(self, session: Session, word_entry_id: int) -> List[CollectedWord]:
        """根据词典条目ID获取收藏单词"""
        return session.query(CollectedWord).filter(CollectedWord.word_entry_id == word_entry_id).all()

# 仓储工厂
class RepositoryFactory:
    """仓储工厂，提供各个仓储的实例"""
    
    _repositories: Dict[str, BaseRepository] = {}
    
    @classmethod
    def get_audio_file_repository(cls) -> AudioFileRepository:
        """获取音频文件仓储"""
        if 'audio_file' not in cls._repositories:
            cls._repositories['audio_file'] = AudioFileRepository()
        return cls._repositories['audio_file']
    
    @classmethod
    def get_transcription_repository(cls) -> TranscriptionRepository:
        """获取转写结果仓储"""
        if 'transcription' not in cls._repositories:
            cls._repositories['transcription'] = TranscriptionRepository()
        return cls._repositories['transcription']
    
    @classmethod
    def get_transcription_segment_repository(cls) -> TranscriptionSegmentRepository:
        """获取转写分段仓储"""
        if 'transcription_segment' not in cls._repositories:
            cls._repositories['transcription_segment'] = TranscriptionSegmentRepository()
        return cls._repositories['transcription_segment']
    
    @classmethod
    def get_translation_repository(cls) -> TranslationRepository:
        """获取翻译结果仓储"""
        if 'translation' not in cls._repositories:
            cls._repositories['translation'] = TranslationRepository()
        return cls._repositories['translation']
    
    @classmethod
    def get_audio_segment_repository(cls) -> AudioSegmentRepository:
        """获取音频分段仓储"""
        if 'audio_segment' not in cls._repositories:
            cls._repositories['audio_segment'] = AudioSegmentRepository()
        return cls._repositories['audio_segment']
    
    @classmethod
    def get_word_entry_repository(cls) -> WordEntryRepository:
        """获取单词词典仓储"""
        if 'word_entry' not in cls._repositories:
            cls._repositories['word_entry'] = WordEntryRepository()
        return cls._repositories['word_entry']
    
    @classmethod
    def get_collected_sentence_repository(cls) -> CollectedSentenceRepository:
        """获取收藏句子仓储"""
        if 'collected_sentence' not in cls._repositories:
            cls._repositories['collected_sentence'] = CollectedSentenceRepository()
        return cls._repositories['collected_sentence']
    
    @classmethod
    def get_collected_word_repository(cls) -> CollectedWordRepository:
        """获取收藏单词仓储"""
        if 'collected_word' not in cls._repositories:
            cls._repositories['collected_word'] = CollectedWordRepository()
        return cls._repositories['collected_word']

# 便捷函数
def get_audio_file_repo() -> AudioFileRepository:
    """获取音频文件仓储"""
    return RepositoryFactory.get_audio_file_repository()

def get_transcription_repo() -> TranscriptionRepository:
    """获取转写结果仓储"""
    return RepositoryFactory.get_transcription_repository()

def get_transcription_segment_repo() -> TranscriptionSegmentRepository:
    """获取转写分段仓储"""
    return RepositoryFactory.get_transcription_segment_repository()

def get_translation_repo() -> TranslationRepository:
    """获取翻译结果仓储"""
    return RepositoryFactory.get_translation_repository()

def get_audio_segment_repo() -> AudioSegmentRepository:
    """获取音频分段仓储"""
    return RepositoryFactory.get_audio_segment_repository()

def get_word_entry_repo() -> WordEntryRepository:
    """获取单词词典仓储"""
    return RepositoryFactory.get_word_entry_repository()

def get_collected_sentence_repo() -> CollectedSentenceRepository:
    """获取收藏句子仓储"""
    return RepositoryFactory.get_collected_sentence_repository()

def get_collected_word_repo() -> CollectedWordRepository:
    """获取收藏单词仓储"""
    return RepositoryFactory.get_collected_word_repository()