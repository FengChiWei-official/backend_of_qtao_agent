import logging

logging.basicConfig(
    level=logging.INFO,  # 日志级别
    format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
)
logger = logging.getLogger(__name__)