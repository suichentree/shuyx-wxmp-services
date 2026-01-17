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
from module_exam.dto.mp_user_question_ebbinghaus_track_dto import MpUserQuestionEbbinghausTrackDTO
from module_exam.model.mp_exam_model import MpExamModel
from module_exam.model.mp_user_exam_model import MpUserExamModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_exam_option_service import MpUserExamOptionService
from module_exam.service.mp_user_question_ebbinghaus_track_service import MpUserQuestionEbbinghausTrackService
from utils.response_util import ResponseUtil,ResponseDTO

# 创建路由实例
router = APIRouter(prefix='/mp/exam/kaoshi', tags=['mp_exam_kaoshi接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserExamOptionService_instance = MpUserExamOptionService()
MpUserQuestionEbbinghausTrackService_instance = MpUserQuestionEbbinghausTrackService()

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

模拟考试抽题概述：每一次模拟考试时，都会按照抽题规则抽取100道题。若题库总题目数不足100道，则会根据题库总题目数抽取题目。

抽题规则是参考艾宾浩斯记忆曲线的原理，艾宾浩斯记忆曲线的原理 ====================
即：用户在模拟考试中答对/答错某一道题目。若该题目之前没在轨迹表中，则会将该问题答题情况记录到用户问题-艾宾浩斯轨迹表。
若该题目之前在轨迹表中，则会根据用户的答题情况更新轨迹表中的数据。
 
用户问题-艾宾浩斯轨迹表有几个核心字段：
status: int = 0  # 题目答题状态，待复习0，已巩固1
last_answer_time: date = None  # 最后答题时间
next_review_day: int = 0  # 下一次复习的时间，单位天
cycle_index: int = 0  # 复习周期索引，从0开始

举例1： 一直答对的复习周期为 [0,1,3,7,14,30]
1. 假设用户在某一天模拟考试中答对一道题，那么这道题会在0天后的模拟考试中抽取出来。
1. 若用户再次答对这道题，那么这道题会在1天后的模拟考试中抽取出来。
2. 若用户再次答对这道题，那么这道题会在3天后的模拟考试中抽取出来。
3. 若再次答对这道题，那么这道题会在7天后的模拟考试中抽取出来。
.....
4. 若用户在复习周期为30的时候，再次答对这道题，那么这道题会被标记为已巩固。则这道题目的抽题权重会降低。

举例2： 一直答错的复习周期为 [0]  即某一道题目答错，该题目的复习周期会重置为0。
1. 假设用户在某一天模拟考试中答错一道题，那么这道题会在0天后的模拟考试中抽取出来。
2. 若用户再次答错这道题，那么这道题会在0天后的模拟考试中抽取出来。
3. 若再次答错这道题，那么这道题会在0天后的模拟考试中抽取出来。
.....

举例3： 交替答对答错的复习周期为 [0,1,3,7,14,30] 和 [0] 交互的情况
1. 假设用户在某一天模拟考试中答对一道题，那么这道题会在0天后的模拟考试中抽取出来。
2. 若用户再次答错这道题，那么这道题会在0天后的模拟考试中抽取出来。
3. 若用户再次答对这道题，那么这道题会在1天后的模拟考试中抽取出来。
4. 若用户再次答对这道题，那么这道题会在3天后的模拟考试中抽取出来。
5. 若用户再次答错这道题，那么这道题会在0天后的模拟考试中抽取出来。
....

注意事项: 
根据艾宾浩斯记忆曲线，用户在一直答对某道题目的情况下，下一次模拟考试中这道题的复习周期会增加。
一旦用户答错了某道题，那么这道题的复习周期就会重置为0。

按照优先级从高到低抽题。不足则从下一级补充，直到满足指定数量的题目。
1. 当天复习题。 即下次复习时间为当天的待复习题目。
2. 已过期待复习题。 即下次复习时间小于当天的待复习题目
3. 未答题过的题目。 即没有在轨迹表中记录的题目
4. 未到期待复习题。 即下次复习时间大于当天的待复习题目
5. 已巩固题目（status=1,cycle_idx=-1）。 即已巩固的题目

"""
@router.post("/start",response_model=ResponseDTO)
def start(exam_id: int = Body(..., embed=True),user_id: int = Body(..., embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/kaoshi/start, user_id={user_id}, exam_id={exam_id}")

    # 使用 with 语句开启事务上下文，自动提交或回滚
    with db_session.begin():
        # 查找最近一次未完成的顺序练习记录（type=1）
        user_exam = MpUserExamService_instance.get_one_by_filters(
            db_session,
            filters=MpUserExamDTO(user_id=user_id, exam_id=exam_id, type=1, finish_time=False).model_dump(),
            sort_by=["-id"],
        )

        # 如果没有未完成的模拟考试记录，创建新的模拟考试记录
        if user_exam is None:
            logger.info("未找到未完成模拟考试，新建一轮模拟考试")
            # 设定模拟考试的抽题总数为100道题
            kaoshi_question_total_count = 100
            # 获取该测试题库的总题目数
            question_total_question_count = MpQuestionService_instance.get_total_by_filters(db_session, filters=MpQuestionDTO(exam_id=exam_id).model_dump())
            # 如果模拟考试的抽题总数大于测试题库的总题目数，则将模拟考试的抽题总数设为测试题库的总题目数。即最多只能抽测试题库的总题目数。
            if kaoshi_question_total_count > question_total_question_count:
                kaoshi_question_total_count = question_total_question_count

            # 根据用户艾宾浩斯轨迹表，开始抽题，返回抽取出的题目id列表
            question_ids:List[int] = MpUserQuestionEbbinghausTrackService_instance.monikaoshi_choose_question_ids(db_session, user_id, exam_id,kaoshi_question_total_count)

            # 新增用户测试数据
            user_exam_dto = MpUserExamDTO(
                user_id=user_id,
                exam_id=exam_id,
                type=1,  # 模拟考试
                type_name="模拟考试",
                correct_count=0,  # 答对题目数为0
                total_count=kaoshi_question_total_count,
                question_ids=question_ids,
                create_time=datetime.now(),
            )
            # 插入新的用户测试记录
            new_userexam: MpUserExamModel = MpUserExamService_instance.add(db_session, dict_data=user_exam_dto.model_dump())

            # 返回结果
            return ResponseUtil.success(code=200, message="success", data={
                "user_id": new_userexam.user_id,
                "user_exam_id": new_userexam.id,
                "exam_id": new_userexam.exam_id,
            })

        else:
            # 表示有未完成的模拟考试记录，则继续考试
            logger.info(f"有未完成的模拟考试记录，继续考试，user_id={user_exam.user_id}, exam_id={user_exam.exam_id}")

            # 返回结果
            return ResponseUtil.success(code=200, message="success", data={
                "user_id": user_exam.user_id,
                "user_exam_id": user_exam.id,
                "exam_id": user_exam.exam_id,
            })

"""
根据题目ID获取题目信息（包含选项），以及该题目的答题信息。
- 模拟考试中获取题目是一次性获取所有题目，而不是每次获取一个题目。
"""
@router.post("/getQuestion", response_model=ResponseDTO)
def getQuestion(user_exam_id: int = Body(..., embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/kaoshi/getQuestion, user_exam_id={user_exam_id}")

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

        # 获取用户考试记录中的所有题目ID列表
        question_ids:List[int] = user_exam.question_ids

        # 查询题目 + 选项
        question_option_dto: List[MpQuestionOptionDTO] = MpQuestionService_instance.get_questions_with_options_by_questionids(db_session, question_ids=question_ids)
        if question_option_dto is None or len(question_option_dto) == 0:
            return ResponseUtil.error(code=400, message="题目数据不存在")

        # 返回结果
        return ResponseUtil.success(code=200, message="success", data={
            "user_exam_id": user_exam.id,
            "questions": [item.model_dump() for item in question_option_dto],
        })

"""
提交模拟考试答案(模拟考试只有题目全部做完，才能交卷)
1. 模拟考试答题数据是一起提交的。
2. 答题数据是一个Map，key是题目id，value是用户选择的选项id列表。单选多选都是题目id列表。
4. user_exam_id 和 answer_map 不能为空，否则报422错误

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

            # 根据question_id 查询题目信息
            question_one = MpQuestionService_instance.get_one_by_filters(db_session,filters=MpQuestionDTO(id=question_id).model_dump())
            # 检查题目是否存在
            if question_one is None:
                return ResponseUtil.error(code=400, message=f"题目不存在,question_id={question_id}")

            # 处理用户选项答案，若是单选，转换为列表格式。
            if isinstance(user_option_ids, list):
                user_answer_ids = user_option_ids
            else:
                return ResponseUtil.error(code=422, message=f"选项格式错误,user_option_ids={user_option_ids}")

            # 根据question_id 查询题目对应的正确选项
            right_options = MpOptionService_instance.get_list_by_filters(
                db_session,
                filters=MpOptionDTO(question_id=question_id, is_right=1, status=0).model_dump(),
            )
            # 题目对应的正确选项id列表
            right_option_ids = [opt.id for opt in right_options]
            # 判断本题是否答对（set集合比较）
            is_option_correct = (set(right_option_ids) == set(user_answer_ids))
            # 若答对则增加答对题目数
            if is_option_correct:
                correct_count += 1
            
            # 保存用户选项记录
            user_option_dto = MpUserExamOptionDTO(
                user_id=user_exam.user_id,
                exam_id=user_exam.exam_id,
                user_exam_id=user_exam.id,
                question_id=question_id,
                question_type=question_one.type,
                option_ids=user_option_ids,
                is_correct=1 if is_option_correct else 0,   #答对1,答错0
            )
            MpUserExamOptionService_instance.add(db_session, dict_data=user_option_dto.model_dump())


            # 更新该问题的答题轨迹记录




            # 先查询用户是否已存在该题目答题轨迹记录
            track_one = MpUserQuestionEbbinghausTrackService_instance.get_one_by_filters(
                db_session,
                filters=MpUserQuestionEbbinghausTrackDTO(
                    user_id=user_exam.user_id,
                    question_id=question_id,
                ).model_dump(),
            )

            # 若不存在，则创建新记录
            if track_one is None:
                track_one = MpUserQuestionEbbinghausTrackDTO(
                    user_id=user_exam.user_id,
                    question_id=question_id,
                    exam_id=user_exam.exam_id,
                    user_exam_id=user_exam.id,
                    is_correct=is_option_correct,
                )
                MpUserQuestionEbbinghausTrackService_instance.add(db_session, dict_data=track_one.model_dump())



        # 更新用户测试记录
        user_exam.correct_count = correct_count
        user_exam.page_no = user_exam.total_count
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

