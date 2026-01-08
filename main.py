# 导入FastAPI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 创建FastAPI应用实例
app = FastAPI(
    title="微信小程序服务API",
    description="微信小程序-测试系统后端API",
    version="1.0.1"
)

# 全局异常处理中间件
# app.middleware("http")(ExceptionMiddleware)
# 认证中间件
# app.middleware("http")(AuthMiddleware)
# 日志中间件
# app.middleware("http")(LoggerMiddleware)
# 添加 GZip 中间件，压缩大于 2000 字节的响应
# app.add_middleware(GZipMiddleware, minimum_size=2000)

# 注册CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*","http://localhost:39666", "http://127.0.0.1:39666"], # 测试环境中允许所有来源，生产环境中请指定具体来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)

# 批量导入控制器路由
from module_exam.controller.common_controller import router as common_router
from module_exam.controller.mp_exam_controller import router as mp_exam_router
from module_exam.controller.mp_exam_kaoshi_controller import router as mp_exam_kaoshi_router
from module_exam.controller.mp_exam_practice_controller import router as mp_exam_practice_router
from module_exam.controller.mp_user_controller import router as mp_user_router
from module_exam.controller.wx_controller import router as wx_router

# 注册所有路由
for router in [common_router, mp_exam_router, mp_exam_kaoshi_router, mp_exam_practice_router, mp_user_router, wx_router]:
    # 通过include_router函数，把各个路由实例加入到FastAPI应用实例中,进行统一管理
    app.include_router(router)

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