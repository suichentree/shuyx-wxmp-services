from datetime import datetime
from typing import List

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from config.database_config import get_db_session

from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO, MpExamCommonDTO
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
from utils.response_util import ResponseUtil, model_to_dto, ResponseDTO
from utils.type_conversion_util import TypeConversionUtil

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
@router.get("/getExamList", response_model=ResponseDTO[List[MpExamCommonDTO]])
def getExamList(page_num:int=1, page_size:int=10,db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getExamList, page_num = {page_num}, page_size = {page_size}')

    # 分页查询，状态正常的考试信息
    dto_dict = MpExamDTO(status=0).model_dump()
    # 获取列表查询结果
    result:List[MpExamModel] = MpExamService_instance.get_page_list_by_filters(db_session, page_num=page_num, page_size=page_size, filters=dto_dict)
    # 响应结果
    return ResponseUtil.success(code=200, message="success", data=result)


"""
模拟考试交卷：一次性提交所有题目的答案，并计算分数
"""
@router.post("/submit")
def submit_exam(user_id: int = Body(...),exam_id: int = Body(...),user_exam_id: int = Body(...),
answer_map: dict[int, List[int]] = Body(...),db_session: Session = Depends(get_db_session)):
    logger.info(f"/mp/kaoshi/submit, user_id={user_id}, exam_id={exam_id}, user_exam_id={user_exam_id}, answer_map={answer_map}")

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
    )

    return ResponseUtil.success(
        data={
            "user_exam_id": user_exam_id,
            "right_num": total_score,
            "error_num": answered_count - total_score,
        }
    )







