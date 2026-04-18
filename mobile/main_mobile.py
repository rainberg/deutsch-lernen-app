"""
德语学习助手 - Kivy版 (用于安卓)
简化版界面，支持核心功能
"""

import os
import sys

# 设置Kivy配置
os.environ['KIVY_LOG_MODE'] = 'MIXED'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock

import threading
import json

# 配置
API_KEY = "fk201403-hCEJwCHpGTrUkdzzkvBW93gvrWCM9vDm"
API_BASE = "https://openai.api2d.net/v1"

# KV语言定义
KV = '''
#:import Factory kivy.factory.Factory

<MainScreen>:
    name: 'main'
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        
        # 标题栏
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            
            Label:
                text: '德语学习助手'
                font_size: '20sp'
                bold: True
        
        # 功能按钮区
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            spacing: dp(10)
            
            Button:
                text: '导入音频'
                on_press: root.import_audio()
                
            Button:
                text: '开始转写'
                on_press: root.start_transcribe()
                
            Button:
                text: '收藏列表'
                on_press: root.show_collection()
        
        # 德语文本区
        BoxLayout:
            orientation: 'vertical'
            
            Label:
                text: '德语原文'
                size_hint_y: None
                height: dp(30)
                halign: 'left'
                text_size: self.size
            
            TextInput:
                id: german_text
                text: ''
                readonly: True
                multiline: True
                size_hint_y: 0.4
        
        # 中文翻译区
        BoxLayout:
            orientation: 'vertical'
            
            Label:
                text: '中文翻译'
                size_hint_y: None
                height: dp(30)
                halign: 'left'
                text_size: self.size
            
            TextInput:
                id: chinese_text
                text: ''
                readonly: True
                multiline: True
                size_hint_y: 0.4
        
        # 操作按钮
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            
            Button:
                text: '收藏句子'
                on_press: root.collect_sentence()
                
            Button:
                text: '复制文本'
                on_press: root.copy_text()
                
            Button:
                text: '导出Anki'
                on_press: root.export_anki()
        
        # 状态栏
        Label:
            id: status_label
            text: '就绪'
            size_hint_y: None
            height: dp(30)

<CollectionScreen>:
    name: 'collection'
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        
        # 标题栏
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            
            Button:
                text: '返回'
                size_hint_x: None
                width: dp(80)
                on_press: root.go_back()
            
            Label:
                text: '收藏列表'
                font_size: '20sp'
                bold: True
        
        # 收藏列表
        ScrollView:
            GridLayout:
                id: collection_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(5)

<WordDetailPopup>:
    title: '单词详情'
    size_hint: 0.9, 0.7
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        spacing: dp(10)
        
        Label:
            id: word_label
            text: ''
            font_size: '24sp'
            bold: True
            size_hint_y: None
            height: dp(40)
        
        Label:
            id: definition_label
            text: ''
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
        
        TextInput:
            id: example_text
            text: ''
            readonly: True
            multiline: True
        
        Button:
            text: '关闭'
            size_hint_y: None
            height: dp(50)
            on_press: root.dismiss()
'''

# 加载KV语言
Builder.load_string(KV)

