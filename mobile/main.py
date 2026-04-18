"""
德语学习助手 - 安卓版 v0.2
核心功能：音频转写德语 → 中文翻译 → 点词查义 → 收藏 → Anki导出
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
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.core.clipboard import Clipboard
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
#:import Factory kivy.factory.Factory
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

<WordButton@Button>:
    font_name: "''' + FONT_NAME + '''"
    font_size: '16sp'
    background_color: 0.95, 0.95, 0.95, 1
    color: 0.1, 0.1, 0.1, 1
    size_hint_y: None
    height: dp(36)

<MainScreen>:
    name: 'main'

    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(8)

        # ── 标题栏 ──
        BoxLayout:
            size_hint_y: None
            height: dp(45)

            CustomLabel:
                text: '德语学习助手'
                font_size: '22sp'
                bold: True
                halign: 'left'
                text_size: self.size
                color: 0.15, 0.45, 0.7, 1

            CustomButton:
                text: '收藏'
                size_hint_x: None
                width: dp(60)
                background_color: 0.3, 0.5, 0.8, 1
                on_press: root.show_collection()

        # ── 功能按钮 ──
        BoxLayout:
            size_hint_y: None
            height: dp(45)
            spacing: dp(8)

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

        # ── 德语原文区 ──
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(4)

            CustomLabel:
                text: '德语原文（点击单词查义）'
                size_hint_y: None
                height: dp(25)
                halign: 'left'
                text_size: self.size
                font_size: '13sp'
                color: 0.4, 0.4, 0.4, 1

            ScrollView:
                id: german_scroll
                do_scroll_x: False
                CustomTextInput:
                    id: german_text
                    hint_text: '转写的德语文本将显示在这里...'
                    multiline: True
                    readonly: True
                    size_hint_y: None
                    height: max(self.minimum_height, dp(100))

        # ── 中文翻译区 ──
        BoxLayout:
            orientation: 'vertical'
            spacing: dp(4)

            CustomLabel:
                text: '中文翻译'
                size_hint_y: None
                height: dp(25)
                halign: 'left'
                text_size: self.size
                font_size: '13sp'
                color: 0.4, 0.4, 0.4, 1

            ScrollView:
                id: chinese_scroll
                do_scroll_x: False
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
            height: dp(45)
            spacing: dp(8)

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
            height: dp(4)
            opacity: 0
            max: 100

        # ── 状态栏 ──
        CustomLabel:
            id: status_label
            text: '就绪'
            size_hint_y: None
            height: dp(25)
            font_size: '12sp'
            color: 0.5, 0.5, 0.5, 1

<CollectionScreen>:
    name: 'collection'

    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(8)

        # 标题栏
        BoxLayout:
            size_hint_y: None
            height: dp(45)

            CustomButton:
                text: '< 返回'
                size_hint_x: None
                width: dp(70)
                background_color: 0.5, 0.5, 0.5, 1
                on_press: root.go_back()

            CustomLabel:
                text: '收藏列表'
                font_size: '20sp'
                bold: True
                halign: 'center'

            CustomButton:
                text: '清空'
                size_hint_x: None
                width: dp(60)
                background_color: 0.8, 0.3, 0.3, 1
                on_press: root.clear_collection()

        # 列表
        ScrollView:
            GridLayout:
                id: collection_list
                cols: 1
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(6)

<WordDetailPopup>:
    title: '单词详情'
    title_font: "''' + FONT_NAME + '''"
    size_hint: 0.92, 0.7

    BoxLayout:
        orientation: 'vertical'
        padding: dp(12)
        spacing: dp(10)

        CustomLabel:
            id: word_label
            text: ''
            font_size: '26sp'
            bold: True
            size_hint_y: None
            height: dp(45)

        CustomLabel:
            id: pos_label
            text: ''
            font_size: '13sp'
            color: 0.5, 0.5, 0.5, 1
            size_hint_y: None
            height: dp(22)

        ScrollView:
            CustomLabel:
                id: definition_label
                text: ''
                text_size: self.width - dp(10), None
                size_hint_y: None
                height: self.texture_size[1]
                halign: 'left'
                valign: 'top'

        CustomLabel:
            id: example_label
            text: ''
            font_size: '13sp'
            color: 0.3, 0.3, 0.3, 1
            text_size: self.width - dp(10), None
            size_hint_y: None
            height: self.texture_size[1]
            halign: 'left'

        BoxLayout:
            size_hint_y: None
            height: dp(45)
            spacing: dp(10)

            CustomButton:
                text: '收藏单词'
                background_color: 0.3, 0.5, 0.8, 1
                on_press: root.collect_word()

            CustomButton:
                text: '关闭'
                background_color: 0.5, 0.5, 0.5, 1
                on_press: root.dismiss()
'''

Builder.load_string(KV)


# ── 简易德语词典 ──
GERMAN_DICT = {
    'hallo': {'pos': 'int.', 'def': '你好', 'ex': 'Hallo, wie geht es Ihnen? (您好！)'},
    'danke': {'pos': 'int.', 'def': '谢谢', 'ex': 'Danke schön! (非常感谢！)'},
    'bitte': {'pos': 'int.', 'def': '请；不客气', 'ex': 'Bitte schön. (不客气。)'},
    'tschüss': {'pos': 'int.', 'def': '再见', 'ex': 'Tschüss, bis morgen! (再见，明天见！)'},
    'ja': {'pos': 'adv.', 'def': '是，对', 'ex': 'Ja, das ist richtig. (是的，这是对的。)'},
    'nein': {'pos': 'adv.', 'def': '不，不是', 'ex': 'Nein, danke. (不，谢谢。)'},
    'gut': {'pos': 'adj.', 'def': '好的，良好的', 'ex': 'Mir geht es gut. (我很好。)'},
    'schlecht': {'pos': 'adj.', 'def': '坏的，不好的', 'ex': 'Das Wetter ist schlecht. (天气不好。)'},
    'wasser': {'pos': 'n.', 'def': '水', 'ex': 'Ein Glas Wasser, bitte. (请来一杯水。)'},
    'essen': {'pos': 'v.', 'def': '吃', 'ex': 'Wir essen zusammen. (我们一起吃饭。)'},
    'trinken': {'pos': 'v.', 'def': '喝', 'ex': 'Möchten Sie trinken? (您想喝点什么吗？)'},
    'schlafen': {'pos': 'v.', 'def': '睡觉', 'ex': 'Ich möchte schlafen. (我想睡觉。)'},
    'arbeiten': {'pos': 'v.', 'def': '工作', 'ex': 'Er arbeitet viel. (他工作很多。)'},
    'lernen': {'pos': 'v.', 'def': '学习', 'ex': 'Ich lerne Deutsch. (我学德语。)'},
    'sprechen': {'pos': 'v.', 'def': '说，讲', 'ex': 'Sprechen Sie Englisch? (您说英语吗？)'},
    'gehen': {'pos': 'v.', 'def': '去，走', 'ex': 'Ich gehe nach Hause. (我回家。)'},
    'kommen': {'pos': 'v.', 'def': '来', 'ex': 'Woher kommen Sie? (您从哪里来？)'},
    'haben': {'pos': 'v.', 'def': '有', 'ex': 'Ich habe Hunger. (我饿了。)'},
    'sein': {'pos': 'v.', 'def': '是；在', 'ex': 'Ich bin müde. (我累了。)'},
    'machen': {'pos': 'v.', 'def': '做，制作', 'ex': 'Was machst du? (你在做什么？)'},
    'wissen': {'pos': 'v.', 'def': '知道', 'ex': 'Ich weiß nicht. (我不知道。)'},
    'sehen': {'pos': 'v.', 'def': '看，看见', 'ex': 'Kannst du das sehen? (你能看见那个吗？)'},
    'hören': {'pos': 'v.', 'def': '听', 'ex': 'Hör zu! (听着！)'},
    'sagen': {'pos': 'v.', 'def': '说，告诉', 'ex': 'Was sagst du? (你说什么？)'},
    'geben': {'pos': 'v.', 'def': '给', 'ex': 'Gib mir das Buch. (把书给我。)'},
    'nehmen': {'pos': 'v.', 'def': '拿，取', 'ex': 'Nimm Platz. (请坐。)'},
    'mögen': {'pos': 'v.', 'def': '喜欢', 'ex': 'Ich mag Musik. (我喜欢音乐。)'},
    'können': {'pos': 'v.', 'def': '能，会', 'ex': 'Ich kann schwimmen. (我会游泳。)'},
    'müssen': {'pos': 'v.', 'def': '必须', 'ex': 'Du musst lernen. (你必须学习。)'},
    'wollen': {'pos': 'v.', 'def': '想要', 'ex': 'Ich will reisen. (我想旅行。)'},
    'sollen': {'pos': 'v.', 'def': '应该', 'ex': 'Du sollst lesen. (你应该阅读。)'},
    'dürfen': {'pos': 'v.', 'def': '被允许', 'ex': 'Darf ich? (我可以吗？)'},
    'ich': {'pos': 'pron.', 'def': '我', 'ex': 'Ich bin Student. (我是学生。)'},
    'du': {'pos': 'pron.', 'def': '你', 'ex': 'Wie alt bist du? (你多大了？)'},
    'er': {'pos': 'pron.', 'def': '他', 'ex': 'Er kommt aus Deutschland. (他来自德国。)'},
    'sie': {'pos': 'pron.', 'def': '她；他们', 'ex': 'Sie ist Lehrerin. (她是老师。)'},
    'es': {'pos': 'pron.', 'def': '它', 'ex': 'Es regnet. (下雨了。)'},
    'wir': {'pos': 'pron.', 'def': '我们', 'ex': 'Wir sind Freunde. (我们是朋友。)'},
    'ihr': {'pos': 'pron.', 'def': '你们', 'ex': 'Ihr seid nett. (你们很好。)'},
    'der': {'pos': 'art.', 'def': '这/那个（阳性）', 'ex': 'Der Mann ist groß. (那个男人很高。)'},
    'die': {'pos': 'art.', 'def': '这/那个（阴性/复数）', 'ex': 'Die Kinder spielen. (孩子们在玩。)'},
    'das': {'pos': 'art.', 'def': '这/那个（中性）', 'ex': 'Das ist interessant. (这很有趣。)'},
    'ein': {'pos': 'art.', 'def': '一个（阳性/中性）', 'ex': 'Ich habe ein Buch. (我有一本书。)'},
    'eine': {'pos': 'art.', 'def': '一个（阴性）', 'ex': 'Das ist eine Frage. (这是一个问题。)'},
    'und': {'pos': 'konj.', 'def': '和，与', 'ex': 'Tom und Maria (汤姆和玛丽)'},
    'oder': {'pos': 'konj.', 'def': '或者', 'ex': 'Kaffee oder Tee? (咖啡还是茶？)'},
    'aber': {'pos': 'konj.', 'def': '但是', 'ex': 'Er ist klein, aber stark. (他矮小但强壮。)'},
    'weil': {'pos': 'konj.', 'def': '因为', 'ex': 'Weil es kalt ist. (因为天气冷。)'},
    'dass': {'pos': 'konj.', 'def': '（引导从句）', 'ex': 'Ich weiß, dass du recht hast. (我知道你是对的。)'},
    'mit': {'pos': 'präp.', 'def': '和...一起，用', 'ex': 'Ich komme mit dem Bus. (我坐公交来。)'},
    'von': {'pos': 'präp.', 'def': '从...，...的', 'ex': 'Von wem ist das? (这是谁的？)'},
    'zu': {'pos': 'präp.', 'def': '到，去', 'ex': 'Zum Bahnhof, bitte. (请去火车站。)'},
    'in': {'pos': 'präp.', 'def': '在...里面', 'ex': 'Im Zimmer (在房间里)'},
    'auf': {'pos': 'präp.', 'def': '在...上面', 'ex': 'Auf dem Tisch (在桌子上)'},
    'für': {'pos': 'präp.', 'def': '为了', 'ex': 'Das ist für dich. (这是给你的。)'},
    'nicht': {'pos': 'adv.', 'def': '不，没有', 'ex': 'Das ist nicht gut. (这不好。)'},
    'auch': {'pos': 'adv.', 'def': '也', 'ex': 'Ich auch. (我也是。)'},
    'noch': {'pos': 'adv.', 'def': '还，仍然', 'ex': 'Noch ein Bier, bitte. (请再来一杯啤酒。)'},
    'nur': {'pos': 'adv.', 'def': '只，仅仅', 'ex': 'Nur eine Frage. (只有一个问题。)'},
    'sehr': {'pos': 'adv.', 'def': '非常', 'ex': 'Sehr gut! (非常好！)'},
    'heute': {'pos': 'adv.', 'def': '今天', 'ex': 'Heute ist Montag. (今天是星期一。)'},
    'morgen': {'pos': 'adv.', 'def': '明天', 'ex': 'Morgen ist frei. (明天有空。)'},
    'gestern': {'pos': 'adv.', 'def': '昨天', 'ex': 'Gestern war kalt. (昨天很冷。)'},
    'immer': {'pos': 'adv.', 'def': '总是', 'ex': 'Immer wieder. (一再地。)'},
    'hier': {'pos': 'adv.', 'def': '这里', 'ex': 'Komm hierher! (来这里！)'},
    'dort': {'pos': 'adv.', 'def': '那里', 'ex': 'Dort drüben. (在那边。)'},
    'wo': {'pos': 'adv.', 'def': '哪里', 'ex': 'Wo ist das Klo? (洗手间在哪里？)'},
    'was': {'pos': 'pron.', 'def': '什么', 'ex': 'Was ist das? (这是什么？)'},
    'wer': {'pos': 'pron.', 'def': '谁', 'ex': 'Wer bist du? (你是谁？)'},
    'wie': {'pos': 'adv.', 'def': '怎样，如何', 'ex': 'Wie geht es Ihnen? (您好吗？)'},
    'warum': {'pos': 'adv.', 'def': '为什么', 'ex': 'Warum nicht? (为什么不？)'},
    'wann': {'pos': 'adv.', 'def': '什么时候', 'ex': 'Wann beginnt es? (什么时候开始？)'},
    'mutter': {'pos': 'f.', 'def': '母亲', 'ex': 'Meine Mutter kocht. (我妈妈在做饭。)'},
    'vater': {'pos': 'm.', 'def': '父亲', 'ex': 'Mein Vater arbeitet. (我爸爸在工作。)'},
    'kind': {'pos': 'n.', 'def': '孩子', 'ex': 'Das Kind spielt. (孩子在玩。)'},
    'frau': {'pos': 'f.', 'def': '女人；妻子', 'ex': 'Die Frau liest. (那个女人在看书。)'},
    'mann': {'pos': 'm.', 'def': '男人；丈夫', 'ex': 'Der Mann läuft. (那个男人在跑步。)'},
    'haus': {'pos': 'n.', 'def': '房子，家', 'ex': 'Ich bin zu Hause. (我在家。)'},
    'schule': {'pos': 'f.', 'def': '学校', 'ex': 'Die Schule beginnt um 8. (学校8点开始。)'},
    'buch': {'pos': 'n.', 'def': '书', 'ex': 'Das Buch ist interessant. (这本书很有趣。)'},
    'auto': {'pos': 'n.', 'def': '汽车', 'ex': 'Das Auto ist schnell. (这辆车很快。)'},
    'straße': {'pos': 'f.', 'def': '街道', 'ex': 'Die Straße ist lang. (这条街很长。)'},
    'stadt': {'pos': 'f.', 'def': '城市', 'ex': 'Berlin ist eine große Stadt. (柏林是一个大城市。)'},
    'land': {'pos': 'n.', 'def': '国家；乡村', 'ex': 'Deutschland ist schön. (德国很美。)'},
    'freund': {'pos': 'm.', 'def': '朋友（男）', 'ex': 'Er ist mein Freund. (他是我的朋友。)'},
    'zeit': {'pos': 'f.', 'def': '时间', 'ex': 'Ich habe keine Zeit. (我没时间。)'},
    'tag': {'pos': 'm.', 'def': '天；白天', 'ex': 'Guten Tag! (您好！)'},
    'jahr': {'pos': 'n.', 'def': '年', 'ex': 'Ein Jahr hat 365 Tage. (一年有365天。)'},
    'leben': {'pos': 'n./v.', 'def': '生活；活着', 'ex': 'Das Leben ist schön. (生活是美好的。)'},
    'arzt': {'pos': 'm.', 'def': '医生（男）', 'ex': 'Ich gehe zum Arzt. (我去看医生。)'},
    'essen': {'pos': 'n.', 'def': '食物', 'ex': 'Das Essen ist lecker. (这食物很好吃。)'},
    'brot': {'pos': 'n.', 'def': '面包', 'ex': 'Ich esse Brot. (我吃面包。)'},
    'kaffee': {'pos': 'm.', 'def': '咖啡', 'ex': 'Einen Kaffee, bitte. (请来一杯咖啡。)'},
    'bier': {'pos': 'n.', 'def': '啤酒', 'ex': 'Ein Bier, bitte. (请来一杯啤酒。)'},
    'rot': {'pos': 'adj.', 'def': '红色的', 'ex': 'Ein rotes Auto. (一辆红色的车。)'},
    'blau': {'pos': 'adj.', 'def': '蓝色的', 'ex': 'Der Himmel ist blau. (天空是蓝色的。)'},
    'groß': {'pos': 'adj.', 'def': '大的', 'ex': 'Ein großer Hund. (一条大狗。)'},
    'klein': {'pos': 'adj.', 'def': '小的', 'ex': 'Ein kleines Kind. (一个小孩子。)'},
    'neu': {'pos': 'adj.', 'def': '新的', 'ex': 'Das ist neu. (这是新的。)'},
    'alt': {'pos': 'adj.', 'def': '老的；旧的', 'ex': 'Wie alt bist du? (你多大了？)'},
    'schön': {'pos': 'adj.', 'def': '美丽的，漂亮的', 'ex': 'Das ist schön! (这真美！)'},
    'schnell': {'pos': 'adj.', 'def': '快的', 'ex': 'Er ist schnell. (他很快。)'},
    'langsam': {'pos': 'adj.', 'def': '慢的', 'ex': 'Bitte langsam. (请慢一点。)'},
    'richtig': {'pos': 'adj.', 'def': '正确的', 'ex': 'Das ist richtig. (这是对的。)'},
    'falsch': {'pos': 'adj.', 'def': '错误的', 'ex': 'Das ist falsch. (这是错的。)'},
    'müde': {'pos': 'adj.', 'def': '疲倦的', 'ex': 'Ich bin müde. (我累了。)'},
    'hungrig': {'pos': 'adj.', 'def': '饿的', 'ex': 'Ich bin hungrig. (我饿了。)'},
    'durstig': {'pos': 'adj.', 'def': '渴的', 'ex': 'Ich bin durstig. (我渴了。)'},
    'glücklich': {'pos': 'adj.', 'def': '幸福的，快乐的', 'ex': 'Ich bin glücklich. (我很幸福。)'},
    'traurig': {'pos': 'adj.', 'def': '悲伤的', 'ex': 'Er ist traurig. (他很悲伤。)'},
    'guten morgen': {'pos': 'int.', 'def': '早上好', 'ex': 'Guten Morgen! Wie geht es Ihnen? (早上好！您好吗？)'},
    'guten tag': {'pos': 'int.', 'def': '你好/日安', 'ex': 'Guten Tag, darf ich vorstellen? (您好，请允许我介绍。)'},
    'guten abend': {'pos': 'int.', 'def': '晚上好', 'ex': 'Guten Abend! (晚上好！)'},
    'gute nacht': {'pos': 'int.', 'def': '晚安', 'ex': 'Gute Nacht! (晚安！)'},
    'auf wiedersehen': {'pos': 'int.', 'def': '再见', 'ex': 'Auf Wiedersehen! (再见！)'},
    'wie geht es': {'pos': 'phr.', 'def': '怎么样', 'ex': 'Wie geht es Ihnen? (您怎么样？)'},
    'ich bin': {'pos': 'phr.', 'def': '我是', 'ex': 'Ich bin Student. (我是学生。)'},
    'es gibt': {'pos': 'phr.', 'def': '有，存在', 'ex': 'Es gibt viele Möglichkeiten. (有很多可能性。)'},
}


class MainScreen(Screen):
    """主屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_audio_path = None
        self.collected_sentences = []
        self.store = None
        self.init_storage()

    def init_storage(self):
        """初始化本地存储"""
        try:
            if platform == 'android':
                from android.storage import app_storage_path
                path = os.path.join(app_storage_path(), 'sentences.json')
            else:
                path = os.path.join(os.path.dirname(__file__), 'sentences.json')
            self.store = JsonStore(path)
            # 加载已有收藏
            for key in self.store:
                item = self.store.get(key)
                self.collected_sentences.append({
                    'german': item.get('german', ''),
                    'chinese': item.get('chinese', '')
                })
        except Exception as e:
            print(f"存储初始化失败: {e}")
            self.store = None

    def import_audio(self):
        """导入音频文件"""
        if platform == 'android':
            try:
                from plyer import filechooser
                filechooser.open_file(
                    on_selection=self.on_audio_selected,
                    filters=["*.mp3", "*.wav", "*.m4a", "*.ogg", "*.mp4", "*.flac"]
                )
            except Exception as e:
                self.ids.status_label.text = f'文件选择器错误: {e}'
        else:
            self.ids.status_label.text = '请在安卓设备上使用文件选择器'

    def on_audio_selected(self, selection):
        """文件选择回调"""
        if selection:
            self.current_audio_path = selection[0]
            filename = os.path.basename(self.current_audio_path)
            self.ids.status_label.text = f'已选择: {filename}'

    def start_transcribe(self):
        """开始转写"""
        if not self.current_audio_path:
            self.show_popup('提示', '请先点击"导入音频"选择音频文件')
            return

        self.ids.status_label.text = '正在转写，请稍候...'
        self.ids.progress.opacity = 1
        self.ids.progress.value = 20

        # 后台线程处理
        thread = threading.Thread(target=self._transcribe_thread)
        thread.daemon = True
        thread.start()

    def _transcribe_thread(self):
        """转写线程"""
        try:
            from openai import OpenAI

            Clock.schedule_once(lambda dt: self._set_status('连接服务器...'), 0)

            client = OpenAI(api_key=API_KEY, base_url=API_BASE)

            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'value', 40), 0)
            Clock.schedule_once(lambda dt: self._set_status('正在转写音频...'), 0)

            # 转写
            with open(self.current_audio_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f,
                    language="de",
                    response_format="text"
                )

            german_text = response if isinstance(response, str) else str(response)

            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'value', 70), 0)
            Clock.schedule_once(lambda dt: self._set_status('正在翻译...'), 0)

            # 翻译
            translation_response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个德语翻译助手。请将以下德语文本翻译为中文。只输出翻译结果，不要加任何说明。"},
                    {"role": "user", "content": german_text}
                ]
            )
            chinese_text = translation_response.choices[0].message.content

            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'value', 100), 0)
            Clock.schedule_once(lambda dt: self._update_result(german_text, chinese_text), 0)

        except ImportError:
            Clock.schedule_once(
                lambda dt: self._set_status('错误: 缺少openai库'), 0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._set_status(f'错误: {str(e)[:80]}'), 0
            )
        finally:
            Clock.schedule_once(lambda dt: setattr(self.ids.progress, 'opacity', 0), 3)

    def _set_status(self, text):
        self.ids.status_label.text = text

    def _update_result(self, german_text, chinese_text):
        """更新结果显示"""
        self.ids.german_text.text = german_text
        self.ids.chinese_text.text = chinese_text
        self.ids.status_label.text = f'转写完成 ({len(german_text)}字)'
        self.ids.progress.value = 100

    def collect_sentence(self):
        """收藏当前句子"""
        german = self.ids.german_text.text.strip()
        chinese = self.ids.chinese_text.text.strip()

        if not german:
            self.ids.status_label.text = '没有可收藏的内容'
            return

        item = {'german': german, 'chinese': chinese}
        self.collected_sentences.append(item)

        if self.store:
            try:
                key = f"item_{int(time.time())}"
                self.store.put(key, german=german, chinese=chinese)
            except Exception as e:
                print(f"保存失败: {e}")

        self.ids.status_label.text = f'已收藏 ({len(self.collected_sentences)}条)'

    def show_collection(self):
        """显示收藏列表"""
        app = App.get_running_app()
        collection_screen = app.root.get_screen('collection')
        collection_screen.load_sentences(self.collected_sentences)
        app.root.current = 'collection'

    def copy_text(self):
        """复制文本"""
        german = self.ids.german_text.text
        chinese = self.ids.chinese_text.text

        if german or chinese:
            text = f"德语: {german}\n\n中文: {chinese}"
            Clipboard.copy(text)
            self.ids.status_label.text = '已复制到剪贴板'
        else:
            self.ids.status_label.text = '没有内容可复制'

    def clear_all(self):
        """清空所有内容"""
        self.ids.german_text.text = ''
        self.ids.chinese_text.text = ''
        self.ids.status_label.text = '已清空'

    def export_anki(self):
        """导出到Anki（生成制表符分隔的txt文件）"""
        if not self.collected_sentences:
            self.show_popup('提示', '没有收藏的句子，请先收藏一些句子')
            return

        try:
            if platform == 'android':
                from android.storage import app_storage_path
                export_dir = app_storage_path()
            else:
                export_dir = os.path.dirname(__file__)

            filepath = os.path.join(export_dir, 'anki_export.txt')

            with open(filepath, 'w', encoding='utf-8') as f:
                # Anki导入格式：正面\t背面
                for item in self.collected_sentences:
                    german = item['german'].replace('\n', ' ').replace('\t', ' ')
                    chinese = item['chinese'].replace('\n', ' ').replace('\t', ' ')
                    f.write(f"{german}\t{chinese}\n")

            self.ids.status_label.text = f'已导出 {len(self.collected_sentences)} 条到 anki_export.txt'
            self.show_popup('导出成功', f'文件已保存到:\n{filepath}\\n\n在Anki中选择"文件→导入"，选择制表符分隔。')

        except Exception as e:
            self.show_popup('导出失败', str(e))

    def show_popup(self, title, message):
        """显示弹窗"""
        popup = Popup(
            title=title,
            title_font=FONT_NAME,
            size_hint=(0.85, None),
            height=dp(200)
        )
        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
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
            height=dp(45),
            background_color=(0.2, 0.6, 0.8, 1)
        )
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.content = content
        popup.open()


