from loguru import logger
import sys

# 移除默认配置
logger.remove(0)
# 自定义的日志输出格式 。 里面添加了process和thread记录，方便查看多进程和线程的信息
log_format= '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level}</level> ' \
            '| <magenta>{process}</magenta>:<yellow>{thread}</yellow> ' \
            '| <cyan>{name}</cyan>:<cyan>{function}</cyan>:<yellow>{line}</yellow> - <level>{message}</level>'

# 添加自定义的控制台日志输出格式
logger.add(sys.stdout,colorize=True,format=log_format)
