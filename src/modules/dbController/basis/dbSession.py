"""
数据库会话管理模块
提供MySQL数据库连接和SQLAlchemy ORM会话管理功能
"""
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Dict, Any
import os
import yaml
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session                

# 设置日志记录
logger = logging.getLogger(__name__)

class DataBaseSession:

    # def __init__(self, config: Dict[str, Any], is_regenerating_table: bool) -> None:
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the database connection.
        Args:
            config (Dict[str, Any]): Dictionary containing database configuration.
            is_regenerating_table (bool): Flag indicating whether to regenerate database tables.
        Raises:
            ValueError: If configuration is incomplete or database type is unsupported.
            KeyError: If required configuration keys are missing.
            Exception: For any uncaught errors during initialization.
        Attributes:
            __config (Dict[str, Any]): Database configuration dictionary.
            __db_type (str): Type of the database (e.g., 'sqlite', 'mysql').
            __is_regenerating_table (bool): Indicates if tables should be regenerated.
            __db_url (str): Database connection URL.
            __engine (sqlalchemy.engine.Engine): SQLAlchemy database engine.
            __SessionMaker (sessionmaker): SQLAlchemy session factory.
        Methods:
            get_session(): Returns a new database session.
            __get_db_url(): Returns a url.
        """

       
        logger.info("Initializing database connection...")
        self.__config = config
        try:
            self.__db_type = self.__config.get("db_type", "NoFound")
            if self.__db_type == "NoFound":
                raise ValueError("Database type not found in configuration.")

            self.__db_config = self.__config.get(self.__db_type, {})
            if not self.__db_config:
                raise ValueError(f"Database configuration for type '{self.__db_type}' not found in the config.")

        except ValueError as e:
            logger.error(f"when initializing database connection: {e}")
            raise
        

        try:
            logger.info(f"Database type: {self.__db_type}")
            logger.info("building database URL...")
            self.__db_url = self.__get_db_url()
            db_cfg = self.__config.get(self.__db_type, {})
            if self.__db_type == "sqlite":
                self.__engine = create_engine(
                    self.__db_url,
                    echo=db_cfg.get("echo", False),
                    connect_args={"check_same_thread": False}
                )
            else:
                logger.info("Creating SQLAlchemy engine...")
                self.__engine = create_engine(
                    self.__db_url,
                    echo=db_cfg.get("echo", False),
                    pool_size=db_cfg.get("pool_size", 5),
                    max_overflow=db_cfg.get("max_overflow", 10),
                    pool_timeout=db_cfg.get("pool_timeout", 30),
                    pool_recycle=db_cfg.get("pool_recycle", 1800),
                    connect_args=db_cfg.get("connection_args", {
                        "charset": "utf8mb4",
                        "connect_timeout": 10
                    })
                )
            self.__SessionMaker = sessionmaker(bind=self.__engine)

        except ValueError as e:
            logger.error(f"when initializing database connection, db url error with db_type wrong: {e}")
            raise
        except KeyError as e:
            logger.error(f"when initializing database connection, db config no found: {e}")
        except Exception as e:
            logger.error(f"uncaught error! {e}")
            raise
        

        """
        self.__is_regenerating_table = is_regenerating_table
        if self.__is_regenerating_table:
            logger.info("Regenerating database tables...")
            from src.modules.dbController.dataModels import Base
            #Base.metadata.drop_all(self.__engine)
            # todo: 是否需要在重新生成表之前删除现有表
            # 重新生成表
            Base.metadata.create_all(self.__engine)
            logger.info("Database tables regenerated successfully.")
        """
        logger.info("Database connection initialized successfully.")

    def __get_db_url(self) -> str:
        """
        获取数据库连接URL
        :param config: 数据库配置字典
        :return: 数据库连接URL字符串
        :raises ValueError: 如果配置不完整或数据库类型不支持
        :raises KeyError: 缺少必要配置
        """
        
        db_url = None

        # 分数据库类型，构建数据库url
        try:
            if self.__db_type in ["mysql", "postgresql"]:
                user = self.__db_config["user"]
                password = self.__db_config["password"]
                host = self.__db_config["host"]
                port = self.__db_config["port"]
                database = self.__db_config["database"]
                driver = self.__db_config["driver"]
                logger.info(f"Connecting to {self.__db_type} database at {host}:{port} with user {user}")
                db_url = f"{self.__db_type}+{driver}://{user}:{password}@{host}:{port}/{database}"
            elif self.__db_type == "sqlite":
                database = self.__db_config["database"]
                logger.info(f"Connecting to {self.__db_type} database at {database}")
                db_url = f"sqlite:///{database}"
            else:
                logger.error(f"Unsupported database type: {self.__db_type}")
                raise ValueError(f"Unsupported database type: {self.__db_type}")
        except KeyError as e:
            logger.error(f"when building db url, an attr no found: {e}")
            raise
        return db_url
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话
        :return: SQLAlchemy会话对象生成器
        """
        session = self.__SessionMaker()
        
        try:
            logger.info("Database session created successfully.")
            yield session

        finally:
            """
            关闭数据库会话
            """
            logger.info("Closing database session...")
            session.close()

class DatabaseSessionManager:
    """
    DataBaseSession 单例管理器
    提供统一的数据库会话管理入口
    """
    _instance = None
    _config: Dict[str, Any] | None = None  # Add this line to define the attribute
    _db_session: DataBaseSession | None = None  # Add this line to define the attribute

    def __new__(cls, db_config: Dict[str, Any]) -> 'DatabaseSessionManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = db_config
            cls._instance._db_session = DataBaseSession(cls._instance._config)
        return cls._instance

    def get_session(self):
        """
        获取新的数据库会话（推荐用 with 管理生命周期）
        """
        if self._db_session is None:
            if self._config is None:
                raise ValueError("DatabaseSessionManager not initialized with config.")
            self._db_session = DataBaseSession(self._config)
        return self._db_session.get_session()


