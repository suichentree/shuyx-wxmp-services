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
from module_exam.dto.mp_user_exam_option_dto import MpUserExamOptionDTO
from module_exam.model.mp_exam_model import MpExamModel
from module_exam.model.mp_user_exam_model import MpUserExamModel
from module_exam.model.mp_user_exam_option_model import MpUserExamOptionModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_exam_option_service import MpUserExamOptionService
from utils.response_util import ResponseUtil, ResponseDTO

# 创建路由实例
router = APIRouter(prefix='/mp/exam/practice', tags=['mp_practice接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserExamOptionService_instance = MpUserExamOptionService()

"""
顺序练习相关接口
"""

"""
获取顺序练习历史记录
"""
@router.post("/history", response_model=ResponseDTO)
def history(user_id: int = Body(..., embed=True), exam_id: int = Body(..., embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/practice/history, user_id={user_id}, exam_id={exam_id}")

    # 查询用户顺序练习历史记录,id降序
    user_exam_history: List[MpUserExamModel] = MpUserExamService_instance.get_list_by_filters(
        db_session, 
        filters=MpUserExamDTO(
            user_id=user_id,
            exam_id=exam_id,
            type=0,  # 顺序练习
        ).model_dump(),
        sort_by=["-id"]
    )

    # 根据exam_id 获取考试信息
    exam_result: MpExamModel = MpExamService_instance.get_one_by_filters(
        db_session, 
        filters=MpExamDTO(id=exam_id).model_dump()
    )

    # 返回结果
    return ResponseUtil.success(code=200, message="success", data={
        "exam_info": exam_result.to_dict() if exam_result else None,
        "user_exam_history": [exam.to_dict() for exam in user_exam_history],
    })


"""
开始/继续顺序练习
1. 检查用户是否有未完成的练习记录
2. 如果有，返回当前练习记录
3. 如果没有，创建新的顺序练习记录，返回新记录
4. exam_id 和 user_id 不能为空，否则报422错误
"""
@router.post("/start", response_model=ResponseDTO)
def start(exam_id: int = Body(..., embed=True), user_id: int = Body(..., embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/practice/start, user_id={user_id}, exam_id={exam_id}")

    # 事务管理
    with db_session.begin():
        # 查询题库总题数
        total_count = MpQuestionService_instance.get_total_by_filters(
            db_session,
            filters=MpQuestionDTO(exam_id=exam_id, status=0).model_dump()
        )
        if total_count == 0:
            return ResponseUtil.error(code=400, message="该考试暂无题目")

        # 查找最近一次未完成的顺序练习记录（type=0）
        user_exam = MpUserExamService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamDTO(user_id=user_id, exam_id=exam_id, type=0, finish_time=False).model_dump(),
            sort_by=["-id"],
        )

        # 如果没有未完成的顺序练习记录，创建新的记录
        if user_exam is None:
            logger.info("未找到未完成顺序练习，创建新的顺序练习记录")
            
            # 获取所有题目ID（按id升序）
            all_questions = MpQuestionService_instance.get_list_by_filters(
                db_session,
                filters=MpQuestionDTO(exam_id=exam_id, status=0).model_dump(),
                sort_by=["id"]
            )
            question_ids = [q.id for q in all_questions]

            # 创建新的顺序练习记录
            user_exam_dto = MpUserExamDTO(
                user_id=user_id,
                exam_id=exam_id,
                type=0,                             # 顺序练习
                last_question_id=question_ids[0],   # 最后做的问题ID，默认初始化为第一题目的id
                correct_count=0,                    # 答对题目数
                total_count=total_count,            # 总题目数
                question_ids=question_ids,          # 保存所有题目ID快照
                create_time=datetime.now(),
                finish_time=None,
            )
            # 保存新记录
            user_exam = MpUserExamService_instance.add(db_session, dict_data=user_exam_dto.model_dump())

        # 返回结果
        return ResponseUtil.success(code=200, message="success", data={
            "user_exam_id": user_exam.id,
        })

"""
根据题目ID获取题目信息（包含选项），以及该题目的答题信息。
- 若question_id参数为空时，则从用户测试记录中获取last_question_id 作为当前题目ID
- 若question_id参数不为空时，则根据question_id获取题目信息
"""
@router.post("/getQuestion", response_model=ResponseDTO)
def getQuestion(user_exam_id: int = Body(..., embed=True),question_id: int = Body(None, embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/practice/getQuestion, user_exam_id={user_exam_id}, question_id={question_id}")

    # 开启事务管理
    with db_session.begin():
        # 查询对应的用户考试记录
        user_exam: MpUserExamModel = MpUserExamService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamDTO(id=user_exam_id).model_dump(),
        )
        # 检查用户考试记录是否存在
        if user_exam is None:
            return ResponseUtil.error(code=400, message="用户考试记录不存在")

        # 若question_id参数为空时，则默认获取当前题目进度
        if question_id is None:
            question_id = user_exam.last_question_id

        # 检查题目ID是否在题目ID列表中
        if question_id not in user_exam.question_ids:
            return ResponseUtil.error(code=400, message="题目ID无效,题目ID不在用户考试记录中")

        # 查询题目 + 选项
        question_option_dto: MpQuestionOptionDTO = MpQuestionService_instance.get_one_questions_with_options(db_session, question_id)
        if question_option_dto is None:
            return ResponseUtil.error(code=400, message="题目数据不存在")

        # 根据题目ID查询当前题目是否已被答题
        user_exam_option:MpUserExamOptionModel = MpUserExamOptionService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamOptionDTO(user_exam_id=user_exam.id, question_id=question_id).model_dump(),
        )
        # 用户是否答题，返回答题信息。
        if user_exam_option is None:
            user_option_ids = None      # 用户选项id列表，为None表示未答题
            is_correct = None           # 是否答对
        else:
            # 用户答题选项（单选是int,多选是列表）
            user_option_ids = user_exam_option.option_ids
            is_correct = user_exam_option.is_correct

        # 返回结果
        return ResponseUtil.success(code=200, message="success", data={
            "user_exam_id": user_exam.id,
            "question_id": question_id,
            "question_ids": user_exam.question_ids,         # 用户考试记录中的所有题目ID列表
            "question_options": question_option_dto.model_dump(),  # 当前题目信息,选项信息
            "selected_option_ids": user_option_ids,               # 用户选择的选项ID列表。若是None则表示未答题。
            "is_correct": is_correct,
        })

"""
提交单题答案
"""
@router.post("/submitAnswer", response_model=ResponseDTO)
def submitAnswer(
    user_exam_id: int = Body(..., embed=True),
    question_id: int = Body(..., embed=True),
    question_type: int = Body(..., embed=True),
    option_ids: List[int] = Body(..., embed=True),  # 单选多选都是列表
    db_session: Session = Depends(get_db_session)
):
    logger.info(f"/mp/exam/practice/submitAnswer, user_exam_id={user_exam_id}, question_id={question_id}, question_type={question_type}, option_ids={option_ids}")

    with db_session.begin():
        # 查询对应的用户考试记录
        user_exam: MpUserExamModel = MpUserExamService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamDTO(id=user_exam_id).model_dump(),
        )
        # 检查用户考试记录是否存在
        if user_exam is None:
            return ResponseUtil.error(code=400, message="用户考试记录不存在")
        # 检查考试是否已完成
        if user_exam.finish_time:
            return ResponseUtil.error(code=400, message="当前考试已完成")

        # 查询问题ID对应的正确选项
        right_options = MpOptionService_instance.get_list_by_filters(
            db_session,
            filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump(),
        )
        right_option_ids = [opt.id for opt in right_options]

        # 判断用户是否答对,对比正确选项列表和用户选项列表是否完全一致
        is_option_correct = (set(right_option_ids) == set(option_ids))

        # 保存用户选项记录
        user_option_dto = MpUserExamOptionDTO(
            user_id=user_exam.user_id,
            exam_id=user_exam.exam_id,
            user_exam_id=user_exam.id,
            question_id=question_id,
            question_type=question_type,
            option_ids=option_ids,
            is_correct=1 if is_option_correct else 0,   #答对=1,答错=0
            create_time=datetime.now(),
        )
        MpUserExamOptionService_instance.add(db_session, dict_data=user_option_dto.model_dump())

        # 更新答对题数
        if is_option_correct:
            user_exam.correct_count += 1

        # 更新最新答题题目ID
        user_exam.last_question_id = question_id

        # 更新用户考试记录
        MpUserExamService_instance.update_by_id(
            db_session,
            id=user_exam.id,
            update_data=user_exam.to_dict(),
        )

        # 返回结果
        return ResponseUtil.success(code=200, message="success", data={
            "user_exam_id": user_exam.id,
            "question_id": question_id,
        })

"""
获取答题卡信息
"""
@router.post("/getAnswerCardInfo", response_model=ResponseDTO)
def getAnswerCardInfo(
    user_exam_id: int = Body(..., embed=True),
    db_session: Session = Depends(get_db_session)
):
    logger.info(f"/mp/exam/practice/getAnswerCardInfo, user_exam_id={user_exam_id}")

    # 开启事务管理
    with db_session.begin():
        # 查询对应的用户考试记录
        user_exam: MpUserExamModel = MpUserExamService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamDTO(id=user_exam_id).model_dump(),
        )
        # 检查用户考试记录是否存在
        if user_exam is None:
            return ResponseUtil.error(code=400, message="用户考试记录不存在")

        # 获取考试记录中所有的问题id
        all_question_ids = user_exam.question_ids or []

        # 拉取所有已答题记录
        user_exam_options:List[MpUserExamOptionModel] = MpUserExamOptionService_instance.get_list_by_filters(
            db_session,
            filters=MpUserExamOptionDTO(user_exam_id=user_exam_id).model_dump()
        )
        # 遍历所有答题记录，获取对应问题id,和答题情况
        user_exam_options_list = []
        for opt in user_exam_options:
            aaa = {}
            aaa["q_id"] = opt.question_id
            aaa["is_correct"] = opt.is_correct
            user_exam_options_list.append(aaa)

        return ResponseUtil.success(code=200, message="success", data={
            "all_question_ids": all_question_ids,
            "user_exam_options_list": user_exam_options_list,
        })

"""
获取顺序练习结果
1. user_exam_id 不能为空，否则报422错误
2. 若用户顺序练习记录不存在，报400错误
3. 若用户顺序练习记录存在，返回顺序练习结果，包含答对题数、总题数、正确率、错误题数、题目详情
"""
@router.post("/practiceResult", response_model=ResponseDTO)
def practiceResult(user_id: int = Body(..., embed=True), user_exam_id: int = Body(..., embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/practice/practiceResult, user_id={user_id}, user_exam_id={user_exam_id}")

    # 查询用户测试记录
    user_exam = MpUserExamService_instance.get_one_by_filters(
        db_session,
        filters=MpUserExamDTO(id=user_exam_id, user_id=user_id, type=0).model_dump(),
    )

    if user_exam is None:
        return ResponseUtil.error(code=400, message="用户顺序练习记录不存在")

    if user_exam.finish_time is None:
        return ResponseUtil.error(code=400, message="用户顺序练习未完成")

    # 查询考试信息
    mp_exam = MpExamService_instance.get_one_by_filters(
        db_session,
        filters=MpExamDTO(id=user_exam.exam_id).model_dump(),
    )

    if mp_exam is None:
        return ResponseUtil.error(code=400, message="考试记录不存在")

    # 计算正确率（百分比，保留2位小数）
    accuracy_rate = round((user_exam.correct_count / user_exam.total_count * 100), 2) if user_exam.total_count > 0 else 0.0

    logger.info(f"用户顺序练习完成，user_exam_id={user_exam_id}, 答对题数={user_exam.correct_count}, 总题数={user_exam.total_count}, 正确率={accuracy_rate}%")

    # 获取题目答题详情信息
    question_details = []
    question_ids = user_exam.question_ids if user_exam.question_ids else []

    for question_id in question_ids:
        # 查询题目信息
        question = MpQuestionService_instance.get_one_by_filters(
            db_session,
            filters=MpQuestionDTO(id=question_id).model_dump()
        )
        if question is None:
            logger.warning(f"question_id={question_id} 不存在，跳过")
            continue

        # 查询用户答案
        user_option_record = MpUserExamOptionService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamOptionDTO(user_exam_id=user_exam_id, question_id=question_id).model_dump()
        )
        user_answer = user_option_record.option_ids if user_option_record else None
        # 统一处理用户答案格式（转为列表）
        if user_answer is not None:
            user_answer_ids = user_answer if isinstance(user_answer, list) else [user_answer]
        else:
            user_answer_ids = []

        # 查询正确答案
        right_options = MpOptionService_instance.get_list_by_filters(
            db_session,
            filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump(),
        )
        correct_answer_ids = [opt.id for opt in right_options]

        # 判断是否答对（集合比较）
        is_correct = (set(correct_answer_ids) == set(user_answer_ids))

        # 构建题目详情
        question_details.append({
            "question_id": question.id,
            "question_type": question.type,
            "question_type_name": question.type_name,
            "question_name": question.name,
            "user_answer": user_answer_ids,
            "correct_answer": correct_answer_ids,
            "is_correct": 1 if is_correct else 0,
        })

    return ResponseUtil.success(code=200, message="success", data={
        "user_exam_id": user_exam.id,
        "exam_id": user_exam.exam_id,
        "exam_name": mp_exam.name,
        "user_id": user_exam.user_id,
        "correct_count": user_exam.correct_count,
        "total_count": user_exam.total_count,
        "accuracy_rate": accuracy_rate,
        "error_count": user_exam.total_count - user_exam.correct_count,
        "question_detail_list": question_details,
    })