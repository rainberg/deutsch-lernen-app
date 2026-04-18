"""
德语语音转中文处理管道
实现: 德语语音 → 德语文本 → 中文翻译
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class SpeechToTextResult:
    """语音转文本结果"""
    german_text: str  # 德语转写文本
    chinese_text: str  # 中文翻译
    segments: List[Dict[str, Any]]  # 分段信息
    confidence: float  # 置信度
    processing_time: float  # 处理时间（秒）

class GermanSpeechToChinese:
    """德语语音转中文处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.config = get_config()
        
        # 初始化OpenAI客户端
        self._init_client()
        
        logger.info("德语语音转中文处理器初始化完成")
    
    def _init_client(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            
            # 获取配置
            api_key = self.config.get("transcription.api_key")
            api_base = self.config.get("transcription.api_base")
            
            # 创建客户端
            self.client = OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            
            logger.info(f"OpenAI客户端初始化完成 (API: {api_base})")
            
        except ImportError:
            raise ImportError("请安装openai包: pip install openai")
        except Exception as e:
            raise RuntimeError(f"初始化OpenAI客户端失败: {e}")
    
    def process_audio(self, audio_path: str, language: str = "de") -> SpeechToTextResult:
        """
        处理音频文件：德语语音 → 中文翻译
        
        Args:
            audio_path: 音频文件路径
            language: 源语言代码（默认德语）
            
        Returns:
            SpeechToTextResult对象
        """
        import time
        start_time = time.time()
        
        logger.info(f"开始处理音频: {audio_path}")
        
        try:
            # 步骤1: 语音转写 (德语语音 → 德语文本)
            logger.info("步骤1: 语音转写 (德语语音 → 德语文本)")
            german_text, segments = self._transcribe_audio(audio_path, language)
            
            if not german_text:
                raise RuntimeError("语音转写结果为空")
            
            logger.info(f"转写完成: {len(german_text)} 字符")
            
            # 步骤2: 文本翻译 (德语文本 → 中文翻译)
            logger.info("步骤2: 文本翻译 (德语文本 → 中文翻译)")
            chinese_text = self._translate_text(german_text)
            
            if not chinese_text:
                raise RuntimeError("翻译结果为空")
            
            logger.info(f"翻译完成: {len(chinese_text)} 字符")
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 返回结果
            result = SpeechToTextResult(
                german_text=german_text,
                chinese_text=chinese_text,
                segments=segments,
                confidence=0.95,  # API模式默认置信度
                processing_time=processing_time
            )
            
            logger.info(f"处理完成，耗时: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"处理音频失败: {e}")
            raise
    
    def _transcribe_audio(self, audio_path: str, language: str) -> tuple:
        """
        使用Whisper API转写音频
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码
            
        Returns:
            (转写文本, 分段信息)
        """
        try:
            # 检查文件大小
            file_size = os.path.getsize(audio_path)
            max_size = 25 * 1024 * 1024  # 25MB
            
            if file_size > max_size:
                logger.warning(f"音频文件过大 ({file_size / 1024 / 1024:.1f}MB)，建议分割")
            
            # 调用Whisper API
            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            # 解析响应
            text = response.text if hasattr(response, 'text') else ""
            
            # 解析分段信息
            segments = []
            if hasattr(response, 'segments'):
                for seg in response.segments:
                    segments.append({
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "").strip()
                    })
            
            return text, segments
            
        except Exception as e:
            logger.error(f"语音转写失败: {e}")
            raise
    
    def _translate_text(self, german_text: str) -> str:
        """
        使用GPT API翻译德语文本为中文
        
        Args:
            german_text: 德语文本
            
        Returns:
            中文翻译
        """
        try:
            # 构建翻译提示
            prompt = f"""请将以下德语文本翻译为中文。保持原文的意思和语气，翻译要自然流畅。

德语原文:
{german_text}

中文翻译:"""
            
            # 调用GPT API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "你是一个专业的德语-中文翻译助手。请将用户提供的德语文本准确翻译为中文。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # 提取翻译结果
            chinese_text = response.choices[0].message.content.strip()
            
            return chinese_text
            
        except Exception as e:
            logger.error(f"文本翻译失败: {e}")
            raise
    
    def process_batch(self, audio_paths: List[str], language: str = "de") -> List[SpeechToTextResult]:
        """
        批量处理音频文件
        
        Args:
            audio_paths: 音频文件路径列表
            language: 源语言代码
            
        Returns:
            SpeechToTextResult列表
        """
        results = []
        
        for i, audio_path in enumerate(audio_paths, 1):
            logger.info(f"处理文件 {i}/{len(audio_paths)}: {audio_path}")
            
            try:
                result = self.process_audio(audio_path, language)
                results.append(result)
            except Exception as e:
                logger.error(f"处理文件失败 {audio_path}: {e}")
                # 创建失败结果
                results.append(SpeechToTextResult(
                    german_text="",
                    chinese_text=f"处理失败: {e}",
                    segments=[],
                    confidence=0.0,
                    processing_time=0.0
                ))
        
        return results

# 便捷函数
def german_speech_to_chinese(audio_path: str) -> Dict[str, str]:
    """
    德语语音转中文（便捷函数）
    
    Args:
        audio_path: 音频文件路径
        
    Returns:
        包含german_text和chinese_text的字典
    """
    processor = GermanSpeechToChinese()
    result = processor.process_audio(audio_path)
    
    return {
        "german_text": result.german_text,
        "chinese_text": result.chinese_text,
        "processing_time": result.processing_time
    }

# 测试函数
def test_speech_to_chinese():
    """测试语音转中文功能"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python speech_to_chinese.py <音频文件路径>")
        return
    
    audio_path = sys.argv[1]
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在 - {audio_path}")
        return
    
    print(f"处理音频: {audio_path}")
    print("=" * 50)
    
    try:
        result = german_speech_to_chinese(audio_path)
        
        print("\n【德语转写】")
        print(result["german_text"])
        
        print("\n【中文翻译】")
        print(result["chinese_text"])
        
        print(f"\n处理时间: {result['processing_time']:.2f}秒")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    test_speech_to_chinese()