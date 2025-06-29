from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

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

    async def get_by_telegram_id_and_types(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        account_type: int,
        transaction_types: List[int],
        skip: int = 0,
        limit: int = 100
    ) -> list[AccountTransaction]:
        """根据Telegram ID、账户类型和交易类型列表获取交易记录"""
        stmt = select(AccountTransaction).where(
            AccountTransaction.telegram_id == telegram_id,
            AccountTransaction.account_type == account_type,
            AccountTransaction.transaction_type.in_(transaction_types)
        ).order_by(AccountTransaction.id.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_telegram_id(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        account_type: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[AccountTransaction]:
        """根据Telegram ID获取交易记录"""
        conditions = [AccountTransaction.telegram_id == telegram_id]
        if account_type is not None:
            conditions.append(AccountTransaction.account_type == account_type)
        
        stmt = select(AccountTransaction).where(*conditions).order_by(
            AccountTransaction.id.desc()
        ).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_fishing_transactions(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> list[AccountTransaction]:
        """获取钓鱼相关的交易记录"""
        # 钓鱼相关的交易类型
        fishing_types = [20, 21, 22]  # 钓鱼费用、钓鱼奖励、传说鱼奖励
        
        return await self.get_by_telegram_id_and_types(
            session=session,
            telegram_id=telegram_id,
            account_type=1,  # 积分账户
            transaction_types=fishing_types,
            skip=skip,
            limit=limit
        )

    async def get_fishing_transactions_count(
        self,
        session: AsyncSession,
        *,
        telegram_id: int
    ) -> int:
        """获取钓鱼相关的交易记录总数"""
        stmt = select(func.count(AccountTransaction.id)).where(
            AccountTransaction.telegram_id == telegram_id,
            AccountTransaction.account_type == 1,  # 积分账户
            AccountTransaction.transaction_type.in_([20, 21, 22])
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

account_transaction = CRUDAccountTransaction(AccountTransaction) 