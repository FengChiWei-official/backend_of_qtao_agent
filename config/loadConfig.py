import yaml
from pathlib import Path

class ConfigLoader:
    def __init__(self, path_to_config_file: str|Path):
        """
        初始化配置加载器
        :param path_to_config_file: 配置文件的路径，可以是str或pathlib.Path
        """
        path = Path(path_to_config_file)
        with open(path_to_config_file, 'r') as file:
            self.config = yaml.safe_load(file)
        

    def get_db_config(self) -> dict:
        """
        获取数据库配置
        :return: 数据库配置字典，自动补全缺失字段
        :raises ValueError: 如果配置文件中没有找到数据库类型或相关配置
        """
        db_type = self.config.get("db_type", default_config["db_type"])
        db_config = self.config.get(db_type, None)
        if db_config is None:
            raise ValueError(f"Database configuration for '{db_type}' not found in the config file.")

        # 补全缺失字段
        for k, v in default_config[db_type].items():
            if k not in db_config:
                if k == "password" or k == "user":
                    raise ValueError(f"Missing required database configuration: {k}")
                db_config[k] = v
        self.config[db_type] = db_config
        self.config["db_type"] = db_type
        return self.config
    

default_config = {
    "db_type": "mysql",
    "mysql": {
        "user": "root",
        "password": "",
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
    },
    "sqlite": {
        "database": "test.db",
        "echo": True,
    }
}