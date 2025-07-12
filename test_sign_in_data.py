#!/usr/bin/env python
"""
测试数据生成脚本：连续签到奖励测试
创建多个测试用户，每个用户具有不同的连续签到天数
"""

import asyncio
import datetime
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from bot.models.base import Base
from bot.models.tg_user_group import User
from bot.models.sign_in_record import SignInRecord
from bot.models.account import Account
from bot.database.db import DATABASE_URL

# 创建异步引擎和会话
async_engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)

# 测试用户配置 (telegram_id, 连续签到天数)
TEST_USERS = [
    {"telegram_id": 10000001, "days": 2, "name": "测试用户1"},
    {"telegram_id": 10000002, "days": 3, "name": "测试用户2"},  # 连续签到3天奖励
    {"telegram_id": 10000003, "days": 7, "name": "测试用户3"},  # 连续签到7天奖励
    {"telegram_id": 10000004, "days": 14, "name": "测试用户4"}, # 连续签到14天奖励
    {"telegram_id": 10000005, "days": 21, "name": "测试用户5"}, # 连续签到21天奖励
    {"telegram_id": 10000006, "days": 30, "name": "测试用户6"}, # 连续签到1个月奖励
    {"telegram_id": 10000007, "days": 60, "name": "测试用户7"}, # 连续签到2个月奖励
    {"telegram_id": 10000008, "days": 90, "name": "测试用户8"}, # 连续签到3个月奖励
    {"telegram_id": 10000009, "days": 179, "name": "测试用户9"}, # 即将达到半年
    {"telegram_id": 10000010, "days": 180, "name": "测试用户10"}, # 连续签到半年奖励
    {"telegram_id": 10000011, "days": 364, "name": "测试用户11"}, # 即将达到一年
    {"telegram_id": 10000012, "days": 365, "name": "测试用户12"}, # 连续签到一年奖励
]

# 测试群组ID
TEST_GROUP_ID = -1002417673222

# 基础签到积分
BASE_POINTS = 100

async def create_test_user(session, telegram_id, name):
    """创建测试用户"""
    # 检查用户是否已存在
    existing_user = await session.scalar(
        select(User).where(User.telegram_id == telegram_id)
    )
    
    if existing_user:
        print(f"用户 {telegram_id} 已存在，ID: {existing_user.id}")
        return existing_user
    
    user = User(
        telegram_id=telegram_id,
        username=f"test_user_{telegram_id}",
        first_name=name,
        last_name="TestUser",
        language_code="en",
        is_premium=False,
        join_source=2,  # 来自群组
        source_group_id=TEST_GROUP_ID
    )
    session.add(user)
    await session.flush()
    print(f"创建用户 {telegram_id}, ID: {user.id}")
    return user

async def create_account(session, user_id, telegram_id, account_type):
    """创建用户账户"""
    # 检查账户是否已存在
    existing_account = await session.scalar(
        select(Account).where(
            Account.telegram_id == telegram_id,
            Account.account_type == account_type
        )
    )
    
    if existing_account:
        print(f"账户类型 {account_type} 对应用户 {telegram_id} 已存在, ID: {existing_account.id}")
        return existing_account
    
    account = Account(
        user_id=user_id,
        telegram_id=telegram_id,
        account_type=account_type,
        total_amount=10000,  # 初始10000积分
        available_amount=10000,
        frozen_amount=0,
        status=1  # 正常
    )
    session.add(account)
    await session.flush()
    print(f"创建账户类型 {account_type} 对应用户 {telegram_id}, ID: {account.id}")
    return account

async def create_sign_in_records(session, user_id, telegram_id, days):
    """创建连续签到记录"""
    # 清除用户之前的签到记录
    await session.execute(
        text(f"DELETE FROM sign_in_records WHERE telegram_id = {telegram_id}")
    )
    
    today = datetime.date.today()
    records = []
    
    # 创建过去N天的签到记录
    for i in range(days, 0, -1):
        sign_date = today - datetime.timedelta(days=i)
        continuous_days = days - i + 1
        
        record = SignInRecord(
            group_id=TEST_GROUP_ID,
            user_id=user_id,
            telegram_id=telegram_id,
            points=BASE_POINTS,
            continuous_days=continuous_days,
            sign_date=sign_date
        )
        session.add(record)
        records.append(record)
    
    await session.flush()
    print(f"为用户 {telegram_id} 创建了 {days} 天的签到记录")
    return records

async def main():
    """主函数"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            for user_config in TEST_USERS:
                telegram_id = user_config["telegram_id"]
                days = user_config["days"]
                name = user_config["name"]
                
                print(f"\n处理用户 {name} (Telegram ID: {telegram_id}), 连续签到 {days} 天")
                
                # 1. 创建用户
                user = await create_test_user(session, telegram_id, name)
                
                # 2. 创建积分账户
                point_account = await create_account(session, user.id, telegram_id, 1)
                
                # 3. 创建钱包账户
                cash_account = await create_account(session, user.id, telegram_id, 2)
                
                # 4. 创建签到记录
                records = await create_sign_in_records(session, user.id, telegram_id, days)
            
            print("\n测试数据生成完成!")
            print("使用下面的命令测试连续签到奖励:")
            print("1. 登录到Telegram测试账号")
            print("2. 加入测试群组")
            print("3. 发送 '签到' 命令测试奖励机制")
            print("\n每个测试用户将触发不同的连续签到奖励:")
            for user in TEST_USERS:
                print(f"- {user['name']} (ID: {user['telegram_id']}): 连续签到 {user['days']} 天")

if __name__ == "__main__":
    asyncio.run(main()) 