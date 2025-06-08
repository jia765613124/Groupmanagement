from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.pool import AsyncAdaptedQueuePool

from bot.config import get_config
from bot.models.base import Base

config = get_config()

# 创建异步引擎，添加连接池配置
engine = create_async_engine(
    str(config.MYSQL_DSN),
    echo=config.DEBUG,
    poolclass=AsyncAdaptedQueuePool,
    pool_pre_ping=True,  # 启用连接健康检查
    pool_recycle=3600,   # 1小时后回收连接
    pool_size=20,        # 连接池大小
    max_overflow=10,     # 最大额外连接数
    pool_timeout=30,  # 连接超时时间
)

# 创建会话工厂
SessionFactory = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession
)

async def init_db():
    """初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
