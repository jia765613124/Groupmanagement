#!/usr/bin/env python3
"""
测试投注消息解析功能
"""

import asyncio
import logging
from bot.handlers.bet_message_monitor import BetMessageParser

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_bet_message_parser():
    """测试投注消息解析功能"""
    print("🧪 测试投注消息解析功能")
    print("=" * 50)
    
    parser = BetMessageParser()
    
    # 测试用例
    test_cases = [
        # 基础投注类型
        "大1000",
        "小500",
        "单200",
        "双300",
        
        # 组合投注
        "大单100",
        "大双150",
        "小单80",
        "小双120",
        "豹子50",
        
        # 数字投注
        "数字8 押100",
        "8 100",
        "数字0 下50",
        "五 押200",
        
        # 金额在前
        "1000大",
        "500小",
        "200单",
        "300双",
        "100大单",
        "150大双",
        "80小单",
        "120小双",
        "50豹子",
        
        # 数字投注（金额在前）
        "1008",
        "1000押8",
        "500下5",
        "200买3",
        
        # 复杂组合
        "大1000 大单100 数字8 押100",
        "小500 单200 豹子50",
        "1000大 500单 1008",
        "大1000，大单100，数字8押100",
        "大1000、大单100、数字8押100",
        
        # 中文数字
        "数字八 押100",
        "数字五 下50",
        "100押八",
        "50下五",
        
        # 边界情况
        "大1",
        "小999999",
        "数字0 押1",
        "数字9 押999999",
        
        # 无效格式
        "无效投注",
        "大",
        "100",
        "数字",
        "押100",
    ]
    
    print("📝 开始测试投注消息解析...")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i:2d}: {test_case}")
        
        try:
            bets = parser.parse_bet_message(test_case)
            
            if bets:
                print(f"    ✅ 解析成功: {len(bets)} 个投注")
                for j, bet in enumerate(bets, 1):
                    if bet["type"] == "bet_type":
                        print(f"       {j}. {bet['bet_type']}: {bet['amount']}U")
                    else:
                        print(f"       {j}. 数字{bet['number']}: {bet['amount']}U")
            else:
                print(f"    ❌ 解析失败: 无法识别投注格式")
                
        except Exception as e:
            print(f"    💥 解析异常: {e}")
        
        print()
    
    print("🎯 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_bet_message_parser()) 