from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO, MpExamCommonDTO
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_option_service import MpUserOptionService
from utils.response_util import ResponseUtil, model_to_dto

# 创建路由实例
router = APIRouter(prefix='/mp/exam', tags=['mp_exam接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserOptionService_instance = MpUserOptionService()

"""
获取测试列表信息
"""
@router.get("/getExamList")
def getExamList(page_num:int=1, page_size:int=10,db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getExamList, page_num = {page_num}, page_size = {page_size}')

    # 构建dto对象，分页查询，状态正常的考试信息
    mp_exam_dto = MpExamDTO(status=0)
    result111 = MpExamService_instance.get_page_list_by_filters(db_session, page_num=page_num, page_size=page_size, filters=mp_exam_dto.model_dump())

    # 将查询结果转换为指定dto类型
    result = model_to_dto(data=result111, dto_cls=MpExamDTO)
    print(result)
    for i in result:
        print(i)
        print(type(i))

    return ResponseUtil.success(code=200, message="success", data=result)


"""
获取测试题目列表信息
"""
@router.post("/getQuestionList")
def getQuestionList(exam_id:int = Body(None,embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getQuestionList, exam_id = {exam_id}')
    # 调用自定义方法获取问题和选项数据
    result = MpQuestionService_instance.get_questions_with_options(db_session, exam_id)
    print(result)

    # 将查询结果转换为指定dto类型
    result = model_to_dto(data=result, dto_cls=MpQuestionOptionDTO)
    print(result)

    return ResponseUtil.success(code=200, message="success", data=result)

















