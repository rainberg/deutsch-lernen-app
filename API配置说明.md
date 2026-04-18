# 德语学习助手 - API模式配置说明

## 概述
本应用现在默认使用云端API进行语音转写，而不是本地Whisper模型。这样可以：
- ✅ 节省本地计算资源
- ✅ 更快的转写速度
- ✅ 无需下载大型模型文件
- ✅ 随时使用最新模型

## 配置信息

### API端点
- **服务提供商**: api2d.net (OpenAI代理)
- **API端点**: https://openai.api2d.net/v1
- **API密钥**: fk201403-hCEJwCHpGTrUkdzzkvBW93gvrWCM9vDm

### 当前配置
```json
{
  "transcription": {
    "use_api": true,
    "api_key": "fk201403-hCEJwCHpGTrUkdzzkvBW93gvrWCM9vDm",
    "api_base": "https://openai.api2d.net/v1"
  }
}
```

## 工作原理

### API模式流程
```
音频文件 → 预处理 → 上传到API → 获取转写结果 → 返回
```

### 支持的功能
1. **语音转写** (transcribe)
   - 将德语语音转写为德语文本
   - 支持多种音频格式

2. **语音翻译** (translate)
   - 将德语语音翻译为英语文本
   - Whisper API特性

## 使用方法

### 1. 基本使用
```python
from src.core.transcriber import WhisperTranscriber

# 创建转写器（自动使用API模式）
transcriber = WhisperTranscriber()

# 转写音频文件
result = transcriber.transcribe_file("audio.mp3", language="de")
print(result.text)
```

### 2. 在GUI中使用
1. 打开应用程序
2. 导入音频/视频文件
3. 点击"开始转写"
4. 系统会自动使用API进行转写

### 3. 命令行使用
```bash
python main.py --process /path/to/audio.mp3
```

## 音频要求

### 支持的格式
- MP3
- MP4
- M4A
- WAV
- FLAC
- OGG
- WEBM

### 文件限制
- **最大文件大小**: 25 MB
- **建议**: 对于长音频，先分割为较小的片段

## 费用说明

### api2d.net 计费
- 按照 OpenAI Whisper API 标准计费
- 约 $0.006 / 分钟
- 建议监控使用量

### 优化建议
1. **预处理音频**
   - 转换为 16kHz 单声道
   - 减小文件大小

2. **批量处理**
   - 一次处理多个短文件
   - 避免重复转写

## 故障排除

### 问题1: API连接失败
**症状**: 无法连接到API服务器
**解决**:
1. 检查网络连接
2. 验证API密钥是否正确
3. 确认api2d.net服务正常

### 问题2: 转写结果为空
**症状**: 返回空文本
**解决**:
1. 检查音频文件是否有声音
2. 确认语言设置正确
3. 尝试其他音频文件

### 问题3: 文件过大
**症状**: 上传失败
**解决**:
1. 使用音频处理工具分割文件
2. 压缩音频质量
3. 转换为更高效的格式

## 切换回本地模式

如果需要切换回本地Whisper模型：

1. 修改 `config.json`:
```json
{
  "transcription": {
    "use_api": false,
    "model_size": "base"
  }
}
```

2. 安装本地依赖:
```bash
pip install openai-whisper torch
```

3. 首次运行会自动下载模型

## 技术细节

### API调用示例
```python
from openai import OpenAI

client = OpenAI(
    api_key="fk201403-hCEJwCHpGTrUkdzzkvBW93gvrWCM9vDm",
    base_url="https://openai.api2d.net/v1"
)

with open("audio.mp3", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language="de",
        response_format="verbose_json"
    )
    print(response.text)
```

### 错误处理
- 自动重试机制
- 详细的错误日志
- 用户友好的错误提示

## 更新日志

### 2026-04-18
- 默认启用API模式
- 配置api2d.net作为API端点
- 优化API调用流程

## 相关链接
- api2d.net: https://api2d.net
- OpenAI Whisper API: https://platform.openai.com/docs/guides/speech-to-text

---

**注意**: 请妥善保管API密钥，不要分享给他人。