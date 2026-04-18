"""
文本显示控件
支持双语显示和单词点击功能
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QScrollArea, QFrame, QSizePolicy, QToolTip, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QPoint, QRect
from PyQt5.QtGui import (
    QFont, QTextCursor, QTextCharFormat, QColor, QPalette,
    QTextDocument, QTextBlockFormat, QMouseEvent
)

from ..utils.config import get_config
from ..utils.logger import get_logger
from ..utils.helpers import split_text_into_sentences

logger = get_logger(__name__)

class ClickableTextEdit(QTextEdit):
    """可点击的文本编辑控件"""
    
    # 定义信号
    word_clicked = pyqtSignal(str, QPoint)  # 单词点击信号
    word_hovered = pyqtSignal(str, QPoint)  # 单词悬停信号
    
    def __init__(self, parent=None):
        """初始化可点击文本编辑控件"""
        super().__init__(parent)
        
        # 设置为只读
        self.setReadOnly(True)
        
        # 启用鼠标跟踪
        self.setMouseTracking(True)
        
        # 设置光标样式
        self.viewport().setCursor(Qt.PointingHandCursor)
        
        # 当前悬停的单词
        self.hovered_word = None
        
        # 单词格式
        self.word_format = QTextCharFormat()
        self.word_format.setForeground(QColor("#2196F3"))
        self.word_format.setFontUnderline(True)
        
        # 普通格式
        self.normal_format = QTextCharFormat()
        self.normal_format.setForeground(QColor("#333333"))
        
        # 高亮格式
        self.highlight_format = QTextCharFormat()
        self.highlight_format.setBackground(QColor("#E3F2FD"))
        
        # 当前高亮的单词
        self.highlighted_word = None
        
        logger.debug("可点击文本编辑控件初始化完成")
    
    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        # 获取鼠标位置的单词
        cursor = self.cursorForPosition(event.pos())
        cursor.select(QTextCursor.WordUnderCursor)
        word = cursor.selectedText().strip()
        
        if word and word != self.hovered_word:
            self.hovered_word = word
            self.word_hovered.emit(word, event.globalPos())
            
            # 显示工具提示
            if word:
                QToolTip.showText(event.globalPos(), f"点击查看详情: {word}")
        
        super().mouseMoveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            # 获取点击位置的单词
            cursor = self.cursorForPosition(event.pos())
            cursor.select(QTextCursor.WordUnderCursor)
            word = cursor.selectedText().strip()
            
            if word:
                self.word_clicked.emit(word, event.globalPos())
                
                # 高亮显示单词
                self._highlight_word(word, cursor)
        
        super().mousePressEvent(event)
    
    def _highlight_word(self, word: str, cursor: QTextCursor):
        """高亮显示单词"""
        # 清除之前的高亮
        if self.highlighted_word:
            self._clear_highlight(self.highlighted_word)
        
        # 高亮当前单词
        self.highlighted_word = word
        
        # 查找所有匹配的单词并高亮
        document = self.document()
        cursor = QTextCursor(document)
        
        while not cursor.isNull():
            cursor = document.find(word, cursor)
            if not cursor.isNull():
                cursor.mergeCharFormat(self.highlight_format)
    
    def _clear_highlight(self, word: str):
        """清除高亮"""
        document = self.document()
        cursor = QTextCursor(document)
        
        while not cursor.isNull():
            cursor = document.find(word, cursor)
            if not cursor.isNull():
                cursor.mergeCharFormat(self.normal_format)
    
    def set_word_color(self, color: QColor):
        """设置单词颜色"""
        self.word_format.setForeground(color)
    
    def set_highlight_color(self, color: QColor):
        """设置高亮颜色"""
        self.highlight_format.setBackground(color)

class BilingualTextDisplay(QWidget):
    """双语文本显示控件"""
    
    # 定义信号
    word_clicked = pyqtSignal(str, dict)  # 单词点击信号
    sentence_clicked = pyqtSignal(int, dict)  # 句子点击信号
    
    def __init__(self, parent=None):
        """初始化双语文本显示控件"""
        super().__init__(parent)
        
        # 获取配置
        self.config = get_config()
        
        # 数据
        self.german_sentences: List[Dict[str, Any]] = []
        self.chinese_sentences: List[Dict[str, Any]] = []
        
        # 初始化UI
        self._init_ui()
        
        # 连接信号
        self._connect_signals()
        
        logger.info("双语文本显示控件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_label = QLabel("转写结果")
        title_label.setProperty("class", "title")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 创建分割窗口
        from PyQt5.QtWidgets import QSplitter
        splitter = QSplitter(Qt.Vertical)
        
        # 德语文本区域
        german_frame = QFrame()
        german_frame.setFrameStyle(QFrame.StyledPanel)
        german_layout = QVBoxLayout(german_frame)
        german_layout.setContentsMargins(5, 5, 5, 5)
        
        german_title = QLabel("德语原文")
        german_title.setProperty("class", "subtitle")
        german_layout.addWidget(german_title)
        
        self.german_text = ClickableTextEdit()
        self.german_text.setPlaceholderText("德语转写结果将在这里显示...")
        german_layout.addWidget(self.german_text)
        
        splitter.addWidget(german_frame)
        
        # 中文翻译区域
        chinese_frame = QFrame()
        chinese_frame.setFrameStyle(QFrame.StyledPanel)
        chinese_layout = QVBoxLayout(chinese_frame)
        chinese_layout.setContentsMargins(5, 5, 5, 5)
        
        chinese_title = QLabel("中文翻译")
        chinese_title.setProperty("class", "subtitle")
        chinese_layout.addWidget(chinese_title)
        
        self.chinese_text = QTextEdit()
        self.chinese_text.setPlaceholderText("中文翻译将在这里显示...")
        self.chinese_text.setReadOnly(True)
        chinese_layout.addWidget(self.chinese_text)
        
        splitter.addWidget(chinese_frame)
        
        # 设置分割比例
        splitter.setSizes([200, 200])
        
        main_layout.addWidget(splitter)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        from PyQt5.QtWidgets import QPushButton
        
        copy_btn = QPushButton("复制双语")
        copy_btn.clicked.connect(self._copy_bilingual)
        button_layout.addWidget(copy_btn)
        
        collect_btn = QPushButton("收藏句子")
        collect_btn.clicked.connect(self._collect_sentence)
        button_layout.addWidget(collect_btn)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 德语文本点击信号
        self.german_text.word_clicked.connect(self._on_word_clicked)
        self.german_text.word_hovered.connect(self._on_word_hovered)
    
    def set_german_text(self, text: str):
        """设置德语文本"""
        self.german_text.clear()
        self.german_text.setPlainText(text)
        
        # 格式化文本
        self._format_german_text(text)
    
    def set_chinese_text(self, text: str):
        """设置中文文本"""
        self.chinese_text.clear()
        self.chinese_text.setPlainText(text)
    
    def set_sentences(self, german_sentences: List[Dict], chinese_sentences: List[Dict]):
        """
        设置句子数据
        
        Args:
            german_sentences: 德语句子列表
            chinese_sentences: 中文句子列表
        """
        self.german_sentences = german_sentences
        self.chinese_sentences = chinese_sentences
        
        # 显示文本
        self._display_sentences()
    
    def _format_german_text(self, text: str):
        """格式化德语文本"""
        # 这里可以添加德语语法高亮等功能
        pass
    
    def _display_sentences(self):
        """显示句子"""
        # 清空文本
        self.german_text.clear()
        self.chinese_text.clear()
        
        # 显示德语句子
        german_content = ""
        for i, sentence in enumerate(self.german_sentences):
            german_content += f"{i+1}. {sentence.get('text', '')}\n\n"
        
        self.german_text.setPlainText(german_content)
        
        # 显示中文句子
        chinese_content = ""
        for i, sentence in enumerate(self.chinese_sentences):
            chinese_content += f"{i+1}. {sentence.get('text', '')}\n\n"
        
        self.chinese_text.setPlainText(chinese_content)
    
    def highlight_sentence(self, index: int):
        """高亮显示句子"""
        if 0 <= index < len(self.german_sentences):
            # 高亮德语句子
            sentence = self.german_sentences[index]
            text = sentence.get('text', '')
            
            # 查找并高亮文本
            cursor = self.german_text.textCursor()
            cursor.setPosition(0)
            
            # 这里需要实现更精确的高亮逻辑
            pass
    
    def _on_word_clicked(self, word: str, global_pos: QPoint):
        """单词点击事件处理"""
        # 查找单词信息
        word_info = {
            'word': word,
            'position': global_pos,
            'sentence_index': self._get_sentence_index_for_word(word)
        }
        
        # 发射信号
        self.word_clicked.emit(word, word_info)
        
        logger.debug(f"单词被点击: {word}")
    
    def _on_word_hovered(self, word: str, global_pos: QPoint):
        """单词悬停事件处理"""
        # 可以显示工具提示或预览
        pass
    
    def _get_sentence_index_for_word(self, word: str) -> int:
        """获取单词所在的句子索引"""
        # 简单实现：查找第一个包含该单词的句子
        for i, sentence in enumerate(self.german_sentences):
            if word in sentence.get('text', ''):
                return i
        return -1
    
    def _copy_bilingual(self):
        """复制双语内容"""
        german_text = self.german_text.toPlainText()
        chinese_text = self.chinese_text.toPlainText()
        
        bilingual_text = f"德语:\n{german_text}\n\n中文:\n{chinese_text}"
        
        clipboard = QApplication.clipboard()
        clipboard.setText(bilingual_text)
        
        logger.info("双语内容已复制到剪贴板")
    
    def _collect_sentence(self):
        """收藏当前选中的句子"""
        # 获取选中的文本
        german_cursor = self.german_text.textCursor()
        german_text = german_cursor.selectedText()
        
        if german_text:
            # 这里需要实现收藏逻辑
            logger.info(f"收藏句子: {german_text[:50]}...")
    
    def clear(self):
        """清空内容"""
        self.german_text.clear()
        self.chinese_text.clear()
        self.german_sentences.clear()
        self.chinese_sentences.clear()
    
    def get_german_text(self) -> str:
        """获取德语文本"""
        return self.german_text.toPlainText()
    
    def get_chinese_text(self) -> str:
        """获取中文文本"""
        return self.chinese_text.toPlainText()
    
    def get_selected_german_text(self) -> str:
        """获取选中的德语文本"""
        return self.german_text.textCursor().selectedText()
    
    def get_selected_chinese_text(self) -> str:
        """获取选中的中文文本"""
        return self.chinese_text.textCursor().selectedText()

class SentenceDisplayWidget(QWidget):
    """句子显示控件"""
    
    # 定义信号
    sentence_clicked = pyqtSignal(int)  # 句子点击信号
    word_clicked = pyqtSignal(str, int)  # 单词点击信号
    
    def __init__(self, parent=None):
        """初始化句子显示控件"""
        super().__init__(parent)
        
        # 句子数据
        self.sentences: List[Dict[str, Any]] = []
        
        # 初始化UI
        self._init_ui()
        
        logger.debug("句子显示控件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 内容控件
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.content_widget)
        
        layout.addWidget(scroll_area)
    
    def set_sentences(self, sentences: List[Dict[str, Any]]):
        """设置句子列表"""
        self.sentences = sentences
        self._update_display()
    
    def _update_display(self):
        """更新显示"""
        # 清空现有内容
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 添加句子
        for i, sentence in enumerate(self.sentences):
            sentence_widget = self._create_sentence_widget(i, sentence)
            self.content_layout.addWidget(sentence_widget)
    
    def _create_sentence_widget(self, index: int, sentence: Dict[str, Any]):
        """创建句子控件"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setProperty("class", "sentence-frame")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 句子编号和时间
        header_layout = QHBoxLayout()
        
        index_label = QLabel(f"#{index + 1}")
        index_label.setProperty("class", "sentence-index")
        header_layout.addWidget(index_label)
        
        time_label = QLabel(f"{sentence.get('start_time', 0):.1f}s - {sentence.get('end_time', 0):.1f}s")
        time_label.setProperty("class", "sentence-time")
        header_layout.addWidget(time_label)
        
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 德语文本
        german_text = sentence.get('german_text', '')
        german_label = QLabel(german_text)
        german_label.setWordWrap(True)
        german_label.setProperty("class", "german-text")
        layout.addWidget(german_label)
        
        # 中文翻译
        chinese_text = sentence.get('chinese_text', '')
        if chinese_text:
            chinese_label = QLabel(chinese_text)
            chinese_label.setWordWrap(True)
            chinese_label.setProperty("class", "chinese-text")
            layout.addWidget(chinese_label)
        
        # 点击事件
        frame.mousePressEvent = lambda event, idx=index: self.sentence_clicked.emit(idx)
        
        return frame
    
    def highlight_sentence(self, index: int):
        """高亮显示句子"""
        # 实现高亮逻辑
        pass

# 测试函数
def test_text_display():
    """测试文本显示控件"""
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    # 创建测试窗口
    window = QMainWindow()
    window.setWindowTitle("文本显示控件测试")
    window.setMinimumSize(800, 600)
    
    # 创建双语文本显示控件
    text_display = BilingualTextDisplay()
    
    # 设置测试数据
    german_text = """Hallo, wie geht es Ihnen? Ich bin sehr froh, Sie kennenzulernen.
Das Wetter ist heute sehr schön, nicht wahr?
Können Sie mir bitte helfen? Ich suche die Bibliothek."""
    
    chinese_text = """你好，您好吗？我很高兴认识您。
今天天气很好，不是吗？
您能帮帮我吗？我在找图书馆。"""
    
    text_display.set_german_text(german_text)
    text_display.set_chinese_text(chinese_text)
    
    window.setCentralWidget(text_display)
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_text_display()