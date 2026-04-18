"""
翻译模块
德语到中文翻译
支持本地模型和API两种模式
"""

import os
import warnings
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)

@dataclass
class TranslationResult:
    """翻译结果"""
    source_text: str  # 源文本
    translated_text: str  # 翻译文本
    source_lang: str  # 源语言
    target_lang: str  # 目标语言
    confidence: float  # 置信度（如果可用）
    model_used: str  # 使用的模型

class Translator:
    """翻译器基类"""
    
    def __init__(self, source_lang: str = "de", target_lang: str = "zh"):
        self.source_lang = source_lang
        self.target_lang = target_lang
    
    def translate(self, text: str, **kwargs) -> TranslationResult:
        """翻译文本"""
        raise NotImplementedError
    
    def translate_batch(self, texts: List[str], **kwargs) -> List[TranslationResult]:
        """批量翻译"""
        return [self.translate(text, **kwargs) for text in texts]
    
    def supports_language_pair(self, source: str, target: str) -> bool:
        """检查是否支持语言对"""
        return source == self.source_lang and target == self.target_lang

class LocalTranslator(Translator):
    """本地翻译模型（使用transformers）"""
    
    # 支持的模型列表
    SUPPORTED_MODELS = {
        "de-zh": [
            "Helsinki-NLP/opus-mt-de-zh",  # 官方德语-中文模型
            "facebook/m2m100_418M",  # 多语言模型，支持de-zh
            "facebook/mbart-large-50-many-to-many-mmt",  # 多语言模型
        ]
    }
    
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None,
                 cache_dir: Optional[str] = None, source_lang: str = "de", target_lang: str = "zh"):
        """
        初始化本地翻译器
        
        Args:
            model_name: 模型名称，如为None则自动选择
            device: 设备（cuda, cpu, auto）
            cache_dir: 模型缓存目录
            source_lang: 源语言
            target_lang: 目标语言
        """
        super().__init__(source_lang, target_lang)
        
        self.model_name = model_name or self._select_model(source_lang, target_lang)
        self.cache_dir = cache_dir
        
        # 自动选择设备
        if device is None:
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        
        self._load_model()
        
        logger.info(f"本地翻译器初始化完成: {self.model_name}, 设备: {self.device}")
    
    def _select_model(self, source_lang: str, target_lang: str) -> str:
        """选择适合语言对的模型"""
        key = f"{source_lang}-{target_lang}"
        if key in self.SUPPORTED_MODELS:
            return self.SUPPORTED_MODELS[key][0]  # 返回第一个推荐模型
        else:
            # 使用多语言模型
            return "facebook/m2m100_418M"
    
    def _load_model(self):
        """加载模型和分词器"""
        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            
            logger.info(f"加载翻译模型: {self.model_name}")
            
            # 加载分词器
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            )
            
            # 加载模型
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True
            ).to(self.device)
            
            # 设置模型为评估模式
            self.model.eval()
            
            # 设置语言代码（针对多语言模型）
            self._setup_language_codes()
            
        except ImportError:
            raise ImportError(
                "请安装transformers包: pip install transformers sentencepiece protobuf"
            )
        except Exception as e:
            raise RuntimeError(f"加载翻译模型失败: {e}")
    
    def _setup_language_codes(self):
        """设置语言代码（针对多语言模型）"""
        # 为不同模型设置语言代码
        if "m2m100" in self.model_name:
            # M2M100模型
            self.src_lang_code = self.source_lang
            self.tgt_lang_code = self.target_lang
            
            # 设置分词器的语言代码
            if hasattr(self.tokenizer, "src_lang"):
                self.tokenizer.src_lang = self.source_lang
                
        elif "mbart" in self.model_name:
            # mBART模型
            # mBART使用不同的语言代码格式
            lang_map = {"de": "de_DE", "zh": "zh_CN", "en": "en_XX"}
            self.src_lang_code = lang_map.get(self.source_lang, self.source_lang)
            self.tgt_lang_code = lang_map.get(self.target_lang, self.target_lang)
            
        elif "opus-mt" in self.model_name:
            # OPUS-MT模型，语言对已固定
            self.src_lang_code = self.source_lang
            self.tgt_lang_code = self.target_lang
            
        else:
            # 默认情况
            self.src_lang_code = self.source_lang
            self.tgt_lang_code = self.target_lang
    
    def translate(self, text: str, max_length: int = 512, **kwargs) -> TranslationResult:
        """
        翻译文本
        
        Args:
            text: 源文本
            max_length: 最大长度
            **kwargs: 额外参数
            
        Returns:
            TranslationResult对象
        """
        import torch
        from transformers import pipeline
        
        start_time = time.time()
        
        try:
            # 预处理文本
            text = text.strip()
            if not text:
                return TranslationResult(
                    source_text=text,
                    translated_text="",
                    source_lang=self.source_lang,
                    target_lang=self.target_lang,
                    confidence=1.0,
                    model_used=self.model_name
                )
            
            # 使用pipeline简化翻译过程
            if not hasattr(self, 'pipeline'):
                self.pipeline = pipeline(
                    "translation",
                    model=self.model,
                    tokenizer=self.tokenizer,
                    device=self.device if self.device != "cpu" else -1,
                    src_lang=self.src_lang_code if hasattr(self, 'src_lang_code') else None,
                    tgt_lang=self.tgt_lang_code if hasattr(self, 'tgt_lang_code') else None
                )
            
            # 执行翻译
            result = self.pipeline(
                text,
                max_length=max_length,
                **kwargs
            )
            
            # 提取翻译结果
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    translated_text = result[0].get("translation_text", "")
                else:
                    translated_text = str(result[0])
            else:
                translated_text = str(result)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            logger.debug(f"翻译完成: {len(text)}字符 -> {len(translated_text)}字符, 耗时: {processing_time:.2f}s")
            
            return TranslationResult(
                source_text=text,
                translated_text=translated_text.strip(),
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                confidence=0.8,  # 本地模型难以获取置信度
                model_used=self.model_name
            )
            
        except Exception as e:
            logger.error(f"翻译失败: {e}")
            # 返回空翻译而不是抛出异常
            return TranslationResult(
                source_text=text,
                translated_text=f"[翻译失败: {str(e)[:50]}]",
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                confidence=0.0,
                model_used=self.model_name
            )
    
    def translate_batch(self, texts: List[str], batch_size: int = 8, **kwargs) -> List[TranslationResult]:
        """批量翻译"""
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            logger.info(f"批量翻译: {i+1}-{min(i+batch_size, len(texts))}/{len(texts)}")
            
            # 这里可以优化为真正的批量处理，但简化实现
            for text in batch:
                results.append(self.translate(text, **kwargs))
        
        return results

