# 导入sqlalchemy框架中的相关字段
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, CHAR, func, Index
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
    page_no: Mapped[int] = MappedColumn(Integer, nullable=False, comment='当前页码')
    score: Mapped[int] = MappedColumn(Integer, nullable=False, comment='大致正确率（单位：%）')
    create_time: Mapped[datetime] = MappedColumn(DateTime, comment='创建时间', default=func.now())
    finish_time: Mapped[datetime] = MappedColumn(DateTime, comment='测试完成时间')

    # 添加索引
    __table_args__ = (
        Index('index_id', 'id'),
        Index('index_user_id', 'user_id'),
        Index('index_exam_id', 'exam_id'),
    )


if __name__ == '__main__':
    aaa = MpUserExamModel(id=1, user_id=1, exam_id=1, type=0, page_no=1, score=0, create_time=datetime.now(), finish_time=datetime.now())
    print(aaa.to_dict())
