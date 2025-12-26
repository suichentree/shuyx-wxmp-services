from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any, Dict, List
from datetime import datetime
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm import class_mapper

# 定义一个泛型类型变量
T = TypeVar('T')

# 定义 Pydantic模型类 ResponseModel。该类可以接受任意类型的泛型参数T，用于表示响应数据的类型。
class ResponseModel(BaseModel, Generic[T]):
    # 响应状态码，默认200
    code: int = 200
    # 响应消息，默认"success"
    message: str = "success"
    # 响应数据，类型为泛型T，可选
    data: Optional[T] = None

# 将 SQLAlchemy 模型对象转换为字典
# 支持单个对象或对象列表
def model_to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    elif isinstance(obj, list):
        # 处理对象列表
        return [model_to_dict(item) for item in obj]
    elif isinstance(obj.__class__, DeclarativeMeta):
        # 处理单个模型对象
        fields = {column.key: getattr(obj, column.key) for column in class_mapper(obj.__class__).columns}
        return fields
    return obj

# 定义响应工具类 ResponseUtil。该类提供各个静态方法，用于创建成功和失败的响应对象。
class ResponseUtil:
    # 定义success方法，用于创建成功的响应对象,默认状态码200，消息"success"
    @staticmethod
    def success(code=200,message="success",data=None):
        # 自动转换数据为可序列化格式
        dict_data = model_to_dict(data)
        return ResponseModel(code=code, message=message, data=dict_data)

    # 定义error方法，用于创建失败的响应对象，默认状态码500，消息"error"
    @staticmethod
    def error(code=500,message="error",data=None):
        # 自动转换数据为可序列化格式
        dict_data = model_to_dict(data)
        return ResponseModel(code=code, message=message, data=dict_data)

    # 定义exception方法，用于创建异常的响应对象，默认状态码400，消息"exception"
    @staticmethod
    def exception(code=400,message="exception",data=None):
        # 自动转换数据为可序列化格式
        dict_data = model_to_dict(data)
        return ResponseModel(code=code, message=message, data=dict_data)

# 使用示例
if __name__ == "__main__":
    items = [{"id": 1, "name": "item1"}]
    print(type(ResponseUtil.success(data=items)))
    print(ResponseUtil.success(data=items))
