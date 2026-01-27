# controller/__init__.py
# 从各个controller文件导入路由实例
from fastapi import APIRouter
from module_exam.controller.common_controller import router as common_router
from module_exam.controller.mp_exam_controller import router as mp_exam_router
from module_exam.controller.mp_exam_kaoshi_controller import router as mp_exam_kaoshi_router
from module_exam.controller.mp_user_controller import router as mp_user_router
from module_exam.controller.wx_controller import router as wx_router
from module_exam.controller.excel_controller import router as excel_router
from module_exam.controller.login_controller import router as login_router
from module_exam.controller.mp_exam_error_practice_controller import router as mp_exam_error_practice_router
from module_exam.controller.mp_exam_sequence_practice_controller import router as mp_exam_sequence_practice_router
from module_exam.controller.mp_exam_random_practice_controller import router as mp_exam_random_practice_router



# 创建总路由实例
api_router = APIRouter()

# 注册所有路由
for router in [common_router, mp_exam_router, mp_exam_kaoshi_router, mp_exam_sequence_practice_router, mp_exam_random_practice_router,
              mp_user_router, wx_router,login_router,mp_exam_error_practice_router,
               excel_router]:
    # 通过include_router函数，把各个路由实例加入到FastAPI应用实例中,进行统一管理
    api_router.include_router(router)

