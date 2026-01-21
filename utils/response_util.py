from pydantic import BaseModel, Field, ConfigDict
from typing import Generic, TypeVar, Optional

# 定义一个泛型类型变量
T = TypeVar('T')

# 定义 Pydantic模型类 ResponseDTO 统一响应类。该类可以接受任意类型的泛型参数T，用于表示响应数据的类型。
class ResponseDTO(BaseModel, Generic[T]):
    code: int = Field(default=200, description="业务状态码，默认200")
    message: str = Field(default="success", description="提示信息，默认success")
    data: Optional[T] = Field(default=None, description="业务数据（默认DTO 类型）,可选")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_encoders={}  # 可自定义序列化规则（如 datetime → 字符串）
    )

# 定义统一响应工具类 ResponseUtil。该类提供各个静态方法，用于创建成功和失败的统一响应对象。
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


# 使用示例
if __name__ == "__main__":
    items = [{"id": 1, "name": "item1"}]
    print(type(ResponseUtil.success(data=items)))
    print(ResponseUtil.success(data=items))