class CollectionScreen(Screen):
    """收藏屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sentences = []

    def load_sentences(self, sentences):
        """加载收藏列表"""
        self.sentences = sentences
        self.ids.collection_list.clear_widgets()

        if not sentences:
            self.ids.collection_list.add_widget(Label(
                text='暂无收藏',
                font_name=FONT_NAME,
                size_hint_y=None,
                height=dp(60)
            ))
            return

        for i, item in enumerate(reversed(sentences)):
            german_preview = item['german'][:50].replace('\n', ' ')
            btn = Button(
                text=f"{len(sentences)-i}. {german_preview}...",
                font_name=FONT_NAME,
                font_size='13sp',
                size_hint_y=None,
                height=dp(55),
                background_color=(0.95, 0.95, 0.95, 1),
                color=(0.1, 0.1, 0.1, 1),
                halign='left',
                text_size=(Window.width * 0.8, None)
            )
            btn.bind(on_press=lambda x, idx=len(sentences)-1-i: self.show_detail(idx))
            self.ids.collection_list.add_widget(btn)

    def show_detail(self, index):
        """显示详情"""
        if index >= len(self.sentences):
            return

        item = self.sentences[index]

        popup = Popup(
            title='收藏详情',
            title_font=FONT_NAME,
            size_hint=(0.92, 0.6)
        )

        content = BoxLayout(orientation='vertical', padding=dp(12), spacing=dp(10))

        scroll = ScrollView()
        detail_layout = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        detail_layout.bind(minimum_height=detail_layout.setter('height'))

        german_label = Label(
            text=f"德语:\n{item['german']}",
            font_name=FONT_NAME,
            text_size=(Window.width * 0.8, None),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        german_label.bind(texture_size=german_label.setter('size'))

        chinese_label = Label(
            text=f"中文:\n{item['chinese']}",
            font_name=FONT_NAME,
            text_size=(Window.width * 0.8, None),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        chinese_label.bind(texture_size=chinese_label.setter('size'))

        detail_layout.add_widget(german_label)
        detail_layout.add_widget(chinese_label)
        scroll.add_widget(detail_layout)
        content.add_widget(scroll)

        # 按钮
        btn_layout = BoxLayout(size_hint_y=None, height=dp(45), spacing=dp(8))

        copy_btn = Button(
            text='复制',
            font_name=FONT_NAME,
            background_color=(0.3, 0.5, 0.8, 1)
        )
        copy_btn.bind(on_press=lambda x: self._copy_item(item))

        del_btn = Button(
            text='删除',
            font_name=FONT_NAME,
            background_color=(0.8, 0.3, 0.3, 1)
        )
        del_btn.bind(on_press=lambda x: (self._delete_item(index), popup.dismiss()))

        close_btn = Button(
            text='关闭',
            font_name=FONT_NAME,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        close_btn.bind(on_press=popup.dismiss)

        btn_layout.add_widget(copy_btn)
        btn_layout.add_widget(del_btn)
        btn_layout.add_widget(close_btn)
        content.add_widget(btn_layout)

        popup.content = content
        popup.open()

    def _copy_item(self, item):
        text = f"德语: {item['german']}\n\n中文: {item['chinese']}"
        Clipboard.copy(text)

    def _delete_item(self, index):
        if 0 <= index < len(self.sentences):
            self.sentences.pop(index)
            self.load_sentences(self.sentences)

    def clear_collection(self):
        """清空收藏"""
        self.sentences.clear()
        self.ids.collection_list.clear_widgets()
        self.ids.collection_list.add_widget(Label(
            text='已清空',
            font_name=FONT_NAME,
            size_hint_y=None,
            height=dp(60)
        ))

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
        self.title = '德语学习助手'
        self._load_font()

        sm = ScreenManager()
        sm.add_widget(MainScreen())
        sm.add_widget(CollectionScreen())
        return sm

    def _load_font(self):
        """加载中文字体"""
        from kivy.core.text import LabelBase
        if os.path.exists(FONT_PATH):
            LabelBase.register(name=FONT_NAME, fn_regular=FONT_PATH)
            print(f"字体加载成功: {FONT_PATH}")
        else:
            print(f"字体文件不存在: {FONT_PATH}，将使用默认字体")

    def on_pause(self):
        return True

    def on_resume(self):
        pass


def main():
    DeutschLernenApp().run()


if __name__ == '__main__':
    main()
