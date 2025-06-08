from typing import Annotated
from sqlalchemy import BigInteger, Text, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base, timestamp, is_deleted

class AccountTransaction(Base):
    """账户交易记录模型
    
    记录所有账户相关的交易，包括充值、消费、转账等操作
    """
    __tablename__ = "account_transactions"
    
    # 主键ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 账户ID
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    # 用户ID
    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    
    # Telegram用户ID
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    # 被邀请人Telegram ID
    invited_telegram_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    
    # 账户类型(1:积分账户 2:钱包账户)
    account_type: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
    
    # 交易类型(1:充值 2:消费 3:转账 4:签到奖励 5:活动奖励 6:冻结 7:解冻)
    transaction_type: Mapped[int] = mapped_column(SmallInteger, nullable=False, index=True)
    
    # 交易金额
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # 交易后余额
    balance: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # 来源ID
    source_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    
    # 群组ID
    group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    
    # 备注
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    __table_args__ = (
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4', 'mysql_collate': 'utf8mb4_general_ci'}
    ) 