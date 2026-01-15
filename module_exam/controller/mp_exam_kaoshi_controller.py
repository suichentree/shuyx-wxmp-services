import json
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
from module_exam.model.mp_question_model import MpQuestionModel
from module_exam.model.mp_user_exam_model import MpUserExamModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_exam_option_service import MpUserExamOptionService
from utils.response_util import ResponseUtil,ResponseDTO

# 创建路由实例
router = APIRouter(prefix='/mp/exam/kaoshi', tags=['mp_exam_kaoshi接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserExamOptionService_instance = MpUserExamOptionService()

"""
模拟考试相关接口
"""

"""
获取该用户对应的模拟考试历史记录
"""
@router.post("/history", response_model=ResponseDTO)
def history(user_id: int = Body(None, embed=True), exam_id: int = Body(None, embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/kaoshi/history, user_id={user_id}, exam_id={exam_id}")

    # 查询用户模拟考试历史记录,id降序
    user_exam_history: List[MpUserExamModel] = MpUserExamService_instance.get_list_by_filters(db_session, filters=MpUserExamDTO(
        user_id=user_id,
        exam_id=exam_id,
        type=1,
    ).model_dump(),sort_by=["-id"])

    # 根据exam_id 获取考试信息
    exam_result: MpExamModel = MpExamService_instance.get_one_by_filters(db_session, filters=MpExamDTO(id=exam_id).model_dump())

    # 返回结果
    return ResponseUtil.success(code=200, message="success", data={
        "exam_info": exam_result.to_dict(),  # to_dict() 方法将模型转换为字典
        "user_exam_history": [exam.to_dict() for exam in user_exam_history],  # to_dict() 方法将模型转换为字典
    })

"""
开始/继续模拟考试 
1. 检查用户是否有未完成的模拟考试记录
2. 如果有，返回未完成的模拟考试记录，并返回模拟考试题目列表
3. 如果没有，创建新的模拟考试记录，并返回模拟考试题目列表
4. exam_id 和 user_id 不能为空，否则报422错误

模拟考试抽取规则概述：若某一道题最近答对了，则下次模拟考试不抽取该题目。即在模拟考试中，只抽取用户最近未做或最近做错的题目。若最终抽取的题目少于100道题，则从最近做对的题目中补充。

模拟考试抽取规则:
1. 若题库总数小于100,则直接返回所有题目。
2. 若题库总数大于等于100,则从总题库中按照规则抽取100道题。
    1. 先获取该用户上一轮模拟考试中，最近做对的题目ID列表。
    2. 从题库中获取所有题目ID列表。
    3. 从所有题目ID列表中，排除最近做对的题目ID列表。
    4. 若题库中剩余题目数大于等于100,则随机抽取100道题。
    5. 若题库中剩余题目数小于100,则从最近做对的题目中补充。

"""
@router.post("/start",response_model=ResponseDTO)
def start(exam_id: int = Body(..., embed=True),user_id: int = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/kaoshi/start, user_id={user_id}, exam_id={exam_id}")

    # 使用 with 语句开启事务上下文，自动提交或回滚
    with db_session.begin():

        # 查找最近一次未完成的测试记录（type=1）
        user_exam = MpUserExamService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamDTO(user_id=user_id, exam_id=exam_id, type=1, finish_time=False).model_dump(),
            sort_by=["-id"],
        )

        # 如果没有未完成的模拟考试记录，创建新的模拟考试记录
        if user_exam is None:
            logger.info("未找到未完成模拟考试，新建一轮模拟考试")

            # 从题库中获取对应题目和选项
            question_option_list: List[MpQuestionOptionDTO] = MpQuestionService_instance.get_questions_with_options(db_session, exam_id)
            # 题目id列表
            question_ids = [q.question.id for q in question_option_list]

            # 创建新的考试记录
            user_exam_dto = MpUserExamDTO(
                user_id=user_id,
                exam_id=exam_id,
                type=1,  # 模拟考试1
                last_question_id=question_ids[0],  # 最后做的问题ID，默认初始化为第一题目的id
                correct_count=0,  # 答对题目数
                total_count=len(question_option_list),  # 总题目数
                question_ids=question_ids,  # 保存所有题目ID快照
                create_time=datetime.now(),
                finish_time=None,
            )
            new_userexam: MpUserExamModel = MpUserExamService_instance.add(db_session, dict_data=user_exam_dto.model_dump())

            # 返回结果
            return ResponseUtil.success(code=200, message="success", data={
                "user_id": new_userexam.user_id,
                "user_exam_id": new_userexam.id,
                "exam_id": new_userexam.exam_id,
                "last_question_id": new_userexam.last_question_id,
                "correct_count": new_userexam.correct_count,
                "total_count": new_userexam.total_count,
                "question_ids": new_userexam.question_ids,
                "questions": question_option_list,
            })

        else:
            # 表示有未完成的模拟考试记录，则继续考试

            # 从题库中获取对应题目和选项
            question_option_list: List[MpQuestionOptionDTO] = MpQuestionService_instance.get_questions_with_options(db_session, exam_id)

            # 返回结果
            return ResponseUtil.success(code=200, message="success", data={
                "user_id": user_exam.user_id,
                "user_exam_id": user_exam.id,
                "exam_id": user_exam.exam_id,
                "last_question_id": user_exam.last_question_id,
                "correct_count": user_exam.correct_count,
                "total_count": user_exam.total_count,
                "question_ids": user_exam.question_ids,
                "questions": question_option_list,
            })


"""
提交模拟考试答案(模拟考试只有题目全部做完，才能交卷)
1. 模拟考试的答题数据是一起提交的。
2. 答题数据是一个Map，key是题目id，value是用户选择的选项id列表。无论单选多选，选项id都要封装在列表中。
3. user_exam_id 和 answer_map 不能为空并且类型要正确，否则报422错误

{question_id: [option_id], question_id: [option_id1, option_id2]}
"""
@router.post("/submitAnswerMap",response_model=ResponseDTO)
def submitAnswerMap(user_exam_id: int = Body(..., embed=True),answer_map: dict = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/kaoshi/submitAnswerMap, user_exam_id={user_exam_id}, answer_map={answer_map}")

    # 使用 with 语句开启事务上下文，自动提交或回滚
    with db_session.begin():

        # 根据user_exam_id 查询用户测试记录
        user_exam = MpUserExamService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamDTO(id=user_exam_id).model_dump(),
        )

        # 检查用户是否有未完成的模拟考试记录
        if user_exam is None:
            return ResponseUtil.error(code=400, message="用户模拟考试记录不存在")

        # 初始化答对题目数为0
        correct_count = 0
        
        # 遍历answerMap,保存用户选项并计算答对题目数
        for qid_str, user_option_ids in answer_map.items():
            # Body 传 dict 时 key 可能是 str，这里统一转 int
            question_id = int(qid_str)
            
            # 判断类型
            if user_option_ids is None or len(user_option_ids) == 0 or not isinstance(user_option_ids, list):
                return ResponseUtil.error(code=422, message=f"题目id={question_id}的选项格式错误")

            # 根据question_id 查询题目信息
            question_info: MpQuestionModel = MpQuestionService_instance.get_one_by_filters(
                db_session,
                filters=MpQuestionDTO(id=question_id, status=0).model_dump(),
            )
            if question_info is None:
                return ResponseUtil.error(code=400, message=f"题目id={question_id}不存在")

            # 根据question_id 查询题目对应的正确选项
            right_options = MpOptionService_instance.get_list_by_filters(
                db_session,
                filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump(),
            )
            # 题目对应的正确选项id列表
            right_option_ids = [opt.id for opt in right_options]

            # 判断本题是否答对（set集合比较，全对得1分，否则0分）
            is_correct = (set(right_option_ids) == set(user_option_ids))
            if is_correct:
                correct_count += 1
            
            # 保存用户选项记录
            user_option_dto = MpUserExamOptionDTO(
                user_id=user_exam.user_id,
                exam_id=user_exam.exam_id,
                user_exam_id=user_exam.id,
                question_id=question_id,
                question_type=question_info.type,       # 题目类型（1：单选题，2：多选题）
                is_correct=1 if is_correct else 0,      # 1表示答对，0表示答错
                option_ids=user_option_ids,
            )
            MpUserExamOptionService_instance.add(db_session, dict_data=user_option_dto.model_dump())
        
        # 更新用户测试记录
        user_exam.correct_count = correct_count
        user_exam.finish_time = datetime.now()
        MpOptionService_instance.update_by_id(db_session, id=user_exam.id, update_data=user_exam.to_dict())

        return ResponseUtil.success(code=200, message="success")


"""
获取模拟考试结果
1. user_exam_id 不能为空，否则报422错误
2. 若用户模拟考试记录不存在，报400错误
3. 若用户模拟考试记录存在，返回用户模拟考试结果，包含答对题数、总题数、正确率、错误题数。
"""
@router.post("/kaoshiResult",response_model=ResponseDTO)
def kaoshiResult(user_id: int = Body(..., embed=True),user_exam_id: int = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/kaoshi/result,user_id={user_id}, user_exam_id={user_exam_id}")

    # 根据user_exam_id 查询用户测试记录
    user_exam = MpUserExamService_instance.get_one_by_filters(
        db_session,
        filters=MpUserExamDTO(id=user_exam_id,user_id=user_id).model_dump(),
    )

    # 查询模拟考试信息
    mp_exam = MpExamService_instance.get_one_by_filters(
        db_session,
        filters=MpExamDTO(id=user_exam.exam_id).model_dump(),
    )

    if user_exam is None:
        return ResponseUtil.error(code=500, message="用户模拟考试记录不存在")

    if user_exam.finish_time is None:
        return ResponseUtil.error(code=500, message="用户模拟考试未完成")

    if mp_exam is None:
        return ResponseUtil.error(code=500, message="模拟考试记录不存在")

    # 计算正确率（百分比，保留2位小数）
    accuracy_rate = round((user_exam.correct_count / user_exam.total_count * 100), 2) if user_exam.total_count > 0 else 0.0

    logger.info(f"用户模拟考试提交完成，user_exam_id={user_exam_id}, 答对题数={user_exam.correct_count}, 总题数={user_exam.total_count}, 正确率={accuracy_rate}%")

    # 获取题目答题详情信息
    question_details = []
    question_ids = user_exam.question_ids if user_exam.question_ids else []
    for question_id in question_ids:
        # 查询题目信息
        question: MpQuestionModel = MpQuestionService_instance.get_one_by_filters(
            db_session,
            filters=MpQuestionDTO(id=question_id).model_dump()
        )
        if question is None:
            logger.warning(f"question_id={question_id} 不存在，跳过")
            continue
        
        # 查询用户答案
        user_exam_option = MpUserExamOptionService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamOptionDTO(user_exam_id=user_exam_id, question_id=question_id).model_dump()
        )
        user_answer_ids = user_exam_option.option_ids if user_exam_option else None

        # 查询正确答案
        right_options = MpOptionService_instance.get_list_by_filters(
            db_session,
            filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump(),
        )
        correct_answer_ids = [opt.id for opt in right_options]
        
        # 构建题目详情
        question_details.append({
            "question_id": question.id,
            "question_type": question.type,
            "question_type_name": question.type_name,
            "question_name": question.name,
            "user_answer": user_answer_ids,
            "correct_answer": correct_answer_ids,
            "is_correct": user_exam_option.is_correct,
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