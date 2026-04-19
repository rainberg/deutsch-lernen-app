"""
德语学习助手 v1.0 - Android版
三页面架构：文件浏览 → 播放学习 → 收藏管理
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
from kivy.uix.filechooser import FileChooserListView
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.core.clipboard import Clipboard
from kivy.core.audio import SoundLoader
from kivy.properties import ListProperty, StringProperty, BooleanProperty
import threading
import time
import re

# ── 配置 ──
API_KEY = "fk2014...9vDm"
API_BASE = "https://openai.api2d.net/v1"

# ── 字体 ──
FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts', 'ChineseSubset.ttf')
FONT_NAME = 'ChineseFont'

# ── Android存储路径 ──
def get_storage_dir():
    if platform == 'android':
        try:
            from android.storage import app_storage_path
            return app_storage_path()
        except Exception:
            pass
    return os.path.dirname(os.path.abspath(__file__))

def get_music_dir():
    if platform == 'android':
        try:
            from android.storage import primary_external_storage_path
            return primary_external_storage_path()
        except Exception:
            pass
    return '/storage/emulated/0'

# ── KV 界面 ──
F = FONT_NAME  # 简写

KV = '''
#:import dp kivy.metrics.dp
#:import sp kivy.metrics.sp
#:import os os

<CT@Label>:
    font_name: "''' + F + '''"
    color: 0.12, 0.12, 0.12, 1

<CB@Button>:
    font_name: "''' + F + '''"
    font_size: '14sp'

<CTI@TextInput>:
    font_name: "''' + F + '''"
    font_size: '14sp'
    foreground_color: 0.12, 0.12, 0.12, 1
    background_color: 0.98, 0.98, 0.98, 1

<SentenceRow>:
    size_hint_y: None
    height: dp(70)
    padding: [dp(8), dp(4)]
    canvas.before:
        Color:
            rgba: self.bg_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(6),]

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(2)

        CT:
            id: time_lbl
            text: root.time_text
            font_size: '11sp'
            color: 0.4, 0.4, 0.4, 1
            size_hint_y: None
            height: dp(18)
            halign: 'left'
            text_size: self.size

        CT:
            id: text_lbl
            text: root.german_text
            font_size: '15sp'
            size_hint_y: None
            height: dp(22)
            halign: 'left'
            text_size: self.width, None

        CT:
            id: cn_lbl
            text: root.chinese_text
            font_size: '12sp'
            color: 0.35, 0.35, 0.35, 1
            size_hint_y: None
            height: dp(18)
            halign: 'left'
            text_size: self.width, None

# ═══════════ 页面1: 文件浏览 ═══════════
<BrowseScreen>:
    name: 'browse'
    BoxLayout:
        orientation: 'vertical'

        # 顶栏
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: [dp(10), 0]
            canvas.before:
                Color:
                    rgba: 0.15, 0.45, 0.7, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            CT:
                text: '选择音频文件'
                font_size: '18sp'
                bold: True
                color: 1, 1, 1, 1

            CB:
                text: '收藏'
                size_hint_x: None
                width: dp(55)
                color: 1, 1, 1, 1
                background_color: 0, 0, 0, 0
                on_press: app.root.current = 'collection'

        # 快捷路径按钮
        BoxLayout:
            size_hint_y: None
            height: dp(38)
            spacing: dp(4)
            padding: [dp(6), dp(2)]

            CB:
                text: '下载目录'
                font_size: '12sp'
                on_press: root.goto_downloads()
                background_color: 0.85, 0.85, 0.85, 1
                color: 0.2, 0.2, 0.2, 1

            CB:
                text: '音乐目录'
                font_size: '12sp'
                on_press: root.goto_music()
                background_color: 0.85, 0.85, 0.85, 1
                color: 0.2, 0.2, 0.2, 1

            CB:
                text: '根目录'
                font_size: '12sp'
                on_press: root.goto_root()
                background_color: 0.85, 0.85, 0.85, 1
                color: 0.2, 0.2, 0.2, 1

        # 文件选择器
        FileChooserListView:
            id: file_chooser
            filters: ['*.mp3', '*.wav', '*.ogg', '*.m4a', '*.flac', '*.wma', '*.aac', '*.mp4', '*.webm']
            on_selection: root.on_file_selected(self.selection)

        # 底部状态
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: [dp(10), dp(4)]

            CT:
                id: browse_status
                text: '请选择音频或视频文件'
                font_size: '13sp'
                color: 0.4, 0.4, 0.4, 1

# ═══════════ 页面2: 播放学习 ═══════════
<StudyScreen>:
    name: 'study'
    BoxLayout:
        orientation: 'vertical'

        # 顶栏
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: [dp(10), 0]
            canvas.before:
                Color:
                    rgba: 0.15, 0.45, 0.7, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            CB:
                text: '< 返回'
                size_hint_x: None
                width: dp(65)
                color: 1, 1, 1, 1
                background_color: 0, 0, 0, 0
                on_press: root.go_back()

            CT:
                id: study_title
                text: '学习'
                font_size: '16sp'
                bold: True
                color: 1, 1, 1, 1
                halign: 'center'

        # ── 播放控制 ──
        BoxLayout:
            size_hint_y: None
            height: dp(88)
            orientation: 'vertical'
            padding: [dp(10), dp(4)]
            spacing: dp(2)
            canvas.before:
                Color:
                    rgba: 0.96, 0.96, 0.96, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            # 进度条
            Slider:
                id: seek_slider
                size_hint_y: None
                height: dp(28)
                min: 0
                max: 100
                value: 0
                cursor_size: (dp(16), dp(16))
                on_touch_up: root.on_seek(self, args[1])

            # 按钮行
            BoxLayout:
                size_hint_y: None
                height: dp(42)
                spacing: dp(8)

                CB:
                    id: play_btn
                    text: '播放'
                    on_press: root.toggle_play()
                    background_color: 0.2, 0.6, 0.8, 1

                CB:
                    text: '停止'
                    on_press: root.stop_audio()
                    background_color: 0.5, 0.5, 0.5, 1

                CT:
                    id: time_label
                    text: '0:00 / 0:00'
                    font_size: '13sp'
                    halign: 'right'
                    size_hint_x: None
                    width: dp(110)

        # ── 操作按钮 ──
        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(6)
            padding: [dp(10), dp(2)]

            CB:
                text: '开始转写'
                on_press: root.start_transcribe()
                background_color: 0.9, 0.55, 0.1, 1
                font_size: '13sp'

            CB:
                text: '收藏当前句'
                on_press: root.collect_current()
                background_color: 0.3, 0.5, 0.8, 1
                font_size: '13sp'

            CB:
                text: '收藏全部'
                on_press: root.collect_all()
                background_color: 0.4, 0.6, 0.9, 1
                font_size: '13sp'

            CB:
                text: '导出Anki'
                on_press: root.export_anki()
                background_color: 0.6, 0.3, 0.8, 1
                font_size: '13sp'

        # ── 进度条 ──
        ProgressBar:
            id: transcribe_progress
            size_hint_y: None
            height: dp(3)
            opacity: 0
            max: 100

        # ── 状态 ──
        CT:
            id: study_status
            text: ''
            size_hint_y: None
            height: dp(22)
            font_size: '11sp'
            color: 0.5, 0.5, 0.5, 1
            padding: [dp(10), 0]

        # ── 句子列表 ──
        ScrollView:
            id: sentence_scroll
            GridLayout:
                id: sentence_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(4)
                padding: [dp(8), dp(4)]

# ═══════════ 页面3: 收藏管理 ═══════════
<CollectionScreen>:
    name: 'collection'
    BoxLayout:
        orientation: 'vertical'

        BoxLayout:
            size_hint_y: None
            height: dp(48)
            padding: [dp(10), 0]
            canvas.before:
                Color:
                    rgba: 0.15, 0.45, 0.7, 1
                Rectangle:
                    pos: self.pos
                    size: self.size

            CB:
                text: '< 返回'
                size_hint_x: None
                width: dp(65)
                color: 1, 1, 1, 1
                background_color: 0, 0, 0, 0
                on_press: app.root.current = 'study'

            CT:
                text: '收藏列表'
                font_size: '18sp'
                bold: True
                color: 1, 1, 1, 1
                halign: 'center'

            CB:
                text: '清空'
                size_hint_x: None
                width: dp(50)
                color: 1, 1, 1, 1
                background_color: 0, 0, 0, 0
                on_press: root.clear_all()

        ScrollView:
            GridLayout:
                id: coll_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(4)
                padding: [dp(8), dp(4)]
'''

Builder.load_string(KV)


# ═══════════ 句子行组件 ═══════════
class SentenceRow(BoxLayout):
    time_text = StringProperty('')
    german_text = StringProperty('')
    chinese_text = StringProperty('')
    bg_color = ListProperty([0.96, 0.96, 0.96, 1])

    def __init__(self, seg_data=None, **kwargs):
        super().__init__(**kwargs)
        self.seg_data = seg_data or {}
        self.is_highlighted = False

    def set_highlight(self, active):
        self.is_highlighted = active
        if active:
            self.bg_color = [0.85, 0.93, 1.0, 1]
        else:
            self.bg_color = [0.96, 0.96, 0.96, 1]


# ═══════════ 页面1: 文件浏览 ═══════════
class BrowseScreen(Screen):

    def on_enter(self):
        # 默认跳到下载目录
        self.goto_downloads()

    def goto_downloads(self):
        dl = os.path.join(get_music_dir(), 'Download')
        if os.path.exists(dl):
            self.ids.file_chooser.path = dl
        else:
            self.ids.file_chooser.path = get_music_dir()

    def goto_music(self):
        music = os.path.join(get_music_dir(), 'Music')
        if os.path.exists(music):
            self.ids.file_chooser.path = music
        else:
            self.ids.file_chooser.path = get_music_dir()

    def goto_root(self):
        if platform == 'android':
            self.ids.file_chooser.path = '/storage/emulated/0'
        else:
            self.ids.file_chooser.path = '/'

    def on_file_selected(self, selection):
        if not selection:
            return
        filepath = selection[0]
        if not os.path.isfile(filepath):
            return

        filename = os.path.basename(filepath)
        size_kb = os.path.getsize(filepath) // 1024
        self.ids.browse_status.text = f'已选择: {filename} ({size_kb}KB)'

        # 跳转到学习页面并加载
        app = App.get_running_app()
        study = app.root.get_screen('study')
        study.load_file(filepath)
        app.root.current = 'study'


# ═══════════ 页面2: 播放学习 ═══════════
class StudyScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.audio_path = None
        self.sound = None
        self.segments = []
        self.sentence_rows = []
        self.current_seg_idx = -1
        self.is_playing = False
        self.update_event = None

    def load_file(self, filepath):
        """加载音频文件"""
        self.audio_path = filepath
        filename = os.path.basename(filepath)
        self.ids.study_title.text = filename[:25]

        # 停止之前的播放
        self._stop_playback()

        # 清空旧句子
        self.ids.sentence_list.clear_widgets()
        self.sentence_rows = []
        self.segments = []
        self.current_seg_idx = -1

        # 加载音频
        self.ids.study_status.text = '正在加载音频...'
        try:
            self.sound = SoundLoader.load(filepath)
            if self.sound:
                duration = self._get_duration()
                if duration > 0:
                    self.ids.seek_slider.max = duration
                    self.ids.time_label.text = f'0:00 / {self._fmt(duration)}'
                    self.ids.study_status.text = f'已加载 {filename} ({self._fmt(duration)})，可播放或转写'
                else:
                    self.ids.seek_slider.max = 9999
                    self.ids.time_label.text = '0:00 / ?:??'
                    self.ids.study_status.text = f'已加载 {filename}，可播放'
            else:
                self.ids.study_status.text = f'无法加载 {filename}，格式可能不支持'
        except Exception as e:
            self.ids.study_status.text = f'加载失败: {e}'
            import traceback
            traceback.print_exc()

    # ── 播放控制 ──
    def toggle_play(self):
        if not self.sound:
            self.ids.study_status.text = '请先选择音频文件'
            return

        if self.is_playing:
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
            try:
                self.sound.play()
                self.is_playing = True
                self.ids.play_btn.text = '暂停'
                self.update_event = Clock.schedule_interval(self._tick, 0.15)
                self.ids.study_status.text = '播放中...'
            except Exception as e:
                self.ids.study_status.text = f'播放失败: {e}'

    def stop_audio(self):
        self._stop_playback()
        self.ids.time_label.text = f'0:00 / {self._fmt(self._get_duration())}'
        self.ids.seek_slider.value = 0
        self._clear_highlights()

    def _stop_playback(self):
        if self.sound:
            try:
                self.sound.stop()
            except Exception:
                pass
        self.is_playing = False
        self.ids.play_btn.text = '播放'
        if self.update_event:
            self.update_event.cancel()
            self.update_event = None

    def _tick(self, dt):
        """播放定时器"""
        if not self.sound or not self.is_playing:
            return
        try:
            pos = self.sound.get_pos()
            dur = self._get_duration()
        except Exception:
            return

        self.ids.seek_slider.value = pos
        self.ids.time_label.text = f'{self._fmt(pos)} / {self._fmt(dur)}'
        self._highlight_at(pos)

        if dur > 0 and pos >= dur - 0.3:
            self._stop_playback()
            self._clear_highlights()
            self.ids.study_status.text = '播放完成'

    def on_seek(self, slider, touch):
        if slider.collide_point(*touch.pos) and self.sound:
            try:
                self.sound.seek(slider.value)
                self._highlight_at(slider.value)
            except Exception:
                pass

    def _highlight_at(self, pos):
        idx = -1
        for i, seg in enumerate(self.segments):
            if seg['start'] <= pos < seg['end']:
                idx = i
                break
        if idx != self.current_seg_idx:
            if 0 <= self.current_seg_idx < len(self.sentence_rows):
                self.sentence_rows[self.current_seg_idx].set_highlight(False)
            if 0 <= idx < len(self.sentence_rows):
                self.sentence_rows[idx].set_highlight(True)
                # 自动滚动
                try:
                    sv = self.ids.sentence_scroll
                    row = self.sentence_rows[idx]
                    layout = self.ids.sentence_list
                    # 简单滚动：设置scroll_y
                    total = layout.height
                    if total > sv.height:
                        row_pos = sum(c.height + layout.spacing for c in list(layout.children)[len(layout.children)-1-idx:])
                        sv.scroll_y = max(0, min(1, 1 - (row_pos / total)))
                except Exception:
                    pass
            self.current_seg_idx = idx

    def _clear_highlights(self):
        for row in self.sentence_rows:
            row.set_highlight(False)
        self.current_seg_idx = -1

    # ── 句子点击 ──
    def on_sentence_tap(self, row):
        seg = row.seg_data
        if seg and self.sound:
            try:
                self.sound.seek(seg['start'])
                self.ids.seek_slider.value = seg['start']
                if not self.is_playing:
                    self.toggle_play()
            except Exception:
                pass

    # ── 转写 ──
    def start_transcribe(self):
        if not self.audio_path:
            self.ids.study_status.text = '请先选择音频文件'
            return

        self.ids.transcribe_progress.opacity = 1
        self.ids.transcribe_progress.value = 0
        self.ids.study_status.text = '正在转写...'

        thread = threading.Thread(target=self._transcribe_thread)
        thread.daemon = True
        thread.start()

    def _transcribe_thread(self):
        try:
            from openai import OpenAI

            Clock.schedule_once(lambda dt: self._set_progress(10, '连接服务器...'), 0)
            client = OpenAI(api_key=API_KEY, base_url=API_BASE)

            Clock.schedule_once(lambda dt: self._set_progress(20, '转写中...'), 0)

            with open(self.audio_path, "rb") as f:
                resp = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="de",
                    response_format="verbose_json"
                )

            segments_raw = []
            for seg in resp.segments:
                segments_raw.append({
                    'start': seg.start,
                    'end': seg.end,
                    'text': seg.text.strip(),
                    'chinese': ''
                })

            Clock.schedule_once(lambda dt: self._set_progress(50, f'转写完成 {len(segments_raw)} 句，翻译中...'), 0)

            # 逐句翻译
            for i, seg in enumerate(segments_raw):
                try:
                    tr = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "将德语翻译为中文，只输出翻译结果。"},
                            {"role": "user", "content": seg['text']}
                        ]
                    )
                    seg['chinese'] = tr.choices[0].message.content.strip()
                except Exception:
                    seg['chinese'] = ''

                pct = 50 + int(45 * (i + 1) / len(segments_raw))
                Clock.schedule_once(lambda dt, p=pct: self._set_progress(p, None), 0)

            Clock.schedule_once(lambda dt: self._build_sentences(segments_raw), 0)
            Clock.schedule_once(lambda dt: self._set_progress(100, f'完成：{len(segments_raw)} 句'), 0)

        except ImportError:
            Clock.schedule_once(lambda dt: self._set_progress(0, '缺少 openai 库'), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._set_progress(0, f'错误: {str(e)[:60]}'), 0)

    def _set_progress(self, value, text):
        if value > 0:
            self.ids.transcribe_progress.value = value
        if value >= 100 or value == 0:
            Clock.schedule_once(lambda dt: setattr(self.ids.transcribe_progress, 'opacity', 0), 2)
        if text:
            self.ids.study_status.text = text

    def _build_sentences(self, segments_data):
        """构建句子列表"""
        self.segments = segments_data
        self.ids.sentence_list.clear_widgets()
        self.sentence_rows = []
        self.current_seg_idx = -1

        for seg in segments_data:
            row = SentenceRow(
                seg_data=seg,
                time_text=self._fmt(seg['start']),
                german_text=seg['text'],
                chinese_text=seg.get('chinese', '')
            )
            row.bind(on_touch_down=lambda inst, touch, r=row: self.on_sentence_tap(r) if inst.collide_point(*touch.pos) else None)
            self.ids.sentence_list.add_widget(row)
            self.sentence_rows.append(row)

    # ── 收藏 ──
    def collect_current(self):
        if 0 <= self.current_seg_idx < len(self.segments):
            seg = self.segments[self.current_seg_idx]
            self._save_item(seg['text'], seg.get('chinese', ''))
        elif self.segments:
            self._save_item('\n'.join(s['text'] for s in self.segments),
                          '\n'.join(s.get('chinese', '') for s in self.segments))
        else:
            self.ids.study_status.text = '没有可收藏的内容'

    def collect_all(self):
        if not self.segments:
            self.ids.study_status.text = '没有可收藏的内容'
            return
        self._save_item('\n'.join(s['text'] for s in self.segments),
                       '\n'.join(s.get('chinese', '') for s in self.segments))

    def _save_item(self, german, chinese):
        try:
            store_path = os.path.join(get_storage_dir(), 'sentences.json')
            store = JsonStore(store_path)
            key = f'item_{int(time.time())}'
            store.put(key, german=german, chinese=chinese)
            count = len(store)
            self.ids.study_status.text = f'已收藏 ({count} 条)'
        except Exception as e:
            self.ids.study_status.text = f'收藏失败: {e}'

    def export_anki(self):
        try:
            store_path = os.path.join(get_storage_dir(), 'sentences.json')
            if not os.path.exists(store_path):
                self.ids.study_status.text = '没有收藏内容'
                return

            store = JsonStore(store_path)
            export_path = os.path.join(get_storage_dir(), 'anki_export.txt')
            count = 0
            with open(export_path, 'w', encoding='utf-8') as f:
                for key in store:
                    item = store.get(key)
                    g = item.get('german', '').replace('\n', ' ').replace('\t', ' ')
                    c = item.get('chinese', '').replace('\n', ' ').replace('\t', ' ')
                    f.write(f'{g}\t{c}\n')
                    count += 1

            self.ids.study_status.text = f'已导出 {count} 条 → anki_export.txt'
        except Exception as e:
            self.ids.study_status.text = f'导出失败: {e}'

    def go_back(self):
        self._stop_playback()
        App.get_running_app().root.current = 'browse'

    # ── 工具方法 ──
    def _get_duration(self):
        try:
            d = getattr(self.sound, 'length', 0)
            return d if d and d > 0 else 0
        except Exception:
            return 0

    @staticmethod
    def _fmt(seconds):
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        return f'{m}:{s:02d}'


# ═══════════ 页面3: 收藏管理 ═══════════
class CollectionScreen(Screen):

    def on_enter(self):
        self.load_data()

    def load_data(self):
        self.ids.coll_list.clear_widgets()
        try:
            store_path = os.path.join(get_storage_dir(), 'sentences.json')
            if not os.path.exists(store_path):
                self.ids.coll_list.add_widget(Label(
                    text='暂无收藏', font_name=F, size_hint_y=None, height=dp(60)
                ))
                return

            store = JsonStore(store_path)
            keys = list(store.keys())
            if not keys:
                self.ids.coll_list.add_widget(Label(
                    text='暂无收藏', font_name=F, size_hint_y=None, height=dp(60)
                ))
                return

            for idx, key in enumerate(reversed(keys)):
                item = store.get(key)
                german = item.get('german', '')
                preview = german[:40].replace('\n', ' ')
                btn = Button(
                    text=f'{len(keys)-idx}. {preview}',
                    font_name=F,
                    font_size='13sp',
                    size_hint_y=None,
                    height=dp(50),
                    background_color=(0.95, 0.95, 0.95, 1),
                    color=(0.1, 0.1, 0.1, 1),
                    halign='left',
                    text_size=(Window.width * 0.8, None)
                )
                btn.bind(on_press=lambda x, k=key: self.show_item(k))
                self.ids.coll_list.add_widget(btn)

        except Exception as e:
            self.ids.coll_list.add_widget(Label(
                text=f'加载失败: {e}', font_name=F, size_hint_y=None, height=dp(60)
            ))

    def show_item(self, key):
        try:
            store_path = os.path.join(get_storage_dir(), 'sentences.json')
            store = JsonStore(store_path)
            item = store.get(key)

            popup = Popup(title='详情', title_font=F, size_hint=(0.92, 0.55))
            content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))

            scroll = ScrollView()
            dl = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(6))
            dl.bind(minimum_height=dl.setter('height'))

            for txt in [f"德语:\n{item['german']}", f"中文:\n{item['chinese']}"]:
                lbl = Label(
                    text=txt, font_name=F,
                    text_size=(Window.width * 0.78, None),
                    size_hint_y=None, halign='left', valign='top'
                )
                lbl.bind(texture_size=lbl.setter('size'))
                dl.add_widget(lbl)
            scroll.add_widget(dl)
            content.add_widget(scroll)

            btns = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(6))
            for txt, color, action in [
                ('复制', (0.3, 0.5, 0.8, 1), lambda x: Clipboard.copy(f"{item['german']}\n\n{item['chinese']}")),
                ('删除', (0.8, 0.3, 0.3, 1), lambda x: (self.delete_item(key), popup.dismiss())),
                ('关闭', (0.5, 0.5, 0.5, 1), lambda x: popup.dismiss())
            ]:
                b = Button(text=txt, font_name=F, background_color=color)
                b.bind(on_press=action)
                btns.add_widget(b)
            content.add_widget(btns)
            popup.content = content
            popup.open()
        except Exception:
            pass

    def delete_item(self, key):
        try:
            store_path = os.path.join(get_storage_dir(), 'sentences.json')
            store = JsonStore(store_path)
            store.delete(key)
            self.load_data()
        except Exception:
            pass

    def clear_all(self):
        try:
            store_path = os.path.join(get_storage_dir(), 'sentences.json')
            if os.path.exists(store_path):
                os.remove(store_path)
            self.load_data()
        except Exception:
            pass


# ═══════════ 应用 ═══════════
class DeutschLernenApp(App):

    def build(self):
        self.title = '德语学习助手'
        self._load_font()

        sm = ScreenManager()
        sm.add_widget(BrowseScreen())     # 首页：文件浏览
        sm.add_widget(StudyScreen())       # 学习页
        sm.add_widget(CollectionScreen())  # 收藏页
        return sm

    def _load_font(self):
        try:
            from kivy.core.text import LabelBase
            if os.path.exists(FONT_PATH):
                LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)
                print(f'字体已加载: {FONT_PATH}')
            else:
                print(f'字体不存在: {FONT_PATH}')
        except Exception as e:
            print(f'字体加载失败: {e}')

    def on_pause(self):
        return True

    def on_resume(self):
        pass


def main():
    DeutschLernenApp().run()


if __name__ == '__main__':
    main()
