"""
德语学习助手 - 安卓版 v0.5
音频播放 + 句子同步 + 转写 + 翻译 + 收藏 + Anki导出
修复：Android content:// URI 处理 + 音频播放稳定性
"""

import os
os.environ['KIVY_LOG_MODE'] = 'MIXED'

from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp, sp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.slider import Slider
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.core.clipboard import Clipboard
from kivy.core.audio import SoundLoader
import threading
import json
import time
import re

# ── 配置 ──
API_KEY = "fk2014...9vDm"
API_BASE = "https://openai.api2d.net/v1"

# ── 字体路径 ──
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'ChineseSubset.ttf')
FONT_NAME = 'ChineseFont'

# ── KV 界面定义 ──
KV = '''
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp

<CustomLabel@Label>:
    font_name: "''' + FONT_NAME + '''"
    color: 0.15, 0.15, 0.15, 1

<CustomButton@Button>:
    font_name: "''' + FONT_NAME + '''"
    font_size: '14sp'

<CustomTextInput@TextInput>:
    font_name: "''' + FONT_NAME + '''"
    font_size: '15sp'
    foreground_color: 0.15, 0.15, 0.15, 1
    background_color: 1, 1, 1, 1
    cursor_color: 0.2, 0.6, 0.8, 1

<SentenceButton>:
    font_name: "''' + FONT_NAME + '''"
    font_size: '15sp'
    background_color: 0.96, 0.96, 0.96, 1
    color: 0.1, 0.1, 0.1, 1
    size_hint_y: None
    height: dp(72)
    halign: 'left'
    valign: 'top'
    text_size: self.width - dp(16), None
    padding: [dp(8), dp(6)]
    background_normal: ''
    canvas.before:
        Color:
            rgba: self.border_color
        RoundedRectangle:
            pos: self.x, self.y
            size: self.width, self.height
            radius: [dp(6),]
        Color:
            rgba: self.highlight_color
        RoundedRectangle:
            pos: self.x + dp(2), self.y + dp(2)
            size: self.width - dp(4), self.height - dp(4)
            radius: [dp(4),]

<MainScreen>:
    name: 'main'

    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(6)

        # ── 标题栏 ──
        BoxLayout:
            size_hint_y: None
            height: dp(42)

            CustomLabel:
                text: '德语学习助手'
                font_size: '20sp'
                bold: True
                halign: 'left'
                text_size: self.size
                color: 0.15, 0.45, 0.7, 1

            CustomButton:
                text: '收藏'
                size_hint_x: None
                width: dp(55)
                background_color: 0.3, 0.5, 0.8, 1
                on_press: root.show_collection()

        # ── 功能按钮 ──
        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(6)

            CustomButton:
                text: '导入音频'
                background_color: 0.2, 0.7, 0.3, 1
                on_press: root.import_audio()

            CustomButton:
                text: '开始转写'
                background_color: 0.9, 0.55, 0.1, 1
                on_press: root.start_transcribe()

            CustomButton:
                text: '导出Anki'
                background_color: 0.6, 0.3, 0.8, 1
                on_press: root.export_anki()

        # ── 音频播放器 ──
        BoxLayout:
            id: player_area
            size_hint_y: None
            height: dp(0)
            opacity: 0
            orientation: 'vertical'
            spacing: dp(4)

            # 播放控制
            BoxLayout:
                size_hint_y: None
                height: dp(42)
                spacing: dp(8)

                CustomButton:
                    id: play_btn
                    text: '播放'
                    size_hint_x: None
                    width: dp(70)
                    background_color: 0.2, 0.6, 0.8, 1
                    on_press: root.toggle_play()

                CustomButton:
                    id: stop_btn
                    text: '停止'
                    size_hint_x: None
                    width: dp(55)
                    background_color: 0.5, 0.5, 0.5, 1
                    on_press: root.stop_audio()

                Slider:
                    id: seek_slider
                    min: 0
                    max: 100
                    value: 0
                    on_touch_up: root.on_slider_seek(self, args[1]) if self.collide_point(*args[1].pos) else None

                CustomLabel:
                    id: time_label
                    text: '0:00/0:00'
                    size_hint_x: None
                    width: dp(90)
                    font_size: '12sp'
                    halign: 'right'

        # ── 句子列表（带时间轴同步）──
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(3)

            CustomLabel:
                text: '转写句子（点击播放对应音频）'
                size_hint_y: None
                height: dp(22)
                halign: 'left'
                text_size: self.size
                font_size: '12sp'
                color: 0.45, 0.45, 0.45, 1

            ScrollView:
                id: sentence_scroll
                do_scroll_x: False
                GridLayout:
                    id: sentence_list
                    cols: 1
                    size_hint_y: None
                    height: self.minimum_height
                    spacing: dp(5)

        # ── 中文翻译区 ──
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(3)
            size_hint_y: None
            height: dp(110)

            CustomLabel:
                text: '中文翻译'
                size_hint_y: None
                height: dp(22)
                halign: 'left'
                text_size: self.size
                font_size: '12sp'
                color: 0.45, 0.45, 0.45, 1

            ScrollView:
                CustomTextInput:
                    id: chinese_text
                    hint_text: '中文翻译将显示在这里...'
                    multiline: True
                    readonly: True
                    size_hint_y: None
                    height: max(self.minimum_height, dp(80))

        # ── 操作按钮 ──
        BoxLayout:
            size_hint_y: None
            height: dp(42)
            spacing: dp(6)

            CustomButton:
                text: '收藏句子'
                background_color: 0.3, 0.5, 0.8, 1
                on_press: root.collect_sentence()

            CustomButton:
                text: '复制文本'
                background_color: 0.5, 0.5, 0.5, 1
                on_press: root.copy_text()

            CustomButton:
                text: '清空'
                background_color: 0.8, 0.3, 0.3, 1
                on_press: root.clear_all()

        # ── 进度条 ──
        ProgressBar:
            id: progress
            size_hint_y: None
            height: dp(3)
            opacity: 0
            max: 100

        # ── 状态栏 ──
        CustomLabel:
            id: status_label
            text: '就绪'
            size_hint_y: None
            height: dp(22)
            font_size: '11sp'
            color: 0.5, 0.5, 0.5, 1

<CollectionScreen>:
    name: 'collection'

    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(6)

        BoxLayout:
            size_hint_y: None
            height: dp(42)

            CustomButton:
                text: '< 返回'
                size_hint_x: None
                width: dp(65)
                background_color: 0.5, 0.5, 0.5, 1
                on_press: root.go_back()

            CustomLabel:
                text: '收藏列表'
                font_size: '18sp'
                bold: True
                halign: 'center'

            CustomButton:
                text: '清空'
                size_hint_x: None
                width: dp(55)
                background_color: 0.8, 0.3, 0.3, 1
                on_press: root.clear_collection()

        ScrollView:
            GridLayout:
                id: collection_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(5)
'''

