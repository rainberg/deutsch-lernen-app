"""
Deutsch Lernen App - 架构设计文档

项目目标：
1. 导入音频/视频文件，自动转写德语内容
2. 提供双语（德语-中文）显示界面
3. 点击单词查看详细解释（词性、释义、例句）
4. 收藏整个例句（含音频、原文、翻译）
5. 导出收藏内容到Anki进行背诵学习

技术架构：
- 前端：PyQt5桌面应用
- 音频处理：pydub + ffmpeg
- 语音转写：OpenAI Whisper（本地运行）
- 翻译：本地翻译模型（transformers + 预训练模型）
- 数据存储：SQLite + SQLAlchemy
- 导出：genanki（生成Anki牌组）

核心模块：
1. audio_processor.py - 音频提取与预处理
2. transcriber.py - 德语语音转写
3. translator.py - 德语→中文翻译
4. word_analyzer.py - 单词分析（词性、释义）
5. database.py - 数据存储（单词、例句、收藏）
6. anki_exporter.py - Anki牌组导出
7. gui_main.py - 主界面

数据流：
1. 用户导入音频/视频 → 提取音频 → Whisper转写 → 分段
2. 分段文本 → 翻译 → 双语显示
3. 用户交互 → 单词点击查询 → 例句收藏
4. 收藏管理 → 导出Anki牌组（含音频片段）

Anki牌组结构：
- 正面：德语例句（音频播放）
- 背面：中文翻译 + 单词解释
- 额外字段：原始音频时间戳、单词详情

扩展性：
- 支持多语言（未来可扩展）
- 插件化翻译/转写引擎
- 云端同步（可选）
"""

# 项目目录结构
PROJECT_STRUCTURE = """
deutsch-lernen-app/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── audio_processor.py    # 音频提取与预处理
│   │   ├── transcriber.py        # 语音转写（Whisper）
│   │   ├── translator.py         # 德语-中文翻译
│   │   ├── word_analyzer.py      # 单词分析与查询
│   │   └── sentence_splitter.py  # 句子分段
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database.py           # SQLite数据库操作
│   │   ├── models.py             # 数据模型定义
│   │   └── repository.py         # 数据访问层
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py        # 主窗口
│   │   ├── audio_player.py       # 音频播放控件
│   │   ├── text_display.py       # 双语文本显示
│   │   ├── word_detail.py        # 单词详情弹窗
│   │   └── collection_manager.py # 收藏管理界面
│   ├── export/
│   │   ├── __init__.py
│   │   ├── anki_exporter.py      # Anki导出器
│   │   └── formats.py            # 导出格式定义
│   └── utils/
│       ├── __init__.py
│       ├── config.py             # 配置文件
│       ├── logger.py             # 日志配置
│       └── helpers.py            # 工具函数
├── tests/
│   ├── __init__.py
│   ├── test_audio.py
│   ├── test_transcription.py
│   └── test_translation.py
├── resources/
│   ├── audio/                    # 示例音频
│   ├── icons/                    # 应用图标
│   └── models/                   # 预训练模型
├── docs/
│   ├── api.md
│   └── user_guide.md
├── .env.example                  # 环境变量示例
├── .gitignore
├── requirements.txt
├── setup.py
└── main.py                       # 应用入口
"""