import unittest, sys, os
import logging
logger = logging.getLogger(__name__)
PATH_TO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PATH_TO_ROOT)
from src.modules.dbController.basis.dbSession import DataBaseSession
from config.loadConfig import ConfigLoader
from unittest.mock import patch
class TestDataBaseSession(unittest.TestCase):
    def setUp(self):
        # 使用sqlite内存数据库，避免真实数据库依赖
        self.config = ConfigLoader(os.path.join(PATH_TO_ROOT, "config", "config.yaml"))
        self.db_session = DataBaseSession(self.config.get_db_config(), is_regenerating_table=True)

    def test_get_session(self):
        # 测试能否成功获取session
        with self.db_session.get_session() as session:
            self.assertIsNotNone(session)
            # session应为SQLAlchemy的Session类型
            from sqlalchemy.orm import Session as SQLASession
            self.assertIsInstance(session, SQLASession)
    
  

    def test_engine_params(self):
        config = {
            "db_type": "sqlite",
            "sqlite": {
                "database": ":memory:",
                "echo": True
            }
        }
        with patch("src.modules.dbController.basis.dbSession.create_engine") as mock_engine:
            DataBaseSession(config, is_regenerating_table=False)
            mock_engine.assert_called_once()
            # 检查参数
            args, kwargs = mock_engine.call_args
            self.assertEqual(args[0], "sqlite:///:memory:")
            self.assertEqual(kwargs.get("echo"), True)
            self.assertIn("connect_args", kwargs)
            self.assertEqual(kwargs["connect_args"], {"check_same_thread": False})

    def test_engine_params_mysql(self):
        config = {
            "db_type": "mysql",
            "mysql": {
                "user": "root",
                "password": "123456",
                "host": "localhost",
                "port": 3306,
                "database": "test_db",
                "driver": "pymysql",
                "echo": True,
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 1800,
                "connection_args": {
                    "charset": "utf8mb4",
                    "connect_timeout": 10
                }
            }
        }
        with patch("src.modules.dbController.basis.dbSession.create_engine") as mock_engine:
            DataBaseSession(config, is_regenerating_table=False)
            mock_engine.assert_called_once()
            args, kwargs = mock_engine.call_args
            self.assertEqual(args[0], "mysql+pymysql://root:123456@localhost:3306/test_db")
            self.assertEqual(kwargs.get("echo"), True)
            self.assertEqual(kwargs.get("pool_size"), 5)
            self.assertEqual(kwargs.get("max_overflow"), 10)
            self.assertEqual(kwargs.get("pool_timeout"), 30)
            self.assertEqual(kwargs.get("pool_recycle"), 1800)
            self.assertIn("connect_args", kwargs)
            self.assertEqual(kwargs["connect_args"], {"charset": "utf8mb4", "connect_timeout": 10})

    def test_automatic_table_regeneration(self):
        # 测试自动表重建功能
        with self.db_session.get_session() as session:
            # 假设有一个User模型，检查是否存在
            from src.modules.dbController.dataModels import User
            user_table_exists = session.query(User).first() is not None
            self.assertTrue(user_table_exists, "User table should exist after initialization with table regeneration.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    # 运行测试
    unittest.main()
