from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO, MpExamCommonDTO
from module_exam.model.mp_exam_model import MpExamModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_exam_option_service import MpUserExamOptionService
from utils.response_util import ResponseUtil

# 创建路由实例
router = APIRouter(prefix='/mp/exam', tags=['mp_exam接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserExamOptionService_instance = MpUserExamOptionService()

"""
获取测试列表信息
"""
@router.post("/getExamList")
def getExamList(page_num:int=Body(...), page_size:int=Body(...),exam_name:str=Body(None),exam_tag:str=Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getExamList, page_num = {page_num}, page_size = {page_size}, exam_name = {exam_name}, exam_tag = {exam_tag}')
    # 获取所有考试标签
    tagList:List[dict] = MpExamService_instance.get_exam_tags(db_session)

    # 构建查询条件
    query_dict = MpExamModel(status=0).to_dict()
    if exam_name and exam_name.strip() != "":
        query_dict['name__like'] = exam_name
    if exam_tag and exam_tag.strip() != "":
        query_dict['tag'] = exam_tag
    # 分页查询
    print(query_dict)
    examList:List[MpExamModel] = MpExamService_instance.get_page_list_by_filters(db_session, page_num=page_num, page_size=page_size, filters=query_dict)

    # 响应结果
    return ResponseUtil.success(code=200, message="success", data={
        "tags": tagList,
        "exams": [MpExamCommonDTO.model_validate(exam) for exam in examList]
    })

