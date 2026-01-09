from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO, MpQuestionDTO
from module_exam.dto.mp_user_exam_dto import MpUserExamDTO
from module_exam.dto.mp_user_option_dto import MpUserOptionDTO
from module_exam.model.mp_exam_model import MpExamModel
from module_exam.model.mp_user_exam_model import MpUserExamModel
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_option_service import MpUserOptionService
from utils.response_util import ResponseUtil,ResponseDTO

# 创建路由实例
router = APIRouter(prefix='/mp/exam/kaoshi', tags=['mp_exam_kaoshi接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserOptionService_instance = MpUserOptionService()

"""
模拟考试相关接口
"""

"""
获取该用户对应的模拟考试历史记录
"""
@router.post("/history", response_model=ResponseDTO[dict])
def history(user_id: int = Body(None, embed=True), exam_id: int = Body(None, embed=True), db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/exam/kaoshi/history, user_id={user_id}, exam_id={exam_id}")

    # 查询用户模拟考试历史记录,id降序
    user_exam_history: List[MpUserExamModel] = MpUserExamService_instance.get_list_by_filters(db_session, filters=MpUserExamDTO(
        user_id=user_id,
        exam_id=exam_id,
        type=1,
    ).model_dump(),sort_by=["-id"])

    # 根据exam_id查询模拟考试信息
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
"""
@router.post("/start",response_model=ResponseDTO[dict])
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
            # 新建一轮模拟考试，从第一题开始
            logger.info("未找到未完成模拟考试，创建新的模拟考试记录")
            # 构建参数
            user_exam_dto = MpUserExamDTO(
                user_id=user_id,
                exam_id=exam_id,
                type=1,
                score=0,
                create_time=datetime.now(),
            )
            # 插入新的用户测试记录
            new_userexam: MpUserExamModel = MpUserExamService_instance.add(db_session, dict_data=user_exam_dto.model_dump())

            # 从题库中获取对应题目和选项
            question_option_list: List[MpQuestionOptionDTO] = MpQuestionService_instance.get_questions_with_options(db_session, exam_id)

            # 返回结果
            return ResponseUtil.success(code=200, message="success", data={
                "user_id": new_userexam.user_id,
                "user_exam_id": new_userexam.id,
                "exam_id": new_userexam.exam_id,
                "page_no": new_userexam.page_no,
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
                "page_no": user_exam.page_no,
                "questions": question_option_list,
            })


"""
提交模拟考试答案(模拟考试只有题目全部做完，才能交卷)
1. 模拟考试答题数据是一起提交的。
2. 答题数据是一个Map，key是题目id，value是用户选择的选项id。
3. 若是单选题，value是用户选择的选项id。若是多选题，value是用户选择的选项id列表。
4. user_exam_id 和 answer_map 不能为空，否则报422错误

{question_id: option_id, question_id: [option_id1, option_id2]}
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

        # 遍历answerMap,将用户选项保存到用户选项表中
        for question_id, option_id in answer_map.items():
            # 构建参数
            user_option_dto = MpUserOptionDTO(
                user_id=user_exam.user_id,
                exam_id=user_exam.exam_id,
                user_exam_id=user_exam.id,
                question_id=question_id,
                option_id=str(option_id),
            )
            # 插入新的用户选项记录
            MpUserOptionService_instance.add(db_session, dict_data=user_option_dto.model_dump())

        # 更新用户测试记录的状态为已完成
        user_exam.finish_time = datetime.now()
        db_session.add(user_exam)

        return ResponseUtil.success(code=200, message="success")




