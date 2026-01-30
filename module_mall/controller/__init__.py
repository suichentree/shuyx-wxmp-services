# controller/__init__.py
# 从各个controller文件导入路由实例
from fastapi import APIRouter

from module_mall.controller.product_controller import router as product_router
from module_mall.controller.order_controller import router as order_router


# 创建总路由实例
api_router = APIRouter()

# 注册所有路由
for router in [product_router,order_router]:
    # 通过include_router函数，把各个路由实例加入到FastAPI应用实例中,进行统一管理
    api_router.include_router(router)

