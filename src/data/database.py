"""
数据库管理模块
提供数据库连接、会话管理和初始化功能
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator, Any
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base
from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseManager:
    """数据库管理器，负责数据库连接和会话管理"""
    
    def __init__(self, db_path: Optional[str] = None, echo: bool = False):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径，如为None则使用配置中的路径
            echo: 是否输出SQL语句
        """
        # 获取配置
        config = get_config()
        
        # 设置数据库路径
        if db_path is None:
            db_path = config.get("database.path", "data/deutsch_lernen.db")
        
        # 确保数据库目录存在
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        # 创建数据库引擎
        self.db_path = db_path
        self.echo = echo or config.get("database.echo", False)
        
        # SQLite连接字符串
        db_url = f"sqlite:///{db_path}"
        
        # 创建引擎，设置SQLite特定选项
        self.engine = create_engine(
            db_url,
            echo=self.echo,
            # SQLite特定选项
            connect_args={"check_same_thread": False},
            pool_pre_ping=True
        )
        
        # 启用SQLite外键支持
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
        
        # 创建会话工厂
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"数据库管理器初始化完成: {db_path}")
    
    def init_db(self):
        """初始化数据库，创建所有表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建完成")
        except SQLAlchemyError as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def drop_db(self):
        """删除所有表（谨慎使用）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("数据库表删除完成")
        except SQLAlchemyError as e:
            logger.error(f"删除数据库表失败: {e}")
            raise
    
    def get_session(self) -> Session:
        """获取新的数据库会话"""
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        提供事务会话的上下文管理器
        
        使用示例:
            with db_manager.session_scope() as session:
                session.add(some_object)
                # 自动提交或回滚
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库事务失败: {e}")
            raise
        finally:
            session.close()
    
    def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> Any:
        """
        执行原始SQL语句
        
        Args:
            sql: SQL语句
            params: 参数字典
            
        Returns:
            执行结果
        """
        with self.session_scope() as session:
            try:
                result = session.execute(sql, params or {})
                return result
            except SQLAlchemyError as e:
                logger.error(f"执行SQL失败: {e}")
                raise
    
    def backup_database(self, backup_path: str):
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
        """
        import shutil
        try:
            # 确保备份目录存在
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            # 复制数据库文件
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"数据库备份完成: {backup_path}")
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            raise
    
    def restore_database(self, backup_path: str):
        """
        从备份恢复数据库
        
        Args:
            backup_path: 备份文件路径
        """
        import shutil
        try:
            # 检查备份文件是否存在
            if not os.path.exists(backup_path):
                raise FileNotFoundError(f"备份文件不存在: {backup_path}")
            
            # 关闭当前连接
            self.engine.dispose()
            
            # 复制备份文件
            shutil.copy2(backup_path, self.db_path)
            
            # 重新创建引擎
            self.engine = create_engine(
                f"sqlite:///{self.db_path}",
                echo=self.echo,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True
            )
            
            # 重新创建会话工厂
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            logger.info(f"数据库恢复完成: {backup_path}")
        except Exception as e:
            logger.error(f"数据库恢复失败: {e}")
            raise
    
    def get_table_stats(self) -> dict:
        """
        获取数据库表统计信息
        
        Returns:
            表统计信息字典
        """
        stats = {}
        with self.session_scope() as session:
            for table_name in Base.metadata.tables.keys():
                try:
                    # 获取表记录数
                    result = session.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = result.scalar()
                    stats[table_name] = count
                except Exception as e:
                    logger.warning(f"获取表 {table_name} 统计失败: {e}")
                    stats[table_name] = -1
        
        return stats
    
    def vacuum_database(self):
        """优化数据库（SQLite VACUUM）"""
        try:
            with self.session_scope() as session:
                session.execute("VACUUM")
            logger.info("数据库优化完成")
        except SQLAlchemyError as e:
            logger.error(f"数据库优化失败: {e}")
            raise
    
    def check_database_integrity(self) -> bool:
        """
        检查数据库完整性
        
        Returns:
            数据库是否完整
        """
        try:
            with self.session_scope() as session:
                result = session.execute("PRAGMA integrity_check")
                integrity = result.scalar()
                if integrity == "ok":
                    logger.info("数据库完整性检查通过")
                    return True
                else:
                    logger.error(f"数据库完整性检查失败: {integrity}")
                    return False
        except SQLAlchemyError as e:
            logger.error(f"数据库完整性检查异常: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")

# 全局数据库管理器实例
_db_manager_instance = None

def get_db_manager(db_path: Optional[str] = None, echo: bool = False) -> DatabaseManager:
    """
    获取数据库管理器实例（单例模式）
    
    Args:
        db_path: 数据库文件路径
        echo: 是否输出SQL语句
        
    Returns:
        数据库管理器实例
    """
    global _db_manager_instance
    
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager(db_path, echo)
    
    return _db_manager_instance

def init_database(db_path: Optional[str] = None, echo: bool = False) -> DatabaseManager:
    """
    初始化数据库
    
    Args:
        db_path: 数据库文件路径
        echo: 是否输出SQL语句
        
    Returns:
        数据库管理器实例
    """
    manager = get_db_manager(db_path, echo)
    manager.init_db()
    return manager

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器
    
    使用示例:
        with get_db_session() as session:
            # 使用session进行数据库操作
    """
    manager = get_db_manager()
    with manager.session_scope() as session:
        yield session