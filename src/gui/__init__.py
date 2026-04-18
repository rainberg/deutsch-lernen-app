"""
GUI用户界面包
包含PyQt5界面组件和主窗口
"""

from .main_window import MainWindow
from .audio_player import AudioPlayerWidget, AudioPlayerDialog
from .text_display import BilingualTextDisplay, ClickableTextEdit, SentenceDisplayWidget
from .word_detail import WordDetailDialog, QuickWordPopup
from .collection_manager import CollectionManagerWidget

__all__ = [
    # 主窗口
    'MainWindow',
    
    # 音频播放控件
    'AudioPlayerWidget',
    'AudioPlayerDialog',
    
    # 文本显示控件
    'BilingualTextDisplay',
    'ClickableTextEdit',
    'SentenceDisplayWidget',
    
    # 单词详情
    'WordDetailDialog',
    'QuickWordPopup',
    
    # 收藏管理
    'CollectionManagerWidget',
]

def launch_application():
    """启动应用程序"""
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
    return app.exec_()