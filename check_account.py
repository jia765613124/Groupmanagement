import asyncio
from bot.database.db import SessionFactory
from bot.crud.account import account as account_crud
from bot.crud.account_transaction import account_transaction
from sqlalchemy import select
from bot.models.account import Account
from bot.models.account_transaction import AccountTransaction

async def check_user_account():
    print("检查用户账户...")
    
    async with SessionFactory() as session:
        # 指定用户ID
        telegram_id = 6657123296  # 请替换为您的实际ID
        
        # 获取用户账户
        accounts = await account_crud.get_by_telegram_id(session, telegram_id)
        
        print(f"用户 {telegram_id} 有 {len(accounts)} 个账户:")
        
        for account in accounts:
            account_type_text = "积分账户" if account.account_type == 1 else "钱包账户" if account.account_type == 2 else f"其他账户({account.account_type})"
            
            if account.account_type == 1:  # 积分账户
                balance = account.available_amount
                print(f"积分账户余额: {balance:,} 积分")
            elif account.account_type == 2:  # 钱包账户
                balance = account.available_amount / 1000000
                print(f"钱包账户余额: {balance:.2f}U")
            else:
                balance = account.available_amount
                print(f"{account_type_text}余额: {balance}")
            
            print(f"  账户ID: {account.id}")
            print(f"  总金额: {account.total_amount}, 可用金额: {account.available_amount}, 冻结金额: {account.frozen_amount}")
            print(f"  状态: {account.status}, 备注: {account.remarks}")
            print()
        
        # 获取用户交易记录
        stmt = select(AccountTransaction).where(
            AccountTransaction.telegram_id == telegram_id
        ).order_by(AccountTransaction.created_at.desc()).limit(10)
        
        result = await session.execute(stmt)
        transactions = result.scalars().all()
        
        print(f"用户 {telegram_id} 最近 {len(transactions)} 笔交易:")
        
        for tx in transactions:
            account_type_text = "积分账户" if tx.account_type == 1 else "钱包账户" if tx.account_type == 2 else f"其他账户({tx.account_type})"
            tx_type_text = "挖矿奖励" if tx.transaction_type == 41 else "购买矿工卡" if tx.transaction_type == 40 else f"其他交易({tx.transaction_type})"
            
            if tx.account_type == 1:  # 积分账户
                amount = tx.amount
                balance = tx.balance
                print(f"{tx_type_text}: {amount:+,} 积分, 余额: {balance:,} 积分")
            elif tx.account_type == 2:  # 钱包账户
                amount = tx.amount / 1000000
                balance = tx.balance / 1000000
                print(f"{tx_type_text}: {amount:+.2f}U, 余额: {balance:.2f}U")
            else:
                amount = tx.amount
                balance = tx.balance
                print(f"{tx_type_text}: {amount:+}, 余额: {balance}")
            
            print(f"  交易ID: {tx.id}, 账户类型: {account_type_text}")
            print(f"  时间: {tx.created_at}, 备注: {tx.remarks}")
            print()

if __name__ == "__main__":
    asyncio.run(check_user_account()) 