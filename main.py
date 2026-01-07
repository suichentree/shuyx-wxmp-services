# 导入FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 导入全局异常处理器
from config.exception_handlers import register_exception_handlers

# 创建FastAPI应用实例
app = FastAPI(
    title="微信小程序服务API",
    description="微信小程序-测试系统后端API",
    version="1.0.1"
)

# 注册全局异常处理器（推荐使用，替代旧的 ExceptionMiddleware）
register_exception_handlers(app)

# 可选中间件（按需启用）
# 认证中间件
# from middlewares.auth_middleware import AuthMiddleware
# app.middleware("http")(AuthMiddleware)
# 日志中间件
# from middlewares.logger_middleware import LoggerMiddleware
# app.middleware("http")(LoggerMiddleware)
# 添加 GZip 中间件，压缩大于 2000 字节的响应
# from fastapi.middleware.gzip import GZipMiddleware
# app.add_middleware(GZipMiddleware, minimum_size=2000)

# 注册CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","http://localhost:39666", "http://127.0.0.1:39666"], # 测试环境中允许所有来源，生产环境中请指定具体来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 导入控制器路由
from module_exam.controller.mp_exam_controller import router as mp_exam_router
# 通过include_router函数，把各个路由实例加入到FastAPI应用实例中,进行统一管理
app.include_router(mp_exam_router)

# 测试运行接口
@app.get("/")
async def root():
    """根路径接口"""
    return {"message": "Hello World , 服务运行正常", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        app='main:app',
        port=39666,
        reload=True,
        log_level="info"  # 添加日志级别配置
    )