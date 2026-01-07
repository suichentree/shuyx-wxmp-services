from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional

# 定义用户模型类型
# 注意：DTO 是数据传输对象，用于在不同层之间传递数据，而不是直接与数据库交互。
# 不同的DTO类，用于不同的场景，有的场景需要返回所有字段，有的场景只需要返回部分字段
class MpUserExamDTO(BaseModel):
    id:Optional[int] = None          # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    user_id:Optional[int] = None
    exam_id:Optional[int] = None
    type:Optional[int] = None           # 用户测试类型  0是顺序练习，1是模拟考试
    page_no:Optional[int] = None
    score:Optional[int] = None
    create_time:Optional[datetime|bool] = None
    finish_time:Optional[datetime|bool] = None

    model_config = ConfigDict(from_attributes=True)

