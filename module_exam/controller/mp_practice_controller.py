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
router = APIRouter(prefix='/mp/practice', tags=['mp_practice接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserOptionService_instance = MpUserOptionService()

"""
顺序练习相关接口设计：
1. 获取当前练习进度对应的题目（自动创建/续做顺序练习）
2. 单选题作答（顺序练习场景）
3. 多选题作答（顺序练习场景）
4. 重置顺序练习，从头开始新一轮练习
"""

"""
公共内部方法
根据 exam_id 和顺序序号（page_no，从 1 开始）获取单个题目及选项
"""
def _get_question_with_options(db_session: Session, exam_id: int, page_no: int) -> dict | None:
    # 使用分页按 id 升序取第 page_no 题
    question_list = MpQuestionService_instance.get_page_list_by_filters(
        db_session,
        page_num=page_no,
        page_size=1,
        filters=MpQuestionDTO(exam_id=exam_id, status=0).model_dump(),
        sort_by=["id"],
    )
    if not question_list:
        return None

    question = question_list[0]
    options = MpOptionService_instance.get_list_by_filters(
        db_session, filters=MpOptionDTO(question_id=question.id, status=0).model_dump(), sort_by=["id"]
    )

    return {
        "question": MpQuestionDTO.model_validate(question).model_dump(),
        "options": model_to_dto(options, MpOptionDTO),
    }

"""
获取当前顺序练习进度对应的题目；若无未完成记录则新建一轮，从第一题开始
"""
@router.post("/getCurrentQuestion", response_model=ResponseDTOBase)
def get_current_question(user_id: int = Body(..., embed=True),exam_id: int = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/practice/getCurrentQuestion, user_id={user_id}, exam_id={exam_id}")

    # 题目总数
    total_count: int = MpQuestionService_instance.get_total_by_filters(
        db_session, filters=MpQuestionDTO(exam_id=exam_id, status=0).model_dump()
    )
    if total_count == 0:
        return ResponseUtil.error(code=400, message="该考试暂无题目")

    # 查找最近一次未完成的顺序练习记录（type=0）
    user_exam = MpUserExamService_instance.get_one_by_filters(
        db_session,
        filters=MpUserExamDTO(user_id=user_id, exam_id=exam_id, type=0, finish_time=False).model_dump(),
        sort_by=["-id"],
    )

    if user_exam is None:
        # 新建一轮顺序练习，从第一题开始
        logger.info("未找到未完成顺序练习，创建新的顺序练习记录")
        new_exam = MpUserExamDTO(
            user_id=user_id,
            exam_id=exam_id,
            type=0,
            page_no=1,
            score=0,
            create_time=datetime.now(),
        )
        user_exam = MpUserExamService_instance.add(db_session, dict_data=new_exam.model_dump())

    # 已经做到最后一题并完成
    if user_exam.page_no > total_count:
        return ResponseUtil.success(
            data={
                "finished": True,
                "message": "当前顺序练习已完成，请重置后重新开始",
            }
        )

    question_data = _get_question_with_options(db_session, exam_id, user_exam.page_no)
    if question_data is None:
        return ResponseUtil.error(code=400, message="未找到对应题目")

    return ResponseUtil.success(
        data={
            "user_exam_id": user_exam.id,
            "exam_id": exam_id,
            "page_no": user_exam.page_no,
            "total": total_count,
            "question": question_data["question"],
            "options": question_data["options"],
        }
    )


"""
顺序练习 - 单选题作答：每题答完立即记录并给出是否正确
"""
@router.post("/danxueAnswer")
def danxue_answer(user_id: int = Body(...),exam_id: int = Body(...),user_exam_id: int = Body(...),question_id: int = Body(...),option_id: int = Body(...),page_no: int = Body(...),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/practice/danxueAnswer, user_id={user_id}, exam_id={exam_id}, user_exam_id={user_exam_id}, question_id={question_id}, option_id={option_id}, page_no={page_no}")

    # 查询选项信息
    option_result = MpOptionService_instance.get_by_id(db_session, id=option_id)
    if option_result is None:
        return ResponseUtil.error(code=400, message="该选项不存在")

    # 题目总数
    question_count: int = MpQuestionService_instance.get_total_by_filters(
        db_session, filters=MpQuestionDTO(exam_id=exam_id, status=0).model_dump()
    )

    # 查询当前顺序练习记录
    user_exam = MpUserExamService_instance.get_by_id(db_session, id=user_exam_id)
    if user_exam is None or user_exam.user_id != user_id or user_exam.exam_id != exam_id:
        return ResponseUtil.error(code=400, message="顺序练习记录不存在或不匹配")

    with db_session.begin():
        # 更新得分与进度
        new_score = user_exam.score + (1 if option_result.is_right == 1 else 0)
        update_data = {
            "page_no": page_no,
            "score": new_score,
        }
        if page_no >= question_count:
            update_data["finish_time"] = datetime.now()

        MpUserExamService_instance.update_by_id(
            db_session=db_session,
            id=user_exam_id,
            update_data=update_data,
            commit=False,
        )

        # 记录用户本题作答
        MpUserOptionService_instance.add(
            db_session=db_session,
            dict_data=MpUserOptionDTO(
                user_id=user_id,
                exam_id=exam_id,
                user_exam_id=user_exam_id,
                is_duoxue=0,
                question_id=question_id,
                option_id=option_id,
                is_right=option_result.is_right,
            ).model_dump(),
            commit=False,
        )

    return ResponseUtil.success(
        data={
            "is_right": option_result.is_right,
            "current_score": new_score,
            "finished": True if page_no >= question_count else False,
        }
    )

"""
顺序练习 - 多选题作答：每题答完立即记录并给出是否正确（全对得 1 分）
"""
@router.post("/duoxueAnswer")
def duoxue_answer(user_id: int = Body(...),exam_id: int = Body(...),user_exam_id: int = Body(...),question_id: int = Body(...),option_ids: List[int] = Body(...),page_no: int = Body(...),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/practice/duoxueAnswer, user_id={user_id}, exam_id={exam_id}, user_exam_id={user_exam_id}, question_id={question_id}, option_ids={option_ids}, page_no={page_no}")

    # 查询题目的正确选项集合
    right_list = MpOptionService_instance.get_list_by_filters(
        db_session, filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump()
    )
    if not right_list:
        return ResponseUtil.error(code=400, message="该多选题无正确选项")

    right_ids: List[int] = [item.id for item in right_list]
    is_same = set(right_ids) == set(option_ids)

    # 题目总数
    question_count: int = MpQuestionService_instance.get_total_by_filters(
        db_session, filters=MpQuestionDTO(exam_id=exam_id, status=0).model_dump()
    )

    # 查询当前顺序练习记录
    user_exam = MpUserExamService_instance.get_by_id(db_session, id=user_exam_id)
    if user_exam is None or user_exam.user_id != user_id or user_exam.exam_id != exam_id:
        return ResponseUtil.error(code=400, message="顺序练习记录不存在或不匹配")

    with db_session.begin():
        # 更新得分与进度
        new_score = user_exam.score + (1 if is_same else 0)
        update_data = {
            "page_no": page_no,
            "score": new_score,
        }
        if page_no >= question_count:
            update_data["finish_time"] = datetime.now()

        MpUserExamService_instance.update_by_id(
            db_session=db_session,
            id=user_exam_id,
            update_data=update_data,
            commit=False,
        )

        # 记录用户本题作答（多选每个选项一条记录）
        for oid in option_ids:
            MpUserOptionService_instance.add(
                db_session=db_session,
                dict_data=MpUserOptionDTO(
                    user_id=user_id,
                    exam_id=exam_id,
                    user_exam_id=user_exam_id,
                    is_duoxue=1,
                    question_id=question_id,
                    option_id=oid,
                    is_right=1 if oid in right_ids else 0,
                ).model_dump(),
                commit=False,
            )

    return ResponseUtil.success(
        data={
            "is_right": 1 if is_same else 0,
            "current_score": new_score,
            "finished": True if page_no >= question_count else False,
        }
    )

"""
重置顺序练习：新开一轮练习，从第一题开始（历史记录保留）
"""
@router.post("/reset")
def reset_practice(user_id: int = Body(..., embed=True),exam_id: int = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/practice/reset, user_id={user_id}, exam_id={exam_id}")

    new_exam = MpUserExamDTO(user_id=user_id,exam_id=exam_id,type=0,page_no=1,score=0,create_time=datetime.now())
    user_exam = MpUserExamService_instance.add(db_session, dict_data=new_exam.model_dump())

    # 获取第一题
    question_data = _get_question_with_options(db_session, exam_id, page_no=1)
    if question_data is None:
        return ResponseUtil.error(code=400, message="该考试暂无题目")

    total_count: int = MpQuestionService_instance.get_total_by_filters(
        db_session, filters=MpQuestionDTO(exam_id=exam_id, status=0).model_dump()
    )

    return ResponseUtil.success(
        data={
            "user_exam_id": user_exam.id,
            "exam_id": exam_id,
            "page_no": 1,
            "total": total_count,
            "question": question_data["question"],
            "options": question_data["options"],
        }
    )
