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
def history(user_id: int = Body(None, embed=True), exam_id: int = Body(None, embed=True), db_session: Session = Depends(get_db_session)):
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
1. 检查用户是否有未完成的顺序练习记录
2. 如果有，返回当前题目进度（根据page_no）
3. 如果没有，创建新的顺序练习记录，返回第一题的题目进度
4. exam_id 和 user_id 不能为空，否则报422错误
"""
@router.post("/start", response_model=ResponseDTO)
def start(exam_id: int = Body(..., embed=True), user_id: int = Body(..., embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/practice/start, user_id={user_id}, exam_id={exam_id}")

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
                type=0,                     # 顺序练习
                page_no=1,                  # 设置初始题目进度为第一题
                correct_count=0,
                total_count=total_count,
                question_ids=question_ids,  # 保存所有题目ID快照
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
根据题目进度获取题目信息（包含选项），以及该题目是否已被答题。
- 若page_no参数为空时，则从用户测试记录中获取题目进度
- 若要获取下一题，则调用时page_no+1
- 若要获取上一题，则调用时page_no-1
"""
@router.post("/getQuestion", response_model=ResponseDTO)
def getQuestion(user_exam_id: int = Body(..., embed=True),page_no: int = Body(None, embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/practice/getQuestion, user_exam_id={user_exam_id}, page_no={page_no}")

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

        # 若page_no参数为空时，则默认获取当前题目进度
        if page_no is None:
            page_no = user_exam.page_no

        # 检查题目进度是否有效
        if page_no is None or page_no < 1 or page_no > user_exam.total_count:
            return ResponseUtil.error(code=400, message="题目进度无效或超出范围")

        # 根据题目进度查询对应的题目ID
        current_question_id = user_exam.question_ids[page_no - 1]

        # 查询题目 + 选项
        question_option_dto: MpQuestionOptionDTO = MpQuestionService_instance.get_one_questions_with_options(db_session, current_question_id)
        if question_option_dto is None:
            return ResponseUtil.error(code=400, message="题目不存在")

        # 根据题目ID查询当前题目是否已被答题
        user_exam_option:MpUserExamOptionModel = MpUserExamOptionService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamOptionDTO(user_exam_id=user_exam.id, question_id=current_question_id).model_dump(),
        )

        # 创建正确答案选项ID集合和列表
        right_options_set = set()
        right_option_ids = []
        # 遍历选项，将正确选项ID添加到集合和列表
        for item in question_option_dto.options:
            if item.is_right == 1:
                right_options_set.add(item.id)
                right_option_ids.append(item.id)

        # 用户是否答题正确
        is_correct = None   
        # 用户是否答题，返回答题信息。
        if user_exam_option is None:
            user_options = None
        else:
            # 用户答题选项（单选是int,多选是列表）
            user_options = user_exam_option.option_ids
            # 创建用户选项集合
            user_options_set = set(user_options if isinstance(user_options, list) else [user_options])
            # 判断集合形式的用户答案是否与正确答案完全匹配
            is_correct = (user_options_set == right_options_set)


        # 返回结果
        return ResponseUtil.success(code=200, message="success", data={
            "user_exam_id": user_exam.id,
            "page_no": page_no,
            "total_count": user_exam.total_count,
            "question": question_option_dto.question.model_dump(),
            "options": [opt.model_dump() for opt in question_option_dto.options],
            "user_options": user_options,  # 用户选择的选项ID列表（单选是int，多选是列表）
            "correct_option_ids": right_option_ids,  # 正确答案选项ID列表
            "is_correct": is_correct,
        })

"""
提交单题答案
"""
@router.post("/submitAnswer", response_model=ResponseDTO)
def submitAnswer(
    user_exam_id: int = Body(..., embed=True),
    question_id: int = Body(..., embed=True),
    option_ids: List[int] | int = Body(..., embed=True),  # 单选是int，多选是List[int]
    db_session: Session = Depends(get_db_session)
):
    logger.info(f"/mp/exam/practice/submitAnswer, user_exam_id={user_exam_id}, question_id={question_id}, option_ids={option_ids}")

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

        # 保存用户选项记录
        user_option_dto = MpUserExamOptionDTO(
            user_id=user_exam.user_id,
            exam_id=user_exam.exam_id,
            user_exam_id=user_exam.id,
            question_id=question_id,
            option_ids=option_ids,
            create_time=datetime.now(),
        )
        MpUserExamOptionService_instance.add(db_session, dict_data=user_option_dto.model_dump())


        # 处理用户选择的选项ID列表
        user_answer_ids = option_ids if isinstance(option_ids, list) else [option_ids] if option_ids else []
        # 查询问题ID对应的正确选项
        right_options = MpOptionService_instance.get_list_by_filters(
            db_session,
            filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump(),
        )
        right_option_ids = [opt.id for opt in right_options]

        # 判断用户选项是否与正确选项完全匹配
        is_correct = (set(right_option_ids) == set(user_answer_ids))

        # 更新答对题数
        if is_correct:
            user_exam.correct_count += 1

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
            "is_correct": 1 if is_correct else 0,
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


        question_ids = user_exam.question_ids or []
        # 拉取所有已答题记录
        user_exam_options = MpUserExamOptionService_instance.get_list_by_filters(
            db_session,
            filters=MpUserExamOptionDTO(user_exam_id=user_exam_id).model_dump()
        )
        option_map = {opt.question_id: opt for opt in user_exam_options}

        answer_card = []
        for idx, question_id in enumerate(question_ids, start=1):
            user_option_record = option_map.get(question_id)
            if user_option_record is None:
                answer_card.append({
                    "page_no": idx,
                    "question_id": question_id,
                    "user_options": None,
                    "is_correct": None
                })
                continue

            user_answer = user_option_record.option_ids
            user_answer_ids = user_answer if isinstance(user_answer, list) else [user_answer]

            right_options = MpOptionService_instance.get_list_by_filters(
                db_session,
                filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump(),
            )
            right_ids = [opt.id for opt in right_options]
            is_correct = 1 if set(user_answer_ids) == set(right_ids) else 0

            answer_card.append({
                "page_no": idx,
                "question_id": question_id,
                "user_options": user_answer_ids,
                "is_correct": is_correct
            })

        return ResponseUtil.success(code=200, message="success", data={
            "answer_card": answer_card,
            "total_count": user_exam.total_count,
            "finished": user_exam.finish_time is not None
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