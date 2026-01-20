from datetime import datetime

from pydantic import BaseModel, ConfigDict, Json
from typing import Optional, List


# 定义用户模型类型
# 注意：DTO 是数据传输对象，用于在不同层之间传递数据，而不是直接与数据库交互。
# 不同的DTO类，用于不同的场景，有的场景需要返回所有字段，有的场景只需要返回部分字段
class MpUserExamDTO(BaseModel):
    id:Optional[int] = None          # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    user_id:Optional[int] = None
    exam_id:Optional[int] = None
    type:Optional[int] = None           # 用户测试类型  0是顺序练习，1是模拟考试
    type_name:Optional[str] = None
    last_question_id:Optional[int] = None        # 最后做的问题ID，用于记录用户最后做题的位置

    correct_count: Optional[int] = None         # 答对题目数
    error_count: Optional[int] = None         # 答错题目数
    total_count:Optional[int] = None            # 总题目数
    question_ids: Optional[List[int]] = None   # 题目ID数组快照，例如：[1, 5, 12, 23, ...] ，不受后续题库变化影响

    create_time:Optional[datetime|bool] = None
    finish_time:Optional[datetime|bool] = None  # NULL表示未完成

    # 将sqlalchemy模型转换为pydantic模型的配置
    model_config = ConfigDict(from_attributes=True)

