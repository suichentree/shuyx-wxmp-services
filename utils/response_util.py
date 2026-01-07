from fastapi import HTTPException
from pydantic import BaseModel, Field, ConfigDict, TypeAdapter
from typing import Generic, TypeVar, Optional, Any, Dict, List, Type

from pydantic_core import ValidationError
from sqlalchemy import Row
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import class_mapper

# 定义一个泛型类型变量
T = TypeVar('T')

# 定义 Pydantic模型类 ResponseDTO。该类可以接受任意类型的泛型参数T，用于表示响应数据的类型。
class ResponseDTO(BaseModel, Generic[T]):
    """
    统一响应体
    - 用法示例：
      @router.get("/xxx", response_model=ResponseDTO[List[MpExamDTO]])
      def xxx():
          return ResponseUtil.success(data=[...])
    """
    code: int = Field(default=200, description="响应状态码，默认200")
    message: str = Field(default="success", description="提示信息，默认success")
    data: Optional[T] = Field(default=None, description="业务数据（默认DTO 类型）,可选")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={}  # 可自定义序列化规则（如 datetime → 字符串）
    )

# 为了方便 Controller 导入，也导出一个不带泛型的版本（用于无需精确类型的场景）
ResponseDTOBase = ResponseDTO[Any]

# 定义响应工具类 ResponseUtil。该类提供各个静态方法，用于创建成功和失败的响应对象。
class ResponseUtil:
    # 定义success方法，用于创建成功的响应对象,默认状态码200，消息"success"
    @staticmethod
    def success(code=200,message="success",data=None):
        # 自动转换数据为可序列化格式
        return ResponseDTO(code=code, message=message, data=data)

    # 定义error方法，用于创建失败的响应对象，默认状态码500，消息"error"
    @staticmethod
    def error(code=500,message="error",data=None):
        # 自动转换数据为可序列化格式
        return ResponseDTO(code=code, message=message, data=data)

    # 定义exception方法，用于创建异常的响应对象，默认状态码400，消息"exception"
    @staticmethod
    def exception(code=400,message="exception",data=None):
        # 自动转换数据为可序列化格式
        return ResponseDTO(code=code, message=message, data=data)

def model_to_dto(data: Any, dto_cls: Type[BaseModel]) -> Any:
    """
    手动复刻 response_model 核心：校验 + 序列化
    :param data: ORM 实例/列表
    :param dto_cls: 目标 DTO 类
    :return: 序列化后的 DTO 数据（字典/字典列表）
    """
    try:
        # 步骤1：校验数据（model_validate → 对应 response_model 的校验）
        if isinstance(data, list):
            # 列表场景：TypeAdapter 批量校验
            validated_data = TypeAdapter(List[dto_cls]).validate_python(data)
        else:
            # 单实例场景：直接校验
            validated_data = dto_cls.model_validate(data)

        # 步骤2：序列化（model_dump → 对应 response_model 的序列化）
        if isinstance(validated_data, list):
            return [item.model_dump() for item in validated_data]
        return validated_data.model_dump()

    except ValidationError as e:
        # 校验失败：抛出明确异常
        raise HTTPException(status_code=400, detail=f"数据校验失败：{e.errors()}")

# 使用示例
if __name__ == "__main__":
    items = [{"id": 1, "name": "item1"}]
    print(type(ResponseUtil.success(data=items)))
    print(ResponseUtil.success(data=items))
