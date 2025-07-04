"""
开奖系统CRUD操作
包含开奖记录、投注记录、返水记录的数据访问层
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from bot.crud.base import CRUDBase
from bot.models.lottery import LotteryDraw, LotteryBet, LotteryCashback


class lottery_draw(CRUDBase[LotteryDraw]):
    """开奖记录CRUD (异步)"""
    
    async def get_by_draw_number(self, session: AsyncSession, game_type: str, draw_number: str) -> Optional[LotteryDraw]:
        stmt = select(LotteryDraw).where(
            LotteryDraw.game_type == game_type,
            LotteryDraw.draw_number == draw_number
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_current_draw(self, session: AsyncSession, group_id: int, game_type: str) -> Optional[LotteryDraw]:
        stmt = select(LotteryDraw).where(
            LotteryDraw.group_id == group_id,
            LotteryDraw.game_type == game_type,
            LotteryDraw.status == 1
        ).order_by(LotteryDraw.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_recent_draws(self, session: AsyncSession, group_id: int, game_type: str, limit: int = 10) -> List[LotteryDraw]:
        stmt = select(LotteryDraw).where(
            LotteryDraw.group_id == group_id,
            LotteryDraw.game_type == game_type,
            LotteryDraw.status == 2
        ).order_by(LotteryDraw.draw_time.desc()).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_recent_draws_all_groups(self, session: AsyncSession, game_type: str, limit: int = 10) -> List[LotteryDraw]:
        """获取所有群组的最近开奖记录"""
        stmt = select(LotteryDraw).where(
            LotteryDraw.game_type == game_type,
            LotteryDraw.status == 2
        ).order_by(LotteryDraw.draw_time.desc()).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_draws_by_date_range(self, session: AsyncSession, group_id: int, game_type: str, start_date: datetime, end_date: datetime) -> List[LotteryDraw]:
        stmt = select(LotteryDraw).where(
            LotteryDraw.group_id == group_id,
            LotteryDraw.game_type == game_type,
            LotteryDraw.draw_time >= start_date,
            LotteryDraw.draw_time <= end_date
        ).order_by(LotteryDraw.draw_time.desc())
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_statistics(self, session: AsyncSession, group_id: int, game_type: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        stmt = select(
            func.count(LotteryDraw.id).label('total_draws'),
            func.sum(LotteryDraw.total_bets).label('total_bets'),
            func.sum(LotteryDraw.total_payout).label('total_payout'),
            func.sum(LotteryDraw.profit).label('total_profit')
        ).where(
            LotteryDraw.group_id == group_id,
            LotteryDraw.game_type == game_type,
            LotteryDraw.draw_time >= start_date,
            LotteryDraw.draw_time <= end_date,
            LotteryDraw.status == 2
        )
        result = await session.execute(stmt)
        row = result.first()
        return {
            'total_draws': row.total_draws or 0,
            'total_bets': row.total_bets or 0,
            'total_payout': row.total_payout or 0,
            'total_profit': row.total_profit or 0
        }


class lottery_bet(CRUDBase[LotteryBet]):
    """投注记录CRUD (异步)"""
    
    async def get_by_draw_number(self, session: AsyncSession, group_id: int, game_type: str, draw_number: str) -> List[LotteryBet]:
        stmt = select(LotteryBet).where(
            LotteryBet.group_id == group_id,
            LotteryBet.game_type == game_type,
            LotteryBet.draw_number == draw_number
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_telegram_id(self, session: AsyncSession, telegram_id: int, group_id: int = None, limit: int = 50) -> List[LotteryBet]:
        stmt = select(LotteryBet).where(LotteryBet.telegram_id == telegram_id)
        if group_id:
            stmt = stmt.where(LotteryBet.group_id == group_id)
        stmt = stmt.order_by(LotteryBet.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_telegram_id_paginated(self, session: AsyncSession, telegram_id: int, skip: int = 0, limit: int = 10) -> List[LotteryBet]:
        """获取用户投注记录（支持分页）"""
        stmt = select(LotteryBet).where(LotteryBet.telegram_id == telegram_id)
        stmt = stmt.order_by(LotteryBet.created_at.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_telegram_id_count(self, session: AsyncSession, telegram_id: int) -> int:
        """获取用户投注记录总数"""
        stmt = select(func.count(LotteryBet.id)).where(LotteryBet.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar() or 0
    
    async def get_by_draw_and_telegram(self, session: AsyncSession, group_id: int, game_type: str, draw_number: str, telegram_id: int) -> List[LotteryBet]:
        stmt = select(LotteryBet).where(
            LotteryBet.group_id == group_id,
            LotteryBet.game_type == game_type,
            LotteryBet.draw_number == draw_number,
            LotteryBet.telegram_id == telegram_id
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_total_bets_by_draw(self, session: AsyncSession, group_id: int, game_type: str, draw_number: str) -> int:
        stmt = select(func.sum(LotteryBet.bet_amount)).where(
            LotteryBet.group_id == group_id,
            LotteryBet.game_type == game_type,
            LotteryBet.draw_number == draw_number
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
    
    async def get_total_payout_by_draw(self, session: AsyncSession, group_id: int, game_type: str, draw_number: str) -> int:
        stmt = select(func.sum(LotteryBet.win_amount)).where(
            LotteryBet.group_id == group_id,
            LotteryBet.game_type == game_type,
            LotteryBet.draw_number == draw_number,
            LotteryBet.is_win == True
        )
        result = await session.execute(stmt)
        return result.scalar() or 0
    
    async def get_user_statistics(self, session: AsyncSession, telegram_id: int, group_id: int = None) -> Dict[str, Any]:
        stmt = select(
            func.count(LotteryBet.id).label('total_bets'),
            func.sum(LotteryBet.bet_amount).label('total_bet_amount'),
            func.sum(LotteryBet.win_amount).label('total_win_amount'),
            func.sum(LotteryBet.cashback_amount).label('total_cashback_amount')
        ).where(LotteryBet.telegram_id == telegram_id)
        if group_id:
            stmt = stmt.where(LotteryBet.group_id == group_id)
        result = await session.execute(stmt)
        row = result.first()
        return {
            'total_bets': row.total_bets or 0,
            'total_bet_amount': row.total_bet_amount or 0,
            'total_win_amount': row.total_win_amount or 0,
            'total_cashback_amount': row.total_cashback_amount or 0
        }
    
    async def get_unclaimed_cashback(self, session: AsyncSession, telegram_id: int, group_id: int = None) -> List[LotteryBet]:
        stmt = select(LotteryBet).where(
            LotteryBet.telegram_id == telegram_id,
            LotteryBet.cashback_claimed == False,
            LotteryBet.cashback_expire_time > datetime.now()
        )
        if group_id:
            stmt = stmt.where(LotteryBet.group_id == group_id)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_expired_cashback(self, session: AsyncSession) -> List[LotteryBet]:
        stmt = select(LotteryBet).where(
            LotteryBet.cashback_claimed == False,
            LotteryBet.cashback_expire_time <= datetime.now()
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_user_draw_bet_type(self, session: AsyncSession, group_id: int, draw_number: str, telegram_id: int, bet_type: str) -> Optional[LotteryBet]:
        """检查用户是否已经对特定投注类型下过注"""
        stmt = select(LotteryBet).where(
            LotteryBet.group_id == group_id,
            LotteryBet.draw_number == draw_number,
            LotteryBet.telegram_id == telegram_id,
            LotteryBet.bet_type == bet_type
        )
        result = await session.execute(stmt)
        return result.scalars().first()


class lottery_cashback(CRUDBase[LotteryCashback]):
    """返水记录CRUD (异步)"""
    
    async def get_by_telegram_id(self, session: AsyncSession, telegram_id: int, group_id: int = None, limit: int = 50) -> List[LotteryCashback]:
        stmt = select(LotteryCashback).where(LotteryCashback.telegram_id == telegram_id)
        if group_id:
            stmt = stmt.where(LotteryCashback.group_id == group_id)
        stmt = stmt.order_by(LotteryCashback.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_unclaimed_by_telegram_id(self, session: AsyncSession, telegram_id: int, group_id: int = None) -> List[LotteryCashback]:
        stmt = select(LotteryCashback).where(
            LotteryCashback.telegram_id == telegram_id,
            LotteryCashback.status == 1
        )
        if group_id:
            stmt = stmt.where(LotteryCashback.group_id == group_id)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_total_unclaimed_amount(self, session: AsyncSession, telegram_id: int, group_id: int = None) -> int:
        stmt = select(func.sum(LotteryCashback.amount)).where(
            LotteryCashback.telegram_id == telegram_id,
            LotteryCashback.status == 1
        )
        if group_id:
            stmt = stmt.where(LotteryCashback.group_id == group_id)
        result = await session.execute(stmt)
        return result.scalar() or 0


# 创建CRUD实例
lottery_draw = lottery_draw(LotteryDraw)
lottery_bet = lottery_bet(LotteryBet)
lottery_cashback = lottery_cashback(LotteryCashback) 