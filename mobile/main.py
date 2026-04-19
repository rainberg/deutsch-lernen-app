"""
极简测试：只做一件事 - 选文件 + 播放MP3
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
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
import threading
import time

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'ChineseSubset.ttf')
FONT_NAME = 'ChineseFont'

KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: dp(15)
    spacing: dp(10)

    Label:
        text: '德语播放器测试'
        font_name: "''' + FONT_NAME + '''"
        font_size: '22sp'
        size_hint_y: None
        height: dp(50)

    Button:
        id: btn_select
        text: '选择音频文件'
        font_name: "''' + FONT_NAME + '''"
        font_size: '16sp'
        size_hint_y: None
        height: dp(50)
        on_press: app.select_file()

    Label:
        id: lbl_file
        text: '未选择文件'
        font_name: "''' + FONT_NAME + '''"
        font_size: '13sp'
        size_hint_y: None
        height: dp(30)

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

        Button:
            text: '停止'
            font_name: "''' + FONT_NAME + '''"
            font_size: '16sp'
            on_press: app.stop_audio()

    Label:
        id: lbl_status
        text: '就绪'
        font_name: "''' + FONT_NAME + '''"
        font_size: '12sp'
        size_hint_y: None
        height: dp(30)
'''


class TestApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sound = None
        self.is_playing = False
        self.tick_event = None
        self.audio_path = None

    def build(self):
        from kivy.core.text import LabelBase
        if os.path.exists(FONT_PATH):
            LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)
        self.root_widget = Builder.load_string(KV)
        return self.root_widget

    def select_file(self):
        """用Android系统文件选择器选文件"""
        self.root_widget.ids.lbl_status.text = '正在打开文件选择器...'

        if platform == 'android':
            try:
                from jnius import autoclass, cast
                Intent = autoclass('android.content.Intent')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')

                intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.setType("audio/*")

                # 需要startActivityForResult
                activity = PythonActivity.mActivity

                # 使用 startActivityForResult 获取结果
                # Kivy/PythonActivity 支持 onActivityResult 回调
                from android import activity as android_activity
                android_activity.bind(on_activity_result=self._on_activity_result)

                activity.startActivityForResult(intent, 42)

                self.root_widget.ids.lbl_status.text = '请在弹出窗口中选择音频文件...'

            except Exception as e:
                self.root_widget.ids.lbl_status.text = f'打开选择器失败: {e}'
                import traceback
                traceback.print_exc()
        else:
            # 桌面模式：用kivy的FileChooserPopup
            self._show_desktop_filechooser()

    def _on_activity_result(self, request_code, result_code, intent_data):
        """Android文件选择结果回调"""
        if request_code != 42:
            return

        from android.activity import RESULT_OK
        if result_code != RESULT_OK or not intent_data:
            Clock.schedule_once(lambda dt: self._set_status('未选择文件'), 0)
            return

        try:
            uri_str = intent_data.getData().toString()
            Clock.schedule_once(lambda dt: self._set_status(f'URI: {uri_str[:50]}...'), 0)

            # 复制到本地
            thread = threading.Thread(target=self._copy_uri_to_local, args=(uri_str,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            Clock.schedule_once(lambda dt: self._set_status(f'处理失败: {e}'), 0)

    def _copy_uri_to_local(self, uri_str):
        """从content:// URI复制文件到本地"""
        try:
            from jnius import autoclass
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
                    name_idx = cursor.getColumnIndex("_display_name")
                    if name_idx >= 0:
                        filename = cursor.getString(name_idx)
                    cursor.close()
            except Exception:
                pass

            Clock.schedule_once(lambda dt, f=filename: self._set_status(f'正在复制: {f}...'), 0)

            # 获取文件大小
            total = 0
            try:
                pfd = resolver.openFileDescriptor(uri, "r")
                total = pfd.getStatSize()
                pfd.close()
            except Exception:
                pass

            # 复制到应用私有目录
            from android.storage import app_storage_path
            local_path = os.path.join(app_storage_path(), filename)

            input_stream = resolver.openInputStream(uri)
            copied = 0
            buf_size = 8192

            with open(local_path, 'wb') as out_f:
                from jnius import jarray
                buffer = jarray('b')(buf_size)
                while True:
                    count = input_stream.read(buffer)
                    if count <= 0:
                        break
                    out_f.write(bytes(buffer[:count]))
                    copied += count

                    if total > 0:
                        kb_c = copied // 1024
                        kb_t = total // 1024
                        Clock.schedule_once(
                            lambda dt, c=kb_c, t=kb_t:
                                self._set_status(f'已复制 {c}KB / {t}KB'),
                            0
                        )

            input_stream.close()

            Clock.schedule_once(lambda dt, p=local_path, f=filename: self._on_file_ready(p, f), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self._set_status(f'复制失败: {e}'), 0)
            import traceback
            traceback.print_exc()

    def _show_desktop_filechooser(self):
        """桌面模式文件选择"""
        content = BoxLayout(orientation='vertical', spacing=5)
        from kivy.uix.filechooser import FileChooserListView
        fc = FileChooserListView(filters=['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac'])
        content.add_widget(fc)

        btn_box = BoxLayout(size_hint_y=None, height=dp(45), spacing=5)
        ok_btn = Button(text='选择')
        cancel_btn = Button(text='取消')
        btn_box.add_widget(ok_btn)
        btn_box.add_widget(cancel_btn)
        content.add_widget(btn_box)

        popup = Popup(title='选择音频文件', content=content, size_hint=(0.95, 0.85))

        def on_ok(inst):
            if fc.selection:
                self._on_file_ready(fc.selection[0], os.path.basename(fc.selection[0]))
            popup.dismiss()

        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _on_file_ready(self, path, filename):
        """文件准备就绪"""
        self.audio_path = path
        self.root_widget.ids.lbl_file.text = f'文件: {filename}'
        self.root_widget.ids.lbl_status.text = '正在加载音频...'

        try:
            self.sound = SoundLoader.load(path)
            if self.sound:
                dur = self._get_dur()
                self.root_widget.ids.slider.max = max(dur, 1)
                self.root_widget.ids.lbl_time.text = f'0:00 / {self._fmt(dur)}'
                self.root_widget.ids.btn_play.disabled = False
                self.root_widget.ids.lbl_status.text = f'加载成功 ({self._fmt(dur)})，可以播放了！'
            else:
                self.root_widget.ids.lbl_status.text = 'SoundLoader返回None，格式可能不支持'
        except Exception as e:
            self.root_widget.ids.lbl_status.text = f'加载异常: {e}'

    def toggle_play(self):
        if not self.sound:
            return

        if self.is_playing:
            self.sound.stop()
            self.is_playing = False
            self.root_widget.ids.btn_play.text = '播放'
            if self.tick_event:
                self.tick_event.cancel()
                self.tick_event = None
        else:
            self.sound.play()
            self.is_playing = True
            self.root_widget.ids.btn_play.text = '暂停'
            self.tick_event = Clock.schedule_interval(self._tick, 0.15)
            self.root_widget.ids.lbl_status.text = '播放中...'

    def stop_audio(self):
        if self.sound:
            self.sound.stop()
        self.is_playing = False
        self.root_widget.ids.btn_play.text = '播放'
        self.root_widget.ids.slider.value = 0
        if self.tick_event:
            self.tick_event.cancel()
            self.tick_event = None
        dur = self._get_dur()
        self.root_widget.ids.lbl_time.text = f'0:00 / {self._fmt(dur)}'

    def _tick(self, dt):
        if not self.sound or not self.is_playing:
            return
        try:
            pos = self.sound.get_pos()
            dur = self._get_dur()
            self.root_widget.ids.slider.value = pos
            self.root_widget.ids.lbl_time.text = f'{self._fmt(pos)} / {self._fmt(dur)}'
            if dur > 0 and pos >= dur - 0.3:
                self.stop_audio()
                self.root_widget.ids.lbl_status.text = '播放完成'
        except Exception:
            pass

    def _set_status(self, text):
        self.root_widget.ids.lbl_status.text = text

    def _get_dur(self):
        try:
            d = getattr(self.sound, 'length', 0)
            return d if d and d > 0 else 0
        except Exception:
            return 0

    @staticmethod
    def _fmt(s):
        s = int(s)
        m, sec = divmod(s, 60)
        return f'{m}:{sec:02d}'

    def on_pause(self):
        return True

    def on_resume(self):
        pass


def main():
    TestApp().run()


if __name__ == '__main__':
    main()