class MainScreen(Screen):
    """主屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_audio = None
        self.collected_sentences = []
    
    def import_audio(self):
        """导入音频文件"""
        if platform == 'android':
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self.on_audio_selected,
                filters=["*.mp3", "*.wav", "*.m4a", "*.ogg", "*.mp4"]
            )
        else:
            self.ids.status_label.text = '请在安卓设备上使用文件选择器'
    
    def on_audio_selected(self, selection):
        """音频文件选择回调"""
        if selection:
            self.current_audio = selection[0]
            filename = os.path.basename(self.current_audio)
            self.ids.status_label.text = f'已选择: {filename}'
    
    def start_transcribe(self):
        """开始转写"""
        if not self.current_audio:
            self.show_popup('提示', '请先导入音频文件')
            return
        
        self.ids.status_label.text = '正在转写...'
        
        # 在后台线程中处理
        thread = threading.Thread(target=self._process_audio)
        thread.start()
    
    def _process_audio(self):
        """处理音频（后台线程）"""
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=API_KEY,
                base_url=API_BASE
            )
            
            # 转写
            with open(self.current_audio, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="de",
                    response_format="text"
                )
            
            german_text = response if isinstance(response, str) else response.text
            
            # 翻译
            translation_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "请将德语翻译为中文"},
                    {"role": "user", "content": german_text}
                ]
            )
            
            chinese_text = translation_response.choices[0].message.content
            
            # 更新UI
            Clock.schedule_once(lambda dt: self._update_ui(german_text, chinese_text), 0)
            
        except Exception as e:
            Clock.schedule_once(lambda dt: self.ids.status_label.text.setText(f'错误: {e}'), 0)
    
    def _update_ui(self, german_text, chinese_text):
        """更新UI"""
        self.ids.german_text.text = german_text
        self.ids.chinese_text.text = chinese_text
        self.ids.status_label.text = '转写完成'
    
    def collect_sentence(self):
        """收藏句子"""
        german = self.ids.german_text.text
        chinese = self.ids.chinese_text.text
        
        if german and chinese:
            self.collected_sentences.append({
                'german': german,
                'chinese': chinese
            })
            self.ids.status_label.text = f'已收藏 ({len(self.collected_sentences)}条)'
        else:
            self.show_popup('提示', '没有可收藏的内容')
    
    def show_collection(self):
        """显示收藏列表"""
        app = App.get_running_app()
        collection_screen = app.root.get_screen('collection')
        collection_screen.update_list(self.collected_sentences)
        app.root.current = 'collection'
    
    def copy_text(self):
        """复制文本"""
        from kivy.core.clipboard import Clipboard
        
        german = self.ids.german_text.text
        chinese = self.ids.chinese_text.text
        
        text = f"德语: {german}\n\n中文: {chinese}"
        Clipboard.copy(text)
        self.ids.status_label.text = '已复制到剪贴板'
    
    def export_anki(self):
        """导出Anki"""
        self.show_popup('提示', 'Anki导出功能开发中...')
    
    def show_popup(self, title, message):
        """显示弹窗"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()

class CollectionScreen(Screen):
    """收藏屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sentences = []
    
    def update_list(self, sentences):
        """更新列表"""
        self.sentences = sentences
        self.ids.collection_list.clear_widgets()
        
        for item in sentences:
            btn = Button(
                text=item['german'][:50] + '...',
                size_hint_y=None,
                height=dp(60)
            )
            btn.bind(on_press=lambda x, i=item: self.show_detail(i))
            self.ids.collection_list.add_widget(btn)
    
    def show_detail(self, item):
        """显示详情"""
        popup = Popup(
            title='句子详情',
            size_hint=(0.9, 0.5)
        )
        
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=f"德语: {item['german']}", text_size=(Window.width*0.8, None)))
        content.add_widget(Label(text=f"中文: {item['chinese']}", text_size=(Window.width*0.8, None)))
        
        close_btn = Button(text='关闭', size_hint_y=None, height=50)
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.content = content
        popup.open()
    
    def go_back(self):
        """返回主屏幕"""
        app = App.get_running_app()
        app.root.current = 'main'

class WordDetailPopup(Popup):
    """单词详情弹窗"""
    pass

class DeutschLernenApp(App):
    """德语学习助手应用"""
    
    def build(self):
        """构建界面"""
        self.title = '德语学习助手'
        
        # 创建屏幕管理器
        sm = ScreenManager()
        sm.add_widget(MainScreen())
        sm.add_widget(CollectionScreen())
        
        return sm
    
    def on_pause(self):
        """应用暂停"""
        return True
    
    def on_resume(self):
        """应用恢复"""
        pass

def main():
    """主函数"""
    DeutschLernenApp().run()

if __name__ == '__main__':
    main()