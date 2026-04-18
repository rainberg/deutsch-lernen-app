"""
Anki导出模块 - 音频学习版
正面：句子音频
背面：德语原文 + 中文翻译
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import logging

import genanki

logger = logging.getLogger(__name__)

@dataclass
class AudioCard:
    """音频学习卡片"""
    german_text: str  # 德语原文
    chinese_text: str  # 中文翻译
    audio_path: Optional[str] = None  # 音频文件路径
    audio_start: float = 0.0  # 音频开始时间（秒）
    audio_end: float = 0.0  # 音频结束时间（秒）
    tags: List[str] = field(default_factory=list)
    notes: str = ""  # 用户笔记
    
    @property
    def guid(self) -> str:
        """生成唯一标识"""
        content = f"{self.german_text}_{self.audio_start}_{self.audio_end}"
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, content))

class AudioBasedExporter:
    """基于音频的Anki导出器"""
    
    # 模型和牌组ID（固定值）
    MODEL_ID = 1607392319
    DECK_ID = 2059400110
    
    def __init__(self, output_dir: str = "exports"):
        """
        初始化导出器
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        self.media_files = []  # 收集媒体文件
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 创建媒体临时目录
        self.media_dir = os.path.join(output_dir, "media")
        os.makedirs(self.media_dir, exist_ok=True)
        
        # 定义卡片模型
        self.model = self._create_model()
        
        logger.info(f"Anki导出器初始化完成，输出目录: {output_dir}")
    
    def _create_model(self) -> genanki.Model:
        """创建卡片模型"""
        
        # 正面模板 - 只显示音频播放按钮
        front_template = '''
<div class="card front-card">
    <div class="audio-section">
        <div class="audio-icon">🎧</div>
        <div class="audio-label">听音频，理解句子含义</div>
        
        {{#Audio}}
        <div class="audio-control">
            [sound:{{Audio}}]
        </div>
        {{/Audio}}
        
        {{^Audio}}
        <div class="no-audio">暂无音频</div>
        {{/Audio}}
    </div>
    
    <div class="hint">点击"显示答案"查看翻译</div>
</div>

<style>
.card {
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    max-width: 500px;
    margin: 0 auto;
    padding: 30px 20px;
    text-align: center;
}

.front-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    min-height: 300px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
}

.audio-section {
    margin-bottom: 30px;
}

.audio-icon {
    font-size: 60px;
    margin-bottom: 15px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}

.audio-label {
    font-size: 18px;
    opacity: 0.9;
    margin-bottom: 20px;
}

.audio-control {
    margin: 20px 0;
}

.no-audio {
    padding: 15px 30px;
    background: rgba(255,255,255,0.2);
    border-radius: 10px;
    font-size: 14px;
}

.hint {
    font-size: 14px;
    opacity: 0.7;
    margin-top: 30px;
    padding: 10px 20px;
    background: rgba(255,255,255,0.1);
    border-radius: 20px;
}
</style>
'''
        
        # 背面模板 - 显示德语和中文
        back_template = '''
<div class="card back-card">
    {{#Audio}}
    <div class="audio-replay">
        [sound:{{Audio}}]
        <span class="replay-hint">🔊 再听一遍</span>
    </div>
    {{/Audio}}
    
    <div class="content">
        <div class="german-section">
            <div class="label">🇩🇪 德语原文</div>
            <div class="german-text">{{Deutsch}}</div>
        </div>
        
        <div class="divider"></div>
        
        <div class="chinese-section">
            <div class="label">🇨🇳 中文翻译</div>
            <div class="chinese-text">{{Chinesisch}}</div>
        </div>
    </div>
    
    {{#Notizen}}
    <div class="notes-section">
        <div class="notes-label">📝 笔记</div>
        <div class="notes-content">{{Notizen}}</div>
    </div>
    {{/Notizen}}
    
    {{#Tags}}
    <div class="tags-section">
        {{Tags}}
    </div>
    {{/Tags}}
</div>

<style>
.back-card {
    background: #ffffff;
    color: #333;
    min-height: 300px;
    border-radius: 20px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
}

.audio-replay {
    padding: 15px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 20px 20px 0 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
}

.replay-hint {
    font-size: 14px;
    opacity: 0.9;
}

.content {
    padding: 30px 20px;
}

.german-section, .chinese-section {
    padding: 15px 0;
}

.label {
    font-size: 12px;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
}

.german-text {
    font-size: 24px;
    font-weight: bold;
    color: #2c3e50;
    line-height: 1.4;
}

.chinese-text {
    font-size: 20px;
    color: #e74c3c;
    line-height: 1.4;
}

.divider {
    height: 1px;
    background: linear-gradient(to right, transparent, #ddd, transparent);
    margin: 20px 0;
}

.notes-section {
    margin: 0 20px 20px;
    padding: 15px;
    background: #f8f9fa;
    border-radius: 10px;
    text-align: left;
}

.notes-label {
    font-size: 12px;
    color: #666;
    margin-bottom: 8px;
}

.notes-content {
    font-size: 14px;
    color: #555;
}

.tags-section {
    padding: 10px 20px 20px;
    font-size: 12px;
    color: #999;
}
</style>
'''
        
        # 字段定义
        fields = [
            {'name': 'Deutsch'},      # 德语原文
            {'name': 'Chinesisch'},   # 中文翻译
            {'name': 'Audio'},        # 音频文件名
            {'name': 'Notizen'},      # 用户笔记
            {'name': 'Tags'},         # 标签
        ]
        
        # 创建模型
        model = genanki.Model(
            self.MODEL_ID,
            'Deutsch Audio Lernen',
            fields=fields,
            templates=[
                {
                    'name': 'Audio → Text',
                    'qfmt': front_template,
                    'afmt': back_template,
                },
            ],
            css='''
.card {
    font-family: 'Microsoft YaHei', 'PingFang SC', Arial, sans-serif;
}
'''
        )
        
        return model
    
    def create_card(self, 
                   german_text: str,
                   chinese_text: str,
                   audio_path: Optional[str] = None,
                   audio_start: float = 0.0,
                   audio_end: float = 0.0,
                   tags: Optional[List[str]] = None,
                   notes: str = "") -> genanki.Note:
        """
        创建Anki卡片
        
        Args:
            german_text: 德语原文
            chinese_text: 中文翻译
            audio_path: 音频文件路径
            audio_start: 音频开始时间
            audio_end: 音频结束时间
            tags: 标签列表
            notes: 用户笔记
            
        Returns:
            Anki Note对象
        """
        audio_filename = ""
        
        # 处理音频文件
        if audio_path and os.path.exists(audio_path):
            # 如果需要截取音频片段
            if audio_start > 0 or audio_end > 0:
                audio_path = self._extract_audio_segment(
                    audio_path, audio_start, audio_end
                )
            
            # 复制音频到媒体目录
            audio_filename = os.path.basename(audio_path)
            dest_path = os.path.join(self.media_dir, audio_filename)
            
            if not os.path.exists(dest_path):
                import shutil
                shutil.copy2(audio_path, dest_path)
            
            self.media_files.append(dest_path)
        
        # 创建Note
        note = genanki.Note(
            model=self.model,
            fields=[
                german_text,
                chinese_text,
                audio_filename,
                notes,
                ' '.join(tags) if tags else ''
            ],
            tags=tags or []
        )
        
        return note
    
    def _extract_audio_segment(self, audio_path: str, start: float, end: float) -> str:
        """
        提取音频片段
        
        Args:
            audio_path: 原始音频路径
            start: 开始时间（秒）
            end: 结束时间（秒）
            
        Returns:
            提取后的音频路径
        """
        try:
            from pydub import AudioSegment
            
            # 加载音频
            audio = AudioSegment.from_file(audio_path)
            
            # 转换为毫秒
            start_ms = int(start * 1000)
            end_ms = int(end * 1000) if end > 0 else len(audio)
            
            # 提取片段
            segment = audio[start_ms:end_ms]
            
            # 生成输出路径
            output_filename = f"segment_{int(start)}_{int(end)}.mp3"
            output_path = os.path.join(self.media_dir, output_filename)
            
            # 导出
            segment.export(output_path, format="mp3")
            
            logger.info(f"音频片段提取成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"音频片段提取失败: {e}")
            return audio_path
    
    def export_from_sentences(self,
                            sentences: List[Dict[str, Any]],
                            deck_name: str = "德语听力训练",
                            output_filename: str = "deutsch_audio.apkg") -> str:
        """
        从句子列表导出牌组
        
        Args:
            sentences: 句子列表，每个句子包含:
                - german_text: 德语原文
                - chinese_text: 中文翻译
                - audio_path: 音频文件路径（可选）
                - audio_start: 开始时间（可选）
                - audio_end: 结束时间（可选）
                - tags: 标签（可选）
                - notes: 笔记（可选）
            deck_name: 牌组名称
            output_filename: 输出文件名
            
        Returns:
            输出文件路径
        """
        logger.info(f"开始导出牌组: {deck_name}, 共 {len(sentences)} 张卡片")
        
        # 创建牌组
        deck = genanki.Deck(self.DECK_ID, deck_name)
        
        # 添加卡片
        for i, sentence in enumerate(sentences, 1):
            try:
                note = self.create_card(
                    german_text=sentence.get('german_text', ''),
                    chinese_text=sentence.get('chinese_text', ''),
                    audio_path=sentence.get('audio_path'),
                    audio_start=sentence.get('audio_start', 0.0),
                    audio_end=sentence.get('audio_end', 0.0),
                    tags=sentence.get('tags'),
                    notes=sentence.get('notes', '')
                )
                deck.add_note(note)
                logger.debug(f"添加卡片 {i}: {sentence.get('german_text', '')[:30]}...")
            except Exception as e:
                logger.error(f"添加卡片失败 {i}: {e}")
        
        # 导出
        output_path = os.path.join(self.output_dir, output_filename)
        
        package = genanki.Package(deck)
        package.media_files = self.media_files
        package.write_to_file(output_path)
        
        logger.info(f"牌组导出完成: {output_path}")
        return output_path
    
    def export_from_database(self,
                           db_path: str,
                           deck_name: str = "德语听力训练",
                           output_filename: str = "deutsch_audio.apkg") -> str:
        """
        从数据库导出收藏的句子
        
        Args:
            db_path: 数据库路径
            deck_name: 牌组名称
            output_filename: 输出文件名
            
        Returns:
            输出文件路径
        """
        from ...data.database import get_db_session
        from ...data.repository import get_collected_sentence_repo
        
        sentences = []
        
        with get_db_session() as session:
            repo = get_collected_sentence_repo()
            collected = repo.get_all(session)
            
            for item in collected:
                segment = item.segment
                if segment and segment.transcription:
                    # 获取翻译
                    translation = segment.translation
                    chinese_text = translation.chinese_text if translation else ''
                    
                    # 获取音频文件
                    audio_file = segment.transcription.audio_file
                    
                    sentences.append({
                        'german_text': segment.german_text,
                        'chinese_text': chinese_text,
                        'audio_path': audio_file.filepath if audio_file else None,
                        'audio_start': segment.start_time,
                        'audio_end': segment.end_time,
                        'tags': item.tags or [],
                        'notes': item.user_notes or ''
                    })
        
        return self.export_from_sentences(sentences, deck_name, output_filename)


# 便捷函数
def export_audio_cards(sentences: List[Dict[str, Any]],
                      output_path: str = "exports/deutsch_audio.apkg",
                      deck_name: str = "德语听力训练") -> str:
    """
    导出音频卡片（便捷函数）
    
    Args:
        sentences: 句子列表
        output_path: 输出路径
        deck_name: 牌组名称
        
    Returns:
        输出文件路径
    """
    output_dir = os.path.dirname(output_path)
    output_filename = os.path.basename(output_path)
    
    exporter = AudioBasedExporter(output_dir)
    return exporter.export_from_sentences(sentences, deck_name, output_filename)


# 测试函数
def test_export():
    """测试导出功能"""
    test_sentences = [
        {
            'german_text': 'Hallo, wie geht es Ihnen?',
            'chinese_text': '你好，您好吗？',
            'audio_path': None,
            'tags': ['问候', '日常'],
            'notes': '正式场合使用'
        },
        {
            'german_text': 'Das Wetter ist heute sehr schön.',
            'chinese_text': '今天天气很好。',
            'audio_path': None,
            'tags': ['天气'],
            'notes': ''
        },
        {
            'german_text': 'Ich möchte ein Glas Wasser, bitte.',
            'chinese_text': '请给我一杯水。',
            'audio_path': None,
            'tags': ['餐厅', '点餐'],
            'notes': '餐厅常用句'
        }
    ]
    
    output = export_audio_cards(test_sentences)
    print(f"测试导出完成: {output}")


if __name__ == "__main__":
    test_export()