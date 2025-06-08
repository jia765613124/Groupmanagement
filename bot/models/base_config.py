from enum import Enum
from sqlalchemy import String, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base
from bot.models.fields import bigint_pk, varchar_field, text_field, enum_field, is_deleted, timestamp, deleted_at


class ConfigType(str, Enum):
    """配置类型枚举"""
    SYSTEM = 'system'
    BUSINESS = 'business'
    SECURITY = 'security'
    NOTIFICATION = 'notification'


class BaseConfig(Base):
    """基础配置表"""
    __tablename__ = 't_search_base_config'

    id: Mapped[bigint_pk]
    config_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment='配置键')
    config_value: Mapped[str | None] = mapped_column(Text, nullable=True, comment='配置值')
    config_type: Mapped[ConfigType] = mapped_column(SQLEnum(ConfigType), nullable=False, comment='配置类型')
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='描述')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1", comment='是否启用')
    created_at: Mapped[timestamp]
    updated_at: Mapped[timestamp]
    is_deleted: Mapped[is_deleted]
    deleted_at: Mapped[deleted_at] 