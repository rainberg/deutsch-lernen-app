"""
测试包
包含单元测试和集成测试
"""

import os
import sys

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 测试配置
TEST_CONFIG = {
    "test_audio_dir": os.path.join(os.path.dirname(__file__), "..", "resources", "audio"),
    "test_export_dir": os.path.join(os.path.dirname(__file__), "..", "resources", "exports"),
    "test_db_path": os.path.join(os.path.dirname(__file__), "test.db"),
}

def setup_test_environment():
    """设置测试环境"""
    # 创建测试目录
    os.makedirs(TEST_CONFIG["test_audio_dir"], exist_ok=True)
    os.makedirs(TEST_CONFIG["test_export_dir"], exist_ok=True)
    
    # 如果测试数据库存在则删除
    if os.path.exists(TEST_CONFIG["test_db_path"]):
        os.remove(TEST_CONFIG["test_db_path"])
    
    print("测试环境设置完成")

def teardown_test_environment():
    """清理测试环境"""
    # 删除测试数据库
    if os.path.exists(TEST_CONFIG["test_db_path"]):
        os.remove(TEST_CONFIG["test_db_path"])
    
    print("测试环境清理完成")

# 测试基类
class BaseTestCase:
    """测试基类，提供通用测试方法"""
    
    @classmethod
    def setup_class(cls):
        """测试类设置"""
        setup_test_environment()
    
    @classmethod
    def teardown_class(cls):
        """测试类清理"""
        teardown_test_environment()
    
    def assertEqual(self, first, second, msg=None):
        """断言相等"""
        if first != second:
            raise AssertionError(msg or f"{first} != {second}")
    
    def assertTrue(self, expr, msg=None):
        """断言为真"""
        if not expr:
            raise AssertionError(msg or f"{expr} is not true")
    
    def assertFalse(self, expr, msg=None):
        """断言为假"""
        if expr:
            raise AssertionError(msg or f"{expr} is not false")
    
    def assertRaises(self, exception, callable_obj, *args, **kwargs):
        """断言抛出异常"""
        try:
            callable_obj(*args, **kwargs)
        except exception:
            return
        except Exception as e:
            raise AssertionError(f"Expected {exception}, got {type(e)}: {e}")
        raise AssertionError(f"Expected {exception} to be raised")