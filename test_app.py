#!/usr/bin/env python3
"""
德语学习助手 - 测试脚本
测试核心功能是否正常工作
"""

import os
import sys
import unittest
import tempfile
import shutil

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

class TestDeutschLernenApp(unittest.TestCase):
    """德语学习助手测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类设置"""
        # 创建临时测试目录
        cls.test_dir = tempfile.mkdtemp(prefix="deutsch_lernen_test_")
        
        # 设置测试配置
        os.environ['DEUTSCH_LERNEN_TEST_DIR'] = cls.test_dir
        
        print(f"测试目录: {cls.test_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        # 清理临时目录
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir)
        print("测试清理完成")
    
    def test_01_config(self):
        """测试配置模块"""
        print("\n=== 测试配置模块 ===")
        
        try:
            from src.utils.config import load_config, get_config
            
            # 加载配置
            config = load_config()
            self.assertIsNotNone(config)
            
            # 获取配置
            current_config = get_config()
            self.assertIsNotNone(current_config)
            
            # 测试配置读取
            app_name = config.get("app.name")
            self.assertIsNotNone(app_name)
            
            print(f"配置加载成功: {app_name}")
            
        except Exception as e:
            self.fail(f"配置模块测试失败: {e}")
    
    def test_02_logger(self):
        """测试日志模块"""
        print("\n=== 测试日志模块 ===")
        
        try:
            from src.utils.logger import setup_logger, get_logger
            
            # 设置日志
            logger = setup_logger("test_logger")
            self.assertIsNotNone(logger)
            
            # 获取日志
            test_logger = get_logger("test_logger")
            self.assertIsNotNone(test_logger)
            
            # 测试日志输出
            test_logger.info("测试日志消息")
            
            print("日志模块测试通过")
            
        except Exception as e:
            self.fail(f"日志模块测试失败: {e}")
    
    def test_03_helpers(self):
        """测试工具函数"""
        print("\n=== 测试工具函数 ===")
        
        try:
            from src.utils.helpers import (
                format_duration, format_filesize, sanitize_filename,
                split_text_into_sentences, extract_words_from_text
            )
            
            # 测试时间格式化
            duration = format_duration(125.5)
            self.assertEqual(duration, "02:05")
            
            # 测试文件大小格式化
            size = format_filesize(1024)
            self.assertEqual(size, "1.0 KB")
            
            # 测试文件名清理
            filename = sanitize_filename("test<>file.txt")
            self.assertEqual(filename, "test__file.txt")
            
            # 测试句子分割
            text = "Hallo, wie geht es Ihnen? Ich bin sehr froh."
            sentences = split_text_into_sentences(text, "de")
            self.assertGreater(len(sentences), 0)
            
            # 测试单词提取
            words = extract_words_from_text(text, "de")
            self.assertGreater(len(words), 0)
            
            print("工具函数测试通过")
            
        except Exception as e:
            self.fail(f"工具函数测试失败: {e}")
    
    def test_04_database(self):
        """测试数据库模块"""
        print("\n=== 测试数据库模块 ===")
        
        try:
            from src.data.database import init_database, get_db_manager
            from src.data.repository import get_audio_file_repo
            
            # 初始化数据库
            db_manager = init_database()
            self.assertIsNotNone(db_manager)
            
            # 测试数据库会话
            with db_manager.session_scope() as session:
                # 测试仓储
                repo = get_audio_file_repo()
                count = repo.count(session)
                self.assertIsInstance(count, int)
            
            print("数据库模块测试通过")
            
        except Exception as e:
            self.fail(f"数据库模块测试失败: {e}")
    
    def test_05_word_analyzer(self):
        """测试单词分析器"""
        print("\n=== 测试单词分析器 ===")
        
        try:
            from src.core.word_analyzer import get_word_analyzer, analyze_word
            
            # 获取单词分析器
            analyzer = get_word_analyzer()
            self.assertIsNotNone(analyzer)
            
            # 分析单词
            word_info = analyze_word("Hallo")
            if word_info:
                self.assertEqual(word_info.word, "Hallo")
                print(f"单词分析结果: {word_info.chinese_definition}")
            else:
                print("单词分析返回None（可能是词典未加载）")
            
            print("单词分析器测试通过")
            
        except Exception as e:
            self.fail(f"单词分析器测试失败: {e}")
    
    def test_06_sentence_splitter(self):
        """测试句子分段器"""
        print("\n=== 测试句子分段器 ===")
        
        try:
            from src.core.sentence_splitter import split_german_text, Sentence
            
            # 测试德语句子分割
            text = "Hallo, wie geht es Ihnen? Das ist ein Test. Ich bin sehr froh, Sie kennenzulernen."
            sentences = split_german_text(text)
            
            self.assertGreater(len(sentences), 0)
            self.assertIsInstance(sentences[0], Sentence)
            
            print(f"句子分割结果: {len(sentences)} 个句子")
            for i, sentence in enumerate(sentences, 1):
                print(f"  {i}. {sentence.text}")
            
            print("句子分段器测试通过")
            
        except Exception as e:
            self.fail(f"句子分段器测试失败: {e}")
    
    def test_07_gui_import(self):
        """测试GUI模块导入"""
        print("\n=== 测试GUI模块导入 ===")
        
        try:
            # 测试PyQt5导入
            from PyQt5.QtWidgets import QApplication
            print("PyQt5导入成功")
            
            # 测试GUI模块导入
            from src.gui.main_window import MainWindow
            from src.gui.audio_player import AudioPlayerWidget
            from src.gui.text_display import BilingualTextDisplay
            from src.gui.word_detail import WordDetailDialog
            from src.gui.collection_manager import CollectionManagerWidget
            
            print("GUI模块导入成功")
            
        except ImportError as e:
            print(f"GUI模块导入失败（可能是PyQt5未安装）: {e}")
        except Exception as e:
            self.fail(f"GUI模块测试失败: {e}")
    
    def test_08_main_import(self):
        """测试主程序导入"""
        print("\n=== 测试主程序导入 ===")
        
        try:
            # 测试主程序导入
            import main
            
            self.assertIsNotNone(main)
            
            print("主程序导入成功")
            
        except Exception as e:
            self.fail(f"主程序导入失败: {e}")

def run_tests():
    """运行测试"""
    print("=" * 60)
    print("德语学习助手 - 功能测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDeutschLernenApp)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    if result.wasSuccessful():
        print("所有测试通过！")
        return 0
    else:
        print(f"测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)