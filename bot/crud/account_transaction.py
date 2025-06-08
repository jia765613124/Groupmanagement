from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.crud.base import CRUDBase
from bot.models.account_transaction import AccountTransaction

class CRUDAccountTransaction(CRUDBase[AccountTransaction]):
    async def create(
        self,
        session: AsyncSession,
        *,
        account_id: int,
        telegram_id: int,
        account_type: int,
        transaction_type: int,
        amount: int,
        balance: int,
        user_id: Optional[int] = None,
        invited_telegram_id: Optional[int] = None,
        source_id: Optional[str] = None,
        group_id: Optional[int] = None,
        remarks: Optional[str] = None
    ) -> AccountTransaction:
        """创建交易记录"""
        transaction_data = {
            "account_id": account_id,
            "user_id": user_id,
            "telegram_id": telegram_id,
            "invited_telegram_id": invited_telegram_id,
            "account_type": account_type,
            "transaction_type": transaction_type,
            "amount": amount,
            "balance": balance,
            "source_id": source_id,
            "group_id": group_id,
            "remarks": remarks
        }
        return await super().create(session=session, obj_in=transaction_data)

    async def get_by_account_id(
        self,
        session: AsyncSession,
        *,
        account_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[AccountTransaction]:
        """获取账户的交易记录"""
        stmt = select(AccountTransaction).where(
            AccountTransaction.account_id == account_id
        ).order_by(AccountTransaction.id.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

account_transaction = CRUDAccountTransaction(AccountTransaction) 