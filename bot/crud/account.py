from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.crud.base import CRUDBase
from bot.models.account import Account


class CRUDAccount(CRUDBase[Account]):
    async def get_by_telegram_id_and_type(self, session: AsyncSession, telegram_id: int, account_type: int) -> Account | None:
        """
        根据 Telegram ID 和账户类型获取账户
        """
        stmt = select(self.model).where(self.model.telegram_id == telegram_id, self.model.account_type == account_type)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_telegram_id(self, session: AsyncSession, telegram_id: int) -> list[Account]:
        """
        根据 Telegram ID 获取所有账户
        """
        # Assuming telegram_id is indexed and you want all accounts for that user
        stmt = select(self.model).where(self.model.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return list(result.scalars().all())


account = CRUDAccount(Account) 