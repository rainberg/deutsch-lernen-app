"""
Anki导出模块
将收藏的句子和单词导出为Anki牌组
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import json

import genanki

logger = logging.getLogger(__name__)

@dataclass
class AnkiCard:
    """Anki卡片数据"""
    front: str  # 卡片正面（德语例句）
    back: str  # 卡片背面（中文翻译+解释）
    audio_path: Optional[str] = None  # 音频文件路径
    tags: List[str] = None  # 标签
    guid: Optional[str] = None  # 唯一标识符
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.guid is None:
            self.guid = str(uuid.uuid4())

@dataclass
class AnkiDeck:
    """Anki牌组数据"""
    name: str  # 牌组名称
    cards: List[AnkiCard]  # 卡片列表
    description: str = ""  # 牌组描述

class AnkiExporter:
    """Anki导出器"""
    
    # 自定义卡片模型ID（固定值，确保一致性）
    MODEL_ID = 1607392319
    DECK_ID = 2059400110
    
    def __init__(self, media_dir: Optional[str] = None):
        """
        初始化Anki导出器
        
        Args:
            media_dir: 媒体文件存储目录，如为None则使用临时目录
        """
        self.media_dir = media_dir or tempfile.mkdtemp(prefix="anki_media_")
        os.makedirs(self.media_dir, exist_ok=True)
        
        # 定义卡片模型
        self.model = self._create_card_model()
        
        logger.info(f"Anki导出器初始化完成，媒体目录: {self.media_dir}")
    
    def _create_card_model(self) -> genanki.Model:
        """创建Anki卡片模型"""
        
        # 卡片模板 - 正面（德语例句+音频）
        front_template = """
