"""
单词详情弹窗
显示单词的详细解释、例句和相关信息
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QTabWidget, QWidget, QGroupBox, QScrollArea,
    QFrame, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from ..utils.config import get_config
from ..utils.logger import get_logger
from ..core.word_analyzer import WordAnalyzer, WordInfo, get_word_analyzer

logger = get_logger(__name__)

class WordDetailDialog(QDialog):
    """单词详情对话框"""
    
    # 定义信号
    word_collected = pyqtSignal(str)  # 单词收藏信号
    
    def __init__(self, word: str, parent=None):
        """
        初始化单词详情对话框
        
        Args:
            word: 单词
            parent: 父控件
        """
        super().__init__(parent)
        
        # 单词
        self.word = word
        
        # 获取配置
        self.config = get_config()
        
        # 获取单词分析器
        self.word_analyzer = get_word_analyzer()
        
        # 单词信息
        self.word_info: Optional[WordInfo] = None
        
        # 初始化UI
        self._init_ui()
        
        # 加载单词信息
        self._load_word_info()
        
        logger.info(f"单词详情对话框初始化完成: {word}")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 设置窗口属性
        self.setWindowTitle(f"单词详情 - {self.word}")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 单词标题
        title_layout = QHBoxLayout()
        
        self.word_label = QLabel(self.word)
        self.word_label.setProperty("class", "title")
        self.word_label.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        title_layout.addWidget(self.word_label)
        
        title_layout.addStretch()
        
        # 难度标签
        self.difficulty_label = QLabel("")
        self.difficulty_label.setProperty("class", "subtitle")
        title_layout.addWidget(self.difficulty_label)
        
        main_layout.addLayout(title_layout)
        
        # 词性和基本信息
        info_layout = QHBoxLayout()
        
        self.pos_label = QLabel("")
        self.pos_label.setFont(QFont("Microsoft YaHei", 12))
        info_layout.addWidget(self.pos_label)
        
        info_layout.addStretch()
        
        # 音标（如果有）
        self.phonetic_label = QLabel("")
        self.phonetic_label.setFont(QFont("Microsoft YaHei", 10))
        info_layout.addWidget(self.phonetic_label)
        
        main_layout.addLayout(info_layout)
        
        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 标签页
        self.tab_widget = QTabWidget()
        
        # 释义标签页
        definition_tab = self._create_definition_tab()
        self.tab_widget.addTab(definition_tab, "释义")
        
        # 例句标签页
        examples_tab = self._create_examples_tab()
        self.tab_widget.addTab(examples_tab, "例句")
        
        # 相关词标签页
        related_tab = self._create_related_tab()
        self.tab_widget.addTab(related_tab, "相关词")
        
        main_layout.addWidget(self.tab_widget)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.collect_btn = QPushButton("添加到收藏")
        self.collect_btn.clicked.connect(self._collect_word)
        button_layout.addWidget(self.collect_btn)
        
        self.search_btn = QPushButton("在线查询")
        self.search_btn.setProperty("class", "secondary")
        self.search_btn.clicked.connect(self._search_online)
        button_layout.addWidget(self.search_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("关闭")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(button_layout)
    
    def _create_definition_tab(self):
        """创建释义标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 德语释义组
        german_group = QGroupBox("德语释义")
        german_layout = QVBoxLayout(german_group)
        
        self.german_definition = QTextEdit()
        self.german_definition.setReadOnly(True)
        self.german_definition.setMaximumHeight(80)
        german_layout.addWidget(self.german_definition)
        
        layout.addWidget(german_group)
        
        # 中文释义组
        chinese_group = QGroupBox("中文释义")
        chinese_layout = QVBoxLayout(chinese_group)
        
        self.chinese_definition = QTextEdit()
        self.chinese_definition.setReadOnly(True)
        self.chinese_definition.setMaximumHeight(80)
        chinese_layout.addWidget(self.chinese_definition)
        
        layout.addWidget(chinese_group)
        
        # 英语释义组
        english_group = QGroupBox("English Definition")
        english_layout = QVBoxLayout(english_group)
        
        self.english_definition = QTextEdit()
        self.english_definition.setReadOnly(True)
        self.english_definition.setMaximumHeight(80)
        english_layout.addWidget(self.english_definition)
        
        layout.addWidget(english_group)
        
        layout.addStretch()
        
        return tab
    
    def _create_examples_tab(self):
        """创建例句标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 例句滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # 例句内容控件
        self.examples_widget = QWidget()
        self.examples_layout = QVBoxLayout(self.examples_widget)
        self.examples_layout.setAlignment(Qt.AlignTop)
        
        scroll_area.setWidget(self.examples_widget)
        
        layout.addWidget(scroll_area)
        
        return tab
    
    def _create_related_tab(self):
        """创建相关词标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 同义词组
        synonyms_group = QGroupBox("同义词")
        synonyms_layout = QVBoxLayout(synonyms_group)
        
        self.synonyms_text = QTextEdit()
        self.synonyms_text.setReadOnly(True)
        self.synonyms_text.setMaximumHeight(80)
        synonyms_layout.addWidget(self.synonyms_text)
        
        layout.addWidget(synonyms_group)
        
        # 反义词组
        antonyms_group = QGroupBox("反义词")
        antonyms_layout = QVBoxLayout(antonyms_group)
        
        self.antonyms_text = QTextEdit()
        self.antonyms_text.setReadOnly(True)
        self.antonyms_text.setMaximumHeight(80)
        antonyms_layout.addWidget(self.antonyms_text)
        
        layout.addWidget(antonyms_group)
        
        # 相关词组
        related_group = QGroupBox("相关词")
        related_layout = QVBoxLayout(related_group)
        
        self.related_text = QTextEdit()
        self.related_text.setReadOnly(True)
        self.related_text.setMaximumHeight(80)
        related_layout.addWidget(self.related_text)
        
        layout.addWidget(related_group)
        
        layout.addStretch()
        
        return tab
    
    def _load_word_info(self):
        """加载单词信息"""
        try:
            # 分析单词
            self.word_info = self.word_analyzer.analyze_word(self.word)
            
            if self.word_info:
                self._update_ui()
            else:
                self._show_no_info()
                
        except Exception as e:
            logger.error(f"加载单词信息失败: {e}")
            self._show_error(str(e))
    
    def _update_ui(self):
        """更新UI显示"""
        if not self.word_info:
            return
        
        # 更新标题
        self.word_label.setText(self.word_info.word)
        
        # 更新词性
        if self.word_info.part_of_speech:
            self.pos_label.setText(f"词性: {self.word_info.part_of_speech}")
        
        # 更新难度
        if self.word_info.difficulty_level:
            difficulty_text = self._get_difficulty_text(self.word_info.difficulty_level)
            self.difficulty_label.setText(f"难度: {difficulty_text}")
        
        # 更新释义
        self.german_definition.setText(self.word_info.german_definition or "暂无德语释义")
        self.chinese_definition.setText(self.word_info.chinese_definition or "暂无中文释义")
        self.english_definition.setText(self.word_info.english_definition or "暂无英语释义")
        
        # 更新例句
        self._update_examples()
        
        # 更新相关词
        self._update_related_words()
    
    def _update_examples(self):
        """更新例句显示"""
        # 清空现有例句
        while self.examples_layout.count():
            child = self.examples_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # 添加例句
        if self.word_info and self.word_info.examples:
            for i, example in enumerate(self.word_info.examples):
                example_frame = self._create_example_frame(i + 1, example)
                self.examples_layout.addWidget(example_frame)
        else:
            no_examples_label = QLabel("暂无例句")
            no_examples_label.setAlignment(Qt.AlignCenter)
            self.examples_layout.addWidget(no_examples_label)
    
    def _create_example_frame(self, index: int, example: Dict[str, str]):
        """创建例句框架"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        frame.setProperty("class", "example-frame")
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 例句编号
        index_label = QLabel(f"例句 {index}")
        index_label.setProperty("class", "example-index")
        layout.addWidget(index_label)
        
        # 德语例句
        german_text = example.get('german', '')
        if german_text:
            german_label = QLabel(german_text)
            german_label.setWordWrap(True)
            german_label.setProperty("class", "german-text")
            layout.addWidget(german_label)
        
        # 中文翻译
        chinese_text = example.get('chinese', '')
        if chinese_text:
            chinese_label = QLabel(chinese_text)
            chinese_label.setWordWrap(True)
            chinese_label.setProperty("class", "chinese-text")
            layout.addWidget(chinese_label)
        
        return frame
    
    def _update_related_words(self):
        """更新相关词显示"""
        if not self.word_info:
            return
        
        # 同义词
        synonyms = self.word_info.synonyms or []
        self.synonyms_text.setText(", ".join(synonyms) if synonyms else "暂无同义词")
        
        # 反义词
        antonyms = self.word_info.antonyms or []
        self.antonyms_text.setText(", ".join(antonyms) if antonyms else "暂无反义词")
        
        # 相关词
        related = self.word_info.related_words or []
        self.related_text.setText(", ".join(related) if related else "暂无相关词")
    
    def _get_difficulty_text(self, level: int) -> str:
        """获取难度文本"""
        difficulty_map = {
            1: "入门",
            2: "初级",
            3: "中级",
            4: "高级",
            5: "精通"
        }
        return difficulty_map.get(level, "未知")
    
    def _show_no_info(self):
        """显示无信息提示"""
        self.word_label.setText(self.word)
        self.pos_label.setText("词性: 未知")
        self.difficulty_label.setText("难度: 未知")
        self.german_definition.setText("暂无释义")
        self.chinese_definition.setText("暂无释义")
        self.english_definition.setText("暂无释义")
    
    def _show_error(self, error_msg: str):
        """显示错误信息"""
        self.word_label.setText(self.word)
        self.pos_label.setText(f"加载失败: {error_msg}")
    
    def _collect_word(self):
        """收藏单词"""
        self.word_collected.emit(self.word)
        self.collect_btn.setText("已收藏")
        self.collect_btn.setEnabled(False)
        logger.info(f"单词已收藏: {self.word}")
    
    def _search_online(self):
        """在线查询"""
        # 构建查询URL
        search_url = f"https://translate.google.com/?sl=de&tl=zh-CN&text={self.word}"
        
        # 打开浏览器
        import webbrowser
        webbrowser.open(search_url)
        
        logger.info(f"在线查询: {self.word}")
    
    def set_word(self, word: str):
        """设置单词"""
        self.word = word
        self.setWindowTitle(f"单词详情 - {word}")
        self._load_word_info()
    
    def get_word(self) -> str:
        """获取当前单词"""
        return self.word

class QuickWordPopup(QWidget):
    """快速单词弹出窗口"""
    
    # 定义信号
    word_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """初始化快速单词弹出窗口"""
        super().__init__(parent)
        
        # 设置窗口属性
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 初始化UI
        self._init_ui()
        
        logger.debug("快速单词弹出窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 内容框架
        self.content_frame = QFrame()
        self.content_frame.setFrameStyle(QFrame.StyledPanel)
        self.content_frame.setProperty("class", "popup-frame")
        
        content_layout = QVBoxLayout(self.content_frame)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # 单词标签
        self.word_label = QLabel("")
        self.word_label.setProperty("class", "popup-word")
        content_layout.addWidget(self.word_label)
        
        # 释义标签
        self.definition_label = QLabel("")
        self.definition_label.setWordWrap(True)
        self.definition_label.setProperty("class", "popup-definition")
        content_layout.addWidget(self.definition_label)
        
        # 点击提示
        self.hint_label = QLabel("点击查看详情")
        self.hint_label.setProperty("class", "popup-hint")
        content_layout.addWidget(self.hint_label)
        
        layout.addWidget(self.content_frame)
    
    def show_popup(self, word: str, definition: str, position: QPoint):
        """
        显示弹出窗口
        
        Args:
            word: 单词
            definition: 释义
            position: 显示位置
        """
        # 更新内容
        self.word_label.setText(word)
        self.definition_label.setText(definition)
        
        # 调整大小
        self.adjustSize()
        
        # 移动到指定位置
        self.move(position)
        
        # 显示
        self.show()
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            word = self.word_label.text()
            self.word_clicked.emit(word)
            self.close()
        
        super().mousePressEvent(event)

# 测试函数
def test_word_detail():
    """测试单词详情对话框"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 测试单词
    test_words = ["Hallo", "danke", "gut", "Wasser"]
    
    for word in test_words:
        dialog = WordDetailDialog(word)
        dialog.exec_()
    
    sys.exit(0)

if __name__ == "__main__":
    test_word_detail()