class APITranslator(Translator):
    """API翻译器（支持多种翻译API）"""
    
    # 支持的API
    API_PROVIDERS = ["openai", "google", "deepl", "azure"]
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None,
                 api_base: Optional[str] = None, source_lang: str = "de", target_lang: str = "zh"):
        """
        初始化API翻译器
        
        Args:
            provider: API提供商（openai, google, deepl, azure）
            api_key: API密钥
            api_base: API基础URL（用于自定义端点）
            source_lang: 源语言
            target_lang: 目标语言
        """
        super().__init__(source_lang, target_lang)
        
        self.provider = provider.lower()
        self.api_key = api_key
        self.api_base = api_base
        
        if self.provider not in self.API_PROVIDERS:
            raise ValueError(f"不支持的API提供商: {provider}")
        
        self._init_client()
        logger.info(f"API翻译器初始化完成: {self.provider}")
    
    def _init_client(self):
        """初始化API客户端"""
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base if self.api_base else "https://api.openai.com/v1"
                )
                self.model = "gpt-4"  # 或 gpt-3.5-turbo
                
            elif self.provider == "google":
                # Google Cloud Translation API
                from google.cloud import translate_v2 as translate
                self.client = translate.Client(credentials=self.api_key)
                
            elif self.provider == "deepl":
                import deepl
                self.client = deepl.Translator(self.api_key)
                
            elif self.provider == "azure":
                from azure.ai.translation.text import TextTranslationClient
                from azure.core.credentials import AzureKeyCredential
                credential = AzureKeyCredential(self.api_key)
                self.client = TextTranslationClient(
                    endpoint=self.api_base,
                    credential=credential
                )
                
        except ImportError as e:
            raise ImportError(f"请安装{self.provider}翻译API所需的包: {e}")
        except Exception as e:
            raise RuntimeError(f"初始化{self.provider}客户端失败: {e}")
    
    def translate(self, text: str, **kwargs) -> TranslationResult:
        """
        使用API翻译文本
        
        Args:
            text: 源文本
            **kwargs: 额外参数
            
        Returns:
            TranslationResult对象
        """
        start_time = time.time()
        
        try:
            text = text.strip()
            if not text:
                return TranslationResult(
                    source_text=text,
                    translated_text="",
                    source_lang=self.source_lang,
                    target_lang=self.target_lang,
                    confidence=1.0,
                    model_used=self.provider
                )
            
            translated_text = ""
            confidence = 0.9  # API通常质量较高
            
            if self.provider == "openai":
                # OpenAI ChatGPT翻译
                response = self.client.chat.completions.create(
                    model=kwargs.get("model", self.model),
                    messages=[
                        {"role": "system", "content": f"你是一个专业的德语到中文翻译助手。请将德语文本准确翻译成中文，保持原文的意思和语气。"},
                        {"role": "user", "content": f"请翻译以下德语文本：\n\n{text}"}
                    ],
                    temperature=0.1,
                    max_tokens=len(text) * 2
                )
                translated_text = response.choices[0].message.content.strip()
                
            elif self.provider == "google":
                # Google Cloud Translation
                result = self.client.translate(
                    text,
                    target_language=self.target_lang,
                    source_language=self.source_lang
                )
                translated_text = result['translatedText']
                
            elif self.provider == "deepl":
                # DeepL翻译
                result = self.client.translate_text(
                    text,
                    target_lang=self.target_lang.upper()
                )
                translated_text = result.text
                
            elif self.provider == "azure":
                # Azure Translator
                response = self.client.translate(
                    body=[text],
                    to=[self.target_lang],
                    from_parameter=self.source_lang
                )
                if response and len(response) > 0:
                    translated_text = response[0].translations[0].text
            
            processing_time = time.time() - start_time
            logger.debug(f"API翻译完成: {len(text)}字符 -> {len(translated_text)}字符, 耗时: {processing_time:.2f}s")
            
            return TranslationResult(
                source_text=text,
                translated_text=translated_text,
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                confidence=confidence,
                model_used=f"{self.provider}-api"
            )
            
        except Exception as e:
            logger.error(f"API翻译失败: {e}")
            return TranslationResult(
                source_text=text,
                translated_text=f"[API翻译失败: {str(e)[:50]}]",
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                confidence=0.0,
                model_used=self.provider
            )

