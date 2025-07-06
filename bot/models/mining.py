"""
挖矿系统数据库模型
包含矿工卡记录、挖矿奖励记录等
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, String, Numeric, Integer, SmallInteger, Boolean, Text, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base, timestamp, is_deleted
from bot.models.fields import bigint_pk, bigint_field


class MiningCard(Base):
    """矿工卡记录模型"""
    __tablename__ = "mining_cards"

    id: Mapped[bigint_pk]
    telegram_id: Mapped[bigint_field]
    card_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="矿工卡类型(青铜/白银/黄金/钻石)")
    cost_usdt: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="购买价格(USDT，单位：0.0001U)")
    daily_points: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="每日挖矿积分")
    total_days: Mapped[int] = mapped_column(Integer, nullable=False, comment="总挖矿天数")
    remaining_days: Mapped[int] = mapped_column(Integer, nullable=False, comment="剩余挖矿天数")
    total_points: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="总可获得积分")
    earned_points: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="已获得积分")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态(1:挖矿中 2:已完成 3:已过期)")
    start_time: Mapped[timestamp]
    end_time: Mapped[timestamp]
    last_reward_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, comment="最后奖励时间")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    __table_args__ = (
        Index('idx_telegram_id', 'telegram_id'),
        Index('idx_card_type', 'card_type'),
        Index('idx_status', 'status'),
        Index('idx_start_time', 'start_time'),
        Index('idx_end_time', 'end_time'),
        Index('idx_last_reward_time', 'last_reward_time'),
        Index('idx_telegram_card_type', 'telegram_id', 'card_type'),
    )


class MiningReward(Base):
    """挖矿奖励记录模型"""
    __tablename__ = "mining_rewards"

    id: Mapped[bigint_pk]
    mining_card_id: Mapped[bigint_field] = mapped_column(comment="矿工卡ID")
    telegram_id: Mapped[bigint_field]
    card_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="矿工卡类型")
    reward_points: Mapped[int] = mapped_column(BigInteger, nullable=False, comment="奖励积分")
    reward_day: Mapped[int] = mapped_column(Integer, nullable=False, comment="奖励天数(第几天)")
    reward_date: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, comment="奖励日期")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态(1:待领取 2:已领取)")
    claimed_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, comment="领取时间")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    __table_args__ = (
        Index('idx_mining_card_id', 'mining_card_id'),
        Index('idx_telegram_id', 'telegram_id'),
        Index('idx_card_type', 'card_type'),
        Index('idx_status', 'status'),
        Index('idx_reward_date', 'reward_date'),
        Index('idx_claimed_time', 'claimed_time'),
        Index('idx_telegram_status', 'telegram_id', 'status'),
    )


class MiningStatistics(Base):
    """挖矿统计模型"""
    __tablename__ = "mining_statistics"

    id: Mapped[bigint_pk]
    telegram_id: Mapped[bigint_field]
    total_cards_purchased: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="总购买矿工卡数量")
    total_cost_usdt: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="总花费USDT(单位：0.0001U)")
    total_earned_points: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, comment="总获得积分")
    bronze_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="青铜矿工卡数量")
    silver_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="白银矿工卡数量")
    gold_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="黄金矿工卡数量")
    diamond_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="钻石矿工卡数量")
    last_mining_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, comment="最后挖矿时间")
    created_at: Mapped[timestamp]
    updated_at: Mapped[timestamp]

    __table_args__ = (
        Index('idx_telegram_id', 'telegram_id'),
        Index('idx_last_mining_time', 'last_mining_time'),
        UniqueConstraint('telegram_id', name='uk_telegram_id'),
    ) 