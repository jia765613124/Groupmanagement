"""
开奖系统数据库模型
包含开奖记录、投注记录等
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, String, Numeric, Integer, SmallInteger, Boolean, Text, TIMESTAMP, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from bot.models.base import Base, timestamp, is_deleted
from bot.models.fields import bigint_pk, bigint_field


class LotteryDraw(Base):
    """开奖记录模型"""
    __tablename__ = "lottery_draws"

    id: Mapped[bigint_pk]
    group_id: Mapped[bigint_field] = mapped_column(comment="群组ID")
    game_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="游戏类型")
    draw_number: Mapped[str] = mapped_column(String(64), nullable=False, comment="期号")
    result: Mapped[int] = mapped_column(Integer, nullable=False, comment="开奖结果(0-9)")
    total_bets: Mapped[bigint_field] = mapped_column(default=0, comment="总投注金额")
    total_payout: Mapped[bigint_field] = mapped_column(default=0, comment="总派奖金额")
    profit: Mapped[bigint_field] = mapped_column(default=0, comment="盈亏金额")
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态(1:进行中 2:已开奖)")
    draw_time: Mapped[timestamp]
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    __table_args__ = (
        Index('idx_group_game', 'group_id', 'game_type'),
        Index('idx_draw_number', 'group_id', 'game_type', 'draw_number'),
        Index('idx_draw_time', 'draw_time'),
        Index('idx_status', 'status'),
        UniqueConstraint('group_id', 'game_type', 'draw_number', name='uk_group_game_draw'),
    )


class LotteryBet(Base):
    """投注记录模型"""
    __tablename__ = "lottery_bets"

    id: Mapped[bigint_pk]
    group_id: Mapped[bigint_field] = mapped_column(comment="群组ID")
    game_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="游戏类型")
    draw_number: Mapped[str] = mapped_column(String(64), nullable=False, comment="期号")
    telegram_id: Mapped[bigint_field]
    bet_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="投注类型")
    bet_amount: Mapped[bigint_field]
    odds: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="赔率")
    is_win: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="是否中奖")
    win_amount: Mapped[bigint_field] = mapped_column(default=0, comment="中奖金额")
    cashback_amount: Mapped[bigint_field] = mapped_column(default=0, comment="返水金额")
    cashback_claimed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, comment="返水是否已领取")
    cashback_expire_time: Mapped[timestamp]
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态(1:投注中 2:已开奖 3:已结算)")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    __table_args__ = (
        Index('idx_group_game', 'group_id', 'game_type'),
        Index('idx_draw_number', 'group_id', 'game_type', 'draw_number'),
        Index('idx_telegram_id', 'telegram_id'),
        Index('idx_bet_type', 'bet_type'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_cashback_expire', 'cashback_expire_time'),
        UniqueConstraint('group_id', 'game_type', 'draw_number', 'telegram_id', 'bet_type', name='uk_group_game_draw_user_bet'),
    )


class LotteryCashback(Base):
    """返水记录模型"""
    __tablename__ = "lottery_cashbacks"

    id: Mapped[bigint_pk]
    group_id: Mapped[bigint_field] = mapped_column(comment="群组ID")
    game_type: Mapped[str] = mapped_column(String(20), nullable=False, comment="游戏类型")
    bet_id: Mapped[bigint_field]
    telegram_id: Mapped[bigint_field]
    amount: Mapped[bigint_field]
    status: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, comment="状态(1:待领取 2:已领取)")
    claimed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True, comment="领取时间")
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="备注")

    __table_args__ = (
        Index('idx_group_game', 'group_id', 'game_type'),
        Index('idx_bet_id', 'bet_id'),
        Index('idx_telegram_id', 'telegram_id'),
        Index('idx_status', 'status'),
        Index('idx_created_at', 'created_at'),
    ) 