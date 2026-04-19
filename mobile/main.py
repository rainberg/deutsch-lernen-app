"""
德语学习助手 v1.2
- 中文字体：用 Android 系统 DroidSansFallback（不需要打包字体）
- 音频播放：用 Android 原生 MediaPlayer（支持所有格式）
- 文件选择：Android SAF Intent
"""

import os
os.environ['KIVY_LOG_MODE'] = 'MIXED'

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
import threading
import time

IS_ANDROID = platform == 'android'

# ── 字体：优先系统字体，兜底打包的字体 ──
FONT_NAME = 'ChineseFont'
FONT_PATH_PACKAGED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'ChineseSubset.ttf')
# Android 系统中文字体路径
ANDROID_SYSTEM_FONTS = [
    '/system/fonts/DroidSansFallback.ttf',
    '/system/fonts/NotoSansCJK-Regular.ttc',
    '/system/fonts/NotoSansSC-Regular.otf',
]

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: dp(15)
    spacing: dp(10)

    # 标题
    Label:
        text: '德语学习助手'
        font_name: "''' + FONT_NAME + '''"
        font_size: '24sp'
        bold: True
        size_hint_y: None
        height: dp(50)
        color: 0.15, 0.45, 0.7, 1

    # 选择文件按钮
    Button:
        id: btn_select
        text: '选择音频文件'
        font_name: "''' + FONT_NAME + '''"
        font_size: '16sp'
        size_hint_y: None
        height: dp(50)
        background_color: 0.2, 0.7, 0.3, 1
        on_press: app.select_file()

    # 文件名
    Label:
        id: lbl_file
        text: '未选择文件'
        font_name: "''' + FONT_NAME + '''"
        font_size: '13sp'
        size_hint_y: None
        height: dp(30)
        color: 0.4, 0.4, 0.4, 1

    # 播放器区域
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(5)

        Slider:
            id: slider
            size_hint_y: None
            height: dp(30)
            min: 0
            max: 100
            value: 0

        Label:
            id: lbl_time
            text: '0:00 / 0:00'
            font_name: "''' + FONT_NAME + '''"
            size_hint_y: None
            height: dp(25)
            color: 0.3, 0.3, 0.3, 1

        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)

            Button:
                id: btn_play
                text: '播放'
                font_name: "''' + FONT_NAME + '''"
                font_size: '16sp'
                on_press: app.toggle_play()
                disabled: True
                background_color: 0.2, 0.6, 0.8, 1

            Button:
                text: '停止'
                font_name: "''' + FONT_NAME + '''"
                font_size: '16sp'
                on_press: app.stop_audio()
                background_color: 0.5, 0.5, 0.5, 1

    # 测试按钮：验证字体
    Button:
        text: '字体测试: 德语学习助手 äöüß'
        font_name: "''' + FONT_NAME + '''"
        font_size: '14sp'
        size_hint_y: None
        height: dp(40)
        background_color: 0.9, 0.9, 0.9, 1
        color: 0.2, 0.2, 0.2, 1

    # 状态
    Label:
        id: lbl_status
        text: '就绪'
        font_name: "''' + FONT_NAME + '''"
        font_size: '12sp'
        size_hint_y: None
        height: dp(30)
        color: 0.5, 0.5, 0.5, 1
