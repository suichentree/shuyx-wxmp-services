# shuyx-wxmp-services

这是微信小程序的服务端代码。包含各个模块的接口。

技术栈：
- FastAPI
- Uvicorn
- MySQL
- SQLAlchemy



# FastAPI 项目架构评审与改进建议

## 一、当前架构总结

### 1.1 分层结构
```
Controller (路由层)
    ↓
Service (业务逻辑层)
    ↓
DAO (数据访问层)
    ↓
Model (ORM 模型层)
```

**评价**：✅ 清晰的三层架构，类似 Spring Boot 风格，适合中大型项目。

---

### 1.2 通用 CRUD 封装

#### BaseDao（数据访问基类）
- ✅ 泛型设计，支持所有 Model 复用
- ✅ 支持动态 filters、排序、分页
- ✅ **已修复**：`add/update/delete` 的 commit/rowcount 问题
- ✅ **已优化**：`get_total_by_filters` 改用 `count()` 避免全量加载

#### BaseService（业务逻辑基类）
- ✅ 透传 DAO 方法，统一 session 管理
- ⚠️ **当前状态**：DAO 层仍在每次操作后 commit（单次提交模式）

---

### 1.3 统一响应格式

#### ResponseDTO + ResponseUtil
```python
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

**评价**：
- ✅ 国内项目常见做法，前端统一处理
- ✅ **已改进**：支持泛型 `ResponseDTO[T]`，可声明精确类型
- ✅ **已补充**：全局异常处理器，自动转换异常为统一格式

---

### 1.4 DTO 使用方式

- ✅ 用 Pydantic BaseModel 定义 DTO
- ✅ `model_to_dto()` 手动校验 + 序列化
- ⚠️ **可优化**：部分路由未声明 `response_model`，导致 OpenAPI 文档不精确

---

## 二、与主流 FastAPI 对比

| 维度 | 当前架构 | 主流 FastAPI | 差异说明 |
|------|----------|--------------|----------|
| **分层** | Controller/Service/DAO | 轻量分层（Router + Service/Usecase） | 你的更偏 Java 风格，主流更轻量 |
| **CRUD 封装** | BaseDao 泛型 + 动态 filters | 直接用 SQLAlchemy 或 Repository 模式 | 你的封装更通用，但灵活性稍低 |
| **事务管理** | DAO 层每次 commit | Service 层控制事务边界 | ⚠️ **关键差异**，需改进 |
| **响应格式** | `{code, message, data}` 统一包装 | 直接返回 DTO，用 HTTP 状态码 | 你的符合国内习惯，主流更 RESTful |
| **response_model** | 部分未声明 | 必须声明，自动生成文档 | ⚠️ **需补充** |
| **异常处理** | 全局 exception_handler | 同样用 exception_handler | ✅ 已补充，与主流一致 |
| **依赖注入** | 用 `Depends(get_db_session)` | 同样方式 | ✅ 完全一致 |
| **类型提示** | 部分接口缺少类型 | 强制类型提示 | ⚠️ 可逐步补充 |

---

## 三、核心问题与改进建议（优先级排序）

### 🔴 P0（必须修复，影响数据一致性）

#### 1. 事务边界问题

**现状**：
```python
# DAO 层每次操作都 commit
def add(self, db_session, dict_data):
    new_instance = self.model(**dict_data)
    db_session.add(new_instance)
    db_session.commit()  # ❌ 这里立即提交
    return new_instance
```

**风险**：
- 模拟考试交卷：插入 20 条 `mp_user_option` + 更新 1 条 `mp_user_exam`
- 若第 15 条插入失败，前 14 条已提交 → **脏数据**

**主流做法**：
```python
# DAO 层不 commit，只执行操作
def add(self, db_session, dict_data):
    new_instance = self.model(**dict_data)
    db_session.add(new_instance)
    db_session.flush()  # 生成 id，但不提交
    return new_instance

# Service 层控制事务
def submit_exam(self, db_session, ...):
    try:
        # 多个 DAO 操作
        for answer in answers:
            self.user_option_dao.add(db_session, answer, commit=False)
        self.user_exam_dao.update_by_id(db_session, id, data, commit=False)
        
        # 统一提交
        db_session.commit()
    except Exception:
        db_session.rollback()
        raise
