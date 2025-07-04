#!/usr/bin/env python3
"""
测试重复投注检查功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.handlers.bet_message_monitor import BetMessageMonitor
from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.lottery_service import LotteryService

async def test_duplicate_bet_check():
    """测试重复投注检查"""
    print("🧪 测试重复投注检查功能")
    print("=" * 50)
    
    async with SessionFactory() as session:
        uow = UoW(session)
        lottery_service = LotteryService(uow)
        
        # 测试参数
        group_id = -1002882701368
        telegram_id = 6262392054
        bet_type = "大"
        bet_amount = 100
        
        print(f"📝 测试参数:")
        print(f"   群组ID: {group_id}")
        print(f"   用户ID: {telegram_id}")
        print(f"   投注类型: {bet_type}")
        print(f"   投注金额: {bet_amount}")
        print()
        
        # 第一次投注
        print("🔄 第一次投注...")
        result1 = await lottery_service.place_bet(group_id, telegram_id, bet_type, bet_amount)
        print(f"   结果: {result1['success']}")
        print(f"   消息: {result1['message']}")
        print()
        
        # 第二次投注（应该失败）
        print("🔄 第二次投注（重复投注）...")
        result2 = await lottery_service.place_bet(group_id, telegram_id, bet_type, bet_amount)
        print(f"   结果: {result2['success']}")
        print(f"   消息: {result2['message']}")
        print()
        
        # 测试不同投注类型（应该成功）
        print("🔄 测试不同投注类型...")
        result3 = await lottery_service.place_bet(group_id, telegram_id, "小", bet_amount)
        print(f"   结果: {result3['success']}")
        print(f"   消息: {result3['message']}")
        print()
        
        # 测试数字投注
        print("🔄 测试数字投注...")
        result4 = await lottery_service.place_bet(group_id, telegram_id, "8", bet_amount)
        print(f"   结果: {result4['success']}")
        print(f"   消息: {result4['message']}")
        print()
        
        # 测试重复数字投注（应该失败）
        print("🔄 测试重复数字投注...")
        result5 = await lottery_service.place_bet(group_id, telegram_id, "8", bet_amount)
        print(f"   结果: {result5['success']}")
        print(f"   消息: {result5['message']}")
        print()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_duplicate_bet_check()) 