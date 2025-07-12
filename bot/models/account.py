from typing import Annotated
from sqlalchemy import BigInteger, Text, SmallInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base, timestamp, is_deleted

class Account(Base):
    """账户模型
    
    存储用户的账户信息，包括积分账户和钱包账户
    """
    __tablename__ = "accounts"
    
    # 主键ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 用户ID
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    
    # Telegram用户ID
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    # 账户类型(1:积分账户 2:钱包账户)
    account_type: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
    
    # 总金额
    total_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    # 可用金额
    available_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    # 冻结金额
    frozen_amount: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    
    # 状态(1:正常 2:冻结)
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, index=True)
    
    # 备注
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 关联用户
    user = relationship("User", back_populates="accounts")
    
    __table_args__ = (
        # 唯一索引：telegram_id + account_type
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}
    ) 