```

**改进方案**（已部分实施，需彻底落地）：
1. ✅ `BaseDao` 的 `add/update/delete` 增加 `commit` 参数（默认 True 兼容旧代码）
2. ⚠️ **待执行**：将"交卷/多写操作"的接口改为 Service 层统一提交
3. ⚠️ **待执行**：逐步迁移所有写操作到 Service 层控制事务

---

### 🟡 P1（强烈建议，影响可维护性和文档质量）

#### 2. 补充 `response_model` 声明

**现状**：
```python
@router.post("/getExamList")  # ❌ 无 response_model
def get_exam_list(...):
    return ResponseUtil.success(data=dto_result)
```

**改进**：
```python
@router.post("/getExamList", response_model=ResponseDTO[List[MpExamDTO]])  # ✅
def get_exam_list(...):
    return ResponseUtil.success(data=dto_result)
```

**收益**：
- ✅ Swagger UI 显示精确的返回字段
- ✅ IDE 自动补全和类型检查
- ✅ FastAPI 自动过滤多余字段（安全性）

**执行计划**：
- [x] 已为 `mp_kaoshi_controller.py` 和 `mp_practice_controller.py` 补充
- [ ] 待补充：`mp_exam_controller.py`、`mp_user_controller.py`

---

#### 3. 让 HTTP 状态码与业务 code 同步

**现状**：
```python
# 业务错误也返回 HTTP 200
return ResponseUtil.error(code=404, message="用户不存在")  # HTTP 200, body.code=404
```

**问题**：
- 监控系统看到的都是 200，无法区分成功/失败
- 网关/负载均衡无法根据状态码做决策

**主流做法**：
```python
# 方式 1：业务错误用 HTTPException
from fastapi import HTTPException
raise HTTPException(status_code=404, detail="用户不存在")  # HTTP 404

# 方式 2：修改 ResponseUtil.error，同步设置 HTTP 状态码
from fastapi import Response
def error(code=500, message="error", data=None):
    response = Response(status_code=code)  # 设置 HTTP 状态码
    return ResponseDTO(code=code, message=message, data=data)
```

**建议**：
- 系统级错误（404、500、401）：用 `HTTPException`
- 业务级错误（如"余额不足"）：继续用 `ResponseUtil.error`，但 HTTP 保持 200

---

### 🟢 P2（可选优化，提升开发体验）

#### 4. filters 语义显式化

**现状**：
```python
# bool 表示"是否为空/非空"（隐藏规则）
filters = {"finish_time": True}  # 表示 finish_time IS NOT NULL
```

**问题**：
- 新成员容易误用：以为 `True` 表示"等于 True"
- 无法表达复杂条件（如大于、小于、like）

**主流做法**：
```python
# 方式 1：显式方法名
dao.get_list_by_filters(filters={"finish_time__isnull": False})

# 方式 2：专门方法
service.get_finished_exams(user_id, exam_id)  # 内部拼接 finish_time IS NOT NULL

# 方式 3：用 SQLAlchemy 表达式（灵活但冗长）
from sqlalchemy import and_, or_
dao.get_list_by_conditions([
    MpUserExamModel.user_id == user_id,
    MpUserExamModel.finish_time != None
])
```

**建议**：
- 保留现有 filters 的 bool 语义（已有代码依赖）
- 在文档中明确说明（避免误用）
- 复杂查询场景：在 Service/DAO 层写专门方法

---

#### 5. 分页接口返回 total

**现状**：
```python
@router.get("/getExamList")
def get_exam_list(page_num: int, page_size: int, ...):
    result = service.get_page_list_by_filters(...)
    return ResponseUtil.success(data=result)  # 只返回当前页数据
```

**问题**：
- 前端无法知道总记录数，无法渲染分页器

**主流做法**：
```python
@router.get("/getExamList", response_model=ResponseDTO[PaginationDTO[MpExamDTO]])
def get_exam_list(...):
    items = service.get_page_list_by_filters(...)
    total = service.get_total_by_filters(...)
    return ResponseUtil.success(data={
        "items": items,
        "total": total,
        "page_num": page_num,
        "page_size": page_size
    })
```

**或定义通用分页 DTO**：
```python
from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar('T')