<div class="card german-card">
    <div class="sentence">{{Deutsch}}</div>
    
    {{#Audio}}
    <div class="audio-player">
        [sound:{{Audio}}]
        <button onclick="playAudio('{{Audio}}')">▶ 播放音频</button>
    </div>
    {{/Audio}}
    
    <div class="hint">点击显示翻译和解释</div>
</div>

<script>
function playAudio(filename) {
    var audio = new Audio(filename);
    audio.play();
}
</script>
"""
        
        # 卡片模板 - 背面（中文翻译+单词解释）
        back_template = """
<div class="card chinese-card">
    <div class="translation">{{Chinesisch}}</div>
    
    {{#Audio}}
    <div class="audio-player">
        [sound:{{Audio}}]
        <button onclick="playAudio('{{Audio}}')">▶ 播放音频</button>
    </div>
    {{/Audio}}
    
    {{#Wörter}}
    <div class="word-explanations">
        <h3>单词解释：</h3>
        {{Wörter}}
    </div>
    {{/Wörter}}
    
    {{#Notizen}}
    <div class="user-notes">
        <h3>我的笔记：</h3>
        {{Notizen}}
    </div>
    {{/Notizen}}
    
    <div class="tags">
        {{#Tags}}<span class="tag">{{Tags}}</span> {{/Tags}}
    </div>
</div>

<style>
.card {
    font-family: Arial, sans-serif;
    font-size: 18px;
    text-align: center;
    color: black;
    background-color: white;
    padding: 20px;
}

.german-card {
    background-color: #f0f8ff;
}

.chinese-card {
    background-color: #fff8f0;
}

.sentence {
    font-size: 22px;
    font-weight: bold;
    margin-bottom: 20px;
    color: #0066cc;
}

.translation {
    font-size: 20px;
    margin-bottom: 20px;
    color: #cc3300;
}

.audio-player {
    margin: 15px 0;
    padding: 10px;
    background-color: #f5f5f5;
    border-radius: 5px;
}

.audio-player button {
    background-color: #4CAF50;
    color: white;
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.audio-player button:hover {
    background-color: #45a049;
}

.word-explanations, .user-notes {
    text-align: left;
    margin: 20px 0;
    padding: 15px;
    background-color: #f9f9f9;
    border-left: 4px solid #4CAF50;
}

.word-explanations h3, .user-notes h3 {
    margin-top: 0;
    color: #333;
}

.hint {
    font-size: 14px;
    color: #666;
    margin-top: 20px;
    font-style: italic;
}

.tags {
    margin-top: 20px;
}

.tag {
    display: inline-block;
    background-color: #e0e0e0;
    padding: 4px 8px;
    margin: 2px;
    border-radius: 3px;
    font-size: 12px;
}
</style>
"""
        
        # 字段定义
        fields = [
            {'name': 'Deutsch'},      # 德语例句
            {'name': 'Chinesisch'},   # 中文翻译
            {'name': 'Audio'},        # 音频文件名
            {'name': 'Wörter'},       # 单词解释（HTML格式）
            {'name': 'Notizen'},      # 用户笔记
            {'name': 'Tags'},         # 标签（逗号分隔）
        ]
        
        # 创建模型
        model = genanki.Model(
            self.MODEL_ID,
            'Deutsch Lernen Model',
            fields=fields,
            templates=[
                {
                    'name': 'Deutsch → Chinesisch',
                    'qfmt': front_template,
                    'afmt': back_template,
                },
            ],
            css='''
.card {
    font-family: arial;
    font-size: 20px;
    text-align: center;
    color: black;
    background-color: white;
}
'''
        )
        
        return model
    
    def export_deck(self, deck: AnkiDeck, output_path: str) -> str:
        """
        导出牌组到文件
        
        Args:
            deck: Anki牌组数据
            output_path: 输出文件路径（.apkg）
            
        Returns:
            输出文件路径
        """
        logger.info(f"开始导出Anki牌组: {deck.name}, 卡片数: {len(deck.cards)}")
        
        try:
            # 创建Anki牌组
            anki_deck = genanki.Deck(
                self.DECK_ID + hash(deck.name) % 1000000,  # 唯一ID
                deck.name
            )
            
            # 添加描述
            anki_deck.description = deck.description
            
            # 收集媒体文件
            media_files = []
            
            # 添加卡片到牌组
            for card in deck.cards:
                # 准备字段数据
                fields = self._prepare_card_fields(card)
                
                # 创建笔记
                note = genanki.Note(
                    model=self.model,
                    fields=fields,
                    tags=card.tags,
                    guid=card.guid
                )
                
                anki_deck.add_note(note)
                
                # 添加音频文件到媒体列表
                if card.audio_path and os.path.exists(card.audio_path):
                    audio_filename = os.path.basename(card.audio_path)
                    media_files.append(card.audio_path)
            
            # 创建牌组包
            package = genanki.Package(anki_deck)
            
            # 添加媒体文件
            if media_files:
                package.media_files = media_files
            
            # 保存到文件
            package.write_to_file(output_path)
            
            logger.info(f"Anki牌组导出成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"导出Anki牌组失败: {e}")
            raise RuntimeError(f"导出Anki牌组失败: {e}")
    
    def _prepare_card_fields(self, card: AnkiCard) -> List[str]:
        """
        准备卡片字段数据
        
        Args:
            card: Anki卡片数据
            
        Returns:
            字段值列表（顺序与模型定义一致）
        """
        # 提取音频文件名
        audio_field = ""
        if card.audio_path and os.path.exists(card.audio_path):
            audio_filename = os.path.basename(card.audio_path)
            audio_field = audio_filename
        
        # 字段顺序: [Deutsch, Chinesisch, Audio, Wörter, Notizen, Tags]
        fields = [
            card.front,                    # Deutsch
            card.back.split('---')[0] if '---' in card.back else card.back,  # Chinesisch (取第一部分)
            audio_field,                   # Audio
            self._extract_word_explanations(card.back),  # Wörter
            self._extract_user_notes(card.back),  # Notizen
            ','.join(card.tags) if card.tags else ''  # Tags
        ]
        
        return fields
    
    def _extract_word_explanations(self, back_text: str) -> str:
        """从背面文本中提取单词解释"""
        # 简单的文本解析，假设单词解释在"单词解释："之后
        import re
        
        # 查找单词解释部分
        word_section = ""
        
        # 尝试不同的模式
        patterns = [
            r'单词解释[：:]\s*(.*?)(?:\n\n|\n---|\n我的笔记|$)',
            r'单词[：:]\s*(.*?)(?:\n\n|\n---|\n我的笔记|$)',
            r'Wörter[：:]\s*(.*?)(?:\n\n|\n---|\n我的笔记|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, back_text, re.DOTALL | re.IGNORECASE)
            if match:
                word_section = match.group(1).strip()
                break
        
        if word_section:
            # 转换为HTML格式
            lines = word_section.split('\n')
            html_lines = []
            for line in lines:
                line = line.strip()
                if line:
                    if '：' in line or ':' in line:
                        # 可能是"单词：解释"格式
                        html_lines.append(f'<div class="word-line">{line}</div>')
                    else:
                        html_lines.append(f'<div>{line}</div>')
            
            return '<br>'.join(html_lines)
        
        return ""
    
    def _extract_user_notes(self, back_text: str) -> str:
        """从背面文本中提取用户笔记"""
        import re
        
        # 查找用户笔记部分
        notes_section = ""
        
        patterns = [
            r'我的笔记[：:]\s*(.*?)(?:\n\n|\n---|\n标签|$)',
            r'Notizen[：:]\s*(.*?)(?:\n\n|\n---|\n标签|$)',
            r'笔记[：:]\s*(.*?)(?:\n\n|\n---|\n标签|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, back_text, re.DOTALL | re.IGNORECASE)
            if match:
                notes_section = match.group(1).strip()
                break
        
        return notes_section
    
    def create_cards_from_sentences(self, sentences: List[Dict[str, Any]], 
                                   audio_dir: Optional[str] = None) -> List[AnkiCard]:
        """
        从句子数据创建Anki卡片
        
        Args:
            sentences: 句子数据列表
            audio_dir: 音频文件目录
            
        Returns:
            Anki卡片列表
        """
        cards = []
        
        for i, sentence in enumerate(sentences):
            try:
                # 提取数据
                german_text = sentence.get('german_text', '')
                chinese_text = sentence.get('chinese_text', '')
                audio_path = sentence.get('audio_path', '')
                word_explanations = sentence.get('word_explanations', [])
                user_notes = sentence.get('user_notes', '')
                tags = sentence.get('tags', [])
                
                if not german_text or not chinese_text:
                    logger.warning(f"句子{i}缺少必要数据，跳过")
                    continue
                
                # 构建卡片正面（德语）
                front = german_text
                
                # 构建卡片背面（中文+解释）
                back_parts = [chinese_text]
                
                # 添加单词解释
                if word_explanations:
                    back_parts.append("\n---\n")
                    back_parts.append("单词解释：")
                    for word_exp in word_explanations:
                        if isinstance(word_exp, dict):
                            word = word_exp.get('word', '')
                            definition = word_exp.get('definition', '')
                            if word and definition:
                                back_parts.append(f"{word}: {definition}")
                        else:
                            back_parts.append(str(word_exp))
                
                # 添加用户笔记
                if user_notes:
                    back_parts.append("\n---\n")
                    back_parts.append(f"我的笔记：{user_notes}")
                
                back = "\n".join(back_parts)
                
                # 解析音频路径
                actual_audio_path = None
                if audio_path:
                    if audio_dir and not os.path.isabs(audio_path):
                        # 相对路径，转换为绝对路径
                        actual_audio_path = os.path.join(audio_dir, audio_path)
                    else:
                        actual_audio_path = audio_path
                    
                    # 检查文件是否存在
                    if not os.path.exists(actual_audio_path):
                        logger.warning(f"音频文件不存在: {actual_audio_path}")
                        actual_audio_path = None
                
                # 创建卡片
                card = AnkiCard(
                    front=front,
                    back=back,
                    audio_path=actual_audio_path,
                    tags=tags,
                    guid=sentence.get('guid')
                )
                
                cards.append(card)
                
                logger.debug(f"创建卡片 {i+1}/{len(sentences)}: {german_text[:50]}...")
                
            except Exception as e:
                logger.error(f"创建卡片失败（句子{i}）: {e}")
                continue
        
        logger.info(f"成功创建 {len(cards)} 张Anki卡片")
        return cards
    
    def create_deck_from_sentences(self, deck_name: str, sentences: List[Dict[str, Any]], 
                                  description: str = "", audio_dir: Optional[str] = None) -> AnkiDeck:
        """
        从句子数据直接创建牌组
        
        Args:
            deck_name: 牌组名称
            sentences: 句子数据列表
            description: 牌组描述
            audio_dir: 音频文件目录
            
        Returns:
            Anki牌组
        """
        cards = self.create_cards_from_sentences(sentences, audio_dir)
        
        deck = AnkiDeck(
            name=deck_name,
            cards=cards,
            description=description
        )
        
        return deck

# 工具函数
def export_to_anki(sentences: List[Dict[str, Any]], output_path: str, 
                  deck_name: str = "Deutsch Lernen", **kwargs) -> str:
    """
    快速导出函数
    
    Args:
        sentences: 句子数据列表
        output_path: 输出文件路径
        deck_name: 牌组名称
        **kwargs: 传递给AnkiExporter的参数
        
    Returns:
        输出文件路径
    """
    exporter = AnkiExporter(**kwargs)
    deck = exporter.create_deck_from_sentences(deck_name, sentences)
    return exporter.export_deck(deck, output_path)

def validate_anki_deck(apkg_path: str) -> bool:
    """验证Anki牌组文件"""
    if not os.path.exists(apkg_path):
        logger.error(f"文件不存在: {apkg_path}")
        return False
    
    if not apkg_path.endswith('.apkg'):
        logger.error(f"文件扩展名不是.apkg: {apkg_path}")
        return False
    
    file_size = os.path.getsize(apkg_path)
    if file_size < 100:  # 最小文件大小
        logger.error(f"文件大小异常: {file_size}字节")
        return False
    
    logger.info(f"Anki牌组验证通过: {apkg_path} ({file_size}字节)")
    return True