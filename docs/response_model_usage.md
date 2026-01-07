# FastAPI 统一响应格式使用指南

## 背景

主流 FastAPI 推荐直接返回 DTO，但我们项目需要统一的 `{code, message, data}` 格式。
通过 `response_model` 声明，既能保留统一格式，又能获得精确的类型提示和 API 文档。

---

## 使用方式

### 1. 基础用法：使用 `ResponseDTOBase`（不需要精确类型）

适用于：返回动态结构、字典、或不需要在文档中展示详细字段的场景。

```python
from utils.response_util import ResponseUtil, ResponseDTOBase

@router.post("/submit", response_model=ResponseDTOBase)
def submit_exam(user_id: int = Body(...), db_session: Session = Depends(get_db_session)):
    # ... 业务逻辑 ...
    return ResponseUtil.success(data={
        "user_exam_id": 123,
        "right_num": 80,
        "error_num": 20
    })
```

**OpenAPI 文档效果**：
```json
{
  "code": 200,
  "message": "success",
  "data": {}  // 显示为通用 object，不展示具体字段
}
```

---

### 2. 高级用法：使用 `ResponseDTO[具体类型]`（推荐）

适用于：返回明确的 DTO 列表或单个对象，需要在 Swagger UI 中展示详细字段结构。

#### 示例 1：返回单个对象

```python
from typing import Dict
from utils.response_util import ResponseUtil, ResponseDTO
from module_exam.dto.mp_exam_dto import MpExamDTO

@router.get("/getExamInfo", response_model=ResponseDTO[MpExamDTO])
def get_exam_info(exam_id: int, db_session: Session = Depends(get_db_session)):
    exam = MpExamService_instance.get_by_id(db_session, exam_id)
    dto_result = model_to_dto(data=exam, dto_cls=MpExamDTO)
    return ResponseUtil.success(data=dto_result)
```

**OpenAPI 文档效果**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "name": "科目一考试",
    "tag": "km1",
    "status": 0,
    "create_time": "2024-01-01T00:00:00"
  }
}
```

#### 示例 2：返回列表

```python
from typing import List
from utils.response_util import ResponseUtil, ResponseDTO
from module_exam.dto.mp_question_dto import MpQuestionOptionDTO

@router.post("/getQuestionList", response_model=ResponseDTO[List[MpQuestionOptionDTO]])
def get_question_list(exam_id: int = Body(...), db_session: Session = Depends(get_db_session)):
    result = MpQuestionService_instance.get_questions_with_options(db_session, exam_id)
    dto_result = model_to_dto(data=result, dto_cls=MpQuestionOptionDTO)
    return ResponseUtil.success(data=dto_result)
```

**OpenAPI 文档效果**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "question": {
        "id": 1,
        "name": "题目内容",
        "type": 1,
        "type_name": "单选题"
      },
      "options": [
        {"id": 1, "content": "选项A", "is_right": 1},
        {"id": 2, "content": "选项B", "is_right": 0}
      ]
    }
  ]
}
```

#### 示例 3：返回复杂嵌套结构

```python
from typing import Dict, Any
from utils.response_util import ResponseUtil, ResponseDTO

# 定义返回结构的 DTO
class SubmitResultDTO(BaseModel):
    user_exam_id: int
    right_num: int
    error_num: int
    finish_time: datetime

@router.post("/submit", response_model=ResponseDTO[SubmitResultDTO])
def submit_exam(...):
    # ... 业务逻辑 ...
    result = SubmitResultDTO(
        user_exam_id=user_exam_id,
        right_num=total_score,
        error_num=answered_count - total_score,
        finish_time=datetime.now()
    )
    return ResponseUtil.success(data=result)
```

---

## 错误响应统一处理

### 方式 1：在业务逻辑中返回错误

```python
@router.post("/submit", response_model=ResponseDTOBase)
def submit_exam(...):
    if not user_exam:
        return ResponseUtil.error(code=404, message="考试记录不存在")
    
    # 正常逻辑
    return ResponseUtil.success(data={...})
```

### 方式 2：抛出 HTTPException（推荐用于严重错误）

```python
from fastapi import HTTPException

@router.post("/submit")
def submit_exam(...):
    if not user_exam:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    
    return ResponseUtil.success(data={...})
```

然后在 `main.py` 中注册全局异常处理器，统一转换为 `{code, message, data}` 格式：

```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None
        }
    )
```

---

## 迁移建议

### 现有代码迁移步骤：

1. **第一步**：给所有路由加 `response_model=ResponseDTOBase`（保证文档有统一格式）
   ```python
   @router.post("/xxx", response_model=ResponseDTOBase)
   ```

2. **第二步**：对于返回固定结构的接口，逐步改用 `ResponseDTO[具体类型]`
   ```python
   @router.post("/getExamList", response_model=ResponseDTO[List[MpExamDTO]])
   ```

3. **第三步**（可选）：对于复杂返回结构，定义专门的 ResponseDTO
   ```python
   class ExamPaperResponseDTO(BaseModel):
       user_exam_id: int
       exam_id: int
       question_num: int
       question_list: List[MpQuestionOptionDTO]
   
   @router.post("/getExamPaper", response_model=ResponseDTO[ExamPaperResponseDTO])
   ```

---

## 常见问题

### Q1：为什么不直接返回 DTO，而要包一层 `{code, message, data}`？

**A**：这是国内项目的常见做法，优点：
- 前端统一处理逻辑（根据 `code` 判断）
- 业务错误和 HTTP 错误分离（HTTP 200 + code 400）
- 可以在 `data` 之外携带额外信息（如分页 `total`、`page_num`）

主流 FastAPI（尤其国外）更倾向 HTTP 状态码直接表达语义，但你这套也完全可行。

### Q2：`ResponseDTOBase` 和 `ResponseDTO[Any]` 有什么区别？

**A**：两者在运行时完全等价，都是 `data: Optional[Any]`。
- `ResponseDTOBase` 是为了简化导入（不用每次写 `[Any]`）
- 推荐用 `ResponseDTOBase`，更简洁

### Q3：如何让 HTTP 状态码和业务 `code` 同步？

**A**：修改 `ResponseUtil`：

```python
class ResponseUtil:
    @staticmethod
    def success(code=200, message="success", data=None):
        return ResponseDTO(code=code, message=message, data=data)
    
    @staticmethod
    def error(code=500, message="error", data=None):
        # 让 FastAPI 的 HTTP 状态码也变成 code
        from fastapi import Response
        response = Response(status_code=code)
        return ResponseDTO(code=code, message=message, data=data)
```

但更推荐：**业务错误用 code，系统错误用 HTTPException**。

---

## 总结

✅ **推荐做法**：
- 路由上加 `response_model=ResponseDTO[具体类型]` 或 `ResponseDTOBase`
- 函数内返回 `ResponseUtil.success(data=...)`
- 既保留统一格式，又有精确文档和类型安全

✅ **最佳实践**：
- 简单接口：`response_model=ResponseDTOBase`
- 返回 DTO 列表/对象：`response_model=ResponseDTO[List[XxxDTO]]`
- 复杂结构：定义专门的 ResponseDTO 类

✅ **与主流 FastAPI 的兼容性**：
- 完全兼容 OpenAPI 标准
- 保留类型提示和自动补全
- Swagger UI 文档清晰展示数据结构
