"""
全局异常处理器
统一将各类异常转换为 {code, message, data} 格式
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from typing import Union
import traceback

from config.log_config import logger


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    处理 HTTPException（如 404、401、403 等）
    """
    logger.warning(f"HTTPException: {exc.status_code} - {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    处理请求参数校验错误（Pydantic 校验失败）
    """
    logger.warning(f"ValidationError: {exc.errors()}")
    
    # 提取第一个错误信息，方便前端展示
    first_error = exc.errors()[0] if exc.errors() else {}
    field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
    msg = first_error.get("msg", "参数校验失败")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": f"参数校验失败: {field} - {msg}",
            "data": {
                "errors": exc.errors()  # 返回详细错误列表供调试
            }
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    处理数据库异常
    """
    logger.error(f"Database Error: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "数据库操作失败",
            "data": {
                "detail": str(exc) if __debug__ else None  # 生产环境不暴露详细错误
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理所有未捕获的异常（兜底）
    """
    logger.error(f"Unhandled Exception: {type(exc).__name__} - {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": {
                "type": type(exc).__name__,
                "detail": str(exc) if __debug__ else None  # 生产环境不暴露详细错误
            }
        }
    )


def register_exception_handlers(app):
    """
    注册所有异常处理器到 FastAPI 应用
    
    使用方式（在 main.py 中调用）：
        from config.exception_handlers import register_exception_handlers
        
        app = FastAPI()
        register_exception_handlers(app)
    """
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("全局异常处理器注册完成")
