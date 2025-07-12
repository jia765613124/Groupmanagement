from typing import Annotated
from datetime import date, datetime
from sqlalchemy import String, Text, BigInteger, Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base
from bot.models.fields import bigint_pk, timestamp

class SignInRecord(Base):
    """签到记录模型"""
    __tablename__ = 'sign_in_records'
    
    # 主键ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 群组ID
    group_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # 用户ID
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    
    # Telegram用户ID
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    # 签到获得的积分
    points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # 连续签到天数
    continuous_days: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # 签到日期
    sign_date: Mapped[date] = mapped_column(Date, nullable=False)
    
    # 备注
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SignInRecord(id={self.id}, telegram_id={self.telegram_id}, sign_date={self.sign_date})>"
    
    @property
    def bonus_points(self):
        """获取连续签到奖励积分"""
        # 连续签到奖励规则：连续签到天数 * 1分
        # 可以根据实际需求调整奖励规则
        if self.continuous_days <= 1:
            return 0
        return self.continuous_days - 1

    @property
    def total_points(self):
        """获取总积分"""
        return self.points + self.bonus_points 