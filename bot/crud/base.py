"""
CRUD 基类模块

提供基本的数据库操作功能。
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from bot.common.service import Service
from bot.common.uow import UoW
from bot.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Service[ModelType], Generic[ModelType]):
    """
    CRUD 基类
    
    提供基本的 CRUD 操作功能。
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化 CRUD 类
        
        Args:
            model: SQLAlchemy 模型类
        """
        super().__init__()
        self.model = model

    async def get(self, session: AsyncSession, id: Any) -> Optional[ModelType]:
        """
        根据ID获取对象
        
        Args:
            session: 数据库会话
            id: 对象ID
            
        Returns:
            对象，如果不存在则返回None
        """
        stmt = select(self.model).where(self.model.id == id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_multi(
        self, session: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多个对象
        
        Args:
            session: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            对象列表
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, *, obj_in: Dict[str, Any]) -> ModelType:
        """
        创建新对象
        
        Args:
            session: 数据库会话
            obj_in: 对象数据
            
        Returns:
            创建的对象
        """
        db_obj = self.model(**obj_in)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
        self,
        session: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Union[Dict[str, Any], ModelType],
        exclude_fields: List[str] = None
    ) -> ModelType:
        """
        更新对象
        
        Args:
            session: 数据库会话
            db_obj: 数据库中的对象
            obj_in: 更新的数据
            exclude_fields: 排除不更新的字段列表
            
        Returns:
            更新后的对象
        """
        exclude_fields = exclude_fields or []
        
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
            
        for field in update_data:
            if field not in exclude_fields:
                setattr(db_obj, field, update_data[field])
                
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def remove(self, session: AsyncSession, *, id: int) -> ModelType:
        """
        删除对象
        
        Args:
            session: 数据库会话
            id: 对象ID
            
        Returns:
            删除的对象
        """
        obj = await self.get(session, id)
        await session.delete(obj)
        await session.commit()
        return obj

    async def exists(self, session: AsyncSession, **filters) -> bool:
        """
        检查记录是否存在
        
        Args:
            session: 数据库会话
            **filters: 过滤条件
            
        Returns:
            是否存在
        """
        obj = await self.get(session, **filters)
        return obj is not None 

    async def get_combined_results(
        self,
        session: AsyncSession,
        keyword: str,
        limit: int = 10,
        offset: int = 0
    ) -> tuple[List[dict], int]:
        """
        获取组合查询结果
        
        Args:
            session: 数据库会话
            keyword: 搜索关键词
            limit: 返回数量限制
            offset: 分页偏移量
            
        Returns:
            tuple: (结果列表, 总数)
        """
        # 构建组合查询
        combined_stmt = (
            select(
                self.model,
                func.row_number().over(
                    order_by=[
                        self.model.member_count.desc(),
                        self.model.last_activity_at.desc()
                    ]
                ).label('row_num')
            )
            .where(self.model.name.like(f'%{keyword}%'))
            .where(self.model.status == 'active')
            .where(self.model.is_deleted == False)
            .order_by(
                self.model.member_count.desc(),
                self.model.last_activity_at.desc()
            )
            .offset(offset)
            .limit(limit)
        )
        
        # 构建计数查询
        count_stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.name.like(f'%{keyword}%'))
            .where(self.model.status == 'active')
            .where(self.model.is_deleted == False)
        )
        
        # 执行查询
        result = await session.execute(combined_stmt)
        count_result = await session.execute(count_stmt)
        
        # 返回结果和总数
        items = result.scalars().all()
        total = count_result.scalar()
        
        return list(items), total 