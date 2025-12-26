from fastapi import Request
from loguru import logger
from typing import Callable

# 日志中间件
async def LoggerMiddleware(request: Request, call_next: Callable):
    # 初始化请求信息字典
    request_info = {
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client": str(request.client) if request.client else None
    }
    # 记录请求信息
    logger.info(f"Request Info: {request_info}")

    # 继续处理请求，并获取响应对象
    response = await call_next(request)

    # 返回响应对象
    return response