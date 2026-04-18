"""
收藏管理界面
管理收藏的例句和单词
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QTabWidget,
    QGroupBox, QFrame, QSplitter, QMenu, QAction,
    QHeaderView, QTreeWidget, QTreeWidgetItem, QInputDialog,
    QMessageBox, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QIcon

from ..utils.config import get_config
from ..utils.logger import get_logger
from ..data.database import get_db_session
from ..data.repository import (
    get_collected_sentence_repo, get_collected_word_repo,
    get_word_entry_repo
)

logger = get_logger(__name__)

class CollectionManagerWidget(QWidget):
    """收藏管理控件"""
    
    # 定义信号
    sentence_selected = pyqtSignal(dict)  # 句子选中信号
    word_selected = pyqtSignal(dict)  # 单词选中信号
    export_requested = pyqtSignal()  # 导出请求信号
    
    def __init__(self, parent=None):
        """初始化收藏管理控件"""
        super().__init__(parent)
        
        # 获取配置
        self.config = get_config()
        
        # 数据
        self.collected_sentences: List[Dict[str, Any]] = []
        self.collected_words: List[Dict[str, Any]] = []
        
        # 初始化UI
        self._init_ui()
        
        # 加载数据
        self._load_data()
        
        # 定时刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_data)
        self.refresh_timer.start(30000)  # 30秒刷新一次
        
        logger.info("收藏管理控件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 标题
        title_layout = QHBoxLayout()
        
        title_label = QLabel("收藏管理")
        title_label.setProperty("class", "title")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self._refresh_data)
        title_layout.addWidget(refresh_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出到Anki")
        export_btn.clicked.connect(self._export_to_anki)
        title_layout.addWidget(export_btn)
        
        main_layout.addLayout(title_layout)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 收藏句子标签页
        sentences_tab = self._create_sentences_tab()
        self.tab_widget.addTab(sentences_tab, "收藏句子")
        
        # 收藏单词标签页
        words_tab = self._create_words_tab()
        self.tab_widget.addTab(words_tab, "收藏单词")
        
        # 学习进度标签页
        progress_tab = self._create_progress_tab()
        self.tab_widget.addTab(progress_tab, "学习进度")
        
        main_layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("清空收藏")
        clear_btn.setProperty("class", "danger")
        clear_btn.clicked.connect(self._clear_collection)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        main_layout.addLayout(button_layout)
    
    def _create_sentences_tab(self):
        """创建收藏句子标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 分割窗口
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧列表
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 搜索框
        search_layout = QHBoxLayout()
        
        from PyQt5.QtWidgets import QLineEdit
        self.sentence_search = QLineEdit()
        self.sentence_search.setPlaceholderText("搜索收藏句子...")
        self.sentence_search.textChanged.connect(self._search_sentences)
        search_layout.addWidget(self.sentence_search)
        
        left_layout.addLayout(search_layout)
        
        # 句子列表
        self.sentence_list = QListWidget()
        self.sentence_list.itemClicked.connect(self._on_sentence_clicked)
        self.sentence_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sentence_list.customContextMenuRequested.connect(self._show_sentence_context_menu)
        left_layout.addWidget(self.sentence_list)
        
        splitter.addWidget(left_frame)
        
        # 右侧详情
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 德语原文
        german_group = QGroupBox("德语原文")
        german_layout = QVBoxLayout(german_group)
        
        self.sentence_german = QTextEdit()
        self.sentence_german.setReadOnly(True)
        self.sentence_german.setMaximumHeight(100)
        german_layout.addWidget(self.sentence_german)
        
        right_layout.addWidget(german_group)
        
        # 中文翻译
        chinese_group = QGroupBox("中文翻译")
        chinese_layout = QVBoxLayout(chinese_group)
        
        self.sentence_chinese = QTextEdit()
        self.sentence_chinese.setReadOnly(True)
        self.sentence_chinese.setMaximumHeight(100)
        chinese_layout.addWidget(self.sentence_chinese)
        
        right_layout.addWidget(chinese_group)
        
        # 笔记
        notes_group = QGroupBox("学习笔记")
        notes_layout = QVBoxLayout(notes_group)
        
        self.sentence_notes = QTextEdit()
        self.sentence_notes.setPlaceholderText("在这里添加学习笔记...")
        notes_layout.addWidget(self.sentence_notes)
        
        # 保存笔记按钮
        save_notes_btn = QPushButton("保存笔记")
        save_notes_btn.clicked.connect(self._save_sentence_notes)
        notes_layout.addWidget(save_notes_btn)
        
        right_layout.addWidget(notes_group)
        
        # 标签
        tags_group = QGroupBox("标签")
        tags_layout = QVBoxLayout(tags_group)
        
        self.sentence_tags = QTextEdit()
        self.sentence_tags.setMaximumHeight(60)
        self.sentence_tags.setPlaceholderText("输入标签，用逗号分隔...")
        tags_layout.addWidget(self.sentence_tags)
        
        right_layout.addWidget(tags_group)
        
        splitter.addWidget(right_frame)
        
        # 设置分割比例
        splitter.setSizes([300, 300])
        
        layout.addWidget(splitter)
        
        return tab
    
    def _create_words_tab(self):
        """创建收藏单词标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 分割窗口
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧列表
        left_frame = QFrame()
        left_frame.setFrameStyle(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # 搜索框
        search_layout = QHBoxLayout()
        
        from PyQt5.QtWidgets import QLineEdit
        self.word_search = QLineEdit()
        self.word_search.setPlaceholderText("搜索收藏单词...")
        self.word_search.textChanged.connect(self._search_words)
        search_layout.addWidget(self.word_search)
        
        left_layout.addLayout(search_layout)
        
        # 单词列表
        self.word_list = QListWidget()
        self.word_list.itemClicked.connect(self._on_word_clicked)
        self.word_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.word_list.customContextMenuRequested.connect(self._show_word_context_menu)
        left_layout.addWidget(self.word_list)
        
        splitter.addWidget(left_frame)
        
        # 右侧详情
        right_frame = QFrame()
        right_frame.setFrameStyle(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # 单词信息
        word_group = QGroupBox("单词信息")
        word_layout = QVBoxLayout(word_group)
        
        self.word_label = QLabel("")
        self.word_label.setProperty("class", "title")
        self.word_label.setAlignment(Qt.AlignCenter)
        word_layout.addWidget(self.word_label)
        
        self.word_pos = QLabel("")
        word_layout.addWidget(self.word_pos)
        
        right_layout.addWidget(word_group)
        
        # 释义
        definition_group = QGroupBox("释义")
        definition_layout = QVBoxLayout(definition_group)
        
        self.word_definition = QTextEdit()
        self.word_definition.setReadOnly(True)
        definition_layout.addWidget(self.word_definition)
        
        right_layout.addWidget(definition_group)
        
        # 例句
        examples_group = QGroupBox("例句")
        examples_layout = QVBoxLayout(examples_group)
        
        self.word_examples = QTextEdit()
        self.word_examples.setReadOnly(True)
        examples_layout.addWidget(self.word_examples)
        
        right_layout.addWidget(examples_group)
        
        splitter.addWidget(right_frame)
        
        # 设置分割比例
        splitter.setSizes([300, 300])
        
        layout.addWidget(splitter)
        
        return tab
    
    def _create_progress_tab(self):
        """创建学习进度标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 统计信息
        stats_group = QGroupBox("学习统计")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("加载中...")
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(stats_group)
        
        # 复习队列
        review_group = QGroupBox("待复习")
        review_layout = QVBoxLayout(review_group)
        
        self.review_list = QListWidget()
        review_layout.addWidget(self.review_list)
        
        # 开始复习按钮
        start_review_btn = QPushButton("开始复习")
        start_review_btn.clicked.connect(self._start_review)
        review_layout.addWidget(start_review_btn)
        
        layout.addWidget(review_group)
        
        # 学习记录
        history_group = QGroupBox("学习记录")
        history_layout = QVBoxLayout(history_group)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        history_layout.addWidget(self.history_text)
        
        layout.addWidget(history_group)
        
        return tab
    
    def _load_data(self):
        """加载数据"""
        try:
            # 加载收藏句子
            self._load_sentences()
            
            # 加载收藏单词
            self._load_words()
            
            # 更新统计
            self._update_stats()
            
            logger.info("收藏数据加载完成")
            
        except Exception as e:
            logger.error(f"加载收藏数据失败: {e}")
    
    def _load_sentences(self):
        """加载收藏句子"""
        self.sentence_list.clear()
        self.collected_sentences.clear()
        
        try:
            with get_db_session() as session:
                repo = get_collected_sentence_repo()
                sentences = repo.get_recently_collected(session, limit=100)
                
                for sentence in sentences:
                    # 获取关联的转写分段
                    segment = sentence.segment
                    if segment:
                        item_data = {
                            'id': sentence.id,
                            'german_text': segment.german_text,
                            'chinese_text': segment.translation.chinese_text if segment.translation else '',
                            'start_time': segment.start_time,
                            'end_time': segment.end_time,
                            'user_notes': sentence.user_notes,
                            'tags': sentence.tags,
                            'created_at': sentence.created_at
                        }
                        
                        self.collected_sentences.append(item_data)
                        
                        # 添加到列表
                        item = QListWidgetItem(segment.german_text[:50] + "...")
                        item.setData(Qt.UserRole, item_data)
                        self.sentence_list.addItem(item)
                        
        except Exception as e:
            logger.error(f"加载收藏句子失败: {e}")
    
    def _load_words(self):
        """加载收藏单词"""
        self.word_list.clear()
        self.collected_words.clear()
        
        try:
            with get_db_session() as session:
                repo = get_collected_word_repo()
                word_repo = get_word_entry_repo()
                
                # 获取所有收藏单词
                words = repo.get_all(session, limit=100)
                
                for word in words:
                    # 获取单词条目
                    word_entry = word_repo.get_by_id(session, word.word_entry_id)
                    if word_entry:
                        item_data = {
                            'id': word.id,
                            'word': word_entry.word,
                            'part_of_speech': word_entry.part_of_speech,
                            'chinese_definition': word_entry.chinese_definition,
                            'german_definition': word_entry.german_definition,
                            'examples': word_entry.examples,
                            'context': word.context,
                            'created_at': word.created_at
                        }
                        
                        self.collected_words.append(item_data)
                        
                        # 添加到列表
                        item = QListWidgetItem(word_entry.word)
                        item.setData(Qt.UserRole, item_data)
                        self.word_list.addItem(item)
                        
        except Exception as e:
            logger.error(f"加载收藏单词失败: {e}")
    
    def _refresh_data(self):
        """刷新数据"""
        self._load_data()
    
    def _update_stats(self):
        """更新统计信息"""
        sentence_count = len(self.collected_sentences)
        word_count = len(self.collected_words)
        
        stats_text = f"""
        收藏句子: {sentence_count} 句
        收藏单词: {word_count} 个
        今日学习: 0 句子, 0 单词
        本周学习: 0 句子, 0 单词
        """
        
        self.stats_label.setText(stats_text)
    
    def _on_sentence_clicked(self, item):
        """句子点击事件"""
        data = item.data(Qt.UserRole)
        if data:
            # 更新详情显示
            self.sentence_german.setText(data.get('german_text', ''))
            self.sentence_chinese.setText(data.get('chinese_text', ''))
            self.sentence_notes.setText(data.get('user_notes', ''))
            
            tags = data.get('tags', [])
            if tags:
                self.sentence_tags.setText(", ".join(tags))
            
            # 发射信号
            self.sentence_selected.emit(data)
    
    def _on_word_clicked(self, item):
        """单词点击事件"""
        data = item.data(Qt.UserRole)
        if data:
            # 更新详情显示
            self.word_label.setText(data.get('word', ''))
            self.word_pos.setText(f"词性: {data.get('part_of_speech', '未知')}")
            self.word_definition.setText(data.get('chinese_definition', ''))
            
            examples = data.get('examples', [])
            if examples:
                example_text = ""
                for i, ex in enumerate(examples, 1):
                    example_text += f"{i}. {ex.get('german', '')}\n   {ex.get('chinese', '')}\n\n"
                self.word_examples.setText(example_text)
            
            # 发射信号
            self.word_selected.emit(data)
    
    def _search_sentences(self, text):
        """搜索句子"""
        for i in range(self.sentence_list.count()):
            item = self.sentence_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def _search_words(self, text):
        """搜索单词"""
        for i in range(self.word_list.count()):
            item = self.word_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def _show_sentence_context_menu(self, position):
        """显示句子右键菜单"""
        menu = QMenu()
        
        view_action = QAction("查看详情", self)
        view_action.triggered.connect(self._view_sentence_details)
        menu.addAction(view_action)
        
        edit_action = QAction("编辑笔记", self)
        edit_action.triggered.connect(self._edit_sentence_notes)
        menu.addAction(edit_action)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._delete_sentence)
        menu.addAction(delete_action)
        
        menu.exec_(self.sentence_list.mapToGlobal(position))
    
    def _show_word_context_menu(self, position):
        """显示单词右键菜单"""
        menu = QMenu()
        
        view_action = QAction("查看详情", self)
        view_action.triggered.connect(self._view_word_details)
        menu.addAction(view_action)
        
        delete_action = QAction("删除", self)
        delete_action.triggered.connect(self._delete_word)
        menu.addAction(delete_action)
        
        menu.exec_(self.word_list.mapToGlobal(position))
    
    def _save_sentence_notes(self):
        """保存句子笔记"""
        current_item = self.sentence_list.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            if data:
                notes = self.sentence_notes.toPlainText()
                
                try:
                    with get_db_session() as session:
                        repo = get_collected_sentence_repo()
                        repo.update(session, data['id'], user_notes=notes)
                        
                    QMessageBox.information(self, "保存成功", "笔记已保存")
                    logger.info(f"句子笔记已保存: {data['id']}")
                    
                except Exception as e:
                    QMessageBox.critical(self, "保存失败", f"保存失败: {e}")
                    logger.error(f"保存句子笔记失败: {e}")
    
    def _view_sentence_details(self):
        """查看句子详情"""
        current_item = self.sentence_list.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            if data:
                # 这里可以打开详情对话框
                pass
    
    def _edit_sentence_notes(self):
        """编辑句子笔记"""
        current_item = self.sentence_list.currentItem()
        if current_item:
            self.sentence_list.setCurrentItem(current_item)
            self.sentence_notes.setFocus()
    
    def _delete_sentence(self):
        """删除句子"""
        current_item = self.sentence_list.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            if data:
                reply = QMessageBox.question(
                    self, "确认删除",
                    "确定要删除这个收藏句子吗？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        with get_db_session() as session:
                            repo = get_collected_sentence_repo()
                            repo.delete(session, data['id'])
                        
                        # 从列表移除
                        row = self.sentence_list.row(current_item)
                        self.sentence_list.takeItem(row)
                        
                        QMessageBox.information(self, "删除成功", "收藏句子已删除")
                        logger.info(f"收藏句子已删除: {data['id']}")
                        
                    except Exception as e:
                        QMessageBox.critical(self, "删除失败", f"删除失败: {e}")
                        logger.error(f"删除收藏句子失败: {e}")
    
    def _view_word_details(self):
        """查看单词详情"""
        current_item = self.word_list.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            if data:
                # 这里可以打开详情对话框
                pass
    
    def _delete_word(self):
        """删除单词"""
        current_item = self.word_list.currentItem()
        if current_item:
            data = current_item.data(Qt.UserRole)
            if data:
                reply = QMessageBox.question(
                    self, "确认删除",
                    "确定要删除这个收藏单词吗？",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    try:
                        with get_db_session() as session:
                            repo = get_collected_word_repo()
                            repo.delete(session, data['id'])
                        
                        # 从列表移除
                        row = self.word_list.row(current_item)
                        self.word_list.takeItem(row)
                        
                        QMessageBox.information(self, "删除成功", "收藏单词已删除")
                        logger.info(f"收藏单词已删除: {data['id']}")
                        
                    except Exception as e:
                        QMessageBox.critical(self, "删除失败", f"删除失败: {e}")
                        logger.error(f"删除收藏单词失败: {e}")
    
    def _clear_collection(self):
        """清空收藏"""
        reply = QMessageBox.question(
            self, "确认清空",
            "确定要清空所有收藏吗？此操作不可恢复！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with get_db_session() as session:
                    sentence_repo = get_collected_sentence_repo()
                    word_repo = get_collected_word_repo()
                    
                    # 删除所有收藏句子
                    for sentence in self.collected_sentences:
                        sentence_repo.delete(session, sentence['id'])
                    
                    # 删除所有收藏单词
                    for word in self.collected_words:
                        word_repo.delete(session, word['id'])
                
                # 清空列表
                self.sentence_list.clear()
                self.word_list.clear()
                self.collected_sentences.clear()
                self.collected_words.clear()
                
                QMessageBox.information(self, "清空成功", "所有收藏已清空")
                logger.info("所有收藏已清空")
                
            except Exception as e:
                QMessageBox.critical(self, "清空失败", f"清空失败: {e}")
                logger.error(f"清空收藏失败: {e}")
    
    def _export_to_anki(self):
        """导出到Anki"""
        self.export_requested.emit()
        
        # 这里需要实现导出逻辑
        QMessageBox.information(self, "导出", "导出到Anki功能待实现")
    
    def _start_review(self):
        """开始复习"""
        QMessageBox.information(self, "复习", "复习功能待实现")
    
    def add_sentence(self, sentence_data: Dict[str, Any]):
        """添加收藏句子"""
        try:
            with get_db_session() as session:
                repo = get_collected_sentence_repo()
                repo.create(session, **sentence_data)
            
            # 刷新列表
            self._load_sentences()
            
            logger.info(f"收藏句子已添加: {sentence_data}")
            
        except Exception as e:
            logger.error(f"添加收藏句子失败: {e}")
    
    def add_word(self, word_data: Dict[str, Any]):
        """添加收藏单词"""
        try:
            with get_db_session() as session:
                repo = get_collected_word_repo()
                repo.create(session, **word_data)
            
            # 刷新列表
            self._load_words()
            
            logger.info(f"收藏单词已添加: {word_data}")
            
        except Exception as e:
            logger.error(f"添加收藏单词失败: {e}")
    
    def get_sentence_count(self) -> int:
        """获取收藏句子数量"""
        return len(self.collected_sentences)
    
    def get_word_count(self) -> int:
        """获取收藏单词数量"""
        return len(self.collected_words)

# 测试函数
def test_collection_manager():
    """测试收藏管理控件"""
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow
    
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("收藏管理测试")
    window.setMinimumSize(800, 600)
    
    collection_manager = CollectionManagerWidget()
    window.setCentralWidget(collection_manager)
    
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_collection_manager()