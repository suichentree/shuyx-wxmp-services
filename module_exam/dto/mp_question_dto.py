from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List

from module_exam.dto.mp_option_dto import MpOptionDTO

# 定义用户模型类型
# 注意：DTO 是数据传输对象，用于在不同层之间传递数据，而不是直接与数据库交互。
class MpQuestionDTO(BaseModel):
    id:Optional[int] = None          # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    exam_id:Optional[int] = None
    name:Optional[str] = None
    type:Optional[int] = None
    type_name:Optional[str] = None
    status:Optional[int] = None
    create_time:Optional[datetime] = None


# 定义问题-选项模型类型
class MpQuestionOptionDTO(BaseModel):
    id: Optional[int] = None  # Optional[int] = None 表示类型可以是int,也可以是 None，默认值为 None
    exam_id: Optional[int] = None
    name: Optional[str] = None
    type: Optional[int] = None
    type_name: Optional[str] = None
    status: Optional[int] = None
    create_time: Optional[datetime] = None
    options: Optional[List[MpOptionDTO]] = []  # 添加选项列表字段



