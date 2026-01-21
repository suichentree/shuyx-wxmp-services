import traceback
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Callable
from config.log_config import logger  # 导入项目配置的日志系统

# 全局异常处理中间件
async def ExceptionMiddleware(request: Request, call_next: Callable):
    try:
        # 正常请求
        response = await call_next(request)
        return response

    except Exception as e:
        # 捕获所有异常并处理
        
        # 获取完整的异常堆栈信息
        error_traceback = traceback.format_exc()
        
        # 使用项目配置的日志系统记录异常信息，包括堆栈
        logger.error(f"ExceptionMiddleware ==> 请求异常: {request.url}\n异常类型: {type(e).__name__}\n异常信息: {str(e)}\n堆栈信息:\n{error_traceback}")

        # 若异常信息包含code和message属性，则封装为JSON响应
        if hasattr(e, 'code') and hasattr(e, 'message'):
            return JSONResponse(
                status_code=e.code,
                content={"code": e.code, "message": e.message}
            )
        else:
            # 将异常信息转换为JSON响应并返回给客户端
            return JSONResponse(
                status_code=500,
                content={"code": 500, "message": f"服务器内部错误: {str(e)}"}
            )