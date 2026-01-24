# 导入sqlalchemy框架中的各个工具
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# mysql数据库的连接URL

# 本地环境访问本地数据库时的连接
# MYSQL_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/shuyx_db"

# 本地环境访问远程数据库时的连接（可以在本地环境进行数据库迁移时使用）
# MYSQL_DATABASE_URL = "mysql+pymysql://xdj_db:jpeNZcdnDBXCR2aA@114.66.42.205:33307/xdj_db?charset=utf8mb4"

# 本地容器访问本地数据库的连接
# host.docker.internal是Docker提供的特殊DNS，自动解析到宿主机IP
MYSQL_DATABASE_URL = "mysql+pymysql://root:123456@host.docker.internal:3306/shuyx_db?charset=utf8mb4"

# 项目部署到远程docker容器时访问远程数据库容器时的连接 172.18.0.2是mysql容器的ip地址。注意需要在同一个docker网络下，xdj_mysql才代表mysql容器。
# MYSQL_DATABASE_URL = "mysql+pymysql://xdj_db:jpeNZcdnDBXCR2aA@xdj_mysql:3306/xdj_db?charset=utf8mb4"


# 创建数据库引擎myEngine
myEngine = create_engine(MYSQL_DATABASE_URL,
    pool_size=10,            # 连接池大小
    pool_timeout=30,        # 池中没有线程最多等待的时间，否则报错
    echo=False              # 是否在控制台打印相关语句等
    )

# 创建会话工厂对象mySessionLocal
mySessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=myEngine, expire_on_commit=False)

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