Builder.load_string(KV)


# ── 句子按钮（支持高亮） ──
from kivy.properties import ListProperty

class SentenceButton(Button):
    highlight_color = ListProperty([0, 0, 0, 0])       # 当前播放高亮
    border_color = ListProperty([0.85, 0.85, 0.85, 1])  # 边框

    def __init__(self, segment_data=None, **kwargs):
        super().__init__(**kwargs)
        self.segment_data = segment_data  # {start, end, text, chinese}
        self.is_playing = False
        self.background_normal = ''

    def set_highlight(self, active):
        self.is_playing = active
        if active:
            self.highlight_color = [0.85, 0.93, 1.0, 1]   # 淡蓝高亮
            self.border_color = [0.2, 0.6, 0.9, 1]        # 蓝色边框
            self.color = [0.05, 0.05, 0.05, 1]
        else:
            self.highlight_color = [0, 0, 0, 0]
            self.border_color = [0.85, 0.85, 0.85, 1]
            self.color = [0.1, 0.1, 0.1, 1]


# ── 主屏幕 ──
class MainScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_audio_path = None
        self.sound = None
        self.segments = []           # [{start, end, text, chinese}, ...]
        self.sentence_buttons = []
        self.current_segment_idx = -1
        self.is_playing = False
        self.update_event = None
        self.collected_sentences = []
        self.store = None
        self._slider_dragging = False
        self.init_storage()

    # ─── 存储 ───
    def init_storage(self):
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                path = os.path.join(app_storage_path(), 'sentences.json')
            else:
                path = os.path.join(os.path.dirname(__file__), 'sentences.json')
            self.store = JsonStore(path)
            for key in self.store:
                item = self.store.get(key)
                self.collected_sentences.append({
                    'german': item.get('german', ''),
                    'chinese': item.get('chinese', '')
                })
        except Exception as e:
            print(f"存储初始化失败: {e}")
            self.store = None

    # ─── 导入音频 ───
    def import_audio(self):
        if platform == 'android':
            try:
                from plyer import filechooser
                filechooser.open_file(
                    on_selection=self.on_audio_selected,
                    filters=["*.mp3", "*.wav", "*.m4a", "*.ogg", "*.mp4", "*.flac", "*.webm"]
                )
            except Exception as e:
                self.ids.status_label.text = f'文件选择器错误: {e}'
        else:
            self.ids.status_label.text = '请在安卓设备上使用文件选择器'

    def on_audio_selected(self, selection):
        """处理选择的文件（Android返回content:// URI需要复制到本地）"""
        if not selection:
            return

        raw_path = selection[0]

        if platform == 'android':
            # Android文件选择器返回content:// URI，需复制到本地
            local_path = self._copy_content_uri_to_local(raw_path)
            if local_path:
                self.current_audio_path = local_path
                filename = os.path.basename(local_path)
                self.ids.status_label.text = f'已加载: {filename}'
            else:
                self.ids.status_label.text = '文件复制失败，请重试'
                return
        else:
            self.current_audio_path = raw_path
            filename = os.path.basename(raw_path)
            self.ids.status_label.text = f'已选择: {filename}'

        self._load_audio_player()

    def _copy_content_uri_to_local(self, uri):
        """将Android content:// URI复制到应用本地存储"""
        try:
            import shutil

            # 获取应用私有目录
            from android.storage import app_storage_path
            local_dir = app_storage_path()

            # 从URI提取文件名
            filename = 'audio_import'
            if '/' in uri:
                parts = uri.split('/')
                for part in reversed(parts):
                    if '.' in part and len(part) > 3:
                        filename = part
                        break

            local_path = os.path.join(local_dir, filename)

            # 方法1: 用Android ContentResolver复制
            try:
                from jnius import autoclass, cast
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                context = PythonActivity.mActivity
                ContentResolver = context.getContentResolver()
                Uri = autoclass('android.net.Uri')
                uri_obj = Uri.parse(uri)
                input_stream = ContentResolver.openInputStream(uri_obj)

                # 读取并写入本地文件
                with open(local_path, 'wb') as out_f:
                    buffer = jarray('b')(4096)
                    while True:
                        count = input_stream.read(buffer)
                        if count <= 0:
                            break
                        out_f.write(bytes(buffer[:count]))
                input_stream.close()
                print(f"文件复制成功: {local_path}")
                return local_path

            except Exception as e1:
                print(f"ContentResolver方式失败: {e1}")

            # 方法2: 直接用shutil（某些设备支持直接访问）
            try:
                if os.path.exists(uri):
                    shutil.copy2(uri, local_path)
                    print(f"直接复制成功: {local_path}")
                    return local_path
            except Exception as e2:
                print(f"直接复制失败: {e2}")

            return None

        except Exception as e:
            print(f"复制文件失败: {e}")
            return None

    def _load_audio_player(self):
        """加载音频到播放器"""
        try:
            if self.sound:
                try:
                    self.sound.stop()
                    self.sound.unload()
                except Exception:
                    pass
                self.sound = None

            path = self.current_audio_path
            self.ids.status_label.text = '正在加载音频...'
            print(f"尝试加载音频: {path}")
            print(f"文件存在: {os.path.exists(path)}, 大小: {os.path.getsize(path) if os.path.exists(path) else 'N/A'}")

            # Kivy SoundLoader（Android上用SDL2_mixer，支持mp3/ogg/wav）
            try:
                self.sound = SoundLoader.load(path)
                print(f"SoundLoader结果: {self.sound}")
            except Exception as e:
                print(f"SoundLoader异常: {e}")
                import traceback
                traceback.print_exc()
                self.sound = None

            if self.sound:
                # 获取时长
                duration = self._get_sound_duration()
                print(f"音频时长: {duration}")

                # 显示播放器
                self.ids.player_area.height = dp(50)
                self.ids.player_area.opacity = 1

                if duration and duration > 0:
                    self.ids.seek_slider.max = duration
                    self.ids.time_label.text = f'0:00/{self._fmt_time(duration)}'
                    self.ids.status_label.text = f'音频已加载 ({self._fmt_time(duration)})，点击播放'
                else:
                    self.ids.seek_slider.max = 9999
                    self.ids.time_label.text = '0:00/?:??'
                    self.ids.status_label.text = '音频已加载，点击播放'
            else:
                self.ids.status_label.text = '无法加载音频，格式可能不支持（支持mp3/ogg/wav）'

        except Exception as e:
            self.ids.status_label.text = f'加载异常: {e}'
            import traceback
            traceback.print_exc()

    def _get_sound_duration(self):
        """安全获取音频时长"""
        try:
            d = getattr(self.sound, 'length', 0)
            return d if d and d > 0 else 0
        except Exception:
            return 0

    def _get_sound_pos(self):
        """安全获取当前播放位置"""
        try:
            return self.sound.get_pos()
        except Exception:
            return 0

    # ─── 播放控制 ───
    def toggle_play(self):
        if not self.sound:
            self.ids.status_label.text = '请先导入音频'
            return

        if self.is_playing:
            # 暂停
            try:
                self.sound.stop()
            except Exception:
                pass
            self.is_playing = False
            self.ids.play_btn.text = '播放'
            if self.update_event:
                self.update_event.cancel()
                self.update_event = None
            self._clear_highlights()
        else:
            # 播放
            try:
                self.sound.play()
                self.is_playing = True
                self.ids.play_btn.text = '暂停'
                self.update_event = Clock.schedule_interval(self._update_playback, 0.15)
                self.ids.status_label.text = '播放中...'
            except Exception as e:
                self.ids.status_label.text = f'播放失败: {e}'

    def stop_audio(self):
        if self.sound:
            try:
                self.sound.stop()
            except Exception:
                pass
        self.is_playing = False
        self.ids.play_btn.text = '播放'
        self.ids.seek_slider.value = 0
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None
        self._clear_highlights()
        dur = self._get_sound_duration()
        self.ids.time_label.text = f'0:00/{self._fmt_time(dur)}'

    def _update_playback(self, dt):
        """定时更新播放进度和句子高亮"""
        if not self.sound or not self.is_playing:
            return

        try:
            pos = self._get_sound_pos()
            duration = self._get_sound_duration()
        except Exception:
            return

        if duration <= 0:
            return

        # 更新进度条
        if not self._slider_dragging:
            self.ids.seek_slider.value = pos

        # 更新时间显示
        self.ids.time_label.text = f'{self._fmt_time(pos)}/{self._fmt_time(duration)}'

        # 高亮当前句子
        self._highlight_at_time(pos)

        # 播放结束
        if pos >= duration - 0.2:
            self.is_playing = False
            self.ids.play_btn.text = '播放'
            if self.update_event:
                self.update_event.cancel()
                self.update_event = None
            self._clear_highlights()
            self.ids.status_label.text = '播放完成'

    def on_slider_seek(self, slider, touch):
        """拖拽进度条跳转"""
        if slider.collide_point(*touch.pos) and self.sound:
            try:
                self.sound.seek(slider.value)
                self._highlight_at_time(slider.value)
            except Exception:
                pass

    def _highlight_at_time(self, pos):
        """根据播放位置高亮对应句子"""
        new_idx = -1
        for i, seg in enumerate(self.segments):
            if seg['start'] <= pos < seg['end']:
                new_idx = i
                break

        if new_idx != self.current_segment_idx:
            # 取消旧高亮
            if 0 <= self.current_segment_idx < len(self.sentence_buttons):
                self.sentence_buttons[self.current_segment_idx].set_highlight(False)

            # 设置新高亮
            if 0 <= new_idx < len(self.sentence_buttons):
                self.sentence_buttons[new_idx].set_highlight(True)
                # 自动滚动到当前句子
                self._scroll_to_sentence(new_idx)

            self.current_segment_idx = new_idx

    def _scroll_to_sentence(self, idx):
        """自动滚动ScrollView使当前句子可见"""
        try:
            scroll = self.ids.sentence_scroll
            btn = self.sentence_buttons[idx]
            # 计算按钮在GridLayout中的位置
            layout = self.ids.sentence_list
            # 按钮在列表中的y位置（从底部算起）
            btn_y = sum(c.height + layout.spacing for c in list(layout.children)[len(layout.children)-1-idx:])

            # scroll_view的高度
            view_height = scroll.height
            content_height = layout.height

            # 计算scroll_y (0=底部, 1=顶部)
            target_scroll_y = max(0, min(1, (btn_y - view_height * 0.3) / (content_height - view_height + 1)))
            # 平滑滚动
            scroll.scroll_y = 1 - target_scroll_y
        except Exception:
            pass

    def _clear_highlights(self):
        for btn in self.sentence_buttons:
            btn.set_highlight(False)
        self.current_segment_idx = -1

    # ─── 点击句子跳转播放 ───
    def on_sentence_tap(self, btn_instance):
        """点击句子 → 跳转到该句开始时间并播放"""
        if not self.sound:
            return
        seg = btn_instance.segment_data
        if seg:
            self.sound.seek(seg['start'])
            self.ids.seek_slider.value = seg['start']
            if not self.is_playing:
                self.toggle_play()
            # 更新翻译区
            self.ids.chinese_text.text = seg.get('chinese', '')
            self._highlight_at_time(seg['start'])

    # ─── 转写 ───
    def start_transcribe(self):
        if not self.current_audio_path:
            self.show_popup('提示', '请先点击"导入音频"选择音频文件')
            return

        self.ids.status_label.text = '正在转写，请稍候...'
        self.ids.progress.opacity = 1
        self.ids.progress.value = 15

        thread = threading.Thread(target=self._transcribe_thread)
        thread.daemon = True
        thread.start()

    def _transcribe_thread(self):
        try:
            from openai import OpenAI

            Clock.schedule_once(lambda dt: self._set_status('连接服务器...'), 0)
            client = OpenAI(api_key=API_KEY, base_url=API_BASE)

            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'value', 30), 0)
            Clock.schedule_once(lambda dt: self._set_status('正在转写音频...'), 0)

            # 用 verbose_json 获取时间戳
            with open(self.current_audio_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="de",
                    response_format="verbose_json"
                )

            # 解析segments
            segments_raw = []
            full_text = ""
            for seg in response.segments:
                text = seg.text.strip()
                segments_raw.append({
                    'start': seg.start,
                    'end': seg.end,
                    'text': text
                })
                full_text += text + " "

            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'value', 60), 0)
            Clock.schedule_once(lambda dt: self._set_status(f'转写完成，{len(segments_raw)}句，正在翻译...'), 0)

            # 逐句翻译
            translated_segments = []
            for i, seg in enumerate(segments_raw):
                try:
                    tr = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "将德语翻译为中文，只输出翻译。"},
                            {"role": "user", "content": seg['text']}
                        ]
                    )
                    chinese = tr.choices[0].message.content.strip()
                except Exception:
                    chinese = "[翻译失败]"
                translated_segments.append({
                    'start': seg['start'],
                    'end': seg['end'],
                    'text': seg['text'],
                    'chinese': chinese
                })

            # 完整翻译（用于收藏区）
            full_chinese = "\n".join(s['chinese'] for s in translated_segments)

            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'value', 100), 0)
            Clock.schedule_once(
                lambda dt: self._update_result(translated_segments, full_text.strip(), full_chinese),
                0
            )

        except ImportError:
            Clock.schedule_once(lambda dt: self._set_status('错误: 缺少openai库'), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._set_status(f'错误: {str(e)[:80]}'), 0)
        finally:
            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'opacity', 0), 3)

    def _set_status(self, text):
        self.ids.status_label.text = text

    def _update_result(self, translated_segments, full_german, full_chinese):
        """更新转写结果到UI"""
        self.segments = translated_segments

        # 清空旧句子列表
        self.ids.sentence_list.clear_widgets()
        self.sentence_buttons = []
        self.current_segment_idx = -1

        # 创建句子按钮
        for i, seg in enumerate(translated_segments):
            time_str = self._fmt_time(seg['start'])
            display_text = f"[{time_str}]  {seg['text']}"

            btn = SentenceButton(
                segment_data=seg,
                text=display_text,
            )
            btn.bind(on_press=self.on_sentence_tap)
            self.ids.sentence_list.add_widget(btn)
            self.sentence_buttons.append(btn)

        # 更新中文区
        self.ids.chinese_text.text = full_chinese
        self.ids.status_label.text = f'转写完成：{len(translated_segments)}个句子'

    # ─── 收藏 ───
    def collect_sentence(self):
        """收藏当前高亮的句子"""
        if 0 <= self.current_segment_idx < len(self.segments):
            seg = self.segments[self.current_segment_idx]
            item = {'german': seg['text'], 'chinese': seg.get('chinese', '')}
        else:
            # 收藏全部
            german = "\n".join(s['text'] for s in self.segments)
            chinese = self.ids.chinese_text.text
            if not german:
                self.ids.status_label.text = '没有可收藏的内容'
                return
            item = {'german': german, 'chinese': chinese}

        self.collected_sentences.append(item)
        if self.store:
            try:
                key = f"item_{int(time.time())}"
                self.store.put(key, german=item['german'], chinese=item['chinese'])
            except Exception as e:
                print(f"保存失败: {e}")

        self.ids.status_label.text = f'已收藏 ({len(self.collected_sentences)}条)'

    def show_collection(self):
        app = App.get_running_app()
        cs = app.root.get_screen('collection')
        cs.load_sentences(self.collected_sentences)
        app.root.current = 'collection'

    def copy_text(self):
        parts = []
        for seg in self.segments:
            parts.append(f"{seg['text']}\n{seg.get('chinese', '')}")
        if parts:
            Clipboard.copy("\n\n".join(parts))
            self.ids.status_label.text = '已复制到剪贴板'

    def clear_all(self):
        self.ids.sentence_list.clear_widgets()
        self.sentence_buttons = []
        self.segments = []
        self.current_segment_idx = -1
        self.ids.chinese_text.text = ''
        self.ids.status_label.text = '已清空'

    def export_anki(self):
        if not self.collected_sentences:
            self.show_popup('提示', '没有收藏的句子')
            return
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                export_dir = app_storage_path()
            else:
                export_dir = os.path.dirname(__file__)
            filepath = os.path.join(export_dir, 'anki_export.txt')
            with open(filepath, 'w', encoding='utf-8') as f:
                for item in self.collected_sentences:
                    g = item['german'].replace('\n', ' ').replace('\t', ' ')
                    c = item['chinese'].replace('\n', ' ').replace('\t', ' ')
                    f.write(f"{g}\t{c}\n")
            self.ids.status_label.text = f'已导出 {len(self.collected_sentences)} 条'
            self.show_popup('导出成功', f'文件: {filepath}\n\nAnki → 文件 → 导入 → 制表符分隔')
        except Exception as e:
            self.show_popup('导出失败', str(e))

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            title_font=FONT_NAME,
            size_hint=(0.85, None),
            height=dp(190)
        )
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        content.add_widget(Label(
            text=message,
            font_name=FONT_NAME,
            text_size=(Window.width * 0.7, None),
            halign='left',
            valign='top'
        ))
        btn = Button(
            text='确定',
            font_name=FONT_NAME,
            size_hint_y=None,
            height=dp(42),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.content = content
        popup.open()

    @staticmethod
    def _fmt_time(seconds):
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        return f'{m}:{s:02d}'


# ── 收藏屏幕 ──
class CollectionScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sentences = []

    def load_sentences(self, sentences):
        self.sentences = sentences
        self.ids.collection_list.clear_widgets()

        if not sentences:
            self.ids.collection_list.add_widget(Label(
                text='暂无收藏',
                font_name=FONT_NAME,
                size_hint_y=None,
                height=dp(50)
            ))
            return

        for i, item in enumerate(reversed(sentences)):
            preview = item['german'][:45].replace('\n', ' ')
            btn = Button(
                text=f"{len(sentences)-i}. {preview}...",
                font_name=FONT_NAME,
                font_size='13sp',
                size_hint_y=None,
                height=dp(52),
                background_color=(0.95, 0.95, 0.95, 1),
                color=(0.1, 0.1, 0.1, 1),
                halign='left',
                text_size=(Window.width * 0.78, None)
            )
            btn.bind(on_press=lambda x, idx=len(sentences)-1-i: self.show_detail(idx))
            self.ids.collection_list.add_widget(btn)

    def show_detail(self, index):
        if index >= len(self.sentences):
            return
        item = self.sentences[index]
        popup = Popup(title='收藏详情', title_font=FONT_NAME, size_hint=(0.92, 0.55))
        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(8))
        scroll = ScrollView()
        dl = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6))
        dl.bind(minimum_height=dl.setter('height'))

        for label_text in [f"德语:\n{item['german']}", f"中文:\n{item['chinese']}"]:
            lbl = Label(
                text=label_text,
                font_name=FONT_NAME,
                text_size=(Window.width * 0.78, None),
                size_hint_y=None,
                halign='left',
                valign='top'
            )
            lbl.bind(texture_size=lbl.setter('size'))
            dl.add_widget(lbl)

        scroll.add_widget(dl)
        content.add_widget(scroll)

        btns = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
        for txt, color, action in [
            ('复制', (0.3, 0.5, 0.8, 1), lambda x: Clipboard.copy(f"{item['german']}\n\n{item['chinese']}")),
            ('删除', (0.8, 0.3, 0.3, 1), lambda x: (self._del(index), popup.dismiss())),
            ('关闭', (0.5, 0.5, 0.5, 1), lambda x: popup.dismiss())
        ]:
            b = Button(text=txt, font_name=FONT_NAME, background_color=color)
            b.bind(on_press=action)
            btns.add_widget(b)
        content.add_widget(btns)
        popup.content = content
        popup.open()

    def _del(self, idx):
        if 0 <= idx < len(self.sentences):
            self.sentences.pop(idx)
            self.load_sentences(self.sentences)

    def clear_collection(self):
        self.sentences.clear()
        self.ids.collection_list.clear_widgets()
        self.ids.collection_list.add_widget(Label(
            text='已清空', font_name=FONT_NAME, size_hint_y=None, height=dp(50)
        ))

    def go_back(self):
        App.get_running_app().root.current = 'main'


# ── 应用 ──

class DeutschLernenApp(App):

    def build(self):
        self.title = '德语学习助手'
        self._load_font()
        sm = ScreenManager()
        sm.add_widget(MainScreen())
        sm.add_widget(CollectionScreen())
        return sm

    def _load_font(self):
        from kivy.core.text import LabelBase
        if os.path.exists(FONT_PATH):
            LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)
            print(f"字体加载成功: {FONT_PATH}")
        else:
            print(f"字体文件不存在: {FONT_PATH}")

    def on_pause(self):
        return True

    def on_resume(self):
        pass


def main():
    DeutschLernenApp().run()


if __name__ == '__main__':
    main()
