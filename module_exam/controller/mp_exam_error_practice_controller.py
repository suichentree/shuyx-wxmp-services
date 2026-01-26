from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO, MpQuestionOptionTraceDTO
from module_exam.model.mp_user_question_ebbinghaus_track import MpUserQuestionEbbinghausTrackModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_exam_option_service import MpUserExamOptionService
from module_exam.service.mp_user_question_ebbinghaus_track_service import MpUserQuestionEbbinghausTrackService
from utils.response_util import ResponseUtil, ResponseDTO

# 创建路由实例
router = APIRouter(prefix='/mp/exam/errorPractice', tags=['mp_exam_errorPractice接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserExamOptionService_instance = MpUserExamOptionService()
MpUserQuestionEbbinghausTrackService_instance = MpUserQuestionEbbinghausTrackService()

"""
错题练习相关接口
"""

"""
根据题目ID从题目轨迹表中获取已做过且错过的题目信息
"""
@router.post("/getQuestion", response_model=ResponseDTO)
def getQuestion(exam_id: int = Body(..., embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/errorPractice/getQuestion, exam_id={exam_id}")

    # 开启事务管理
    with db_session.begin():
        # 查询用户已做过且错过的题目ID列表
        errorQuestions: List[MpUserQuestionEbbinghausTrackModel] = MpUserQuestionEbbinghausTrackService_instance.find_missed_question_ids(db_session, exam_id=exam_id)

        # 检查用户已做过且错过的题目是否存在
        if errorQuestions is None or len(errorQuestions) == 0:
            return ResponseUtil.success(code=200, message="success", data=[])
        else:
            # 获取题目ID，并根据题目ID查询题目 + 选项
            question_ids: List[int] = [item.question_id for item in errorQuestions]
            # 查询题目 + 选项
            question_option_dto: List[MpQuestionOptionDTO] = MpQuestionService_instance.get_questions_with_options_by_questionids(db_session, question_ids=question_ids)

            #遍历，添加错误次数，正确次数，和做题总次数
            question_option_trace_dto: List[MpQuestionOptionTraceDTO] = []
            for item in question_option_dto:
                # 创建MpQuestionOptionTraceDTO实例
                trace_item = MpQuestionOptionTraceDTO(
                    question=item.question,
                    options=item.options,
                    error_count=0,
                    correct_count=0,
                    total_count=0
                )
                trace_item.error_count = next((track.error_count for track in errorQuestions if track.question_id == item.question.id), 0)
                trace_item.correct_count = next((track.correct_count for track in errorQuestions if track.question_id == item.question.id), 0)
                trace_item.total_count = next((track.total_count for track in errorQuestions if track.question_id == item.question.id), 0)
                # 添加到结果列表
                question_option_trace_dto.append(trace_item)

            # 返回结果
            return ResponseUtil.success(code=200, message="success", data={
                "questions": [item.model_dump() for item in question_option_trace_dto],
            })
