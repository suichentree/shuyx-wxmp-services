import random
from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_exam_option_service import MpUserExamOptionService
from utils.response_util import ResponseUtil, ResponseDTO

# 创建路由实例
router = APIRouter(prefix='/mp/exam/random/practice', tags=['随机练习接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserExamOptionService_instance = MpUserExamOptionService()

"""
随机练习相关接口
"""

"""
根据题目ID从题库中随机获取题目
"""
@router.post("/getQuestion", response_model=ResponseDTO)
def getQuestion(exam_id: int = Body(..., embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/random/practice/getQuestion, exam_id={exam_id}")

    # 开启事务管理
    with db_session.begin():
        # 随机获取题目数量
        num: int = 50

        # 随机获取题目
        all_questionids: List[int] = MpQuestionService_instance.get_all_questionids(db_session, exam_id=exam_id)

        print(all_questionids)
        random_questionids: List[int] = random.sample(all_questionids, num)

        # 根据id获取题目
        question_option_dto: List[MpQuestionOptionDTO] = MpQuestionService_instance.get_questions_with_options_by_questionids(db_session, question_ids=random_questionids)

        # 返回结果
        return ResponseUtil.success(code=200, message="success", data={
            "questions": [item.model_dump() for item in question_option_dto],
        })


