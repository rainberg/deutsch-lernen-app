"""
语音转写模块
使用OpenAI Whisper进行德语语音转写
支持本地模型和API两种模式
"""

import os
import tempfile
import warnings
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import logging
import json

import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class TranscriptionResult:
    """转写结果"""
    text: str  # 完整转写文本
    segments: List[Dict[str, Any]]  # 分段信息
    language: str  # 检测到的语言
    confidence: float  # 整体置信度
    model_used: str  # 使用的模型

@dataclass
class TranscriptionSegment:
    """转写分段"""
    start: float  # 开始时间（秒）
    end: float  # 结束时间（秒）
    text: str  # 转写文本
    confidence: float  # 置信度
    words: Optional[List[Dict]] = None  # 单词级别的时间戳（可选）

class WhisperTranscriber:
    """Whisper语音转写器"""
    
    # Whisper模型大小选项（从大到小）
    MODEL_SIZES = ["large-v3", "large-v2", "medium", "small", "base", "tiny"]
    
    def __init__(self, model_size: str = "base", device: Optional[str] = None,
                 model_dir: Optional[str] = None, use_api: bool = False,
                 api_key: Optional[str] = None, api_base: Optional[str] = None):
        """
        初始化Whisper转写器
        
        Args:
            model_size: 模型大小（tiny, base, small, medium, large-v2, large-v3）
            device: 设备（cuda, cpu, auto）
            model_dir: 模型存储目录
            use_api: 是否使用API（而不是本地模型）
            api_key: OpenAI API密钥（如使用API）
            api_base: API基础URL（用于自定义端点）
        """
        self.model_size = model_size
        self.model_dir = model_dir
        self.use_api = use_api
        self.api_key = api_key
        self.api_base = api_base
        
        if not use_api:
            # 本地模型模式
            self._init_local_model(device)
        else:
            # API模式
            self._init_api_client()
            
        logger.info(f"Whisper转写器初始化完成（{'API模式' if use_api else '本地模型'}）")
    
    def _init_local_model(self, device: Optional[str] = None):
        """初始化本地Whisper模型"""
        try:
            import whisper
            self.whisper = whisper
            
            # 自动选择设备
            if device is None:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            logger.info(f"加载Whisper模型: {self.model_size}, 设备: {device}")
            
            # 加载模型
            self.model = whisper.load_model(
                name=self.model_size,
                device=device,
                download_root=self.model_dir
            )
            
            self.device = device
            
        except ImportError:
            raise ImportError(
                "请安装openai-whisper包: pip install openai-whisper"
            )
        except Exception as e:
            raise RuntimeError(f"加载Whisper模型失败: {e}")
    
    def _init_api_client(self):
        """初始化API客户端"""
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base if self.api_base else None
            )
        except ImportError:
            raise ImportError(
                "请安装openai包以使用API模式: pip install openai"
            )
        except Exception as e:
            raise RuntimeError(f"初始化OpenAI客户端失败: {e}")
    
    def transcribe_file(self, audio_path: str, language: str = "de", 
                       task: str = "transcribe", **kwargs) -> TranscriptionResult:
        """
        转写音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（如"de"表示德语）
            task: 任务类型（transcribe或translate）
            **kwargs: 额外参数传递给Whisper
            
        Returns:
            TranscriptionResult对象
        """
        logger.info(f"开始转写: {audio_path}, 语言: {language}, 任务: {task}")
        
        if self.use_api:
            return self._transcribe_with_api(audio_path, language, task, **kwargs)
        else:
            return self._transcribe_local(audio_path, language, task, **kwargs)
    
    def _transcribe_local(self, audio_path: str, language: str, task: str, **kwargs) -> TranscriptionResult:
        """使用本地模型转写"""
        try:
            # 设置转写参数
            options = {
                "language": language,
                "task": task,
                "fp16": False if self.device == "cpu" else True,
                "verbose": False,
                **kwargs
            }
            
            # 执行转写
            result = self.model.transcribe(audio_path, **options)
            
            # 解析结果
            segments = []
            for seg in result.get("segments", []):
                segment = {
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"].strip(),
                    "confidence": seg.get("confidence", 0.0),
                    "words": seg.get("words", None)
                }
                segments.append(segment)
            
            return TranscriptionResult(
                text=result["text"].strip(),
                segments=segments,
                language=result.get("language", language),
                confidence=np.mean([s.get("confidence", 0.0) for s in segments]) if segments else 0.0,
                model_used=f"whisper-{self.model_size}"
            )
            
        except Exception as e:
            logger.error(f"本地转写失败: {e}")
            raise RuntimeError(f"语音转写失败: {e}")
    
    def _transcribe_with_api(self, audio_path: str, language: str, task: str, **kwargs) -> TranscriptionResult:
        """使用API转写"""
        try:
            with open(audio_path, "rb") as audio_file:
                # 准备API请求参数
                api_kwargs = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "language": language,
                    "response_format": "verbose_json",
                    **kwargs
                }
                
                if task == "translate" and language != "en":
                    # 翻译为非英语语言（Whisper API只支持翻译为英语）
                    api_kwargs["task"] = "translate"
                
                # 调用API
                response = self.client.audio.transcriptions.create(**api_kwargs)
                
                # 解析响应
                if hasattr(response, 'text'):
                    # 标准响应格式
                    text = response.text
                    segments = getattr(response, 'segments', [])
                else:
                    # JSON响应格式
                    response_dict = json.loads(response) if isinstance(response, str) else response
                    text = response_dict.get("text", "")
                    segments = response_dict.get("segments", [])
                
                # 转换为标准格式
                formatted_segments = []
                for seg in segments:
                    formatted_segments.append({
                        "start": seg.get("start", 0),
                        "end": seg.get("end", 0),
                        "text": seg.get("text", "").strip(),
                        "confidence": seg.get("confidence", 0.0),
                        "words": seg.get("words", None)
                    })
                
                return TranscriptionResult(
                    text=text.strip(),
                    segments=formatted_segments,
                    language=language,
                    confidence=np.mean([s.get("confidence", 0.0) for s in formatted_segments]) if formatted_segments else 0.0,
                    model_used="whisper-api"
                )
                
        except Exception as e:
            logger.error(f"API转写失败: {e}")
            raise RuntimeError(f"API语音转写失败: {e}")
    
    def transcribe_segment(self, audio_path: str, start_time: float, end_time: float,
                          language: str = "de", **kwargs) -> Optional[TranscriptionSegment]:
        """
        转写音频片段
        
        Args:
            audio_path: 音频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            language: 语言代码
            **kwargs: 额外参数
            
        Returns:
            TranscriptionSegment对象或None（如失败）
        """
        try:
            # 提取音频片段到临时文件
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name
            
            # 使用ffmpeg提取片段
            import subprocess
            cmd = [
                "ffmpeg", "-y",
                "-i", audio_path,
                "-ss", str(start_time),
                "-to", str(end_time),
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                temp_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 转写临时文件
            result = self.transcribe_file(temp_path, language=language, **kwargs)
            
            # 清理临时文件
            os.unlink(temp_path)
            
            if result.segments:
                # 调整时间戳
                seg = result.segments[0]
                return TranscriptionSegment(
                    start=start_time + seg["start"],
                    end=start_time + seg["end"],
                    text=seg["text"],
                    confidence=seg["confidence"],
                    words=seg.get("words")
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"片段转写失败: {e}")
            return None
    
    def detect_language(self, audio_path: str) -> Tuple[str, float]:
        """
        检测音频语言
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            (语言代码, 置信度) 元组
        """
        if self.use_api:
            # API模式不支持直接语言检测
            logger.warning("API模式不支持独立语言检测，使用默认德语")
            return "de", 0.9
        
        try:
            # 加载音频
            import whisper
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # 计算mel spectrogram
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # 检测语言
            _, probs = self.model.detect_language(mel)
            language = max(probs, key=probs.get)
            confidence = float(probs[language])
            
            logger.info(f"检测到语言: {language} (置信度: {confidence:.2f})")
            return language, confidence
            
        except Exception as e:
            logger.error(f"语言检测失败: {e}")
            return "de", 0.5
    
    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        if self.use_api:
            return ["whisper-1"]
        else:
            return self.MODEL_SIZES
    
    @staticmethod
    def get_language_name(code: str) -> str:
        """获取语言名称"""
        language_names = {
            "de": "德语",
            "en": "英语",
            "zh": "中文",
            "fr": "法语",
            "es": "西班牙语",
            "ja": "日语",
            "ko": "韩语"
        }
        return language_names.get(code, code)

class TranscriptionPipeline:
    """转写处理管道"""
    
    def __init__(self, transcriber: WhisperTranscriber, min_segment_duration: float = 2.0):
        """
        初始化转写管道
        
        Args:
            transcriber: Whisper转写器实例
            min_segment_duration: 最小分段时长（秒）
        """
        self.transcriber = transcriber
        self.min_segment_duration = min_segment_duration
    
    def process_audio(self, audio_path: str, language: str = "de", 
                     split_strategy: str = "whisper") -> List[TranscriptionSegment]:
        """
        处理音频文件，返回分段转写结果
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码
            split_strategy: 分段策略（"whisper"使用Whisper分段，"fixed"固定时长，"silence"静音分割）
            
        Returns:
            转写分段列表
        """
        logger.info(f"开始处理音频: {audio_path}")
        
        if split_strategy == "whisper":
            # 使用Whisper自带的分段
            result = self.transcriber.transcribe_file(audio_path, language=language)
            segments = []
            
            for seg in result.segments:
                duration = seg["end"] - seg["start"]
                if duration >= self.min_segment_duration:
                    segment = TranscriptionSegment(
                        start=seg["start"],
                        end=seg["end"],
                        text=seg["text"],
                        confidence=seg["confidence"],
                        words=seg.get("words")
                    )
                    segments.append(segment)
            
            return segments
            
        elif split_strategy in ["fixed", "silence"]:
            # 需要先分割音频，再分别转写
            # 这里简化处理，直接使用Whisper分段
            logger.warning(f"分段策略 '{split_strategy}' 暂未完全实现，使用Whisper分段")
            return self.process_audio(audio_path, language, split_strategy="whisper")
        
        else:
            raise ValueError(f"不支持的分段策略: {split_strategy}")
    
    def merge_segments(self, segments: List[TranscriptionSegment], 
                      max_gap: float = 1.0, max_length: float = 15.0) -> List[TranscriptionSegment]:
        """
        合并相邻的分段
        
        Args:
            segments: 原始分段列表
            max_gap: 最大允许间隔（秒），小于此值则合并
            max_length: 合并后最大时长（秒）
            
        Returns:
            合并后的分段列表
        """
        if not segments:
            return []
        
        merged = []
        current = segments[0]
        
        for next_seg in segments[1:]:
            gap = next_seg.start - current.end
            
            # 检查是否应该合并
            should_merge = (
                gap <= max_gap and
                (next_seg.end - current.start) <= max_length
            )
            
            if should_merge:
                # 合并分段
                current = TranscriptionSegment(
                    start=current.start,
                    end=next_seg.end,
                    text=current.text + " " + next_seg.text,
                    confidence=(current.confidence + next_seg.confidence) / 2,
                    words=(current.words or []) + (next_seg.words or []) if current.words or next_seg.words else None
                )
            else:
                # 保存当前分段，开始新的分段
                merged.append(current)
                current = next_seg
        
        # 添加最后一个分段
        merged.append(current)
        
        logger.info(f"分段合并完成: {len(segments)} -> {len(merged)}")
        return merged

# 简单工厂函数
def create_transcriber(model_size: str = "base", use_api: bool = False, **kwargs) -> WhisperTranscriber:
    """创建转写器实例"""
    return WhisperTranscriber(model_size=model_size, use_api=use_api, **kwargs)