class PaginationDTO(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page_num: int
    page_size: int
    total_pages: int

# 使用
@router.get("/getExamList", response_model=ResponseDTO[PaginationDTO[MpExamDTO]])
def get_exam_list(...):
    items = ...
    total = ...
    return ResponseUtil.success(data=PaginationDTO(
        items=items,
        total=total,
        page_num=page_num,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    ))
```

---

#### 6. 补充类型提示

**现状**：
```python
def get_exam_list(page_num, page_size, db_session):  # ❌ 缺少类型
    ...
```

**改进**：
```python
from sqlalchemy.orm import Session
from typing import List

def get_exam_list(
    page_num: int = 1,
    page_size: int = 10,
    db_session: Session = Depends(get_db_session)
) -> ResponseDTO[List[MpExamDTO]]:  # ✅ 完整类型提示
    ...
```

**收益**：
- IDE 自动补全
- mypy 静态类型检查
- 团队协作更清晰

---

## 四、已完成的改进

### ✅ 通用 CRUD 底座修复
- [x] `BaseDao.add()` 改用 `session.add/commit/refresh`（保证拿到自增 id）
- [x] `BaseDao.update_by_id/delete_by_id()` 改用 `result.rowcount` 判断
- [x] `BaseDao.get_total_by_filters()` 改用 `count(*)` 避免全量加载

### ✅ 统一响应格式增强
- [x] `ResponseDTO` 支持泛型 `ResponseDTO[T]`
- [x] 导出 `ResponseDTOBase` 简化无精确类型场景
- [x] 补充使用文档 `docs/response_model_usage.md`

### ✅ 全局异常处理
- [x] 实现 `config/exception_handlers.py`
- [x] 处理 HTTPException、ValidationError、SQLAlchemyError、通用 Exception
- [x] 统一转换为 `{code, message, data}` 格式
- [x] 在 `main.py` 中注册

### ✅ 接口改进示例
- [x] `mp_kaoshi_controller.py` 补充 `response_model`
- [x] `mp_practice_controller.py` 补充 `response_model`
- [x] 修复 `mp_exam_controller.py` 中漏传 `db_session` 的 `update_by_id` 调用
- [x] 修复 `mp_user_controller.py` 中同样问题

---

## 五、后续执行计划

### 阶段 1：基础设施完善（1-2 天）
- [ ] 将 `BaseDao` 的 commit 默认改为 False（需同步修改所有调用处，建议分批）
- [ ] 为"交卷/多写操作"接口补充事务控制（Service 层统一 commit）
- [ ] 补充剩余 Controller 的 `response_model` 声明

### 阶段 2：文档与规范（1 天）
- [ ] 编写团队开发规范文档（如何使用 BaseDao/Service、response_model 规范）
- [ ] 补充单元测试示例（测试 Service 层事务回滚）

### 阶段 3：可选优化（按需）
- [ ] 实现通用分页 DTO
- [ ] filters 语义文档化
- [ ] 补充全量类型提示

---

## 六、总结

### 你当前架构的优点 ✅
1. **清晰的分层**：Controller/Service/DAO 职责明确
2. **高度复用**：BaseDao/BaseService 泛型封装减少重复代码
3. **统一规范**：ResponseDTO + model_to_dto 保证一致性
4. **可扩展性**：容易新增表/接口

### 与主流 FastAPI 的主要差异 ⚠️
1. **事务管理**：你的在 DAO 层 commit，主流在 Service 层
2. **响应风格**：你的用 `{code, message, data}`，主流直接返回 DTO + HTTP 状态码
3. **文档生成**：你的部分接口缺 `response_model`，主流强制声明

### 改进后的收益 🎯
- ✅ 数据一致性：事务统一管理，避免脏数据
- ✅ 文档质量：Swagger UI 精确展示字段结构
- ✅ 类型安全：IDE 自动补全，减少低级错误
- ✅ 团队协作：规范清晰，新人上手快

---

## 七、参考资源

### 主流 FastAPI 项目示例
- [FastAPI 官方教程 - SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [full-stack-fastapi-template](https://github.com/tiangolo/full-stack-fastapi-template) - Tiangolo 官方脚手架
- [fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)

### 你当前架构类似的项目
- Spring Boot (Java) - 三层架构经典实现
- Django REST Framework (Python) - Serializer + ViewSet 模式

### SQLAlchemy 事务管理
- [SQLAlchemy Session 事务管理](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [FastAPI with SQLAlchemy - Transaction Management](https://fastapi.tiangolo.com/advanced/sql-databases-peewee/)
