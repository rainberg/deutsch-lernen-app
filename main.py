"""
德语学习助手 - 主程序入口
集成所有模块，启动应用程序
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入项目模块
from src.utils.config import load_config, get_config
from src.utils.logger import init_logging, get_logger
from src.data.database import init_database, get_db_manager

# 初始化日志
init_logging()
logger = get_logger(__name__)

def setup_environment():
    """设置运行环境"""
    # 确保必要的目录存在
    config = get_config()
    
    directories = [
        config.get("paths.data_dir", "data"),
        config.get("paths.audio_dir", "data/audio"),
        config.get("paths.exports_dir", "exports"),
        config.get("paths.logs_dir", "logs"),
        config.get("paths.models_dir", "models"),
        config.get("paths.cache_dir", "cache"),
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            logger.info(f"创建目录: {directory}")
    
    logger.info("运行环境设置完成")

def init_application():
    """初始化应用程序"""
    try:
        # 加载配置
        config = load_config()
        logger.info("配置加载完成")
        
        # 初始化数据库
        db_manager = init_database()
        logger.info("数据库初始化完成")
        
        # 验证配置
        if not config.validate():
            logger.warning("配置验证失败，使用默认配置")
            config.reset_to_default()
        
        logger.info("应用程序初始化完成")
        return True
        
    except Exception as e:
        logger.error(f"应用程序初始化失败: {e}")
        return False

def run_gui():
    """运行图形界面"""
    try:
        from PyQt5.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        # 创建应用程序
        app = QApplication(sys.argv)
        app.setApplicationName("德语学习助手")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("Deutsch Lernen")
        
        # 设置应用程序图标
        # app.setWindowIcon(QIcon("resources/icons/app_icon.png"))
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        logger.info("图形界面启动完成")
        
        # 运行应用程序
        return app.exec_()
        
    except ImportError as e:
        logger.error(f"导入PyQt5失败: {e}")
        print("错误: 无法导入PyQt5，请确保已安装PyQt5")
        print("安装命令: pip install PyQt5")
        return 1
    except Exception as e:
        logger.error(f"启动图形界面失败: {e}")
        print(f"错误: {e}")
        return 1

def run_cli():
    """运行命令行界面"""
    try:
        from src.cli.main_cli import MainCLI
        
        # 创建命令行界面
        cli = MainCLI()
        
        logger.info("命令行界面启动完成")
        
        # 运行命令行界面
        return cli.run()
        
    except ImportError as e:
        logger.error(f"导入CLI模块失败: {e}")
        print("错误: 无法导入CLI模块")
        return 1
    except Exception as e:
        logger.error(f"启动命令行界面失败: {e}")
        print(f"错误: {e}")
        return 1

def process_audio_file(file_path: str, output_dir: str = None):
    """
    处理音频文件（命令行模式）
    
    Args:
        file_path: 音频文件路径
        output_dir: 输出目录
    """
    try:
        from src.core.audio_processor import AudioProcessor
        from src.core.transcriber import WhisperTranscriber
        from src.core.translator import LocalTranslator
        from src.core.sentence_splitter import split_german_text
        
        logger.info(f"开始处理音频文件: {file_path}")
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return False
        
        # 创建音频处理器
        audio_processor = AudioProcessor()
        
        # 获取音频信息
        audio_info = audio_processor.get_audio_info(file_path)
        logger.info(f"音频信息: {audio_info}")
        
        # 提取音频（如果是视频文件）
        audio_path = file_path
        if audio_info.format in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
            logger.info("检测到视频文件，提取音频...")
            audio_path = audio_processor.extract_audio(file_path)
            logger.info(f"音频提取完成: {audio_path}")
        
        # 创建转写器
        transcriber = WhisperTranscriber()
        
        # 转写音频
        logger.info("开始转写音频...")
        transcription_result = transcriber.transcribe(audio_path)
        logger.info(f"转写完成: {len(transcription_result.text)} 字符")
        
        # 分割句子
        logger.info("开始分割句子...")
        sentences = split_german_text(transcription_result.text)
        logger.info(f"句子分割完成: {len(sentences)} 个句子")
        
        # 创建翻译器
        translator = LocalTranslator()
        
        # 翻译句子
        logger.info("开始翻译句子...")
        translations = []
        for sentence in sentences:
            translation = translator.translate(sentence.text)
            translations.append(translation.translated_text)
        logger.info("翻译完成")
        
        # 保存结果
        if output_dir:
            output_path = os.path.join(output_dir, os.path.basename(file_path) + ".txt")
        else:
            output_path = file_path + ".txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("德语转写结果:\n")
            f.write("=" * 50 + "\n")
            f.write(transcription_result.text + "\n\n")
            
            f.write("句子分割:\n")
            f.write("=" * 50 + "\n")
            for i, sentence in enumerate(sentences, 1):
                f.write(f"{i}. {sentence.text}\n")
            f.write("\n")
            
            f.write("中文翻译:\n")
            f.write("=" * 50 + "\n")
            for i, translation in enumerate(translations, 1):
                f.write(f"{i}. {translation}\n")
        
        logger.info(f"结果已保存到: {output_path}")
        print(f"处理完成！结果已保存到: {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"处理音频文件失败: {e}")
        print(f"错误: {e}")
        return False

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="德语学习助手")
    parser.add_argument("--gui", action="store_true", help="启动图形界面")
    parser.add_argument("--cli", action="store_true", help="启动命令行界面")
    parser.add_argument("--process", type=str, help="处理音频文件")
    parser.add_argument("--output", type=str, help="输出目录")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--version", action="version", version="德语学习助手 0.1.0")
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    # 初始化应用程序
    if not init_application():
        logger.error("应用程序初始化失败")
        return 1
    
    # 根据参数运行相应模式
    if args.process:
        # 处理音频文件模式
        return 0 if process_audio_file(args.process, args.output) else 1
    elif args.cli:
        # 命令行界面模式
        return run_cli()
    else:
        # 默认启动图形界面
        return run_gui()

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        print("\n程序已退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行出错: {e}")
        print(f"程序运行出错: {e}")
        sys.exit(1)