#!/usr/bin/env python
"""
重置签到数据工具
用于清除特定用户的签到记录，方便重新测试
"""

import asyncio
import datetime
from sqlalchemy import select, delete, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.models.sign_in_record import SignInRecord
from bot.models.account import Account
from bot.models.account_transaction import AccountTransaction
from bot.database.db import DATABASE_URL

# 创建异步引擎和会话
async_engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

async def reset_user_checkin_data(telegram_id: int, reset_points: bool = False):
    """重置用户签到数据"""
    print(f"正在重置用户 {telegram_id} 的签到数据...")
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. 删除签到记录
            result = await session.execute(
                delete(SignInRecord).where(SignInRecord.telegram_id == telegram_id)
            )
            deleted_count = result.rowcount
            print(f"删除了 {deleted_count} 条签到记录")
            
            # 2. 删除签到交易记录
            result = await session.execute(
                delete(AccountTransaction).where(
                    AccountTransaction.telegram_id == telegram_id,
                    AccountTransaction.transaction_type == 4  # 签到类型
                )
            )
            deleted_count = result.rowcount
            print(f"删除了 {deleted_count} 条签到交易记录")
            
            # 3. 重置积分（如果需要）
            if reset_points:
                # 获取用户积分账户
                point_account = await session.scalar(
                    select(Account).where(
                        Account.telegram_id == telegram_id,
                        Account.account_type == 1  # 积分账户
                    )
                )
                
                if point_account:
                    old_balance = point_account.available_amount
                    point_account.available_amount = 10000  # 重置为初始值
                    point_account.total_amount = 10000
                    print(f"重置积分账户余额: {old_balance} -> {point_account.available_amount}")
                else:
                    print("未找到积分账户")

async def reset_all_checkin_data():
    """重置所有签到数据（危险操作）"""
    print("警告：此操作将删除所有用户的签到记录！")
    confirm = input("输入 'YES' 确认: ")
    
    if confirm != 'YES':
        print("操作已取消")
        return
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. 删除所有签到记录
            result = await session.execute(delete(SignInRecord))
            deleted_count = result.rowcount
            print(f"删除了所有 {deleted_count} 条签到记录")
            
            # 2. 删除所有签到交易记录
            result = await session.execute(
                delete(AccountTransaction).where(
                    AccountTransaction.transaction_type == 4  # 签到类型
                )
            )
            deleted_count = result.rowcount
            print(f"删除了所有 {deleted_count} 条签到交易记录")

async def display_menu():
    """显示菜单"""
    print("\n=== 签到数据重置工具 ===")
    print("1. 重置特定用户的签到数据")
    print("2. 重置特定用户的签到数据并重置积分")
    print("3. 重置所有用户的签到数据（危险）")
    print("0. 退出")
    
    choice = input("\n请选择操作: ")
    
    if choice == '1':
        try:
            telegram_id = int(input("请输入用户的Telegram ID: "))
            await reset_user_checkin_data(telegram_id, reset_points=False)
            print("操作完成")
        except ValueError:
            print("无效的ID，请输入数字")
    
    elif choice == '2':
        try:
            telegram_id = int(input("请输入用户的Telegram ID: "))
            await reset_user_checkin_data(telegram_id, reset_points=True)
            print("操作完成")
        except ValueError:
            print("无效的ID，请输入数字")
    
    elif choice == '3':
        await reset_all_checkin_data()
    
    elif choice == '0':
        return False
    
    return True

async def main():
    """主函数"""
    continue_loop = True
    while continue_loop:
        continue_loop = await display_menu()
    
    print("程序已退出")

if __name__ == "__main__":
    asyncio.run(main()) 