from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Callable
from utils.jwt_util import JWTUtil

# 认证中间件
async def AuthMiddleware(request: Request, call_next: Callable):
    # 精确匹配的路径
    exact_paths = ["/", "/login", "/logout", "/docs", "/redoc", "/openapi.json"]

    # 测试路径前缀（支持通配符效果）
    test_path_prefixes = [
        "/test/",  # 匹配所有以XXX开头的路径
    ]

    # 检查是否是精确匹配的路径
    if request.url.path in exact_paths:
        # 直接放行
        return await call_next(request)

    # 检查是否是测试路径前缀匹配的路径,如果是,直接放行
    for prefix in test_path_prefixes:
        if request.url.path.startswith(prefix):
            return await call_next(request)

    # 获取 Authorization 头
    auth_header = request.headers.get("Authorization")

    # 验证 token
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "未授权访问，需要有效的token"}
        )

    # 获取token
    token = auth_header.split(" ")[1]
    # 验证token是否有效
    if JWTUtil.verify_token(token) is False:
        return JSONResponse(
            status_code=401,
            content={"detail": "无效的 token"}
        )

    # 验证通过，继续处理请求
    return await call_next(request)