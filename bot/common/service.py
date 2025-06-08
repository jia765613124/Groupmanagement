import logging
from typing import Generic, Iterable, Sequence, TypeVar

from sqlalchemy import Select, UnaryExpression, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.base import ExecutableOption

from bot.models.base import Base

logger = logging.getLogger("Service")
TModel = TypeVar("TModel", bound=type[Base])


class Service(Generic[TModel]):
    """
    通用服务基类
    
    提供基础的数据库操作功能，包括查询、添加、更新和删除等操作。
    支持分页、排序和条件过滤。
    
    Generic:
        TModel: 数据库模型类型
    """
    
    model: TModel
    options: Iterable[ExecutableOption] | ExecutableOption | None

    def _build_get_query(
        self,
        *filters,
        limit: int | None = 1000,
        offset: int | None = None,
        options: Iterable[ExecutableOption] | ExecutableOption | None = None,
        stmt: Select | None = None,
        **filters_by,
    ) -> Select:
        """
        构建查询语句
        
        Args:
            *filters: 过滤条件
            limit: 返回结果的最大数量
            offset: 结果偏移量
            options: SQLAlchemy 查询选项
            stmt: 基础查询语句
            **filters_by: 关键字过滤条件
            
        Returns:
            构建好的查询语句
        """
        if offset is None:
            offset = 0

        if stmt is None:
            stmt = select(self.model)
        if not isinstance(stmt, Select):
            raise TypeError("stmt must be a Select object")

        logger.debug(f"Building query for {self.model.__name__}")

        if options:
            options = tuple(self.options)
        elif options is None:
            options = ()
        elif not isinstance(options, (Iterable, Sequence)):
            options = (options,)

        stmt = stmt.options(*options)

        if filters:
            stmt = stmt.filter(*filters)
        if filters_by:
            stmt = stmt.filter_by(**filters_by)

        if limit is not None and limit > 0:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)
        return stmt

    async def get_all(
        self,
        session: AsyncSession,
        *filters,
        limit: int | None = 1000,
        offset: int = 0,
        options: Iterable[ExecutableOption] | ExecutableOption | None | bool = None,
        order_by: UnaryExpression[TModel] | None = None,
        **filters_by,
    ) -> Sequence[TModel]:
        """
        获取所有符合条件的记录
        
        Args:
            session: 数据库会话
            *filters: 过滤条件
            limit: 返回结果的最大数量
            offset: 结果偏移量
            options: SQLAlchemy 查询选项
            order_by: 排序条件
            **filters_by: 关键字过滤条件
            
        Returns:
            符合条件的记录列表
        """
        if options is True:
            options = self.options
        stmt = self._build_get_query(
            *filters, limit=limit, offset=offset, options=options, **filters_by
        )
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        result = await session.execute(stmt)
        return result.unique().scalars().all()

    async def get_count(
        self,
        session: AsyncSession,
        *filters,
        **filters_by,
    ) -> int:
        """
        获取符合条件的记录数量
        
        Args:
            session: 数据库会话
            *filters: 过滤条件
            **filters_by: 关键字过滤条件
            
        Returns:
            记录数量
        """
        stmt = select(func.count(self.model.id))
        stmt = self._build_get_query(
            *filters, limit=None, offset=None, stmt=stmt, **filters_by
        )
        result = await session.execute(stmt)
        return result.scalar()

    async def get(
        self,
        session: AsyncSession,
        *filters,
        options: Iterable[ExecutableOption] | ExecutableOption | bool | None = None,
        **filters_by,
    ) -> TModel | None:
        """
        获取单条记录
        
        Args:
            session: 数据库会话
            *filters: 过滤条件
            options: SQLAlchemy 查询选项
            **filters_by: 关键字过滤条件
            
        Returns:
            符合条件的记录，如果没有则返回None
        """
        if options is True:
            options = self.options
        stmt = self._build_get_query(
            *filters, limit=1, options=options, **filters_by
        )
        result = await session.execute(stmt)
        return result.unique().scalars().first()

    async def get_for_update(
        self,
        session: AsyncSession,
        *filters,
        options: Iterable[ExecutableOption] | ExecutableOption | bool | None = None,
        **filters_by,
    ) -> TModel | None:
        """
        获取单条记录并锁定（用于更新）
        
        Args:
            session: 数据库会话
            *filters: 过滤条件
            options: SQLAlchemy 查询选项
            **filters_by: 关键字过滤条件
            
        Returns:
            符合条件的记录，如果没有则返回None
        """
        if options is True:
            options = self.options
        stmt = self._build_get_query(
            *filters, limit=None, offset=None, options=options, **filters_by
        )
        result = await session.execute(stmt.with_for_update())
        return result.scalar_one_or_none()

    async def add(self, session: AsyncSession, **kwargs) -> TModel:
        """
        添加新记录
        
        Args:
            session: 数据库会话
            **kwargs: 记录属性
            
        Returns:
            新创建的记录
        """
        user_app = self.model(**kwargs)
        session.add(user_app)

        return user_app

    async def update(self, session: AsyncSession, obj: TModel, **kwargs) -> TModel:
        """
        更新记录
        
        Args:
            session: 数据库会话
            obj: 要更新的记录
            **kwargs: 要更新的属性
            
        Returns:
            更新后的记录
        """
        for key, value in kwargs.items():
            setattr(obj, key, value)

        return obj

    async def delete(self, session: AsyncSession, obj: TModel) -> None:
        """
        删除记录
        
        Args:
            session: 数据库会话
            obj: 要删除的记录
        """
        await session.delete(obj)

    def asc(self, column_name: str) -> UnaryExpression[TModel]:
        """
        创建升序排序表达式
        
        Args:
            column_name: 列名
            
        Returns:
            升序排序表达式
        """
        if not getattr(self.model, column_name):
            raise ValueError(f"Column {column_name} not found in model {self.model}")
        return asc(getattr(self.model, column_name))

    def desc(self, column_name: str) -> UnaryExpression[TModel]:
        """
        创建降序排序表达式
        
        Args:
            column_name: 列名
            
        Returns:
            降序排序表达式
        """
        if not getattr(self.model, column_name):
            raise ValueError(f"Column {column_name} not found in model {self.model}")
        return desc(getattr(self.model, column_name))
