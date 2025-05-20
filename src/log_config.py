# log_config.py
import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 创建 logs 目录
current_dir = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(current_dir, "../logs")

os.makedirs(LOG_DIR, exist_ok=True)

# 日志文件路径
APP_LOG_FILE = os.path.join(LOG_DIR, "sys.log")

logger = logging.getLogger("AppLogger")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(message)s"
)

app_log_handler = TimedRotatingFileHandler(
    APP_LOG_FILE, when="midnight", interval=1, backupCount=7, encoding="utf-8"
)
app_log_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

logger.addHandler(app_log_handler)
logger.addHandler(console_handler)

logger.info("日志系统初始化完成")
