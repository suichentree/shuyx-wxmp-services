# 导入sqlalchemy框架中的相关字段
from datetime import datetime
from typing import List

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index, JSON
from sqlalchemy.orm import Mapped, MappedColumn

# 导入公共基类
from module_exam.model.base_model import myBaseModel

class MpUserExamModel(myBaseModel):
    """
    用户测试表 mp_user_exam
    """
    __tablename__ = 'mp_user_exam'

    id: Mapped[int] = MappedColumn(Integer, primary_key=True, autoincrement=True, comment='用户测试id')
    user_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户id')
    exam_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='测试id')
    type: Mapped[int] = MappedColumn(Integer, nullable=False, comment='用户测试类型  0是顺序练习，1是模拟考试')
    type_name: Mapped[str] = MappedColumn(String(20), nullable=False, comment='用户测试类型名称')
    last_question_id: Mapped[int] = MappedColumn(Integer, nullable=False, comment='最后做的问题ID，用于记录用户最后做题的位置')
    correct_count: Mapped[int] = MappedColumn(Integer, nullable=False, comment='答对题目数')
    error_count: Mapped[int] = MappedColumn(Integer, nullable=False, comment='答错题目数')
    total_count: Mapped[int] = MappedColumn(Integer, nullable=False, comment='总题目数')
    question_ids: Mapped[List[int]] = MappedColumn(JSON, nullable=False, comment='题目ID数组快照，例如：[1, 5, 12, 23, ...] ，不受后续题库变化影响')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())
    finish_time: Mapped[datetime] = MappedColumn(DateTime, comment='测试完成时间')

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_exam_id', 'exam_id'),
    )


if __name__ == '__main__':
    aaa = MpUserExamModel(id=1, user_id=1, exam_id=1, type=0, last_question_id=1, create_time=datetime.now(), finish_time=datetime.now())
    print(aaa.to_dict())
