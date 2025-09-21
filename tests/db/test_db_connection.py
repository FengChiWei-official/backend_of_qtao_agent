import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

import pytest
from sqlalchemy import text
from config.loadConfig import ConfigLoader
from src.modules.dbController import DatabaseSessionManager
from src.utils import root_path

@pytest.fixture(scope="module")
def db_session():
    """
    Pytest fixture to set up and tear down the database session.
    """
    PATH_TO_ROOT = root_path.get_root_path()
    DEFAULT_PATH_TO_CONFIG = PATH_TO_ROOT / "config" / "config.yaml"
    config = ConfigLoader(DEFAULT_PATH_TO_CONFIG).get_db_config()
    
    db_manager = DatabaseSessionManager(config)
    with db_manager.get_session() as session:
        try:
            yield session
        finally:
            pass # The session is automatically closed by the context manager

def test_database_connection(db_session):
    """
    Tests the database connection by executing a simple query.
    """
    try:
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar_one() == 1, "The result of 'SELECT 1' should be 1."
        print("数据库连接成功！")
    except Exception as e:
        pytest.fail(f"数据库连接失败: {e}")


