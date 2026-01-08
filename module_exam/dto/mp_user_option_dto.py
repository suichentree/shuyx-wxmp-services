from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import Optional

# 定义用户模型类型
# 注意：DTO 是数据传输对象，用于在不同层之间传递数据，而不是直接与数据库交互。
# 不同的DTO类，用于不同的场景，有的场景需要返回所有字段，有的场景只需要返回部分字段
class MpUserOptionDTO(BaseModel):
    id:Optional[int] = None          # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    user_id:Optional[int] = None
    exam_id:Optional[int] = None
    user_exam_id:Optional[int] = None
    question_id:Optional[int] = None
    option_id: Optional[str] = None
    create_time:Optional[datetime] = None

    # 将sqlalchemy模型转换为pydantic模型的配置
    model_config = ConfigDict(from_attributes=True)


