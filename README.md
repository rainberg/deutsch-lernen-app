# 德语学习助手 - Deutsch Lernen App

一个用于德语学习的桌面应用程序，支持音频/视频转写、翻译、单词查询、例句收藏和Anki导出功能。

## 功能特性

### 核心功能
1. **音频/视频转写** - 支持多种音频格式，使用Whisper进行德语语音转写
2. **双语显示** - 德语原文和中文翻译对照显示
3. **单词查询** - 点击单词查看详细解释（词性、释义、例句）
4. **例句收藏** - 收藏重要的例句进行重点学习
5. **Anki导出** - 将收藏内容导出到Anki牌组进行背诵

### 技术特性
- **本地处理** - 支持本地Whisper模型，无需网络连接
- **离线词典** - 内置德语词典，支持快速查询
- **数据库存储** - 使用SQLite数据库存储学习记录
- **可扩展架构** - 模块化设计，易于扩展新功能

## 项目结构

```
deutsch-lernen-app/
├── src/                    # 源代码目录
│   ├── core/              # 核心功能模块
│   │   ├── audio_processor.py    # 音频处理
│   │   ├── transcriber.py        # 语音转写
│   │   ├── translator.py         # 翻译模块
│   │   ├── word_analyzer.py      # 单词分析
│   │   └── sentence_splitter.py  # 句子分段
│   ├── data/              # 数据层
│   │   ├── models.py             # 数据模型
│   │   ├── database.py           # 数据库管理
│   │   └── repository.py         # 数据访问层
│   ├── gui/               # 图形界面
│   │   ├── main_window.py        # 主窗口
│   │   ├── audio_player.py       # 音频播放器
│   │   ├── text_display.py       # 文本显示
│   │   ├── word_detail.py        # 单词详情
│   │   └── collection_manager.py # 收藏管理
│   ├── export/            # 导出功能
│   │   └── anki_exporter.py      # Anki导出
│   └── utils/             # 工具模块
│       ├── config.py             # 配置管理
│       ├── logger.py             # 日志系统
│       └── helpers.py            # 工具函数
├── tests/                 # 测试文件
├── resources/             # 资源文件
│   ├── audio/             # 音频文件
│   ├── models/            # 模型文件
│   └── exports/           # 导出文件
├── main.py               # 主程序入口
├── requirements.txt      # 依赖列表
└── config.json          # 配置文件
```

## 安装和运行

### 环境要求
- Python 3.8+
- PyQt5
- FFmpeg（用于音频处理）

### 安装步骤

1. **克隆项目**
```bash
cd /home/deutsch-lernen-app
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **安装FFmpeg**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

### 运行应用程序

1. **图形界面模式**
```bash
python main.py
```

2. **命令行模式**
```bash
python main.py --cli
```

3. **处理音频文件**
```bash
python main.py --process /path/to/audio/file.mp3 --output /path/to/output
```

## 使用说明

### 图形界面操作

1. **导入音频/视频文件**
   - 点击"打开文件"按钮
   - 选择音频或视频文件
   - 支持格式：MP3, WAV, FLAC, M4A, OGG, MP4, AVI, MKV等

2. **语音转写**
   - 导入文件后，点击"开始转写"按钮
   - 系统将自动识别德语语音并转写为文本

3. **单词查询**
   - 在转写结果中点击任意单词
   - 系统将显示单词的详细解释

4. **收藏句子**
   - 选中要收藏的句子
   - 点击"收藏句子"按钮

5. **导出到Anki**
   - 点击"导出到Anki"按钮
   - 系统将生成.apkg文件，可直接导入Anki

### 配置说明

配置文件`config.json`包含以下设置：

```json
{
  "app": {
    "name": "Deutsch Lernen App",
    "version": "0.1.0"
  },
  "transcription": {
    "model_size": "base",
    "language": "de"
  },
  "translation": {
    "model_name": "Helsinki-NLP/opus-mt-de-zh",
    "source_lang": "de",
    "target_lang": "zh"
  }
}
```

## 开发说明

### 运行测试
```bash
python test_app.py
```

### 代码结构
- **src/core/** - 核心业务逻辑
- **src/data/** - 数据访问层
- **src/gui/** - 图形界面组件
- **src/export/** - 导出功能
- **src/utils/** - 工具函数

### 扩展开发
1. 添加新的翻译模型：修改`translator.py`
2. 添加新的词典：修改`word_analyzer.py`
3. 添加新的导出格式：在`export/`目录添加新模块

## 已知问题

1. **PyQt5依赖问题** - 某些系统可能需要额外安装系统依赖
2. **Whisper模型下载** - 首次使用需要下载模型文件
3. **FFmpeg路径** - 需要确保FFmpeg在系统PATH中

## 许可证

本项目采用MIT许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 项目地址：/home/deutsch-lernen-app
- 配置文件：config.json

## 更新日志

### v0.1.0 (2026-04-18)
- 初始版本发布
- 实现基本功能：
  - 音频/视频转写
  - 德语-中文翻译
  - 单词查询
  - 例句收藏
  - Anki导出
- 图形界面支持
- 数据库存储
- 配置管理