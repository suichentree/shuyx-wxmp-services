# shuyx-wxmp-services

这是微信小程序的服务端代码，提供考试相关的接口服务，支持模拟考试、练习等功能。

## 技术栈

- **Web框架**: FastAPI
- **服务器**: Uvicorn
- **数据库**: MySQL
- **ORM**: SQLAlchemy 2.x
- **认证**: JWT
- **文档**: Swagger UI (自动生成)

## 项目结构

├── config/ # 配置文件目录 
│ ├── database_config.py # 数据库配置 
│ └── log_config.py # 日志配置 
├── middlewares/ # 中间件 
│ ├── auth_middleware.py # 认证中间件 
│ ├── exception_middleware.py # 异常处理中间件 
│ └── logger_middleware.py # 日志中间件 
├── module_exam/ # 考试模块 
│ ├── controller/ # 路由层 
│ ├── service/ # 业务逻辑层 
│ ├── dao/ # 数据访问层 
│ ├── model/ # ORM模型层 
│ └── dto/ # 数据传输对象 
├── utils/ # 工具类 
│ ├── conversion_util.py # 转换工具 
│ ├── jwt_util.py # JWT工具 
│ └── response_util.py # 响应工具 
├── main.py # 项目入口 
├── requirements.txt # 依赖声明 
└── README.md # 项目说明

## 分层架构

项目采用清晰的三层架构设计：

Controller (路由层) → Service (业务逻辑层) → DAO (数据访问层) → Model (ORM模型层)

✅ 清晰的三层架构，类似 Spring Boot 风格，适合中大型项目。

> 各层职责
- **Controller层**: 处理HTTP请求，参数验证，响应格式化
- **Service层**: 实现业务逻辑，事务管理
- **DAO层**: 数据库操作，通用CRUD封装
- **Model层**: 数据库表结构映射，ORM模型定义

## 快速开始

### 1. 依赖库 requirements.txt

> 如何生成requirements.txt？

```bash
# 通过该命令生成requirements.txt
pip freeze > requirements.txt

# 说明：
# 1. 该文件包含项目所有依赖库的版本信息，用于确保项目在不同环境中的一致性。
# 2. 建议在项目根目录下执行该命令，将所有直接依赖库及其子依赖库写入requirements.txt。
```

> 如何一次性安装所有依赖库？

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `config/database_config.py` 文件，配置数据库连接：

```python
MYSQL_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/shuyx_db"
```

### 3. 初始化数据库

#### 方式一：使用Alembic迁移工具（推荐）

```bash
# 初始化Alembic（首次使用）
alembic init alembic

# 生成初始迁移脚本
alembic revision --autogenerate -m "Initial database setup"

# 应用迁移
alembic upgrade head
```

#### 方式二：使用简单脚本（开发环境快速测试）

```bash
python update_db.py
```

### 4. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:39666` 启动

## 数据库管理

### 数据库迁移工具（Alembic）

#### 生成迁移脚本

当修改数据库模型后，执行以下命令生成迁移脚本：

```bash
alembic revision --autogenerate -m "描述变更内容"
```

#### 应用迁移

```bash
# 应用所有未应用的迁移
alembic upgrade head

# 应用指定数量的迁移
alembic upgrade +1
```

#### 回滚迁移

```bash
# 回滚上一个迁移
alembic downgrade -1

# 回滚到初始状态
alembic downgrade base
```

#### 查看迁移状态

```bash
# 查看当前迁移状态
alembic current

# 查看迁移历史
alembic history
```

## API文档

服务启动后，可通过以下地址访问自动生成的API文档：

- Swagger UI: `http://localhost:39666/docs`
- ReDoc: `http://localhost:39666/redoc`

## 开发规范

### 代码风格

- 使用PEP 8代码风格
- 函数和方法要有类型提示
- 接口要声明`response_model`，确保Swagger文档准确性

### 数据库操作规范

- 单个数据库操作可直接在DAO层提交
- 多个相关数据库操作应在Service层统一管理事务
- 避免在Controller层直接操作数据库

### 响应格式

所有API接口统一返回以下格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

- `code`: HTTP状态码或业务错误码
- `message`: 响应消息
- `data`: 响应数据

### 通用 CRUD 封装

#### BaseDao（数据访问基类）
- ✅ 泛型设计，支持所有 Model 复用
- ✅ 支持动态 filters、排序、分页
- `add/update/delete`方法支持事务控制

#### BaseService（业务逻辑基类）
- ✅ 透传 DAO 方法，统一 session 管理


### 统一响应格式 ResponseDTO + ResponseUtil

- `ResponseDTO`支持泛型，可声明精确类型
- 全局异常处理器，自动转换异常为统一格式
- 支持HTTP状态码与业务code同步

```python
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### DTO 使用方式

- ✅ 用 Pydantic BaseModel 定义 DTO
- ✅ `model_to_dto()` 手动校验 + 序列化

### 接口改进

- 补充`response_model`声明，提升Swagger文档质量
- 修复部分接口的事务管理问题
- 优化数据库查询性能

### 中间件支持

- 实现认证中间件，基于JWT验证
- 全局异常处理中间件
- 请求日志中间件

## 后续计划

### 阶段1：基础设施完善
- 完成所有接口的`response_model`补充
- 完善数据库迁移脚本管理
- 实现更细粒度的权限控制

### 阶段2：功能增强
- 增加考试统计分析功能
- 实现错题集和学习进度跟踪
- 优化用户体验和性能

### 阶段3：部署与监控
- 容器化部署支持（Docker）
- 增加API监控和日志分析
- 实现自动化测试

## 参考资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.x文档](https://docs.sqlalchemy.org/en/20/)
- [Alembic文档](https://alembic.sqlalchemy.org/en/latest/)
- [FastAPI最佳实践](https://github.com/zhanymkanov/fastapi-best-practices)

## 许可证

[MIT License](LICENSE)