class HybridTranslator(Translator):
    """混合翻译器：优先使用API，失败时回退到本地模型"""
    
    def __init__(self, primary_translator: Translator, fallback_translator: Translator):
        """
        初始化混合翻译器
        
        Args:
            primary_translator: 主要翻译器（通常为API）
            fallback_translator: 备用翻译器（通常为本地模型）
        """
        super().__init__(primary_translator.source_lang, primary_translator.target_lang)
        self.primary = primary_translator
        self.fallback = fallback_translator
    
    def translate(self, text: str, **kwargs) -> TranslationResult:
        """尝试主要翻译器，失败时使用备用"""
        try:
            result = self.primary.translate(text, **kwargs)
            # 检查翻译结果是否有效
            if result.translated_text and not result.translated_text.startswith("[翻译失败"):
                return result
            else:
                raise ValueError("主要翻译器返回无效结果")
        except Exception as e:
            logger.warning(f"主要翻译器失败，使用备用: {e}")
            return self.fallback.translate(text, **kwargs)

# 简单工厂函数
def create_translator(translator_type: str = "local", **kwargs) -> Translator:
    """
    创建翻译器实例
    
    Args:
        translator_type: 翻译器类型（"local", "api", "hybrid"）
        **kwargs: 传递给翻译器的参数
        
    Returns:
        翻译器实例
    """
    if translator_type == "local":
        return LocalTranslator(**kwargs)
    elif translator_type == "api":
        return APITranslator(**kwargs)
    elif translator_type == "hybrid":
        primary = create_translator("api", **kwargs)
        fallback = create_translator("local", **kwargs)
        return HybridTranslator(primary, fallback)
    else:
        raise ValueError(f"不支持的翻译器类型: {translator_type}")

# 工具函数
def split_long_text(text: str, max_chars: int = 1000) -> List[str]:
    """分割长文本为多个片段"""
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= max_chars:
            current_chunk += sentence + ". "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks