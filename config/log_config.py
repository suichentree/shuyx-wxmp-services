from loguru import logger
import sys
import os

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 移除默认配置
logger.remove(0)

# 自定义日志格式
log_format = '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> | <magenta>{process}</magenta>:<yellow>{thread}</yellow> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<yellow>{line}</yellow> - <level>{message}</level>'

# 添加控制台日志
logger.add(sys.stdout, colorize=True, format=log_format)

# 添加文件日志，每天轮转，保留7天
logger.add("logs/app_{time:YYYY-MM-DD}.log", format=log_format, rotation="00:00", retention="7 days")