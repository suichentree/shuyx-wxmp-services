from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO, MpExamCommonDTO
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO, MpQuestionDTO
from module_exam.dto.mp_user_exam_dto import MpUserExamDTO
from module_exam.dto.mp_user_option_dto import MpUserOptionDTO
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_option_service import MpUserOptionService
from utils.response_util import ResponseUtil, model_to_dto

# 创建路由实例
router = APIRouter(prefix='/mp/exam', tags=['mp_exam接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserOptionService_instance = MpUserOptionService()

"""
获取测试列表信息
"""
@router.get("/getExamList")
def getExamList(page_num:int=1, page_size:int=10,db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getExamList, page_num = {page_num}, page_size = {page_size}')

    # 构建dto对象，分页查询，状态正常的考试信息
    mp_exam_dto = MpExamDTO(status=0)
    result = MpExamService_instance.get_page_list_by_filters(db_session, page_num=page_num, page_size=page_size, filters=mp_exam_dto.model_dump())
    # 将查询结果转换为指定dto类型
    dto_result = model_to_dto(data=result, dto_cls=MpExamDTO)
    # 返回结果
    return ResponseUtil.success(code=200, message="success", data=dto_result)


"""
获取测试题目列表信息
"""
@router.post("/getQuestionList")
def getQuestionList(exam_id:int = Body(None,embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getQuestionList, exam_id = {exam_id}')
    # 调用自定义方法获取问题和选项数据
    result = MpQuestionService_instance.get_questions_with_options(db_session, exam_id)
    # 将查询结果转换为指定dto类型
    dto_result = model_to_dto(data=result, dto_cls=MpQuestionOptionDTO)
    # 返回结果
    return ResponseUtil.success(code=200, message="success", data=dto_result)


"""
获取测试进度信息
"""
@router.post("/getExamProgress")
def getExamProgress(user_id:int = Body(None),exam_id:int = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getExamProgress, user_id = {user_id}, exam_id = {exam_id}')
    # 调用服务层方法，查询考试进度信息
    mp_user_exam_dto = MpUserExamDTO(user_id=user_id, exam_id=exam_id)  #构建dto
    result = MpUserExamService_instance.get_one_by_filter(db_session,filters=mp_user_exam_dto.model_dump())
    # 将查询结果转换为指定dto类型
    dto_result = model_to_dto(data=result, dto_cls=MpUserExamDTO)
    # 返回结果
    return ResponseUtil.success(code=200, message="success", data=dto_result)


"""
单选题答题
"""
@router.post("/danxue_Answer")
def danxueAnswer(user_id:int = Body(None),exam_id:int = Body(None),question_id:int = Body(None),option_id:int = Body(None),page_no:int = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/danxue_Answer, user_id = {user_id}, exam_id = {exam_id}, question_id = {question_id}, option_id = {option_id}, page_no = {page_no}')

    # 查询选项信息
    option_result = MpOptionService_instance.get_by_id(id=option_id)
    if option_result is None:
        return ResponseUtil.error(code=400, message="该选项不存在")

    # 根据exam_id查询某个测试的题目个数
    mp_question_dict = MpQuestionDTO(exam_id=exam_id).model_dump()
    question_count:int = MpQuestionService_instance.get_total_by_filters(db_session,filters=mp_question_dict)

    # 查询用户是否有没做完的测试记录
    user_exam_result = MpUserExamService_instance.find_last_one_not_finished_user_exam(db_session,user_id=user_id, exam_id=exam_id)
    if user_exam_result is None:
        logger.info(f'用户 user_id = {user_id}, exam_id = {exam_id}, 无未做完测试，创建新的测试记录')
        # 创建新的测试记录
        MpUserExamService_instance.add(db_session,data=MpUserExamDTO(
            user_id=user_id,
            exam_id=exam_id,
            page_no=page_no,
            score=option_result.score,
            create_time=datetime.now(),
        ).model_dump())
    else:
        logger.info(f'用户 user_id = {user_id}, exam_id = {exam_id}, 有未做完测试，继续测试')
        # 若该选项是正确选项，则分数加1
        if option_result.is_right == 1:
           user_exam_result.score += 1

        # 更新当前页码
        user_exam_result.page_no = page_no
        # 若题号和题目数相等，则表示这是最后一题,还需要更新finish_time
        if page_no == question_count:
            user_exam_result.finish_time = datetime.now()
        # 更新测试记录
        MpUserExamService_instance.update_by_id(id=user_exam_result.id,update_data=user_exam_result)

    # 新增新的用户选项记录
    MpUserOptionService_instance.add(data=MpUserOptionDTO(
        user_id=user_id,
        exam_id=exam_id,
        is_duoxue=0,
        question_id=question_id,
        option_id=option_id,
        is_right=option_result.is_right,
    ).model_dump())

    return ResponseUtil.success()


"""
多选题答题
"""
@router.post("/duoxue_Answer")
def duoxue_Answer(user_id:int = Body(None),exam_id:int = Body(None),question_id:int = Body(None),optionIds:List[int] = Body(None),page_no:int = Body(None)):
    logger.info(f'/mp/exam/duoxue_Answer, user_id = {user_id}, exam_id = {exam_id}, question_id = {question_id}, option_ids = {optionIds}, page_no = {page_no}')

    # 使用 session_execute_query 方法 查询题目的正确选项集合
    rightList:List[MpOptionDTO] = MpOptionService_instance.session_execute_query(
        lambda db_session: db_session.query(MpOptionModel).filter(MpOptionModel.question_id == questionId, MpOptionModel.score == 1).all()
    )
    rightIds:List[int] = [item.id for item in rightList]

    # 将正确的选项集合与用户选项的数组进行对比
    isSame:bool
    if set(rightIds) == set(optionIds):
        isSame = True
    else:
        isSame = False

    logger.info(f'用户选择的选项 optionIds = {optionIds}, 多选题目的正确选项 = {rightIds}, 是否相同 = {isSame}')

    # 根据exam_id查询某个测试的题目个数
    question_count:int = MpQuestionService_instance.get_total_by_filters(filters=MpQuestionDTO(exam_id=examId))

    # 使用 session_execute_query 方法  查询用户是否有没做完的测试记录
    mp_user_exam_result: MpUserExamDTO = MpUserExamService_instance.session_execute_query(
        lambda db_session: db_session.query(MpUserExamModel).filter(
            MpUserExamModel.user_id == userId,
            MpUserExamModel.exam_id == int(examId),
            MpUserExamModel.finish_time == None,
        ).first()
    )

    if mp_user_exam_result is None:
        logger.info(f'用户 userId = {userId}, examId = {examId}, 无未做完测试，创建新的测试记录')
        # 创建新的测试记录
        MpUserExamService_instance.add(data=MpUserExamDTO(
            user_id=userId,
            exam_id=examId,
            page_no=pageNo,
            score=1 if isSame else 0,
            create_time=datetime.now(),
        ))
    else:
        logger.info(f'用户 userId = {userId}, examId = {examId}, 有未做完测试，继续测试')
        mp_user_exam_result.page_no = pageNo
        if isSame:
            mp_user_exam_result.score += mp_user_exam_result.score
        else:
            mp_user_exam_result.score = 0

        # 若题号和题目数相等，则表示这是最后一题,还需要更新finish_time
        if pageNo == question_count:
            mp_user_exam_result.finish_time = datetime.now()
        # 更新测试记录
        MpUserExamService_instance.update_by_id(id=mp_user_exam_result.id, update_data=mp_user_exam_result)

    # 创建新的用户选项信息
    for optionId in optionIds:
        new_user_option = MpUserOptionDTO(
            user_id=userId,
            exam_id=examId,
            is_duoxue=1,
            question_id=questionId,
            option_id=optionId,
            is_right=1 if rightIds.__contains__(optionId) else 0,
        )
        # 新增新的用户选项记录
        MpUserOptionService_instance.add(data=new_user_option)

    return ResponseUtil.success()










