from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.crud.base import CRUDBase
from bot.models.sign_in_record import SignInRecord
from bot.models.tg_user_group import User
from bot.models.account import Account

class CRUDSignInRecord(CRUDBase[SignInRecord]):
    async def get_by_telegram_id_and_date(
        self, 
        session: AsyncSession, 
        telegram_id: int, 
        group_id: int, 
        sign_date: date
    ) -> SignInRecord | None:
        """
        根据Telegram ID和日期获取签到记录
        """
        stmt = select(self.model).where(
            self.model.telegram_id == telegram_id,
            self.model.group_id == group_id,
            self.model.sign_date == sign_date
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_telegram_id_and_date_any_group(
        self, 
        session: AsyncSession, 
        telegram_id: int, 
        sign_date: date
    ) -> SignInRecord | None:
        """
        根据Telegram ID和日期获取任意群组的签到记录
        """
        stmt = select(self.model).where(
            self.model.telegram_id == telegram_id,
            self.model.sign_date == sign_date
        ).limit(1)  # 只取第一条记录
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_yesterday_record(
        self,
        session: AsyncSession,
        telegram_id: int,
        group_id: int,
        today: date
    ) -> SignInRecord | None:
        """
        获取昨天的签到记录
        """
        yesterday = today - timedelta(days=1)
        return await self.get_by_telegram_id_and_date(
            session, telegram_id, group_id, yesterday
        )

    async def get_yesterday_record_any_group(
        self,
        session: AsyncSession,
        telegram_id: int,
        today: date
    ) -> SignInRecord | None:
        """
        获取昨天的签到记录（任意群组）
        """
        yesterday = today - timedelta(days=1)
        stmt = select(self.model).where(
            self.model.telegram_id == telegram_id,
            self.model.sign_date == yesterday
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def calculate_continuous_days(
        self,
        session: AsyncSession,
        telegram_id: int,
        group_id: int,
        today: date
    ) -> int:
        """
        计算连续签到天数
        """
        yesterday_record = await self.get_yesterday_record(
            session, telegram_id, group_id, today
        )
        
        if yesterday_record:
            return yesterday_record.continuous_days + 1
        return 1
    
    async def calculate_continuous_days_across_groups(
        self,
        session: AsyncSession,
        telegram_id: int,
        today: date
    ) -> int:
        """
        计算跨群组的连续签到天数
        """
        yesterday_record = await self.get_yesterday_record_any_group(
            session, telegram_id, today
        )
        
        if yesterday_record:
            return yesterday_record.continuous_days + 1
        return 1
    
    async def create_sign_in(
        self,
        session: AsyncSession,
        group_id: int,
        user_id: int,
        telegram_id: int,
        points: int,
        continuous_days: int,
        sign_date: date
    ) -> SignInRecord:
        """
        创建签到记录
        """
        sign_in_record = SignInRecord(
            group_id=group_id,
            user_id=user_id,
            telegram_id=telegram_id,
            points=points,
            continuous_days=continuous_days,
            sign_date=sign_date
        )
        session.add(sign_in_record)
        await session.flush()
        return sign_in_record


sign_in_record = CRUDSignInRecord(SignInRecord) 