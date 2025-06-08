from typing import Annotated
import uuid

from sqlalchemy import String, BigInteger, Integer, Boolean, Text, Enum, DateTime, TIMESTAMP, text
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func


# UUID 主键字段类型
# 使用 UUID() 作为默认值
uuid_pk = Annotated[
    str,
    mapped_column(
        String(36),  # 字符串长度 36
        primary_key=True,  # 主键
        unique=True,  # 唯一
        server_default=text("UUID()"),  # 数据库默认值
    ),
]


# 聊天 ID 字段类型
# 使用 BigInteger 存储大整数
chat_id_bigint = Annotated[int, mapped_column(BigInteger(), unique=True)]

# 主键字段类型
bigint_pk = Annotated[int, mapped_column(BigInteger(), primary_key=True, autoincrement=True)]

# 时间戳字段类型
timestamp = Annotated[DateTime, mapped_column(
    TIMESTAMP,
    server_default=func.current_timestamp(),
    onupdate=func.current_timestamp()
)]

# 创建时间字段类型
created_at = Annotated[DateTime, mapped_column(
    TIMESTAMP,
    server_default=func.current_timestamp()
)]

# 更新时间字段类型
updated_at = Annotated[DateTime, mapped_column(
    TIMESTAMP,
    server_default=func.current_timestamp(),
    onupdate=func.current_timestamp()
)]

# 删除时间字段类型
deleted_at = Annotated[DateTime | None, mapped_column(
    TIMESTAMP,
    nullable=True
)]

# 软删除字段类型
is_deleted = Annotated[bool, mapped_column(Boolean, default=False, server_default="0")]

# 状态字段类型
status_tinyint = Annotated[int, mapped_column(Integer, default=1, server_default="1")]

# 文本字段类型
text_field = Annotated[str, mapped_column(Text, nullable=True)]

# 枚举字段类型
def enum_field(enum_type):
    return Annotated[str, mapped_column(Enum(enum_type), nullable=False)]

# 大整数字段类型
bigint_field = Annotated[int, mapped_column(BigInteger, nullable=False)]

# 字符串字段类型
def varchar_field(length: int, nullable: bool = False):
    return Annotated[str, mapped_column(String(length), nullable=nullable)]
