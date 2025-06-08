from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, String, Numeric, Integer, SmallInteger, Boolean, Text, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base


class RechargeOrder(Base):
    """充值订单模型"""
    __tablename__ = "recharge_orders"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    order_no: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, comment="订单编号")
    group_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="群组ID")
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, comment="用户ID")
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="Telegram用户ID")
    amount: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, comment="充值金额")
    coin_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="币种类型(USDT_TRC20/USDT_ERC20)")
    points: Mapped[int] = mapped_column(Integer, nullable=False, comment="可获得积分")
    bonus_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="奖励积分")
    address: Mapped[str] = mapped_column(String(100), nullable=False, comment="收款地址")
    tx_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, unique=True, comment="交易哈希")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态(1:待支付 2:支付中 3:已完成 4:已取消 5:异常)")
    expire_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, comment="订单过期时间")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否删除(0:未删除 1:已删除)")
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now, comment="创建时间")
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now, onupdate=datetime.now, comment="更新时间")
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, comment="删除时间")

    # 定义索引
    __table_args__ = (
        UniqueConstraint('order_no', name='uk_order_no'),
        UniqueConstraint('tx_hash', name='uk_tx_hash'),
        Index('idx_user_id', 'user_id'),
        Index('idx_telegram_id', 'telegram_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_is_deleted', 'is_deleted'),
    )

    # 订单状态枚举
    class Status:
        PENDING = 1    # 待支付
        PROCESSING = 2 # 支付中
        COMPLETED = 3  # 已完成
        CANCELLED = 4  # 已取消
        ERROR = 5      # 异常

    # 币种类型枚举
    class CoinType:
        USDT_TRC20 = "USDT_TRC20"
        USDT_ERC20 = "USDT_ERC20"

    def __repr__(self) -> str:
        return f"<RechargeOrder(id={self.id}, order_no='{self.order_no}', amount={self.amount}, status={self.status})>" 