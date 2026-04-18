"""
数据模型和数据库操作包
包含SQLAlchemy模型和数据库访问层
"""

from .models import (
    Base,
    AudioFile,
    Transcription,
    TranscriptionSegment,
    Translation,
    AudioSegment,
    WordEntry,
    CollectedSentence,
    CollectedWord,
    DatabaseManager
)

from .database import (
    DatabaseManager,
    get_db_manager,
    init_database,
    get_db_session
)

from .repository import (
    BaseRepository,
    AudioFileRepository,
    TranscriptionRepository,
    TranscriptionSegmentRepository,
    TranslationRepository,
    AudioSegmentRepository,
    WordEntryRepository,
    CollectedSentenceRepository,
    CollectedWordRepository,
    RepositoryFactory,
    get_audio_file_repo,
    get_transcription_repo,
    get_transcription_segment_repo,
    get_translation_repo,
    get_audio_segment_repo,
    get_word_entry_repo,
    get_collected_sentence_repo,
    get_collected_word_repo
)

__all__ = [
    # SQLAlchemy基类
    'Base',
    
    # 数据模型
    'AudioFile',
    'Transcription',
    'TranscriptionSegment',
    'Translation',
    'AudioSegment',
    'WordEntry',
    'CollectedSentence',
    'CollectedWord',
    
    # 数据库管理
    'DatabaseManager',
    'get_db_manager',
    'init_database',
    'get_db_session',
    
    # 仓储类
    'BaseRepository',
    'AudioFileRepository',
    'TranscriptionRepository',
    'TranscriptionSegmentRepository',
    'TranslationRepository',
    'AudioSegmentRepository',
    'WordEntryRepository',
    'CollectedSentenceRepository',
    'CollectedWordRepository',
    'RepositoryFactory',
    
    # 便捷函数
    'get_audio_file_repo',
    'get_transcription_repo',
    'get_transcription_segment_repo',
    'get_translation_repo',
    'get_audio_segment_repo',
    'get_word_entry_repo',
    'get_collected_sentence_repo',
    'get_collected_word_repo'
]