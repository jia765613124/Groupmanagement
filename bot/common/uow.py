from typing import Self
from sqlalchemy.ext.asyncio import AsyncSession


class UoW:
    """
    工作单元（Unit of Work）模式实现类
    
    用于管理数据库事务，提供事务的提交、回滚和关闭功能。
    支持上下文管理器协议，可以自动处理事务的提交和回滚。
    """
    
    def __init__(self: Self, session: AsyncSession):
        """
        初始化工作单元
        
        Args:
            session: SQLAlchemy 异步会话对象
        """
        self.session = session

    async def commit(self):
        """
        提交当前事务
        
       将当前事务中的所有更改永久保存到数据库中。
       """
        await self.session.commit()

    async def rollback(self):
        """
        回滚当前事务
        
        撤销当前事务中的所有更改，恢复到事务开始前的状态。
        """
        await self.session.rollback()

    async def close(self):
        """
        关闭数据库会话
        
        释放数据库连接资源。
        """
        await self.session.close()

    async def __aenter__(self) -> Self:
        """
        异步上下文管理器入口
        
        Returns:
            当前工作单元实例
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        
        根据是否有异常决定提交或回滚事务，并关闭会话。
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常追踪信息
        """
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        await self.close()
