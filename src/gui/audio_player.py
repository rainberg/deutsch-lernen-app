"""
音频播放控件
提供音频播放、暂停、进度显示等功能
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QStyle, QSizePolicy, QFrame, QGroupBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtGui import QFont, QIcon

from ..utils.config import get_config
from ..utils.logger import get_logger
from ..utils.helpers import format_duration

logger = get_logger(__name__)

class AudioPlayerWidget(QWidget):
    """音频播放控件"""
    
    # 定义信号
    position_changed = pyqtSignal(int)  # 位置变化信号
    duration_changed = pyqtSignal(int)  # 时长变化信号
    state_changed = pyqtSignal(int)  # 状态变化信号
    playback_finished = pyqtSignal()  # 播放完成信号
    
    def __init__(self, parent=None):
        """
        初始化音频播放控件
        
        Args:
            parent: 父控件
        """
        super().__init__(parent)
        
        # 获取配置
        self.config = get_config()
        
        # 初始化播放器
        self.player = QMediaPlayer()
        
        # 当前文件路径
        self.current_file = None
        
        # 初始化UI
        self._init_ui()
        
        # 连接信号
        self._connect_signals()
        
        # 定时器用于更新进度
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_progress)
        self.update_timer.start(100)  # 每100ms更新一次
        
        logger.info("音频播放控件初始化完成")
    
    def _init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # 文件信息组
        info_group = QGroupBox("音频信息")
        info_layout = QVBoxLayout(info_group)
        
        # 文件名
        self.file_label = QLabel("未加载文件")
        self.file_label.setProperty("class", "title")
        self.file_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.file_label)
        
        # 时长和格式信息
        details_layout = QHBoxLayout()
        
        self.duration_label = QLabel("时长: 00:00")
        details_layout.addWidget(self.duration_label)
        
        self.format_label = QLabel("格式: -")
        details_layout.addWidget(self.format_label)
        
        self.size_label = QLabel("大小: -")
        details_layout.addWidget(self.size_label)
        
        info_layout.addLayout(details_layout)
        
        main_layout.addWidget(info_group)
        
        # 进度组
        progress_group = QGroupBox("播放进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 时间显示
        time_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("00:00")
        time_layout.addWidget(self.current_time_label)
        
        time_layout.addStretch()
        
        self.total_time_label = QLabel("00:00")
        time_layout.addWidget(self.total_time_label)
        
        progress_layout.addLayout(time_layout)
        
        # 进度滑块
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setMinimum(0)
        self.progress_slider.setMaximum(1000)
        self.progress_slider.setValue(0)
        self.progress_slider.sliderMoved.connect(self._on_slider_moved)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        progress_layout.addWidget(self.progress_slider)
        
        main_layout.addWidget(progress_group)
        
        # 控制组
        control_group = QGroupBox("播放控制")
        control_layout = QVBoxLayout(control_group)
        
        # 播放控制按钮
        button_layout = QHBoxLayout()
        
        # 后退按钮
        self.backward_btn = QPushButton("<<")
        self.backward_btn.setMaximumWidth(50)
        self.backward_btn.clicked.connect(self._backward)
        button_layout.addWidget(self.backward_btn)
        
        # 播放/暂停按钮
        self.play_btn = QPushButton("播放")
        self.play_btn.setMinimumWidth(80)
        self.play_btn.clicked.connect(self._toggle_playback)
        button_layout.addWidget(self.play_btn)
        
        # 停止按钮
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setMaximumWidth(50)
        self.stop_btn.clicked.connect(self._stop)
        button_layout.addWidget(self.stop_btn)
        
        # 前进按钮
        self.forward_btn = QPushButton(">>")
        self.forward_btn.setMaximumWidth(50)
        self.forward_btn.clicked.connect(self._forward)
        button_layout.addWidget(self.forward_btn)
        
        control_layout.addLayout(button_layout)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        
        volume_label = QLabel("音量:")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_value_label = QLabel("80%")
        self.volume_value_label.setMinimumWidth(40)
        volume_layout.addWidget(self.volume_value_label)
        
        control_layout.addLayout(volume_layout)
        
        # 播放速度控制
        speed_layout = QHBoxLayout()
        
        speed_label = QLabel("速度:")
        speed_layout.addWidget(speed_label)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(25)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_value_label = QLabel("1.0x")
        self.speed_value_label.setMinimumWidth(40)
        speed_layout.addWidget(self.speed_value_label)
        
        control_layout.addLayout(speed_layout)
        
        main_layout.addWidget(control_group)
        
        # 设置初始状态
        self._update_button_states()
    
    def _connect_signals(self):
        """连接信号和槽"""
        # 播放器信号
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.stateChanged.connect(self._on_state_changed)
        self.player.mediaStatusChanged.connect(self._on_media_status_changed)
    
    def load_file(self, file_path: str) -> bool:
        """
        加载音频文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否加载成功
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"文件不存在: {file_path}")
                return False
            
            # 检查文件格式
            supported_formats = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma']
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext not in supported_formats:
                logger.warning(f"不支持的音频格式: {file_ext}")
                return False
            
            # 创建媒体内容
            media_content = QMediaContent(QUrl.fromLocalFile(file_path))
            
            # 设置媒体
            self.player.setMedia(media_content)
            
            # 更新当前文件
            self.current_file = file_path
            
            # 更新UI
            self._update_file_info(file_path)
            
            logger.info(f"音频文件已加载: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"加载音频文件失败: {e}")
            return False
    
    def _update_file_info(self, file_path: str):
        """更新文件信息显示"""
        filename = os.path.basename(file_path)
        self.file_label.setText(filename)
        
        # 获取文件信息
        file_size = os.path.getsize(file_path)
        from ..utils.helpers import format_filesize
        self.size_label.setText(f"大小: {format_filesize(file_size)}")
        
        # 格式
        file_ext = os.path.splitext(file_path)[1].lower()
        self.format_label.setText(f"格式: {file_ext[1:].upper()}")
    
    def play(self):
        """播放"""
        if self.player.mediaStatus() == QMediaPlayer.NoMedia:
            logger.warning("没有加载音频文件")
            return
        
        self.player.play()
        logger.debug("开始播放")
    
    def pause(self):
        """暂停"""
        self.player.pause()
        logger.debug("暂停播放")
    
    def stop(self):
        """停止"""
        self.player.stop()
        logger.debug("停止播放")
    
    def set_position(self, position: int):
        """
        设置播放位置
        
        Args:
            position: 位置（毫秒）
        """
        self.player.setPosition(position)
    
    def set_volume(self, volume: int):
        """
        设置音量
        
        Args:
            volume: 音量 (0-100)
        """
        self.player.setVolume(volume)
        self.volume_slider.setValue(volume)
        self.volume_value_label.setText(f"{volume}%")
    
    def set_playback_rate(self, rate: float):
        """
        设置播放速度
        
        Args:
            rate: 播放速度 (0.25-2.0)
        """
        from PyQt5.QtMultimedia import QMediaPlayer
        self.player.setPlaybackRate(rate)
        self.speed_slider.setValue(int(rate * 100))
        self.speed_value_label.setText(f"{rate:.1f}x")
    
    def get_position(self) -> int:
        """
        获取当前播放位置
        
        Returns:
            位置（毫秒）
        """
        return self.player.position()
    
    def get_duration(self) -> int:
        """
        获取音频总时长
        
        Returns:
            时长（毫秒）
        """
        return self.player.duration()
    
    def get_state(self) -> QMediaPlayer.State:
        """
        获取播放状态
        
        Returns:
            播放状态
        """
        return self.player.state()
    
    def is_playing(self) -> bool:
        """
        是否正在播放
        
        Returns:
            是否正在播放
        """
        return self.player.state() == QMediaPlayer.PlayingState
    
    def is_paused(self) -> bool:
        """
        是否已暂停
        
        Returns:
            是否已暂停
        """
        return self.player.state() == QMediaPlayer.PausedState
    
    def is_stopped(self) -> bool:
        """
        是否已停止
        
        Returns:
            是否已停止
        """
        return self.player.state() == QMediaPlayer.StoppedState
    
    def seek_forward(self, milliseconds: int = 5000):
        """
        快进
        
        Args:
            milliseconds: 快进毫秒数
        """
        current_pos = self.player.position()
        new_pos = min(current_pos + milliseconds, self.player.duration())
        self.player.setPosition(new_pos)
    
    def seek_backward(self, milliseconds: int = 5000):
        """
        快退
        
        Args:
            milliseconds: 快退毫秒数
        """
        current_pos = self.player.position()
        new_pos = max(current_pos - milliseconds, 0)
        self.player.setPosition(new_pos)
    
    def _toggle_playback(self):
        """切换播放/暂停"""
        if self.player.state() == QMediaPlayer.PlayingState:
            self.pause()
        else:
            self.play()
    
    def _stop(self):
        """停止播放"""
        self.stop()
    
    def _forward(self):
        """快进"""
        self.seek_forward()
    
    def _backward(self):
        """快退"""
        self.seek_backward()
    
    def _on_slider_moved(self, position):
        """滑块移动事件"""
        # 将滑块位置转换为音频位置
        duration = self.player.duration()
        if duration > 0:
            audio_pos = int((position / 1000) * duration)
            self.player.setPosition(audio_pos)
    
    def _on_slider_pressed(self):
        """滑块按下事件"""
        # 暂停更新进度
        self.update_timer.stop()
    
    def _on_slider_released(self):
        """滑块释放事件"""
        # 恢复更新进度
        self.update_timer.start(100)
    
    def _on_volume_changed(self, volume):
        """音量变化事件"""
        self.player.setVolume(volume)
        self.volume_value_label.setText(f"{volume}%")
    
    def _on_speed_changed(self, speed):
        """速度变化事件"""
        rate = speed / 100.0
        self.player.setPlaybackRate(rate)
        self.speed_value_label.setText(f"{rate:.1f}x")
    
    def _on_position_changed(self, position):
        """位置变化事件"""
        # 更新当前时间显示
        self.current_time_label.setText(format_duration(position / 1000))
        
        # 更新进度滑块
        duration = self.player.duration()
        if duration > 0:
            slider_pos = int((position / duration) * 1000)
            self.progress_slider.setValue(slider_pos)
        
        # 发射信号
        self.position_changed.emit(position)
    
    def _on_duration_changed(self, duration):
        """时长变化事件"""
        # 更新总时长显示
        self.total_time_label.setText(format_duration(duration / 1000))
        self.duration_label.setText(f"时长: {format_duration(duration / 1000)}")
        
        # 发射信号
        self.duration_changed.emit(duration)
    
    def _on_state_changed(self, state):
        """状态变化事件"""
        self._update_button_states()
        self.state_changed.emit(state)
    
    def _on_media_status_changed(self, status):
        """媒体状态变化事件"""
        if status == QMediaPlayer.EndOfMedia:
            # 播放完成
            self.playback_finished.emit()
            logger.debug("音频播放完成")
    
    def _update_progress(self):
        """更新进度显示"""
        if self.player.state() == QMediaPlayer.PlayingState:
            # 更新已在_on_position_changed中处理
            pass
    
    def _update_button_states(self):
        """更新按钮状态"""
        state = self.player.state()
        
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setText("暂停")
            self.play_btn.setProperty("class", "secondary")
        else:
            self.play_btn.setText("播放")
            self.play_btn.setProperty("class", "")
        
        # 刷新样式
        self.play_btn.style().unpolish(self.play_btn)
        self.play_btn.style().polish(self.play_btn)
    
    def clear(self):
        """清空播放器"""
        self.player.setMedia(QMediaContent())
        self.current_file = None
        self.file_label.setText("未加载文件")
        self.duration_label.setText("时长: 00:00")
        self.format_label.setText("格式: -")
        self.size_label.setText("大小: -")
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self.progress_slider.setValue(0)
        logger.debug("播放器已清空")
    
    def closeEvent(self, event):
        """关闭事件"""
        self.stop()
        self.update_timer.stop()
        event.accept()

class AudioPlayerDialog(QWidget):
    """音频播放器对话框"""
    
    def __init__(self, parent=None):
        """初始化对话框"""
        super().__init__(parent)
        self.setWindowTitle("音频播放器")
        self.setMinimumSize(400, 300)
        
        # 创建播放器控件
        self.player_widget = AudioPlayerWidget(self)
        
        # 布局
        layout = QVBoxLayout(self)
        layout.addWidget(self.player_widget)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        load_btn = QPushButton("加载文件")
        load_btn.clicked.connect(self._load_file)
        button_layout.addWidget(load_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_file(self):
        """加载文件"""
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "打开音频文件",
            "",
            "音频文件 (*.mp3 *.wav *.flac *.m4a *.ogg);;所有文件 (*.*)"
        )
        
        if file_path:
            self.player_widget.load_file(file_path)

# 测试函数
def test_audio_player():
    """测试音频播放器"""
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    window = AudioPlayerDialog()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_audio_player()