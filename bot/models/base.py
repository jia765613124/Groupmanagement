from datetime import datetime
from typing import Annotated
from sqlalchemy import MetaData, func, DateTime, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from bot.models.fields import timestamp, is_deleted

# 创建元数据
metadata = MetaData()

class Base(AsyncAttrs, DeclarativeBase):
    """所有模型的基类
    
    提供通用的字段和方法
    """
    metadata = metadata

    __abstract__ = True  # 标记为抽象类，不会创建对应的表

    # 创建时间
    created_at: Mapped[timestamp]
    
    # 更新时间
    updated_at: Mapped[timestamp]
    
    # 删除时间
    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        nullable=True
    )
    
    # 是否删除
    is_deleted: Mapped[is_deleted]
