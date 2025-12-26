from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Callable

# 全局异常处理中间件
async def ExceptionMiddleware(request: Request, call_next: Callable):
    print("ExceptionMiddleware===============")
    try:
        # 正常处理请求
        response = await call_next(request)
        return response
    except Exception as e:
        # 捕获所有异常并处理

        # 若异常信息包含code和message属性
        if hasattr(e, 'code') and hasattr(e, 'message'):
            return JSONResponse(
                status_code=e.code,
                content={"code": e.code, "message": e.message}
            )
        else:
            # 将异常信息转换为JSON响应
            return JSONResponse(
                status_code=500,
                content={"code": 500,"message": f"服务异常信息= {str(e)}"}
            )