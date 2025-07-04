#!/usr/bin/env python3
"""
测试投注记录查询命令
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.common.lottery_service import LotteryService
from bot.common.uow import UoW
from bot.database.db import SessionFactory

async def test_bets_command():
    """测试投注记录查询功能"""
    print("🧪 测试投注记录查询功能")
    print("=" * 50)
    
    # 测试用户ID
    test_user_id = 6262392054
    
    try:
        async with SessionFactory() as session:
            uow = UoW(session)
            lottery_service = LotteryService(uow)
            
            print(f"📝 查询用户 {test_user_id} 的投注记录...")
            
            # 获取用户投注历史
            result = await lottery_service.get_user_bet_history(
                telegram_id=test_user_id,
                limit=10
            )
            
            if result["success"]:
                bets = result["history"]
                
                if not bets:
                    print("📝 用户没有投注记录")
                    return
                
                print(f"✅ 找到 {len(bets)} 条投注记录")
                print()
                
                # 显示投注记录
                for i, bet in enumerate(bets, 1):
                    created_time = bet["created_at"][5:16]  # 取 MM-DD HH:MM
                    
                    if bet["is_win"]:
                        status = "✅ 中奖"
                        win_info = f" +{bet['win_amount']}积分"
                    else:
                        status = "❌ 未中"
                        win_info = ""
                    
                    print(f"{i}. {bet['bet_type']} {bet['bet_amount']}积分")
                    print(f"   期号: {bet['draw_number']}")
                    print(f"   时间: {created_time}")
                    print(f"   状态: {status}{win_info}")
                    print()
                
                # 计算统计信息
                total_bets = len(bets)
                total_bet_amount = sum(bet["bet_amount"] for bet in bets)
                total_win_amount = sum(bet["win_amount"] for bet in bets if bet["is_win"])
                win_count = sum(1 for bet in bets if bet["is_win"])
                
                print("📊 统计信息:")
                print(f"总投注: {total_bets} 次")
                print(f"总投注金额: {total_bet_amount:,} 积分")
                print(f"中奖次数: {win_count} 次")
                print(f"总中奖金额: {total_win_amount:,} 积分")
                print(f"胜率: {(win_count/total_bets*100):.1f}%")
                
            else:
                print(f"❌ 获取投注记录失败: {result['message']}")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_bets_formatting():
    """测试投注记录格式化"""
    print("\n🧪 测试投注记录格式化")
    print("=" * 50)
    
    # 模拟投注记录数据
    mock_bets = [
        {
            "bet_type": "大",
            "bet_amount": 1000,
            "draw_number": "20250705055006227910990",
            "created_at": "2025-07-05 05:37:18",
            "is_win": True,
            "win_amount": 2360
        },
        {
            "bet_type": "小单",
            "bet_amount": 100,
            "draw_number": "20250705055006227910990",
            "created_at": "2025-07-05 05:37:25",
            "is_win": False,
            "win_amount": 0
        },
        {
            "bet_type": "8",
            "bet_amount": 100,
            "draw_number": "20250705055006227910990",
            "created_at": "2025-07-05 05:37:32",
            "is_win": False,
            "win_amount": 0
        }
    ]
    
    print("📝 模拟投注记录:")
    print()
    
    for i, bet in enumerate(mock_bets, 1):
        if bet["is_win"]:
            status = "✅ 中奖"
            win_info = f" +{bet['win_amount']}积分"
        else:
            status = "❌ 未中"
            win_info = ""
        
        print(f"{i}. {bet['bet_type']} {bet['bet_amount']}积分")
        print(f"   期号: {bet['draw_number']}")
        print(f"   时间: {bet['created_at']}")
        print(f"   状态: {status}{win_info}")
        print()
    
    # 计算统计
    total_bets = len(mock_bets)
    total_bet_amount = sum(bet["bet_amount"] for bet in mock_bets)
    total_win_amount = sum(bet["win_amount"] for bet in mock_bets if bet["is_win"])
    win_count = sum(1 for bet in mock_bets if bet["is_win"])
    
    print("📊 统计信息:")
    print(f"总投注: {total_bets} 次")
    print(f"总投注金额: {total_bet_amount:,} 积分")
    print(f"中奖次数: {win_count} 次")
    print(f"总中奖金额: {total_win_amount:,} 积分")
    print(f"胜率: {(win_count/total_bets*100):.1f}%")

if __name__ == "__main__":
    import asyncio
    
    # 运行测试
    asyncio.run(test_bets_command())
    test_bets_formatting() 