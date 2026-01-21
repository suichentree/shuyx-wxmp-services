from fastapi import APIRouter, Body, Depends, UploadFile, FastAPI, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.params import File
import pandas as pd
from typing import List, Optional
from pydantic import BaseModel
import os
from datetime import datetime

from config.database_config import get_db_session
from config.log_config import logger
from module_exam.dto.mp_exam_dto import MpExamDTO
from module_exam.dto.mp_option_dto import MpOptionDTO
from module_exam.dto.mp_question_dto import  MpQuestionDTO
from module_exam.service.mp_exam_service import MpExamService
from module_exam.service.mp_option_service import MpOptionService
from module_exam.service.mp_question_service import MpQuestionService
from module_exam.service.mp_user_exam_service import MpUserExamService
from module_exam.service.mp_user_exam_option_service import MpUserExamOptionService
from utils.response_util import ResponseUtil

# 创建路由实例
router = APIRouter(prefix='/mp/exam2', tags=['mp_exam2接口'])
# 创建服务实例
MpExamService_instance = MpExamService()
MpOptionService_instance = MpOptionService()
MpQuestionService_instance = MpQuestionService()
MpUserExamService_instance = MpUserExamService()
MpUserExamOptionService_instance = MpUserExamOptionService()

@router.post("/importDataByExcel",description="上传包含题目、选项、答案等信息的Excel文件，解析后导入数据库。")
async def importDataByExcel(exam_name: str = Body(...), file: UploadFile = File(...), db_session: Session = Depends(get_db_session)):
    """
    从Excel文件导入考试数据
    :param file: 上传的Excel文件
    :return: 导入结果
    """

    # 解析Excel文件
    parsed_data = parse_excel_file(file)
    print(parsed_data)

    # 检查数据是否有效
    if parsed_data is None or len(parsed_data) == 0 or not isinstance(parsed_data, list):
        return ResponseUtil.error(message="Excel文件内容为空或格式错误")

    # 事务管理(自动提交和回滚)
    with db_session.begin():
        # 创建新的考试记录
        new_exam = MpExamService_instance.add(db_session, dict_data=MpExamDTO(
            name=exam_name,
            tag="特种安全作业",
            status=0,
            created_time=datetime.now(),
        ).model_dump())

        # 遍历，创建新的题目记录
        for item in parsed_data:
            # 新增题目记录, excel文件中只有选择题、判断题。其中选择题都是单选题
            new_question = MpQuestionService_instance.add(db_session, dict_data=MpQuestionDTO(
                exam_id=new_exam.id,
                name=item['question_content'],
                type= 1 if item['question_type'] == '选择题' else 3 if item['question_type'] == '判断题' else None,  # 1:单选题, 3:判断题
                type_name= "单选题" if item['question_type'] == '选择题' else "判断题" if item['question_type'] == '判断题' else None,
                status=0,
                analysis=item['analysis'],
                created_time=datetime.now(),
            ).model_dump())

            # 处理选项数据  {content,is_right}
            options_list = []
            if item['question_type'] == '判断题':
                options_list.append({'content':'对','is_right':1 if item['correct_answer'] == '对' else 0})
                options_list.append({'content':'错','is_right':1 if item['correct_answer'] == '错' else 0})
            elif item['question_type'] == '选择题':
                if item['option_a'] != '':
                    options_list.append({'content':item['option_a'],'is_right':1 if item['correct_answer'] == 'A' else 0})
                if item['option_b'] != '':
                    options_list.append({'content':item['option_b'],'is_right':1 if item['correct_answer'] == 'B' else 0})
                if item['option_c'] != '':
                    options_list.append({'content':item['option_c'],'is_right':1 if item['correct_answer'] == 'C' else 0})
                if item['option_d'] != '':
                    options_list.append({'content':item['option_d'],'is_right':1 if item['correct_answer'] == 'D' else 0})
                if item['option_e'] != '':
                    options_list.append({'content':item['option_e'],'is_right':1 if item['correct_answer'] == 'E' else 0})
                if item['option_f'] != '':
                    options_list.append({'content':item['option_f'],'is_right':1 if item['correct_answer'] == 'F' else 0})

            # 新增选项记录
            for option in options_list:
                MpOptionService_instance.add(db_session, dict_data=MpOptionDTO(
                    question_id=new_question.id,
                    content=option['content'],
                    is_right=option['is_right'],
                    status=0,
                    created_time=datetime.now(),
                ).model_dump())

        return ResponseUtil.success(
            message="数据导入成功",
            data={
                "exam_id": new_exam.id,
                "exam_name": new_exam.name,
            }
        )

# 解析Excel文件
def parse_excel_file(file: UploadFile):
    HEADER_MAPPING = {
        "题目": "question_content",  # 题目内容
        "类型": "question_type",  # 题目类型（选择题/判断题）
        "选项A": "option_a",  # 选项A
        "选项B": "option_b",  # 选项B
        "选项C": "option_c",  # 选项C（判断题可能为空）
        "选项D": "option_d",  # 选项D（多数情况为空）
        "选项E": "option_e",  # 选项E（多数情况为空）
        "选项F": "option_f",  # 选项F（多数情况为空）
        "答案": "correct_answer",  # 正确答案
        "解析": "analysis"  # 题目解析（可能为空）
    }


    try:
        # 步骤1：文件类型校验（仅允许.xlsx，防止非Excel文件上传）
        file_ext = os.path.splitext(file.filename)[-1].lower()
        if file_ext != ".xlsx" and file_ext != ".xls":
            raise HTTPException(
                status_code=400,
                detail=f"仅支持.xlsx .xls 格式文件，当前上传格式：{file_ext}"
            )

        # 步骤2：读取上传的Excel文件（用文件对象，无需保存到本地）
        df = pd.read_excel(
            io=file.file,  # 直接读取上传的文件对象
            engine="openpyxl",  # 处理.xlsx格式
            usecols=list(HEADER_MAPPING.keys()),  # 只读取需要的表头
            keep_default_na=False  # 空单元格转为空字符串，避免None
        )

        # 步骤3：校验Excel表头是否完整（防止缺失关键列）
        excel_headers = df.columns.tolist()
        missing_headers = [h for h in HEADER_MAPPING.keys() if h not in excel_headers]
        if missing_headers:
            raise HTTPException(
                status_code=400,
                detail=f"Excel表头缺失，需包含以下字段：{', '.join(missing_headers)}"
            )

        # 步骤4：表头映射（中文表头→规范英文字段名）
        df.rename(columns=HEADER_MAPPING, inplace=True)

        # 步骤5：转换为字典列表（符合Pydantic模型结构）
        parsed_data = df.to_dict(orient="records")

        # 步骤6：空数据处理（若Excel无内容）
        if not parsed_data:
            raise HTTPException(status_code=200, detail="上传的Excel文件为空，无题库数据可返回")

        # 关闭文件对象（避免资源泄漏）
        file.file.close()

        # 返回数据
        return parsed_data

        # 异常处理：覆盖核心场景
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="上传文件读取失败，文件不存在")
    except Exception as e:
        # 确保异常时关闭文件
        if hasattr(file, "file") and not file.file.closed:
            file.file.close()
        raise HTTPException(
            status_code=500,
            detail=f"Excel解析失败：{str(e)}（请确认文件未损坏且格式正确）"
        )
