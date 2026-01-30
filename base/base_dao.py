from typing import Generic, TypeVar, Type, List, Optional, Dict, Any

from sqlalchemy import asc, delete, desc, func, select, update, text
from sqlalchemy.orm import Session

from base.base_model import myBaseModel

# 定义泛型类型变量，约束为SQLAlchemy的Base模型
ModelType = TypeVar("ModelType", bound=myBaseModel)

class BaseDao(Generic[ModelType]):
    """通用DAO基类，封装所有表的通用CRUD方法"""
    def __init__(self, model: Type[ModelType]):
        """
        初始化BaseDAO
        :param model: 关联的SQLAlchemy数据库模型（如User、Order）
        """
        self.model = model

    def _build_filter_conditions(self, filters: Dict):
        """
        构建查询条件，支持高级查询
        :param filters: 查询条件字典
            - 等值查询: {"field": value}
            - 模糊查询: {"field__like": value}
            - 大于查询: {"field__gt": value}
            - 小于查询: {"field__lt": value}
            - 大于等于: {"field__gte": value}
            - 小于等于: {"field__lte": value}
            - 包含查询: {"field__in": [value1, value2]}
            - 为空查询: {"field__isnull": True/False}
        :return: 过滤条件列表
        """
        conditions = []
        if not filters:
            return conditions

        # 遍历查询条件字典，构建查询条件
        for field, value in filters.items():
            # 若字段值为None，则跳过
            if value is None:
                continue

            # 若字典字段包含__，则为特殊查询类型，如模糊查询、范围查询等
            if "__" in field:
                # 将字典键按“__”拆分为字段名和查询类型
                field_name, query_type = field.split("__", 1)

                # 如果字段不存在于模型类中，则跳过
                if not hasattr(self.model, field_name):
                    continue

                # 获取模型类中对应的字段对象
                model_field = getattr(self.model, field_name)

                # 根据查询类型构建不同的条件
                if query_type == "like":
                    # 模糊查询
                    conditions.append(model_field.like(f"%{value}%"))
                elif query_type == "gt":
                    # 大于
                    conditions.append(model_field > value)
                elif query_type == "lt":
                    # 小于
                    conditions.append(model_field < value)
                elif query_type == "gte":
                    # 大于等于
                    conditions.append(model_field >= value)
                elif query_type == "lte":
                    # 小于等于
                    conditions.append(model_field <= value)
                elif query_type == "in":
                    # 包含查询
                    if isinstance(value, (list, tuple)):
                        conditions.append(model_field.in_(value))
                elif query_type == "isnull":
                    # 为空查询
                    if value:
                        conditions.append(model_field.is_(None))
                    else:
                        conditions.append(model_field.is_not(None))
            # 处理普通查询
            elif hasattr(self.model, field):
                # 获取模型类中对应的字段对象
                model_field = getattr(self.model, field)
                # 若值为bool类型
                if isinstance(value, bool):
                    if value:
                        # True，表示该查询字段为非空值
                        conditions.append(model_field.is_not(None))
                    else:
                        # False，表示该查询字段为空值
                        conditions.append(model_field.is_(None))
                # 若值为非None
                elif value is not None:
                    # 设置查询条件为该字段为value
                    conditions.append(model_field == value)

        return conditions

    def get_by_id(self, db_session: Session, id: int) -> Optional[ModelType]:
        """
        根据ID获取单条记录（注意包含字段id）
            id: 记录ID
        """
        # 构建sqlalchemy查询语句
        sql = select(self.model).where(self.model.id == id)
        # 执行查询语句并返回查询结果对象
        result = db_session.execute(sql)
        # 从查询结果对象中获取单条记录（如果存在）
        return result.scalar_one_or_none()

    def get_list_by_ids(self, db_session: Session, ids: List[int]) -> List[ModelType]:
        """
        根据ID列表获取多条记录（注意包含字段id）
            ids: 记录ID列表
        """
        # 构建sqlalchemy查询语句
        sql = select(self.model).where(self.model.id.in_(ids))
        # 执行查询语句并返回查询结果对象
        result = db_session.execute(sql)
        # 从查询结果对象中获取多条记录（如果存在）
        return result.scalars().all()

    def get_total_by_filters(self,db_session: Session,filters: Dict = None) -> int:
        """
        根据条件获取记录总数
            filters: 查询条件,字典类型。例如 {"filed1": value1, "filed2": value2}
        """
        # 构建 count(*) 查询，避免全量加载导致的性能问题
        sql = select(func.count()).select_from(self.model)
        # 动态构建查询条件 and 查询
        conditions = self._build_filter_conditions(filters)
        if conditions:
            sql = sql.where(*conditions)

        # 执行查询语句并返回查询结果对象
        result = db_session.execute(sql)
        # 返回记录总数
        return int(result.scalar_one())

    def get_one_by_filters(self, db_session: Session, filters: Dict = None,sort_by: List[str] = None) -> Optional[ModelType]:
        """
        根据条件获取单条记录
            filters: 查询条件，字典类型。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序。
        """
        # 初始化查询对象，选择模型的所有字段
        sql = select(self.model)
        # 动态构建查询条件 and 查询
        conditions = self._build_filter_conditions(filters)
        if conditions:
            sql = sql.where(*conditions)

        # 动态构建排序条件
        if sort_by:
            # 遍历排序字段列表
            for sort_field in sort_by:
                # 判断排序方向
                if sort_field.startswith('-'):
                    # 降序
                    field_name = sort_field[1:]
                    if hasattr(self.model, field_name):
                        sql = sql.order_by(desc(getattr(self.model, field_name)))
                else:
                    # 升序
                    if hasattr(self.model, sort_field):
                        sql = sql.order_by(asc(getattr(self.model, sort_field)))

        # 添加limit(1)限制，确保只返回第一条记录
        sql = sql.limit(1)

        # 执行查询语句并返回查询结果对象
        result = db_session.execute(sql)
        # 从查询结果对象中获取单条记录（如果存在）
        return result.scalar_one_or_none()

    def get_list_by_filters(self,db_session: Session,filters: Dict = None,sort_by: List[str] = None) -> List[ModelType]:
        """
        根据条件获取查询列表（支持条件过滤+排序）
            filters: 查询条件字典。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序。
        """

        # 初始化查询对象，选择模型的所有字段
        sql = select(self.model)

        # 动态构建查询条件 and 查询
        conditions = self._build_filter_conditions(filters)
        if conditions:
            sql = sql.where(*conditions)

        # 动态构建排序条件
        if sort_by:
            # 遍历排序字段列表
            for sort_field in sort_by:
                # 判断排序方向
                if sort_field.startswith('-'):
                    # 降序
                    field_name = sort_field[1:]
                    if hasattr(self.model, field_name):
                        sql = sql.order_by(desc(getattr(self.model, field_name)))
                else:
                    # 升序
                    if hasattr(self.model, sort_field):
                        sql = sql.order_by(asc(getattr(self.model, sort_field)))

        # 执行查询语句并返回查询结果对象
        result = db_session.execute(sql)
        # 从查询结果对象中获取所有记录
        return result.scalars().all()


    def get_page_list_by_filters(self,db_session: Session,page_num: int,page_size: int,filters: Dict = None,sort_by: List[str] = None) -> List[ModelType]:
        """
        根据条件获取分页查询列表（支持分页+条件过滤+排序）
            page_num: 页码
            page_size: 每页大小
            filters: 查询条件字典。例如 {"filed1": value1, "filed2": value2}
            sort_by: 排序字段，是一个字符串列表。例如 ["field1", "-field2"] 表示按field1升序，按field2降序排序。
        """

        # 初始化查询对象，选择模型的所有字段
        sql = select(self.model)

        # 动态构建查询条件 and 查询
        conditions = self._build_filter_conditions(filters)
        if conditions:
            sql = sql.where(*conditions)

        # 动态构建排序条件
        if sort_by:
            # 遍历排序字段列表
            for sort_field in sort_by:
                # 判断排序方向
                if sort_field.startswith('-'):
                    # 降序
                    field_name = sort_field[1:]
                    if hasattr(self.model, field_name):
                        sql = sql.order_by(desc(getattr(self.model, field_name)))
                else:
                    # 升序
                    if hasattr(self.model, sort_field):
                        sql = sql.order_by(asc(getattr(self.model, sort_field)))

        # 计算分页偏移量
        offset_value = (page_num - 1) * page_size
        # 构建分页查询
        sql = sql.offset(offset_value).limit(page_size)
        # 执行查询语句并返回查询结果对象
        result = db_session.execute(sql)
        # 从查询结果对象中获取所有记录
        return result.scalars().all()


    def add(self, db_session: Session, dict_data: Dict = None) -> ModelType:
        """
        添加新记录
            dict_data: 新记录的字典数据
        """
        # 使用 ORM add，确保实例被 Session 管理，commit 后可 refresh 拿到自增 id
        new_instance = self.model(**(dict_data or {}))
        db_session.add(new_instance)
        # flush方法可以在不提交事务的情况下刷新实例。确保获取到自增 id
        db_session.flush()
        return new_instance

    def update_by_id(self,db_session: Session,id: int,update_data: Dict = None) -> bool:
        """
        根据ID更新信息
            id: 要更新的记录ID
            update_data: 更新数据字典
        """

        # 1. 先查询记录是否存在
        db_obj = self.get_by_id(db_session, id)
        # 若不存在，则返回False
        if not db_obj:
            return False

        # 2. 先过滤掉id字段和None值，不允许更新
        filtered_data = {k: v for k, v in (update_data or {}).items() if k != "id" and hasattr(self.model, k) and v is not None}

        # 3. 构建SQLAlchemy 2.x的update语句
        stmt = update(self.model).where(self.model.id == id).values(**filtered_data)
        # 4. 执行更新语句
        result = db_session.execute(stmt)
        # 判断是否有记录被更新（受影响行数>0）
        return (result.rowcount or 0) > 0

    def delete_by_id(self, db_session: Session, id: int) -> bool:
        """
        根据ID删除记录
            id: 要删除的记录ID
        """

        # 1. 先查询记录是否存在
        db_obj = self.get_by_id(db_session, id)
        if not db_obj:
            return False

        # 2. 构建SQLAlchemy 2.x的delete语句
        stmt = delete(self.model).where(self.model.id == id)
        # 3. 执行删除语句
        result = db_session.execute(stmt)
        # 判断是否有记录被删除（受影响行数>0）
        return (result.rowcount or 0) > 0

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
        result = db_session.execute(text(sql), params or {})
        # 获取列名
        columns = result.keys()
        # 获取单行数据
        row = result.fetchone()
        if row:
            return dict(zip(columns, row))
        return None

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
        result = db_session.execute(text(sql), params or {})
        # 获取列名
        columns = result.keys()
        # 将每行数据转换为字典
        return [dict(zip(columns, row)) for row in result.fetchall()]

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
        result = db_session.execute(text(sql), params or {})
        return result.scalar()