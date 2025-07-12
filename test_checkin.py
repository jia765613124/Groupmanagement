#!/usr/bin/env python
"""
测试签到功能脚本
模拟特定用户签到，用于测试连续签到奖励机制
"""

import asyncio
import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.models.base import Base
from bot.models.tg_user_group import User
from bot.models.sign_in_record import SignInRecord
from bot.models.account import Account
from bot.models.account_transaction import AccountTransaction
from bot.database.db import DATABASE_URL
from bot.handlers.checkin_handler import CONTINUOUS_CHECKIN_RULES

# 创建异步引擎和会话
async_engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# 测试群组ID
TEST_GROUP_ID = -1002417673222

# 基础签到积分
BASE_POINTS = 100

async def simulate_checkin(telegram_id: int):
    """模拟用户签到"""
    print(f"模拟用户 {telegram_id} 签到...")
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. 获取用户
            user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
            if not user:
                print(f"用户 {telegram_id} 不存在")
                return
            
            print(f"用户: {user.first_name} (ID: {user.id})")
            
            # 2. 获取账户
            point_account = await session.scalar(
                select(Account).where(
                    Account.telegram_id == telegram_id,
                    Account.account_type == 1  # 积分账户
                )
            )
            
            if not point_account:
                print(f"用户 {telegram_id} 无积分账户")
                return
            
            old_balance = point_account.available_amount
            print(f"当前积分余额: {old_balance}")
            
            # 3. 检查今天是否已签到
            today = datetime.date.today()
            has_checked = await session.scalar(
                select(SignInRecord).where(
                    SignInRecord.telegram_id == telegram_id,
                    SignInRecord.sign_date == today
                )
            )
            
            if has_checked:
                print(f"用户今天已经签到过了")
                return
            
            # 4. 查找最近的签到记录，计算连续天数
            yesterday = today - datetime.timedelta(days=1)
            yesterday_record = await session.scalar(
                select(SignInRecord).where(
                    SignInRecord.telegram_id == telegram_id,
                    SignInRecord.sign_date == yesterday
                ).order_by(SignInRecord.id.desc())
            )
            
            continuous_days = 1
            if yesterday_record:
                continuous_days = yesterday_record.continuous_days + 1
            
            print(f"连续签到天数: {continuous_days}")
            
            # 5. 计算奖励积分
            bonus_points = 0
            bonus_description = ""
            
            # 查找符合条件的最高奖励等级
            for rule in sorted(CONTINUOUS_CHECKIN_RULES, key=lambda x: x["days"], reverse=True):
                if continuous_days == rule["days"]:
                    bonus_points = rule["bonus"]
                    bonus_description = rule["description"]
                    break
            
            # 6. 创建签到记录
            record = SignInRecord(
                group_id=TEST_GROUP_ID,
                user_id=user.id,
                telegram_id=telegram_id,
                points=BASE_POINTS,
                continuous_days=continuous_days,
                sign_date=today
            )
            session.add(record)
            await session.flush()
            
            # 7. 更新账户积分
            total_points = BASE_POINTS + record.bonus_points + bonus_points
            point_account.total_amount += total_points
            point_account.available_amount += total_points
            
            # 8. 创建交易记录
            transaction = AccountTransaction(
                account_id=point_account.id,
                user_id=user.id,
                telegram_id=telegram_id,
                account_type=1,  # 积分账户
                transaction_type=4,  # 签到奖励
                amount=total_points,
                balance=point_account.available_amount,
                group_id=TEST_GROUP_ID,
                remarks=f"签到奖励 (连续{continuous_days}天)"
            )
            session.add(transaction)
            
            # 9. 打印结果
            print("\n=== 签到结果 ===")
            print(f"基础积分: {BASE_POINTS}")
            
            if record.bonus_points > 0:
                print(f"连续签到奖励: {record.bonus_points}")
            
            if bonus_points > 0:
                print(f"特殊奖励: {bonus_points} ({bonus_description})")
            
            print(f"总奖励: {total_points}")
            print(f"新积分余额: {point_account.available_amount}")
            print(f"增加积分: {point_account.available_amount - old_balance}")

async def display_rules():
    """显示连续签到奖励规则"""
    print("\n=== 连续签到奖励规则 ===")
    for rule in sorted(CONTINUOUS_CHECKIN_RULES, key=lambda x: x["days"]):
        print(f"{rule['description']}: +{rule['bonus']} 积分")

async def main():
    """主函数"""
    print("=== 签到测试工具 ===")
    
    # 显示规则
    await display_rules()
    
    # 获取用户输入
    try:
        telegram_id = int(input("\n请输入要测试的用户Telegram ID: "))
        await simulate_checkin(telegram_id)
    except ValueError:
        print("无效的ID，请输入数字")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 