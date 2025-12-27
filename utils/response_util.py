from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any, Dict, List
from datetime import datetime

from sqlalchemy import Row
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


# 将 SQLAlchemy 模型对象转换为字典
# 支持单个对象、对象列表、元组结果集以及Row对象
def model_to_dict(obj: Any) -> Any:
    if obj is None:
        return None

    elif isinstance(obj, list):
        # 检查是否是Row对象列表
        if obj and isinstance(obj[0], Row):
            return [model_to_dict(row) for row in obj]
        # 检查是否是join查询返回的元组列表
        elif obj and isinstance(obj[0], tuple):
            return process_join_result(obj)
        # 处理普通对象列表
        return [model_to_dict(item) for item in obj]

    elif hasattr(obj, '_asdict'):

        # 处理SQLAlchemy的Row对象或命名元组
        return {k: model_to_dict(v) for k, v in obj._asdict().items()}

    elif isinstance(obj, tuple):
        # 处理单个元组（join查询结果）
        result = {}
        for item in obj:
            if isinstance(item.__class__, DeclarativeMeta):
                # 获取模型名称（小写）作为键
                model_name = item.__class__.__name__.lower().replace('model', '')
                result[model_name] = model_to_dict(item)
        return result

    elif isinstance(obj.__class__, DeclarativeMeta):
        # 处理单个模型对象
        fields = {column.key: getattr(obj, column.key) for column in class_mapper(obj.__class__).columns}
        return fields

    return obj


def process_join_result(join_result: List[tuple]) -> List[Dict[str, Any]]:
    """
    处理join查询返回的结果集，将一对多关系转换为嵌套结构
    例如：问题和选项的一对多关系，将选项嵌套到问题中
    """
    if not join_result:
        return []

    # 用于存储最终结果的字典，key为键，value为值
    result_dict = {}

    for item in join_result:
        # 假设元组中第一个元素是主模型，第二个元素是关联模型
        main_model = item[0]
        related_model = item[1] if len(item) > 1 else None

        # 获取主模型的ID
        main_id = getattr(main_model, 'id')

        # 如果主模型不在结果字典中，添加它
        if main_id not in result_dict:
            main_model_dict = model_to_dict(main_model)
            # 初始化关联模型列表
            related_model_name = related_model.__class__.__name__.lower().replace('model', '') + 's'
            main_model_dict[related_model_name] = []
            result_dict[main_id] = main_model_dict

        # 如果有关联模型，添加到主模型的关联列表中
        if related_model:
            related_model_name = related_model.__class__.__name__.lower().replace('model', '') + 's'
            result_dict[main_id][related_model_name].append(model_to_dict(related_model))

    # 返回结果列表
    return list(result_dict.values())


# 使用示例
if __name__ == "__main__":
    items = [{"id": 1, "name": "item1"}]
    print(type(ResponseUtil.success(data=items)))
    print(ResponseUtil.success(data=items))
