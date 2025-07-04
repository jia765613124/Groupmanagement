#!/usr/bin/env python3
"""
测试真实投注反馈场景
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.handlers.bet_message_monitor import BetMessageParser

def test_real_bet_scenarios():
    """测试真实投注场景"""
    print("🧪 测试真实投注反馈场景")
    print("=" * 50)
    
    parser = BetMessageParser()
    
    # 真实投注消息测试
    test_messages = [
        "大1000 大单100 数字8 押100",  # 包含重复投注
        "小500 单200 豹子50",           # 正常投注
        "数字8 押1000",                 # 数字投注
        "大1000 大1000",                # 重复投注
        "1000大 500单 1008",            # 不同格式
    ]
    
    for i, message in enumerate(test_messages, 1):
        print(f"测试 {i}: '{message}'")
        print("-" * 40)
        
        # 解析投注
        bets = parser.parse_bet_message(message)
        
        if bets:
            print(f"✅ 解析成功，找到 {len(bets)} 个投注:")
            for j, bet in enumerate(bets, 1):
                if bet["type"] == "bet_type":
                    print(f"   {j}. {bet['bet_type']} {bet['amount']}积分")
                else:
                    print(f"   {j}. 数字{bet['number']} {bet['amount']}积分")
        else:
            print("❌ 解析失败，未找到有效投注")
        
        print()
    
    print("📝 预期反馈示例:")
    print("=" * 50)
    
    # 模拟各种反馈场景
    scenarios = [
        {
            "title": "重复投注场景",
            "message": "大1000 大单100 数字8 押100",
            "expected_feedback": """❌ 投注失败

📝 解析到 3 个投注，但全部失败

🔍 失败原因:
   • 大 1000积分: 您已经对 大 下过注了，不能重复投注
   • 大单 100积分: 您已经对 大单 下过注了，不能重复投注
   • 数字8 100积分: 您已经对 8 下过注了，不能重复投注

💡 请检查投注格式和余额"""
        },
        {
            "title": "部分成功场景",
            "message": "小500 单200 豹子50",
            "expected_feedback": """⚠️ 部分投注成功

📝 成功: 2/3
💰 成功投注:
   • 小: 500积分
   • 单: 200积分

❌ 失败投注:
   • 豹子 50积分: 积分余额不足"""
        },
        {
            "title": "全部成功场景",
            "message": "小500 单200",
            "expected_feedback": """✅ 投注成功

📝 成功投注 2 个
💰 投注详情:
   • 小: 500积分
   • 单: 200积分"""
        }
    ]
    
    for scenario in scenarios:
        print(f"📋 {scenario['title']}")
        print(f"消息: {scenario['message']}")
        print("预期反馈:")
        print(scenario['expected_feedback'])
        print("-" * 50)

if __name__ == "__main__":
    test_real_bet_scenarios() 