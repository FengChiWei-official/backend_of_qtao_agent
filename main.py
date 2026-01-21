import logging
from sys import path
from src.utils import root_path
PATH_TO_ROOT = root_path.get_root_path()
DEFAULT_PATH_TO_CONFIG = PATH_TO_ROOT / "config" / "config.yaml"
path.append(str(PATH_TO_ROOT))

from config import ConfigLoader

if __name__ == "__main__":
    import uvicorn

    import argparse
    parser = argparse.ArgumentParser(description="Start backend server")
    parser.add_argument(
        '--config',
        type=str,
        default=DEFAULT_PATH_TO_CONFIG,
        help='Path to the configuration file.'
    )
    args = parser.parse_args()
    server_config = ConfigLoader(args.config).get_server_config()

    # 日志级别兼容字符串和int
    log_level_str = server_config.get("log_level", "info")
    log_level = getattr(logging, str(log_level_str).upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format=server_config.get("log_format", "%(asctime)s - %(levelname)s - %(message)s"),
        force=True,
        handlers=[
            logging.StreamHandler(),  # 输出到控制台
            # logging.FileHandler(PATH_TO_ROOT / "logs" / "backend.log")  # 输出到文件
        ]
    )
    uvicorn.run(
        "src.app:app",
        host=server_config.get("host", "0.0.0.0"),
        port=server_config.get("port", 8000),
        reload=server_config.get("reload", True),
        # Limit which directories the reloader watches. This avoids permission errors
        # when watchfiles tries to access database files (e.g. database_for_trial/my_data).
        # We watch the backend package directory only.
        reload_dirs=[str(PATH_TO_ROOT / "backend")]

    )




