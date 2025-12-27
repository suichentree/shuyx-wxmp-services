from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO
from module_exam.dto.mp_option_dto import MpOptionDTO
from module_exam.dto.mp_question_dto import MpQuestionDTO
from module_exam.dto.mp_user_exam_dto import MpUserExamDTO
from module_exam.dto.mp_user_option_dto import MpUserOptionDTO
from module_exam.model.mp_option_model import MpOptionModel
from module_exam.model.mp_user_exam_model import MpUserExamModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_option_service import MpUserOptionService
from module_exam.service.mp_user_service import MpUserService
from utils.response_util import ResponseUtil

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

    # 分页查询，状态正常的考试信息
    mp_exam_dto_dict = MpExamDTO(status=0).model_dump()

    result = MpExamService_instance.get_page_list_by_filters(db_session, page_num=page_num, page_size=page_size, filters=mp_exam_dto_dict)
    print(result)
    # 若result为空，则返回空列表。不为空则返回result
    return ResponseUtil.success(data=result if result is not None else [])

"""
获取测试题目列表信息
"""
@router.post("/getQuestionList")
def getQuestionList(exam_id:int = Body(None,embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getQuestionList, exam_id = {exam_id}')

    # 调用自定义方法获取问题和选项数据
    result = MpQuestionService_instance.get_questions_with_options(db_session, exam_id)
    print(result)
    return ResponseUtil.success(data=result if result is not None else [])

















