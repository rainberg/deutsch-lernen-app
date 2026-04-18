"""
主窗口模块
提供应用程序的主界面
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar, QLabel,
    QFileDialog, QMessageBox, QProgressBar, QDockWidget,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton,
    QGroupBox, QTabWidget, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QTimer, pyqtSignal, QSettings
from PyQt5.QtGui import QIcon, QFont, QKeySequence, QPixmap

from ..utils.config import get_config
from ..utils.logger import get_logger
from ..utils.helpers import format_duration, format_filesize

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """主窗口类"""
    
    # 定义信号
    file_opened = pyqtSignal(str)  # 文件打开信号
    transcription_started = pyqtSignal()  # 转写开始信号
    transcription_completed = pyqtSignal()  # 转写完成信号
    
    def __init__(self, config=None):
        """
        初始化主窗口
        
        Args:
            config: 配置对象
        """
        super().__init__()
        
        # 获取配置
        self.config = config or get_config()
        
        # 初始化UI
        self._init_ui()
        
        # 初始化菜单和工具栏
        self._init_menu()
        self._init_toolbar()
        self._init_statusbar()
        
        # 初始化布局
        self._init_layout()
        
        # 连接信号
        self._connect_signals()
        
        # 加载设置
        self._load_settings()
        
        # 定时器用于更新状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)  # 每秒更新一次
        
        logger.info("主窗口初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 设置窗口标题和大小
        self.setWindowTitle("德语学习助手 - Deutsch Lernen App")
        self.setMinimumSize(1200, 800)
        
        # 设置窗口图标
        # self.setWindowIcon(QIcon("resources/icons/app_icon.png"))
        
        # 设置字体
        font = QFont("Microsoft YaHei", 10)
        self.setFont(font)
        
        # 设置样式
        self._set_style()
    
    def _set_style(self):
        """设置样式表"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        
        QMenuBar {
            background-color: #ffffff;
            border-bottom: 1px solid #ddd;
            padding: 2px;
        }
        
        QMenuBar::item {
            padding: 5px 10px;
            border-radius: 3px;
        }
        
        QMenuBar::item:selected {
            background-color: #e0e0e0;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #ddd;
            padding: 5px;
        }
        
        QMenu::item {
            padding: 5px 20px;
            border-radius: 3px;
        }
        
        QMenu::item:selected {
            background-color: #e0e0e0;
        }
        
        QToolBar {
            background-color: #ffffff;
            border-bottom: 1px solid #ddd;
            padding: 2px;
            spacing: 5px;
        }
        
        QToolButton {
            background-color: transparent;
            border: 1px solid transparent;
            border-radius: 3px;
            padding: 5px;
            margin: 2px;
        }
        
        QToolButton:hover {
            background-color: #e0e0e0;
            border: 1px solid #ccc;
        }
        
        QToolButton:pressed {
            background-color: #d0d0d0;
        }
        
        QStatusBar {
            background-color: #ffffff;
            border-top: 1px solid #ddd;
            padding: 2px;
        }
        
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        
        QTabWidget::pane {
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f0f0f0;
            border: 1px solid #ddd;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 5px 10px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 1px solid #ffffff;
        }
        
        QTabBar::tab:hover {
            background-color: #e0e0e0;
        }
        
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 15px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #45a049;
        }
        
        QPushButton:pressed {
            background-color: #3d8b40;
        }
        
        QPushButton:disabled {
            background-color: #cccccc;
            color: #666666;
        }
        
        QPushButton[class="secondary"] {
            background-color: #2196F3;
        }
        
        QPushButton[class="secondary"]:hover {
            background-color: #1976D2;
        }
        
        QPushButton[class="danger"] {
            background-color: #f44336;
        }
        
        QPushButton[class="danger"]:hover {
            background-color: #d32f2f;
        }
        
        QProgressBar {
            border: 1px solid #ddd;
            border-radius: 5px;
            text-align: center;
            background-color: #f0f0f0;
        }
        
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 4px;
        }
        
        QSplitter::handle {
            background-color: #ddd;
            width: 2px;
            height: 2px;
        }
        
        QSplitter::handle:hover {
            background-color: #4CAF50;
        }
        
        QLabel {
            color: #333333;
        }
        
        QLabel[class="title"] {
            font-size: 16px;
            font-weight: bold;
            color: #2196F3;
        }
        
        QLabel[class="subtitle"] {
            font-size: 12px;
            color: #666666;
        }
        
        QTextEdit {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 5px;
            background-color: #ffffff;
        }
        
        QListWidget {
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #ffffff;
        }
        
        QListWidget::item {
            padding: 5px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        QListWidget::item:selected {
            background-color: #e3f2FD;
            color: #1976D2;
        }
        
        QListWidget::item:hover {
            background-color: #f5f5f5;
        }
        """
        
        self.setStyleSheet(style)
    
    def _init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        # 打开文件
        open_action = QAction("打开音频/视频文件(&O)", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.setStatusTip("打开音频或视频文件进行学习")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        # 最近文件
        recent_menu = file_menu.addMenu("最近文件(&R)")
        self._update_recent_files_menu(recent_menu)
        
        file_menu.addSeparator()
        
        # 导出
        export_action = QAction("导出到Anki(&E)", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setStatusTip("将收藏的句子导出到Anki牌组")
        export_action.triggered.connect(self._export_to_anki)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # 退出
        exit_action = QAction("退出(&X)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 编辑菜单
        edit_menu = menubar.addMenu("编辑(&E)")
        
        # 撤销
        undo_action = QAction("撤销(&U)", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.setStatusTip("撤销上一步操作")
        undo_action.triggered.connect(self._undo)
        edit_menu.addAction(undo_action)
        
        # 重做
        redo_action = QAction("重做(&R)", self)
        redo_action.setShortcut(QKeySequence.Redo)
        redo_action.setStatusTip("重做上一步操作")
        redo_action.triggered.connect(self._redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        # 复制
        copy_action = QAction("复制(&C)", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.setStatusTip("复制选中的文本")
        copy_action.triggered.connect(self._copy)
        edit_menu.addAction(copy_action)
        
        # 粘贴
        paste_action = QAction("粘贴(&P)", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.setStatusTip("粘贴剪贴板内容")
        paste_action.triggered.connect(self._paste)
        edit_menu.addAction(paste_action)
        
        # 视图菜单
        view_menu = menubar.addMenu("视图(&V)")
        
        # 全屏
        fullscreen_action = QAction("全屏(&F)", self)
        fullscreen_action.setShortcut(QKeySequence.FullScreen)
        fullscreen_action.setStatusTip("切换全屏模式")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
        
        view_menu.addSeparator()
        
        # 音频播放器
        audio_player_action = QAction("音频播放器(&A)", self)
        audio_player_action.setCheckable(True)
        audio_player_action.setChecked(True)
        audio_player_action.setStatusTip("显示/隐藏音频播放器")
        audio_player_action.triggered.connect(self._toggle_audio_player)
        view_menu.addAction(audio_player_action)
        
        # 收藏管理
        collection_action = QAction("收藏管理(&C)", self)
        collection_action.setCheckable(True)
        collection_action.setChecked(True)
        collection_action.setStatusTip("显示/隐藏收藏管理面板")
        collection_action.triggered.connect(self._toggle_collection_panel)
        view_menu.addAction(collection_action)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        # 设置
        settings_action = QAction("设置(&S)", self)
        settings_action.setStatusTip("打开设置对话框")
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)
        
        tools_menu.addSeparator()
        
        # 数据库管理
        db_action = QAction("数据库管理(&D)", self)
        db_action.setStatusTip("管理数据库")
        db_action.triggered.connect(self._manage_database)
        tools_menu.addAction(db_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        # 帮助文档
        help_action = QAction("帮助文档(&H)", self)
        help_action.setShortcut(QKeySequence.HelpContents)
        help_action.setStatusTip("打开帮助文档")
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)
        
        help_menu.addSeparator()
        
        # 关于
        about_action = QAction("关于(&A)", self)
        about_action.setStatusTip("关于本应用程序")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _init_toolbar(self):
        """初始化工具栏"""
        toolbar = self.addToolBar("工具栏")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        # 打开文件
        open_btn = QPushButton("打开文件")
        open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(open_btn)
        
        toolbar.addSeparator()
        
        # 转写按钮
        self.transcribe_btn = QPushButton("开始转写")
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.clicked.connect(self._start_transcription)
        toolbar.addWidget(self.transcribe_btn)
        
        # 翻译按钮
        self.translate_btn = QPushButton("翻译")
        self.translate_btn.setEnabled(False)
        self.translate_btn.clicked.connect(self._start_translation)
        toolbar.addWidget(self.translate_btn)
        
        toolbar.addSeparator()
        
        # 收藏按钮
        self.collect_btn = QPushButton("收藏句子")
        self.collect_btn.setEnabled(False)
        self.collect_btn.clicked.connect(self._collect_sentence)
        toolbar.addWidget(self.collect_btn)
        
        # 导出按钮
        export_btn = QPushButton("导出Anki")
        export_btn.clicked.connect(self._export_to_anki)
        toolbar.addWidget(export_btn)
        
        # 弹簧
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        toolbar.addWidget(self.progress_bar)
    
    def _init_statusbar(self):
        """初始化状态栏"""
        self.statusbar = self.statusBar()
        
        # 文件信息
        self.file_label = QLabel("未打开文件")
        self.statusbar.addWidget(self.file_label, 1)
        
        # 音频时长
        self.duration_label = QLabel("")
        self.statusbar.addWidget(self.duration_label)
        
        # 转写状态
        self.transcription_label = QLabel("")
        self.statusbar.addWidget(self.transcription_label)
        
        # 时间显示
        self.time_label = QLabel("")
        self.statusbar.addPermanentWidget(self.time_label)
    
    def _init_layout(self):
        """初始化主布局"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建分割窗口
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧面板 - 收藏管理
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # 中间面板 - 主内容区
        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # 右侧面板 - 单词详情
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # 设置分割比例
        main_splitter.setSizes([250, 700, 250])
        
        main_layout.addWidget(main_splitter)
    
    def _create_left_panel(self):
        """创建左侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 收藏管理组
        collection_group = QGroupBox("收藏管理")
        collection_layout = QVBoxLayout(collection_group)
        
        # 收藏句子列表
        self.collected_list = QListWidget()
        self.collected_list.itemClicked.connect(self._on_collected_item_clicked)
        collection_layout.addWidget(self.collected_list)

        
        # 收藏按钮
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加")
        add_btn.clicked.connect(self._collect_sentence)
        button_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("移除")
        remove_btn.setProperty("class", "danger")
        remove_btn.clicked.connect(self._remove_collected)
        button_layout.addWidget(remove_btn)
        
        collection_layout.addLayout(button_layout)
        
        layout.addWidget(collection_group)
        
        # 最近文件组
        recent_group = QGroupBox("最近文件")
        recent_layout = QVBoxLayout(recent_group)
        
        self.recent_list = QListWidget()
        self.recent_list.itemDoubleClicked.connect(self._on_recent_item_double_clicked)
        recent_layout.addWidget(self.recent_list)
        
        layout.addWidget(recent_group)
        
        return panel
    
    def _create_center_panel(self):
        """创建中间面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 转写结果页
        transcription_tab = self._create_transcription_tab()
        self.tab_widget.addTab(transcription_tab, "转写结果")
        
        # 翻译结果页
        translation_tab = self._create_translation_tab()
        self.tab_widget.addTab(translation_tab, "翻译结果")
        
        layout.addWidget(self.tab_widget)
        
        # 音频播放器（占位）
        audio_frame = QFrame()
        audio_frame.setFrameStyle(QFrame.StyledPanel)
        audio_frame.setMinimumHeight(100)
        audio_layout = QVBoxLayout(audio_frame)
        
        audio_label = QLabel("音频播放器（待实现）")
        audio_label.setAlignment(Qt.AlignCenter)
        audio_layout.addWidget(audio_label)
        
        layout.addWidget(audio_frame)
        
        return panel
    
    def _create_transcription_tab(self):
        """创建转写结果标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 转写文本显示
        self.transcription_text = QTextEdit()
        self.transcription_text.setPlaceholderText("转写结果将在这里显示...")
        self.transcription_text.setReadOnly(True)
        layout.addWidget(self.transcription_text)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("复制文本")
        copy_btn.clicked.connect(self._copy_transcription)
        button_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("保存到文件")
        save_btn.clicked.connect(self._save_transcription)
        button_layout.addWidget(save_btn)

        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return tab
    
    def _create_translation_tab(self):
        """创建翻译结果标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 翻译文本显示
        self.translation_text = QTextEdit()
        self.translation_text.setPlaceholderText("翻译结果将在这里显示...")
        self.translation_text.setReadOnly(True)
        layout.addWidget(self.translation_text)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        copy_btn = QPushButton("复制翻译")
        copy_btn.clicked.connect(self._copy_translation)
        button_layout.addWidget(copy_btn)
        
        save_btn = QPushButton("保存到文件")
        save_btn.clicked.connect(self._save_translation)
        button_layout.addWidget(save_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        return tab
    
    def _create_right_panel(self):
        """创建右侧面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 单词详情组
        word_group = QGroupBox("单词详情")
        word_layout = QVBoxLayout(word_group)
        
        # 单词显示
        self.word_label = QLabel("点击单词查看详情")
        self.word_label.setProperty("class", "title")
        self.word_label.setAlignment(Qt.AlignCenter)
        word_layout.addWidget(self.word_label)
        
        # 词性
        self.pos_label = QLabel("")
        self.pos_label.setAlignment(Qt.AlignCenter)
        word_layout.addWidget(self.pos_label)
        
        # 释义
        self.definition_text = QTextEdit()
        self.definition_text.setMaximumHeight(100)
        self.definition_text.setReadOnly(True)
        word_layout.addWidget(self.definition_text)
        
        # 例句
        self.examples_text = QTextEdit()
        self.examples_text.setMaximumHeight(150)
        self.examples_text.setReadOnly(True)
        word_layout.addWidget(self.examples_text)

        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        add_word_btn = QPushButton("添加到收藏")
        add_word_btn.clicked.connect(self._add_word_to_collection)
        button_layout.addWidget(add_word_btn)
        
        word_layout.addLayout(button_layout)
        
        layout.addWidget(word_group)
        
        # 学习进度组
        progress_group = QGroupBox("学习进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 统计信息
        self.stats_label = QLabel("今日学习: 0 句子, 0 单词")
        progress_layout.addWidget(self.stats_label)
        
        # 进度条
        self.study_progress = QProgressBar()
        self.study_progress.setValue(0)
        progress_layout.addWidget(self.study_progress)
        
        layout.addWidget(progress_group)
        
        # 添加弹性空间
        layout.addStretch()
        
        return panel
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 文件打开信号
        self.file_opened.connect(self._on_file_opened)
        
        # 转写信号
        self.transcription_started.connect(self._on_transcription_started)
        self.transcription_completed.connect(self._on_transcription_completed)
    
    def _load_settings(self):
        """加载设置"""
        settings = QSettings("DeutschLernen", "App")
        
        # 恢复窗口几何
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        # 恢复窗口状态
        state = settings.value("windowState")
        if state:
            self.restoreState(state)
    
    def _save_settings(self):
        """保存设置"""
        settings = QSettings("DeutschLernen", "App")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
    
    def _update_status(self):
        """更新状态栏"""
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(current_time)
    
    def _update_recent_files_menu(self, menu):
        """更新最近文件菜单"""
        menu.clear()
        
        # 从配置获取最近文件
        recent_files = self.config.get("app.recent_files", [])
        
        for file_path in recent_files[:5]:  # 最多显示5个
            if os.path.exists(file_path):
                action = QAction(os.path.basename(file_path), self)
                action.setData(file_path)
                action.triggered.connect(lambda checked, path=file_path: self._open_recent_file(path))
                menu.addAction(action)
        
        if not recent_files:
            menu.addAction("无最近文件").setEnabled(False)
    
    def _on_file_opened(self, file_path: str):
        """文件打开事件处理"""
        # 更新文件标签
        filename = os.path.basename(file_path)
        self.file_label.setText(f"已打开: {filename}")
        
        # 启用按钮
        self.transcribe_btn.setEnabled(True)
        
        # 添加到最近文件
        recent_files = self.config.get("app.recent_files", [])
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        recent_files = recent_files[:10]  # 保留最近10个
        self.config.set("app.recent_files", recent_files)
        self.config.save()
        
        logger.info(f"文件已打开: {file_path}")
    
    def _on_transcription_started(self):
        """转写开始事件处理"""
        self.transcribe_btn.setEnabled(False)
        self.transcribe_btn.setText("转写中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.transcription_label.setText("正在转写...")
    
    def _on_transcription_completed(self):
        """转写完成事件处理"""
        self.transcribe_btn.setEnabled(True)
        self.transcribe_btn.setText("开始转写")
        self.progress_bar.setVisible(False)
        self.transcription_label.setText("转写完成")
        self.translate_btn.setEnabled(True)
    
    def _on_collected_item_clicked(self, item):
        """收藏项点击事件"""
        # 获取选中的收藏句子
        sentence_text = item.text()
        
        # 在转写文本中高亮显示
        # 这里需要实现高亮逻辑
        
        logger.debug(f"选中收藏句子: {sentence_text}")
    
    def _on_recent_item_double_clicked(self, item):
        """最近文件双击事件"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self._open_file(file_path)
    
    # 菜单和工具栏动作实现
    def _open_file(self, file_path=None):
        """打开文件"""
        if file_path is None:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "打开音频/视频文件",
                "",
                "音频文件 (*.mp3 *.wav *.flac *.m4a *.ogg);;视频文件 (*.mp4 *.avi *.mkv *.mov *.wmv);;所有文件 (*.*)"
            )
        
        if file_path:
            self.file_opened.emit(file_path)
    
    def _open_recent_file(self, file_path):
        """打开最近文件"""
        if os.path.exists(file_path):
            self._open_file(file_path)
        else:
            QMessageBox.warning(self, "文件不存在", f"文件不存在: {file_path}")
    
    def _export_to_anki(self):
        """导出到Anki"""
        QMessageBox.information(self, "导出", "导出到Anki功能待实现")
    
    def _undo(self):
        """撤销"""
        # 获取当前焦点部件并执行撤销
        focused = self.focusWidget()
        if hasattr(focused, 'undo'):
            focused.undo()
    
    def _redo(self):
        """重做"""
        focused = self.focusWidget()
        if hasattr(focused, 'redo'):
            focused.redo()
    
    def _copy(self):
        """复制"""
        focused = self.focusWidget()
        if hasattr(focused, 'copy'):
            focused.copy()
    
    def _paste(self):
        """粘贴"""
        focused = self.focusWidget()
        if hasattr(focused, 'paste'):
            focused.paste()
    
    def _toggle_fullscreen(self):
        """切换全屏"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    def _toggle_audio_player(self, checked):
        """切换音频播放器显示"""
        # 实现音频播放器显示/隐藏
        pass
    
    def _toggle_collection_panel(self, checked):
        """切换收藏面板显示"""
        # 实现收藏面板显示/隐藏
        pass
    
    def _open_settings(self):
        """打开设置"""
        QMessageBox.information(self, "设置", "设置对话框待实现")
    
    def _manage_database(self):
        """管理数据库"""
        QMessageBox.information(self, "数据库管理", "数据库管理功能待实现")
    
    def _show_help(self):
        """显示帮助"""
        QMessageBox.information(self, "帮助", "帮助文档待实现")
    
    def _show_about(self):
        """显示关于"""
        about_text = """
        <h2>德语学习助手</h2>
        <p>版本: 0.1.0</p>
        <p>一个用于德语学习的桌面应用程序</p>
        <p>功能:</p>
        <ul>
            <li>音频/视频转写</li>
            <li>德语-中文翻译</li>
            <li>单词查询</li>
            <li>例句收藏</li>
            <li>Anki导出</li>
        </ul>
        """
        QMessageBox.about(self, "关于", about_text)
    
    def _start_transcription(self):
        """开始转写"""
        self.transcription_started.emit()
        # 这里需要调用转写模块
        # 暂时模拟转写完成
        QTimer.singleShot(2000, self.transcription_completed.emit)
    
    def _start_translation(self):
        """开始翻译"""
        QMessageBox.information(self, "翻译", "翻译功能待实现")
    
    def _collect_sentence(self):
        """收藏句子"""
        QMessageBox.information(self, "收藏", "收藏功能待实现")
    
    def _remove_collected(self):
        """移除收藏"""
        current_item = self.collected_list.currentItem()
        if current_item:
            row = self.collected_list.row(current_item)
            self.collected_list.takeItem(row)
    
    def _copy_transcription(self):
        """复制转写文本"""
        self.transcription_text.copy()
    
    def _save_transcription(self):
        """保存转写文本"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存转写文本",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.transcription_text.toPlainText())
                QMessageBox.information(self, "保存成功", f"转写文本已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存失败: {e}")
    
    def _copy_translation(self):
        """复制翻译文本"""
        self.translation_text.copy()
    
    def _save_translation(self):
        """保存翻译文本"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存翻译文本",
            "",
            "文本文件 (*.txt);;所有文件 (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.translation_text.toPlainText())
                QMessageBox.information(self, "保存成功", f"翻译文本已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "保存失败", f"保存失败: {e}")
    
    def _add_word_to_collection(self):
        """添加单词到收藏"""
        QMessageBox.information(self, "收藏单词", "收藏单词功能待实现")
    
    def closeEvent(self, event):
        """关闭事件"""
        # 保存设置
        self._save_settings()
        
        # 停止定时器
        self.status_timer.stop()
        
        # 接受关闭事件
        event.accept()
        
        logger.info("主窗口已关闭")

def main():
    """主函数"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    # 创建应用程序
    app = QApplication(sys.argv)
    app.setApplicationName("德语学习助手")
    app.setApplicationVersion("0.1.0")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()