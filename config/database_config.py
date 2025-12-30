# 导入sqlalchemy框架中的各个工具
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# mysql数据库的连接URL
MYSQL_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/shuyx_db"

# 创建数据库引擎myEngine
myEngine = create_engine(MYSQL_DATABASE_URL,
    pool_size=10,            # 连接池大小
    pool_timeout=30,        # 池中没有线程最多等待的时间，否则报错
    echo=False              # 是否在控制台打印相关语句等
    )

# 创建会话工厂对象mySessionLocal
mySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=myEngine, expire_on_commit=False)

# 创建统一数据库模型基类
class myBase(DeclarativeBase):
    pass

# 该函数每次通过会话工厂创建新的会话session对象。确保每个请求都有独立的会话。从而避免了并发访问同一个会话对象导致的事务冲突
def get_db_session():
    db_session = mySessionLocal()  #每次通过会话工厂创建新的会话session对象
    try:
        yield db_session
    except:
        db_session.rollback()
        raise
    finally:
        db_session.close()