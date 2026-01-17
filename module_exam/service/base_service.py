from typing import Generic, TypeVar, Type, List, Optional, Dict, Any

from sqlalchemy import text
from sqlalchemy.orm import Session
from module_exam.dao.base_dao import BaseDao
from module_exam.model.base_model import myBaseModel

# 定义泛型类型变量，约束为SQLAlchemy的Base模型
ModelType = TypeVar("ModelType", bound=myBaseModel)

class BaseService(Generic[ModelType]):
    """通用Service基类，封装通用业务逻辑"""
    def __init__(self, dao: BaseDao[ModelType]):
        """
        初始化BaseService
        :param dao: 关联的DAO实例（如UserDAO）
        """
        self.dao = dao

    def get_by_id(self, db_session: Session, id: int) -> Optional[ModelType]:
        """
        根据ID获取单条记录（注意包含字段id）
            id: 记录ID
        """
        return self.dao.get_by_id(db_session, id)

    def get_total_by_filters(self, db_session: Session, filters: Dict = None) -> int:
        """
        根据条件获取记录总数
            filters: 查询条件,字典类型。例如 {"filed1": value1, "filed2": value2}
        """
        return self.dao.get_total_by_filters(db_session, filters)

    def get_one_by_filters(self, db_session: Session, filters: Dict = None,sort_by: List[str] = None) -> Optional[ModelType]:
        """
        根据条件获取单条记录
            filters: 查询条件，字典类型。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序
        """

        return self.dao.get_one_by_filters(db_session, filters, sort_by)

    def get_list_by_filters(self,db_session: Session,filters: Dict = None,sort_by: List[str] = None) -> List[ModelType]:
        """
        根据条件获取查询列表（支持条件过滤+排序）
            filters: 查询条件字典。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序。
        """
        return self.dao.get_list_by_filters(db_session, filters, sort_by)

    def get_page_list_by_filters(self,db_session: Session,page_num: int,page_size: int,filters: Dict = None,sort_by: List[str] = None) -> List[ModelType]:
        """
        根据条件获取分页查询列表（支持分页+条件过滤+排序）
            page_num: 页码
            page_size: 每页大小
            filters: 查询条件字典。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序。
        """
        return self.dao.get_page_list_by_filters(db_session, page_num, page_size, filters, sort_by)

    def add(self, db_session: Session, dict_data: Dict = None) -> ModelType:
        """
        添加新记录
            dict_data: 新记录的字典数据
        """
        return self.dao.add(db_session, dict_data)

    def update_by_id(self,db_session: Session,id: int,update_data: Dict = None) -> bool:
        """
        根据ID更新信息
            id: 要更新的记录ID
            update_data: 更新数据字典
        """
        return self.dao.update_by_id(db_session, id, update_data)

    def delete_by_id(self, db_session: Session, id: int) -> bool:
        """
        根据ID删除记录
            id: 要删除的记录ID
        """
        return self.dao.delete_by_id(db_session, id)

    def get_one_by_execute_sql(self, db_session: Session, sql: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        执行原生SQL查询，返回单行数据
        :param sql: SQL查询语句
        :param params: 参数字典，如 {"id": 1, "name": "test"}
        :return: 查询结果字典，如果没有结果返回None

        示例：
        # 查询单条记录
        single_record = self.get_one_by_execute_sql(db_session, "SELECT * FROM table_name WHERE id = :id", {"id": 1})

        """
        return self.dao.get_one_by_execute_sql(db_session, sql, params)

    def get_list_by_execute_sql(self, db_session: Session, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        执行原生SQL查询，返回多行数据
        :param sql: SQL查询语句
        :param params: 参数字典，如 {"id": 1, "name": "test"}
        :return: 查询结果列表，每行数据为字典格式

        示例：
        # 查询多条记录
        records: List[Dict[str, Any]] = self.get_list_by_execute_sql(db_session, "SELECT * FROM table_name WHERE name LIKE :name", {"name": "%test%"})

        """
        return self.dao.get_list_by_execute_sql(db_session, sql, params)

    def query_scalar_sql(self, db_session: Session, sql: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """
        执行原生SQL查询，返回单个标量值。例如查询总记录数、最大值、最小值等。
        :param sql: SQL查询语句
        :param params: 参数字典，如 {"id": 1, "name": "test"}
        :return: 查询结果标量值，如果没有结果返回None

        示例：
        # 查询总记录数
        total_count = self.query_scalar_sql(db_session, "SELECT COUNT(*) FROM table_name")
        # 查询最大值
        max_value = self.query_scalar_sql(db_session, "SELECT MAX(field_name) FROM table_name")
        # 查询最小值
        min_value = self.query_scalar_sql(db_session, "SELECT MIN(field_name) FROM table_name")


        """
        return self.dao.query_scalar_sql(db_session, sql, params)