"""
获取测试进度信息
"""
@router.post("/getExamProgress")
def getExamProgress(user_id:int = Body(None),exam_id:int = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/getExamProgress, user_id = {user_id}, exam_id = {exam_id}')
    # 调用服务层方法，查询考试进度信息
    mp_user_exam_dto = MpUserExamDTO(user_id=user_id, exam_id=exam_id)  #构建dto
    result = MpUserExamService_instance.get_one_by_filters(db_session,filters=mp_user_exam_dto.model_dump())
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
    option_result = MpOptionService_instance.get_by_id(db_session,id=option_id)
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
        MpUserExamService_instance.add(db_session,dict_data=MpUserExamDTO(
            user_id=user_id,
            exam_id=exam_id,
            page_no=page_no,
            score=option_result.is_right,
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
    MpUserOptionService_instance.add(db_session=db_session,dict_data=MpUserOptionDTO(
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
def duoxue_Answer(user_id:int = Body(None),exam_id:int = Body(None),question_id:int = Body(None),optionIds:List[int] = Body(None),page_no:int = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/duoxue_Answer, user_id = {user_id}, exam_id = {exam_id}, question_id = {question_id}, option_ids = {optionIds}, page_no = {page_no}')

    # 查询题目的正确选项集合
    rightList = MpOptionService_instance.get_list_by_filters(db_session,filters=MpOptionDTO(question_id=question_id,is_right=1).model_dump())
    # 若查询结果为空，则表示该多选题无正确选项
    if not rightList:
        return ResponseUtil.error(code=400, message="该多选题无正确选项")
    # 获取正确选项的Id列表
    rightIds:List[int] = [item.id for item in rightList]

    # 将正确的选项集合与用户选项的数组进行对比
    isSame:bool
    if set(rightIds) == set(optionIds):
        isSame = True
    else:
        isSame = False
    logger.info(f'用户选择的选项 optionIds = {optionIds}, 多选题目的正确选项 = {rightIds}, 是否相同 = {isSame}')

    # 根据exam_id查询某个测试的题目个数
    question_count:int = MpQuestionService_instance.get_total_by_filters(db_session,filters=MpQuestionDTO(exam_id=exam_id).model_dump())

    # 查询用户是否有没做完的测试记录
    mp_user_exam_result = MpUserExamService_instance.find_last_one_not_finished_user_exam(db_session,user_id=user_id, exam_id=exam_id)

    if mp_user_exam_result is None:
        logger.info(f'用户 user_id = {user_id}, exam_id = {exam_id}, 无未做完测试，创建新的测试记录')
        # 创建新的测试记录
        MpUserExamService_instance.add(db_session=db_session,dict_data=MpUserExamDTO(
            user_id=user_id,
            exam_id=exam_id,
            page_no=page_no,
            score=1 if isSame else 0,
            create_time=datetime.now(),
        ).model_dump())
    else:
        logger.info(f'用户 user_id = {user_id}, exam_id = {exam_id}, 有未做完测试，继续测试')
        mp_user_exam_result.page_no = page_no
        if isSame:
            mp_user_exam_result.score += mp_user_exam_result.score
        else:
            mp_user_exam_result.score = 0

        # 若题号和题目数相等，则表示这是最后一题,还需要更新finish_time
        if page_no == question_count:
            mp_user_exam_result.finish_time = datetime.now()
        # 更新测试记录
        MpUserExamService_instance.update_by_id(id=mp_user_exam_result.id, update_data=mp_user_exam_result.model_dump())

    # 创建新的用户选项信息
    for optionId in optionIds:
        new_user_option = MpUserOptionDTO(
            user_id=user_id,
            exam_id=exam_id,
            is_duoxue=1,
            question_id=question_id,
            option_id=optionId,
            is_right=1 if rightIds.__contains__(optionId) else 0,
        )
        # 新增新的用户选项记录
        MpUserOptionService_instance.add(db_session=db_session,dict_data=new_user_option.model_dump())

    return ResponseUtil.success()




"""
计算并获取测试结果
"""
@router.post("/result")
def result(user_id:int = Body(None),exam_id:int = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/result, user_id = {user_id}, exam_id = {exam_id}')

    JsonArray = []

    # 查询用户最近一次完成的测试记录
    last_finish_user_exam = MpUserExamService_instance.find_last_one_finished_user_exam(db_session,user_id=user_id, exam_id=exam_id)

    if last_finish_user_exam is None:
        return ResponseUtil.success(data={"message": "用户未完成任何测试"})
    else:
        JsonArray.append({
            "user_exam_id": last_finish_user_exam.id,
            "right_num": last_finish_user_exam.score,
            "error_num": last_finish_user_exam.page_no - last_finish_user_exam.score,
        })

    JsonArray2 = []
    # 根据user_id和exam_id查询全部完成的测试记录
    all_finish_user_exams = MpUserExamService_instance.get_list_by_filters(db_session,filters=MpUserExamDTO(user_id=user_id,exam_id=exam_id,finish_time = True).model_dump())
    for user_exam in all_finish_user_exams:
        JsonArray2.append({
            "sum_num": user_exam.page_no,
            "right_num": user_exam.score,
            "error_num": user_exam.page_no - user_exam.score,
            "time_num": user_exam.finish_time
        })
    JsonArray.append(JsonArray2)

    return ResponseUtil.success(data=JsonArray)



"""
查询用户测试历史记录
"""
@router.post("/history")
def history(user_id:int = Body(None,embed=True),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/history, user_id = {user_id}')
    JsonArray = []

    # 查询该用户的全部测试历史记录
    examlist = MpExamService_instance.get_list_by_filters(db_session=db_session,filters=MpExamDTO(user_id=user_id).model_dump())
    # 遍历所有测试记录，将其转换为json格式
    for exam in examlist:
        # 根据exam_id 查询对应的测试信息
        exam_id = exam.id

        # 根据exam_id 和 user_id 查询用户最近的完成的测试基类
        last_user_exam = MpUserExamService_instance.find_last_one_finished_user_exam(db_session,user_id=user_id, exam_id=exam_id)

        # 若用户有做过该测试，则取最近一次的测试记录
        if last_user_exam is not None:
            exam_info = MpExamService_instance.get_by_id(db_session,id=last_user_exam.exam_id)
            # 将历史测试记录转换为json格式，并添加到JsonArray中
            JsonArray.append({
                "examId": exam_info.id,
                "examName": exam_info.name,
                "finishTime": last_user_exam.finish_time,
            })

    return ResponseUtil.success(data=JsonArray)



"""
进行问题分析
"""
@router.post("/questionAnalyse")
def questionAnalyse(user_id:int = Body(None),examId = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/questionAnalyse, user_id = {user_id}, exam_id = {examId}')
    JsonArray = []

    # 获取最近一次完成的测试记录
    last_finish_user_exam:MpUserExamDTO = MpUserExamService_instance.find_last_one_finished_user_exam(db_session,user_id=user_id, exam_id=examId)
    if last_finish_user_exam is None:
        return ResponseUtil.error(data={"message": "用户未完成任何测试"})
    else:
        last_finish_user_exam_id = last_finish_user_exam.id

    # 查询最近一次测试的问题列表
    last_question_list  = MpQuestionService_instance.get_list_by_filters(db_session,filters=MpQuestionDTO(
        exam_id=examId,
    ).model_dump())
    # 遍历所有问题，将其转换为json格式
    for question in last_question_list:
        json = {}
        json['questionId'] = question.id
        qtype = question.type

        # 查询某个测试的某个问题的选项数据
        uOption = MpUserOptionService_instance.get_list_by_filters(db_session,filters=MpUserOptionDTO(
            user_exam_id=last_finish_user_exam_id,
            question_id=question.id,
        ).model_dump())

        if qtype == "单选题":
            # 单选题
            if uOption[0].is_right == 1:
                json['isAnswerCorrect'] = 1
            else:
                json['isAnswerCorrect'] = 0

        elif qtype == "多选题":
            # 多选题
            # 查询用户选择的选项集合
            choiceIds = []
            for u in uOption:
                choiceIds.append(u.option_id)

            # 查询正确的选项集合
            rightIds = []
            right_items  = MpOptionService_instance.get_list_by_filters(db_session,filters=MpOptionDTO(
                question_id=question.id,
                score=1,
            ).model_dump())
            for r in right_items:
                rightIds.append(r.id)

            # 将正确选项集合和用户选择的选项集合进行对比
            if set(choiceIds) == set(rightIds):
                isSame = True
            else:
                isSame = False

            # 根据对比结果判断用户是否回答正确
            if isSame:
                json['isAnswerCorrect'] = 1
            else:
                json['isAnswerCorrect'] = 0

        JsonArray.append(json)

    return ResponseUtil.success(data=JsonArray)



"""
选项分析
"""
@router.post("/optionAnalyse")
def optionAnalyse(user_exam_id:int = Body(None),questionId = Body(None),db_session: Session = Depends(get_db_session)):
    logger.info(f'/mp/exam/optionAnalyse, user_exam_id = {user_exam_id}, question_id = {questionId}')
    JsonArray = []
    json = {}

    # 用户选择的选项id集合
    choiceNums = []

    # 查询用户选择的选项id集合
    choiceIds = []
    uoptions = MpUserOptionService_instance.get_list_by_filters(db_session,filters=MpUserOptionDTO(
        user_exam_id=user_exam_id,
        question_id=questionId,
    ).model_dump())
    for u in uoptions:
        choiceIds.append(u.option_id)

    # 根据question_id 查询问题内容
    question = MpQuestionService_instance.get_one_by_filters(db_session,filters=MpQuestionDTO(
        id=questionId,
    ).model_dump())
    json['question_name'] = question.name
    JsonArray.append(json)

    # 根据question_id 查询选项内容
    options = MpOptionService_instance.get_list_by_filters(db_session,filters=MpOptionDTO(
        question_id=questionId,
    ).model_dump())
    JsonArray2 = []
    num:int = 0
    for o in options:
        option_num:str = f"A{num}"
        json2 = {
            "option_num": option_num,
            "option_name": o['content'],
            "isRight": 1 if o['score'] > 1 else 0,
        }
        if choiceIds.__contains__(o.id):
            choiceNums.append(option_num+"")

        JsonArray2.append(json2)
        num += 1

    JsonArray.append(JsonArray2)
    # 描述文本
    json3 = {
        "text":choiceNums.__dict__
    }
    JsonArray.append(json3)

    return ResponseUtil.success(data=JsonArray)

