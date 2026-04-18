"""
音频处理器
处理音频/视频文件的导入、提取、分段和格式转换
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
import logging

from pydub import AudioSegment as PydubAudioSegment
from pydub.silence import split_on_silence
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AudioInfo:
    """音频文件信息"""
    filepath: str
    filename: str
    format: str
    duration: float  # 秒
    filesize: int  # 字节
    sample_rate: int
    channels: int
    bit_depth: Optional[int] = None

@dataclass
class AudioSegment:
    """音频分段"""
    start_time: float  # 秒
    end_time: float  # 秒
    duration: float
    audio_data: Optional[np.ndarray] = None  # 原始音频数据（可选）
    filepath: Optional[str] = None  # 分段文件路径（如已导出）

class AudioProcessor:
    """音频处理器"""
    
    SUPPORTED_AUDIO_FORMATS = ['.mp3', '.wav', '.flac', '.m4a', '.ogg']
    SUPPORTED_VIDEO_FORMATS = ['.mp4', '.avi', '.mkv', '.mov', '.wmv']
    
    def __init__(self, ffmpeg_path: Optional[str] = None):
        """
        初始化音频处理器
        
        Args:
            ffmpeg_path: ffmpeg可执行文件路径，如为None则自动查找
        """
        self.ffmpeg_path = ffmpeg_path or self._find_ffmpeg()
        if not self.ffmpeg_path:
            raise RuntimeError("未找到ffmpeg，请安装ffmpeg并将其添加到PATH中")
            
        logger.info(f"使用ffmpeg路径: {self.ffmpeg_path}")
    
    @staticmethod
    def _find_ffmpeg() -> Optional[str]:
        """查找系统ffmpeg路径"""
        for path in ['ffmpeg', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']:
            try:
                subprocess.run([path, '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                return path
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        return None
    
    def get_audio_info(self, filepath: str) -> AudioInfo:
        """
        获取音频/视频文件信息
        
        Args:
            filepath: 文件路径
            
        Returns:
            AudioInfo对象
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"文件不存在: {filepath}")
            
        # 使用ffprobe获取文件信息
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a:0',
            '-show_entries', 'stream=duration,sample_rate,channels,bits_per_sample:format=size',
            '-of', 'json',
            filepath
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            info = json.loads(result.stdout)
            
            stream = info['streams'][0] if info['streams'] else {}
            format_info = info.get('format', {})
            
            duration = float(stream.get('duration', 0))
            sample_rate = int(stream.get('sample_rate', 44100))
            channels = int(stream.get('channels', 2))
            bit_depth = int(stream.get('bits_per_sample', 0)) or None
            filesize = int(format_info.get('size', 0))
            
            filename = os.path.basename(filepath)
            file_format = os.path.splitext(filename)[1].lower()
            
            return AudioInfo(
                filepath=filepath,
                filename=filename,
                format=file_format,
                duration=duration,
                filesize=filesize,
                sample_rate=sample_rate,
                channels=channels,
                bit_depth=bit_depth
            )
            
        except (subprocess.CalledProcessError, KeyError, json.JSONDecodeError) as e:
            logger.warning(f"ffprobe失败，使用pydub获取基本信息: {e}")
            # 回退到pydub
            try:
                audio = PydubAudioSegment.from_file(filepath)
                return AudioInfo(
                    filepath=filepath,
                    filename=os.path.basename(filepath),
                    format=os.path.splitext(filepath)[1].lower(),
                    duration=len(audio) / 1000.0,  # pydub使用毫秒
                    filesize=os.path.getsize(filepath),
                    sample_rate=audio.frame_rate,
                    channels=audio.channels,
                    bit_depth=audio.sample_width * 8
                )
            except Exception as e2:
                raise RuntimeError(f"无法获取音频信息: {e2}")
    
    def extract_audio(self, input_path: str, output_path: Optional[str] = None, 
                     format: str = 'wav', sample_rate: int = 16000) -> str:
        """
        从视频文件提取音频或转换音频格式
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径，如为None则生成临时文件
            format: 输出格式 (wav, mp3等)
            sample_rate: 采样率
            
        Returns:
            输出文件路径
        """
        if output_path is None:
            ext = '.wav' if format == 'wav' else f'.{format}'
            output_path = tempfile.mktemp(suffix=ext)
        
        # 构建ffmpeg命令
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-vn',  # 不包含视频
            '-acodec', 'pcm_s16le' if format == 'wav' else 'libmp3lame',
            '-ar', str(sample_rate),
            '-ac', '1',  # 单声道，有助于语音识别
            '-y',  # 覆盖输出文件
            output_path
        ]
        
        logger.info(f"提取音频: {input_path} -> {output_path}")
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"音频提取失败: {e.stderr}")
            raise RuntimeError(f"音频提取失败: {e}")
    
    def split_by_silence(self, audio_path: str, min_silence_len: int = 500, 
                        silence_thresh: int = -40, keep_silence: int = 100,
                        min_segment_len: int = 1000) -> List[AudioSegment]:
        """
        根据静音分割音频
        
        Args:
            audio_path: 音频文件路径
            min_silence_len: 最小静音长度（毫秒）
            silence_thresh: 静音阈值（dBFS）
            keep_silence: 在分段开头保留的静音（毫秒）
            min_segment_len: 最小分段长度（毫秒）
            
        Returns:
            音频分段列表
        """
        try:
            audio = PydubAudioSegment.from_file(audio_path)
            
            # 分割音频
            chunks = split_on_silence(
                audio,
                min_silence_len=min_silence_len,
                silence_thresh=silence_thresh,
                keep_silence=keep_silence
            )
            
            # 过滤太短的分段
            chunks = [chunk for chunk in chunks if len(chunk) >= min_segment_len]
            
            # 转换为AudioSegment对象
            segments = []
            current_time = 0.0
            
            for chunk in chunks:
                duration = len(chunk) / 1000.0  # 转换为秒
                segment = AudioSegment(
                    start_time=current_time,
                    end_time=current_time + duration,
                    duration=duration
                )
                segments.append(segment)
                current_time += duration
            
            logger.info(f"音频分割完成: {len(segments)}个分段")
            return segments
            
        except Exception as e:
            logger.error(f"音频分割失败: {e}")
            raise
    
    def split_by_fixed_duration(self, audio_path: str, segment_duration: float = 10.0, 
                              overlap: float = 0.5) -> List[AudioSegment]:
        """
        按固定时长分割音频
        
        Args:
            audio_path: 音频文件路径
            segment_duration: 分段时长（秒）
            overlap: 分段重叠时长（秒）
            
        Returns:
            音频分段列表
        """
        try:
            audio = PydubAudioSegment.from_file(audio_path)
            total_duration = len(audio) / 1000.0  # 秒
            
            segments = []
            start_time = 0.0
            
            while start_time < total_duration:
                end_time = min(start_time + segment_duration, total_duration)
                actual_duration = end_time - start_time
                
                if actual_duration > 0.5:  # 至少0.5秒
                    segment = AudioSegment(
                        start_time=start_time,
                        end_time=end_time,
                        duration=actual_duration
                    )
                    segments.append(segment)
                
                start_time += (segment_duration - overlap)
            
            logger.info(f"固定时长分割完成: {len(segments)}个分段")
            return segments
            
        except Exception as e:
            logger.error(f"固定时长分割失败: {e}")
            raise
    
    def extract_segment(self, input_path: str, start_time: float, end_time: float,
                       output_path: Optional[str] = None) -> str:
        """
        提取音频分段
        
        Args:
            input_path: 输入音频文件路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒）
            output_path: 输出文件路径，如为None则生成临时文件
            
        Returns:
            输出文件路径
        """
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.wav')
        
        duration = end_time - start_time
        
        # 构建ffmpeg命令
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-acodec', 'copy',
            '-y',
            output_path
        ]
        
        logger.info(f"提取音频分段: {start_time:.2f}-{end_time:.2f}s -> {output_path}")
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"音频分段提取失败: {e.stderr}")
            raise RuntimeError(f"音频分段提取失败: {e}")
    
    def normalize_audio(self, input_path: str, output_path: str, target_loudness: float = -20.0) -> str:
        """
        音频归一化（调整音量）
        
        Args:
            input_path: 输入音频文件路径
            output_path: 输出文件路径
            target_loudness: 目标响度（LUFS）
            
        Returns:
            输出文件路径
        """
        cmd = [
            self.ffmpeg_path,
            '-i', input_path,
            '-filter:a', f'loudnorm=I={target_loudness}',
            '-y',
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"音频归一化失败: {e.stderr}")
            raise RuntimeError(f"音频归一化失败: {e}")
    
    def get_waveform(self, audio_path: str, num_points: int = 1000) -> np.ndarray:
        """
        获取音频波形数据（用于可视化）
        
        Args:
            audio_path: 音频文件路径
            num_points: 采样点数
            
        Returns:
            归一化的波形数据数组
        """
        try:
            audio = PydubAudioSegment.from_file(audio_path)
            samples = np.array(audio.get_array_of_samples())
            
            # 转换为单声道（如果需要）
            if audio.channels > 1:
                samples = samples.reshape(-1, audio.channels).mean(axis=1)
            
            # 下采样
            if len(samples) > num_points:
                step = len(samples) // num_points
                samples = samples[::step][:num_points]
            
            # 归一化到[-1, 1]
            if samples.dtype != np.float32:
                samples = samples.astype(np.float32)
                if np.abs(samples).max() > 0:
                    samples = samples / np.abs(samples).max()
            
            return samples
            
        except Exception as e:
            logger.error(f"获取波形数据失败: {e}")
            return np.zeros(num_points)
    
    @classmethod
    def is_supported_format(cls, filepath: str) -> bool:
        """检查文件格式是否支持"""
        ext = os.path.splitext(filepath)[1].lower()
        return ext in cls.SUPPORTED_AUDIO_FORMATS + cls.SUPPORTED_VIDEO_FORMATS

import json  # 添加到文件末尾