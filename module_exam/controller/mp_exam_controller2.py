from fastapi import APIRouter, Body, Depends, UploadFile, FastAPI, HTTPException, File, UploadFile
from sqlalchemy.orm import Session
from fastapi.params import File
import pandas as pd
from typing import List, Optional
from pydantic import BaseModel
import os

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
from utils.response_util import ResponseUtil, ResponseDTO

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
    with db_session.begin():
        # 解析Excel文件
        parsed_data = parse_excel_file(file)
        print(parsed_data)

        # 创建考试记录
        exam_dto = MpExamDTO(
            name=exam_name,
            tag="特种安全作业",
            status=0
        )
        exam = MpExamService_instance.add(db_session, dict_data=exam_dto.model_dump())
        
        # 导入题目和选项
        question_count = 0
        option_count = 0
        
        for index, row in df.iterrows():
            # 解析题目类型
            type_map = {
                '单选题': 1,
                '多选题': 2,
                '判断题': 3
            }
            question_type = type_map.get(row['类型'], 1)
            type_name = row['类型']
            
            # 创建题目记录
            question_dto = MpQuestionDTO(
                exam_id=exam.id,
                name=row['题目'],
                type=question_type,
                type_name=type_name,
                status=0
            )
            question = MpQuestionService_instance.add(db_session, dict_data=question_dto.model_dump())
            question_count += 1
            
            # 解析正确答案
            correct_answers = []
            if isinstance(row['答案'], str):
                correct_answers = [ans.strip().upper() for ans in row['答案'].split(',')]
            
            # 创建选项记录
            options = [
                ('A', row['选项A']),
                ('B', row['选项B']),
                ('C', row['选项C']),
                ('D', row['选项D'])
            ]
            
            for option_label, option_content in options:
                if pd.notna(option_content):  # 跳过空选项
                    is_right = 1 if option_label in correct_answers else 0
                    
                    option_dto = MpOptionDTO(
                        question_id=question.id,
                        content=option_content,
                        is_right=is_right,
                        status=0
                    )
                    MpOptionService_instance.add(db_session, dict_data=option_dto.model_dump())
                    option_count += 1
        
        return ResponseUtil.success(
            message="数据导入成功",
            data={
                "exam_id": exam.id,
                "exam_name": exam.name,
                "imported_questions": question_count,
                "imported_options": option_count
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
