"""
德语学习助手 - 安卓简化版
最小化依赖，适合打包测试
"""

import os
os.environ['KIVY_LOG_MODE'] = 'MIXED'

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
import threading

# KV语言定义
KV = '''
<MainScreen>:
    name: 'main'
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(15)
        spacing: dp(10)
        
        # 标题
        Label:
            text: '德语学习助手'
            font_size: '24sp'
            bold: True
            size_hint_y: None
            height: dp(60)
            color: 0.2, 0.6, 0.8, 1
        
        # 德语输入区
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(5)
            
            Label:
                text: '德语原文'
                size_hint_y: None
                height: dp(30)
                halign: 'left'
                text_size: self.size
            
            TextInput:
                id: german_input
                hint_text: '在此输入德语文本...'
                multiline: True
        
        # 中文翻译区
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(5)
            
            Label:
                text: '中文翻译'
                size_hint_y: None
                height: dp(30)
                halign: 'left'
                text_size: self.size
            
            TextInput:
                id: chinese_output
                hint_text: '翻译结果将显示在这里...'
                readonly: True
                multiline: True
        
        # 操作按钮
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            spacing: dp(10)
            
            Button:
                text: '翻译'
                on_press: root.translate_text()
                background_color: 0.2, 0.7, 0.3, 1
            
            Button:
                text: '清空'
                on_press: root.clear_text()
                background_color: 0.8, 0.3, 0.3, 1
            
            Button:
                text: '收藏'
                on_press: root.save_to_collection()
                background_color: 0.3, 0.5, 0.8, 1
        
        # 快捷词按钮
        BoxLayout:
            size_hint_y: None
            height: dp(45)
            spacing: dp(5)
            
            Button:
                text: 'Hallo'
                on_press: root.add_word('Hallo')
                font_size: '12sp'
            
            Button:
                text: 'Danke'
                on_press: root.add_word('Danke')
                font_size: '12sp'
            
            Button:
                text: 'Bitte'
                on_press: root.add_word('Bitte')
                font_size: '12sp'
            
            Button:
                text: 'Tschüss'
                on_press: root.add_word('Tschüss')
                font_size: '12sp'
        
        # 状态栏
        Label:
            id: status
            text: '就绪'
            size_hint_y: None
            height: dp(30)
            font_size: '12sp'
            color: 0.5, 0.5, 0.5, 1

<CollectionScreen>:
    name: 'collection'
    
    BoxLayout:
        orientation: 'vertical'
        padding: dp(10)
        
        BoxLayout:
            size_hint_y: None
            height: dp(50)
            
            Button:
                text: '< 返回'
                size_hint_x: None
                width: dp(80)
                on_press: root.go_back()
            
            Label:
                text: '收藏列表'
                font_size: '20sp'
                bold: True
        
        ScrollView:
            GridLayout:
                id: list_layout
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(5)
'''

Builder.load_string(KV)

class MainScreen(Screen):
    """主屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = None
        self.init_storage()
    
    def init_storage(self):
        """初始化存储"""
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                path = os.path.join(app_storage_path(), 'collection.json')
            else:
                path = 'collection.json'
            self.store = JsonStore(path)
        except:
            self.store = None
    
    def translate_text(self):
        """翻译文本（简化版：使用本地词典）"""
        german = self.ids.german_input.text.strip()
        
        if not german:
            self.ids.status.text = '请输入德语文本'
            return
        
        self.ids.status.text = '翻译中...'
        
        # 简单的本地词典翻译
        dictionary = {
            'hallo': '你好',
            'danke': '谢谢',
            'bitte': '请；不客气',
            'tschüss': '再见',
            'guten morgen': '早上好',
            'guten tag': '你好/日安',
            'guten abend': '晚上好',
            'ja': '是',
            'nein': '不',
            'wie geht es ihnen': '您好吗',
            'ich bin': '我是',
            'gut': '好',
            'schlecht': '坏',
            'wasser': '水',
            'essen': '吃',
            'trinken': '喝',
            'schlafen': '睡觉',
            'arbeiten': '工作',
            'lernen': '学习',
            'sprechen': '说',
        }
        
        # 尝试翻译
        german_lower = german.lower()
        if german_lower in dictionary:
            chinese = dictionary[german_lower]
        else:
            chinese = f"[本地词典未找到] {german}"
        
        self.ids.chinese_output.text = chinese
        self.ids.status.text = '翻译完成'
    
    def clear_text(self):
        """清空文本"""
        self.ids.german_input.text = ''
        self.ids.chinese_output.text = ''
        self.ids.status.text = '已清空'
    
    def add_word(self, word):
        """添加快捷词"""
        current = self.ids.german_input.text
        if current:
            self.ids.german_input.text = current + ' ' + word
        else:
            self.ids.german_input.text = word
    
    def save_to_collection(self):
        """保存到收藏"""
        german = self.ids.german_input.text.strip()
        chinese = self.ids.chinese_output.text.strip()
        
        if not german or not chinese:
            self.ids.status.text = '没有可收藏的内容'
            return
        
        if self.store:
            try:
                import time
                key = f"item_{int(time.time())}"
                self.store.put(key, german=german, chinese=chinese)
                self.ids.status.text = f'已收藏'
            except Exception as e:
                self.ids.status.text = f'收藏失败: {e}'
        else:
            self.ids.status.text = '存储未初始化'
    
    def show_collection(self):
        """显示收藏"""
        app = App.get_running_app()
        app.root.current = 'collection'

class CollectionScreen(Screen):
    """收藏屏幕"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = None
    
    def on_enter(self):
        """进入屏幕时刷新列表"""
        self.load_collection()
    
    def load_collection(self):
        """加载收藏"""
        self.ids.list_layout.clear_widgets()
        
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                path = os.path.join(app_storage_path(), 'collection.json')
            else:
                path = 'collection.json'
            
            if os.path.exists(path):
                store = JsonStore(path)
                for key in store:
                    item = store.get(key)
                    btn = Button(
                        text=f"{item['german'][:30]}...",
                        size_hint_y=None,
                        height=dp(50)
                    )
                    btn.bind(on_press=lambda x, i=item: self.show_item(i))
                    self.ids.list_layout.add_widget(btn)
            
            if len(self.ids.list_layout.children) == 0:
                self.ids.list_layout.add_widget(
                    Label(text='暂无收藏', size_hint_y=None, height=dp(50))
                )
        except Exception as e:
            self.ids.list_layout.add_widget(
                Label(text=f'加载失败: {e}', size_hint_y=None, height=dp(50))
            )
    
    def show_item(self, item):
        """显示详情"""
        popup = Popup(
            title='收藏详情',
            size_hint=(0.9, 0.5)
        )
        
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        content.add_widget(Label(text=f"德语: {item['german']}", halign='left'))
        content.add_widget(Label(text=f"中文: {item['chinese']}", halign='left'))
        
        close_btn = Button(text='关闭', size_hint_y=None, height=dp(50))
        close_btn.bind(on_press=popup.dismiss)
        content.add_widget(close_btn)
        
        popup.content = content
        popup.open()
    
    def go_back(self):
        """返回"""
        app = App.get_running_app()
        app.root.current = 'main'

class DeutschLernenApp(App):
    """德语学习助手"""
    
    def build(self):
        self.title = '德语学习助手'
        
        sm = ScreenManager()
        sm.add_widget(MainScreen())
        sm.add_widget(CollectionScreen())
        
        return sm

if __name__ == '__main__':
    DeutschLernenApp().run()