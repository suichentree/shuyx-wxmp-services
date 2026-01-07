from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO
from module_exam.dto.mp_option_dto import MpOptionDTO
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO, MpQuestionDTO
from module_exam.dto.mp_user_exam_dto import MpUserExamDTO
from module_exam.dto.mp_user_option_dto import MpUserOptionDTO
from module_exam.model.mp_exam_model import MpExamModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_option_service import MpUserOptionService
from utils.response_util import ResponseUtil, model_to_dto, ResponseDTO, ResponseDTOBase

# 创建路由实例
router = APIRouter(prefix='/mp/kaoshi', tags=['mp_kaoshi接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserOptionService_instance = MpUserOptionService()

"""
模拟考试相关接口设计：
1. 获取试卷题目（可随机抽题）
2. 交卷（一次性提交整套题目的作答数据，并计算得分）
3. 获取最近一次模拟考试结果
4. 查询用户模拟考试历史记录
"""

"""
获取一套模拟考试试卷题目（默认全部题目，可指定抽取数量并随机打乱）
"""
@router.post("/getExamPaper", response_model=ResponseDTOBase)
def get_exam_paper(exam_id: int = Body(..., embed=True),user_id: int = Body(..., embed=True)
,question_num: int | None = Body(None, embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/kaoshi/getExamPaper, user_id={user_id}, exam_id={exam_id}, question_num={question_num}")

    # 获取所有题目和选项
    question_option_list: List[MpQuestionOptionDTO] = MpQuestionService_instance.get_questions_with_options(
        db_session, exam_id
    )

    # 若指定数量且小于题库总量，则随机抽题
    if question_num is not None and 0 < question_num < len(question_option_list):
        import random

        question_option_list = random.sample(question_option_list, question_num)

    # 创建一条本次模拟考试记录（type=1）
    user_exam = MpUserExamDTO(
        user_id=user_id,
        exam_id=exam_id,
        type=1,
        page_no=0,
        score=0,
        create_time=datetime.now(),
    )
    new_user_exam = MpUserExamService_instance.add(db_session, dict_data=user_exam.model_dump())

    # 返回本次试卷的题目及其选项，以及 user_exam_id
    dto_result = model_to_dto(data=question_option_list, dto_cls=MpQuestionOptionDTO)
    return ResponseUtil.success(
        data={
            "user_exam_id": new_user_exam.id,
            "exam_id": exam_id,
            "question_num": len(question_option_list),
            "question_list": dto_result,
        }
    )

"""
模拟考试交卷：一次性提交所有题目的答案，并计算分数
"""
@router.post("/submit", response_model=ResponseDTOBase)
def submit_exam(user_id: int = Body(...),exam_id: int = Body(...),user_exam_id: int = Body(...),
answer_map: dict[int, List[int]] = Body(...),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/kaoshi/submit, user_id={user_id}, exam_id={exam_id}, user_exam_id={user_exam_id}, answer_map={answer_map}")

    # 用事务包住：插入多条 user_option + 更新 user_exam，保证原子性
    with db_session.begin():
        total_score = 0
        answered_count = 0

        for qid_str, option_ids in answer_map.items():
            # Body 传 dict 时 key 可能是 str，这里统一转 int
            question_id = int(qid_str)
            if not option_ids:
                continue

            # 查询题目信息，判断题型（单选/多选/判断）
            question = MpQuestionService_instance.get_one_by_filters(
                db_session, filters=MpQuestionDTO(id=question_id).model_dump()
            )
            if question is None:
                logger.warning(f"question_id={question_id} 不存在，跳过")
                continue

            # 查询正确选项
            right_options = MpOptionService_instance.get_list_by_filters(
                db_session,
                filters=MpOptionDTO(question_id=question_id, is_right=1).model_dump(),
            )
            right_ids: List[int] = [opt.id for opt in right_options]

            # 计算本题是否作答正确（全对得1分，否则0分）
            is_right_question = 1 if set(right_ids) == set(option_ids) else 0
            if is_right_question:
                total_score += 1
            answered_count += 1

            # 记录用户选项（多选题会插多条）
            is_duoxue = 1 if question.type == 2 else 0
            for oid in option_ids:
                MpUserOptionService_instance.add(
                    db_session=db_session,
                    dict_data=MpUserOptionDTO(
                        user_id=user_id,
                        exam_id=exam_id,
                        user_exam_id=user_exam_id,
                        question_id=question_id,
                        option_id=oid,
                        is_duoxue=is_duoxue,
                        is_right=1 if oid in right_ids else 0,
                    ).model_dump(),
                    commit=False,
                )

        # 更新本次模拟考试记录
        update_data = {
            "page_no": answered_count,
            "score": total_score,
            "finish_time": datetime.now(),
            "type": 1,
        }
        MpUserExamService_instance.update_by_id(
            db_session=db_session,
            id=user_exam_id,
            update_data=update_data,
            commit=False,
        )

    return ResponseUtil.success(
        data={
            "user_exam_id": user_exam_id,
            "right_num": total_score,
            "error_num": answered_count - total_score,
        }
    )

"""
获取用户最近一次模拟考试结果
"""
@router.post("/lastResult")
def last_result(user_id: int = Body(..., embed=True),exam_id: int = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/kaoshi/lastResult, user_id={user_id}, exam_id={exam_id}")

    # 只查询 type=1（模拟考试）的完成记录
    last_finish_user_exam = MpUserExamService_instance.get_one_by_filters(
        db_session,
        filters=MpUserExamDTO(
            user_id=user_id,
            exam_id=exam_id,
            type=1,
            finish_time=True,
        ).model_dump(),
        sort_by=["-id"],
    )
    if last_finish_user_exam is None:
        return ResponseUtil.success(data={"message": "用户暂无模拟考试记录"})

    data = {
        "user_exam_id": last_finish_user_exam.id,
        "right_num": last_finish_user_exam.score,
        "error_num": last_finish_user_exam.page_no - last_finish_user_exam.score,
        "finish_time": last_finish_user_exam.finish_time,
    }
    return ResponseUtil.success(data=data)

"""
查询用户所有模拟考试历史记录（按考试分组，展示最近一次模拟结果）
"""
@router.post("/history")
def kaoshi_history(user_id: int = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/kaoshi/history, user_id={user_id}")

    JsonArray = []

    # 查询该用户参与过的考试列表（只考虑 type=1 的记录）
    user_exams = MpUserExamService_instance.get_list_by_filters(
        db_session,
        filters=MpUserExamDTO(user_id=user_id, type=1, finish_time=True).model_dump(),
        sort_by=["exam_id", "-id"],
    )
    # 根据 exam_id 去重，只保留每个 exam 的最近一次记录
    handled_exam_ids: set[int] = set()
    for ue in user_exams:
        if ue.exam_id in handled_exam_ids:
            continue
        handled_exam_ids.add(ue.exam_id)
        exam_info = MpExamService_instance.get_by_id(db_session, id=ue.exam_id)
        if exam_info is None:
            continue
        JsonArray.append(
            {
                "examId": exam_info.id,
                "examName": exam_info.name,
                "finishTime": ue.finish_time,
                "right_num": ue.score,
                "error_num": ue.page_no - ue.score,
            }
        )

    return ResponseUtil.success(data=JsonArray)