'''


class AndroidPlayer:
    """Android 原生 MediaPlayer 封装"""

    def __init__(self):
        self.player = None
        self._duration = 0

    def load(self, filepath):
        """加载音频文件"""
        try:
            from jnius import autoclass
            MediaPlayer = autoclass('android.media.MediaPlayer')
            self.player = MediaPlayer()
            self.player.setDataSource(filepath)
            self.player.prepare()
            self._duration = self.player.getDuration() / 1000.0  # ms -> seconds
            return True
        except Exception as e:
            print(f"Android MediaPlayer加载失败: {e}")
            import traceback
            traceback.print_exc()
            return False

    def play(self):
        if self.player:
            self.player.start()

    def pause(self):
        if self.player:
            self.player.pause()

    def stop(self):
        if self.player:
            self.player.stop()

    def release(self):
        if self.player:
            try:
                self.player.release()
            except Exception:
                pass
            self.player = None

    def get_pos(self):
        """获取当前播放位置（秒）"""
        if self.player:
            try:
                return self.player.getCurrentPosition() / 1000.0
            except Exception:
                pass
        return 0.0

    def seek(self, seconds):
        """跳转到指定位置"""
        if self.player:
            try:
                self.player.seekTo(int(seconds * 1000))
            except Exception:
                pass

    @property
    def length(self):
        return self._duration

    def is_playing(self):
        if self.player:
            try:
                return self.player.isPlaying()
            except Exception:
                pass
        return False


class TestApp(App):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.player = None          # AndroidPlayer 或 Kivy SoundLoader
        self.kivy_sound = None      # Kivy SoundLoader 备用
        self.use_android_player = False
        self.is_playing = False
        self.tick_event = None
        self.audio_path = None

    def build(self):
        self._load_font()
        return Builder.load_string(KV)

    def _load_font(self):
        """加载中文字体"""
        from kivy.core.text import LabelBase

        # 优先：Android 系统字体
        if IS_ANDROID:
            for sys_font in ANDROID_SYSTEM_FONTS:
                if os.path.exists(sys_font):
                    try:
                        LabelBase.register(name=FONT_NAME, fn_regular=sys_font)
                        print(f"使用系统字体: {sys_font}")
                        self.root.ids.lbl_status.text = f'字体: {os.path.basename(sys_font)}'
                        return
                    except Exception as e:
                        print(f"系统字体加载失败: {e}")

        # 兜底：打包的字体
        if os.path.exists(FONT_PATH_PACKAGED):
            try:
                LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH_PACKAGED)
                print(f"使用打包字体: {FONT_PATH_PACKAGED}")
                return
            except Exception as e:
                print(f"打包字体加载失败: {e}")

        print("警告：没有可用的中文字体")

    def select_file(self):
        """选择音频文件"""
        if IS_ANDROID:
            self._android_select()
        else:
            self._desktop_select()

    def _android_select(self):
        """Android: 用系统文件选择器"""
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
            intent.addCategory(Intent.CATEGORY_OPENABLE)
            intent.setType("audio/*")

            from android import activity as android_activity
            android_activity.bind(on_activity_result=self._on_result)

            PythonActivity.mActivity.startActivityForResult(intent, 42)
            self.root.ids.lbl_status.text = '请选择音频文件...'

        except Exception as e:
            self.root.ids.lbl_status.text = f'打开选择器失败: {e}'

    def _desktop_select(self):
        """桌面: Kivy文件选择"""
        from kivy.uix.popup import Popup
        from kivy.uix.filechooser import FileChooserListView

        content = BoxLayout(orientation='vertical', spacing=5)
        fc = FileChooserListView(filters=['*.mp3', '*.wav', '*.ogg', '*.m4a'])
        content.add_widget(fc)

        btn_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=5)
        ok = Button(text='选择')
        cancel = Button(text='取消')
        btn_box.add_widget(ok)
        btn_box.add_widget(cancel)
        content.add_widget(btn_box)

        popup = Popup(title='选择文件', content=content, size_hint=(0.95, 0.85))

        def on_ok(inst):
            if fc.selection:
                self._load_file(fc.selection[0])
            popup.dismiss()

        ok.bind(on_press=on_ok)
        cancel.bind(on_press=popup.dismiss)
        popup.open()

    def _on_result(self, req_code, result_code, intent_data):
        """Android文件选择回调"""
        if req_code != 42:
            return

        from android.activity import RESULT_OK
        if result_code != RESULT_OK or not intent_data:
            Clock.schedule_once(lambda dt: self._status('未选择文件'), 0)
            return

        uri_str = intent_data.getData().toString()
        Clock.schedule_once(lambda dt: self._status(f'已选择文件'), 0)

        # 后台复制到本地
        threading.Thread(target=self._copy_file, args=(uri_str,), daemon=True).start()

    def _copy_file(self, uri_str):
        """从content:// URI复制文件到本地"""
        try:
            from jnius import autoclass, jarray
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Uri = autoclass('android.net.Uri')

            activity = PythonActivity.mActivity
            resolver = activity.getContentResolver()
            uri = Uri.parse(uri_str)

            # 获取文件名
            filename = 'audio.mp3'
            try:
                cursor = resolver.query(uri, None, None, None, None)
                if cursor and cursor.moveToFirst():
                    idx = cursor.getColumnIndex("_display_name")
                    if idx >= 0:
                        filename = cursor.getString(idx)
                    cursor.close()
            except Exception:
                pass

            # 复制到本地
            from android.storage import app_storage_path
            local_path = os.path.join(app_storage_path(), filename)

            Clock.schedule_once(lambda dt: self._status(f'复制中: {filename}...'), 0)

            input_stream = resolver.openInputStream(uri)
            with open(local_path, 'wb') as f:
                buf = jarray('b')(8192)
                while True:
                    n = input_stream.read(buf)
                    if n <= 0:
                        break
                    f.write(bytes(buf[:n]))
            input_stream.close()

            size_kb = os.path.getsize(local_path) // 1024
            Clock.schedule_once(lambda dt: self._load_file(local_path), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self._status(f'复制失败: {e}'), 0)
            import traceback
            traceback.print_exc()

    def _load_file(self, path):
        """加载音频文件"""
        self.audio_path = path
        filename = os.path.basename(path)
        self.root.ids.lbl_file.text = f'文件: {filename}'
        self._status('加载中...')

        # 释放旧的播放器
        self._release_player()

        loaded = False

        # 方案1: Android MediaPlayer（首选，支持所有格式）
        if IS_ANDROID:
            try:
                self.player = AndroidPlayer()
                if self.player.load(path):
                    self.use_android_player = True
                    loaded = True
                    dur = self.player.length
                    self.root.ids.slider.max = max(dur, 1)
                    self.root.ids.lbl_time.text = f'0:00 / {self._fmt(dur)}'
                    self.root.ids.btn_play.disabled = False
                    self._status(f'加载成功 ({self._fmt(dur)})，可播放')
                    print(f"Android MediaPlayer: 时长={dur}s")
            except Exception as e:
                print(f"Android MediaPlayer异常: {e}")
                self.player = None

        # 方案2: Kivy SoundLoader（兜底）
        if not loaded:
            try:
                from kivy.core.audio import SoundLoader
                self.kivy_sound = SoundLoader.load(path)
                if self.kivy_sound:
                    self.use_android_player = False
                    loaded = True
                    dur = getattr(self.kivy_sound, 'length', 0) or 0
                    self.root.ids.slider.max = max(dur, 1)
                    self.root.ids.lbl_time.text = f'0:00 / {self._fmt(dur)}'
                    self.root.ids.btn_play.disabled = False
                    self._status(f'Kivy加载成功 ({self._fmt(dur)})，可播放')
                    print(f"SoundLoader: 时长={dur}s")
                else:
                    self._status('SoundLoader返回None')
            except Exception as e:
                print(f"SoundLoader异常: {e}")

        if not loaded:
            self._status('加载失败，格式可能不支持')

    def toggle_play(self):
        """播放/暂停"""
        if self.use_android_player and self.player:
            if self.is_playing:
                self.player.pause()
                self.is_playing = False
                self.root.ids.btn_play.text = '播放'
                if self.tick_event:
                    self.tick_event.cancel()
                    self.tick_event = None
            else:
                self.player.play()
                self.is_playing = True
                self.root.ids.btn_play.text = '暂停'
                self.tick_event = Clock.schedule_interval(self._tick_android, 0.15)
                self._status('播放中...')
        elif self.kivy_sound:
            if self.is_playing:
                self.kivy_sound.stop()
                self.is_playing = False
                self.root.ids.btn_play.text = '播放'
                if self.tick_event:
                    self.tick_event.cancel()
                    self.tick_event = None
            else:
                self.kivy_sound.play()
                self.is_playing = True
                self.root.ids.btn_play.text = '暂停'
                self.tick_event = Clock.schedule_interval(self._tick_kivy, 0.15)
                self._status('播放中...')

    def stop_audio(self):
        """停止"""
        if self.use_android_player and self.player:
            try:
                self.player.stop()
                self.player.seek(0)
            except Exception:
                pass
        elif self.kivy_sound:
            try:
                self.kivy_sound.stop()
            except Exception:
                pass

        self.is_playing = False
        self.root.ids.btn_play.text = '播放'
        self.root.ids.slider.value = 0
        if self.tick_event:
            self.tick_event.cancel()
            self.tick_event = None

        dur = self._get_duration()
        self.root.ids.lbl_time.text = f'0:00 / {self._fmt(dur)}'

    def _tick_android(self, dt):
        """Android MediaPlayer 定时器"""
        if not self.is_playing or not self.player:
            return
        try:
            pos = self.player.get_pos()
            dur = self.player.length
            self.root.ids.slider.value = pos
            self.root.ids.lbl_time.text = f'{self._fmt(pos)} / {self._fmt(dur)}'
            if dur > 0 and pos >= dur - 0.5:
                self.stop_audio()
                self._status('播放完成')
        except Exception:
            pass

    def _tick_kivy(self, dt):
        """Kivy SoundLoader 定时器"""
        if not self.is_playing or not self.kivy_sound:
            return
        try:
            pos = self.kivy_sound.get_pos()
            dur = getattr(self.kivy_sound, 'length', 0) or 0
            self.root.ids.slider.value = pos
            self.root.ids.lbl_time.text = f'{self._fmt(pos)} / {self._fmt(dur)}'
            if dur > 0 and pos >= dur - 0.5:
                self.stop_audio()
                self._status('播放完成')
        except Exception:
            pass

    def _release_player(self):
        """释放播放器资源"""
        if self.tick_event:
            self.tick_event.cancel()
            self.tick_event = None
        self.is_playing = False
        if self.player:
            try:
                self.player.release()
            except Exception:
                pass
            self.player = None
        if self.kivy_sound:
            try:
                self.kivy_sound.unload()
            except Exception:
                pass
            self.kivy_sound = None

    def _get_duration(self):
        if self.use_android_player and self.player:
            return self.player.length
        elif self.kivy_sound:
            return getattr(self.kivy_sound, 'length', 0) or 0
        return 0

    def _status(self, text):
        self.root.ids.lbl_status.text = text

    @staticmethod
    def _fmt(s):
        s = int(s)
        m, sec = divmod(s, 60)
        return f'{m}:{sec:02d}'

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self._release_player()


def main():
    TestApp().run()


if __name__ == '__main__':
    main()
