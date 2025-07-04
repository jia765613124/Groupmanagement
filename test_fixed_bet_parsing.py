#!/usr/bin/env python3
"""
测试修复后的投注解析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.handlers.bet_message_monitor import BetMessageParser

def test_fixed_bet_parsing():
    """测试修复后的投注解析"""
    print("🧪 测试修复后的投注解析")
    print("=" * 50)
    
    parser = BetMessageParser()
    
    # 测试用例
    test_cases = [
        "大1000 大单100 数字8 押100",  # 原始问题消息
        "大1000 大单100 数字8押100",   # 无空格版本
        "大1000 大单100 8 100",        # 简化数字格式
        "大1000 大单100 8押100",       # 简化无空格格式
        "数字8 押100",                 # 单独数字投注
        "数字8押100",                  # 单独数字投注无空格
        "8 100",                       # 简化数字投注
        "8押100",                      # 简化数字投注无空格
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: '{test_case}'")
        
        try:
            bets = parser.parse_bet_message(test_case)
            
            if bets:
                print(f"    ✅ 解析成功，找到 {len(bets)} 个投注:")
                for j, bet in enumerate(bets, 1):
                    if bet["type"] == "bet_type":
                        print(f"      {j}. 类型投注: {bet['bet_type']} {bet['amount']}积分")
                    elif bet["type"] == "number":
                        print(f"      {j}. 数字投注: 数字{bet['number']} {bet['amount']}积分")
                    print(f"         原始文本: {bet['original_text']}")
            else:
                print(f"    ❌ 解析失败，未找到有效投注")
                
        except Exception as e:
            print(f"    ❌ 解析出错: {e}")
        
        print()

if __name__ == "__main__":
    test_fixed_bet_parsing() 