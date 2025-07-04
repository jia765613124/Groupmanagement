#!/usr/bin/env python3
"""
测试投注反馈功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.handlers.bet_message_monitor import BetMessageMonitor

def test_bet_feedback():
    """测试投注反馈功能"""
    print("🧪 测试投注反馈功能")
    print("=" * 50)
    
    monitor = BetMessageMonitor()
    
    # 模拟投注数据
    test_cases = [
        {
            "name": "全部成功",
            "bets": [
                {"type": "bet_type", "bet_type": "大", "amount": 100, "original_text": "大100"},
                {"type": "number", "number": "8", "amount": 50, "original_text": "数字8 押50"}
            ],
            "success_count": 2,
            "failed_bets": []
        },
        {
            "name": "全部失败",
            "bets": [
                {"type": "bet_type", "bet_type": "大", "amount": 100, "original_text": "大100"},
                {"type": "number", "number": "8", "amount": 50, "original_text": "数字8 押50"}
            ],
            "success_count": 0,
            "failed_bets": [
                {
                    "bet": {"type": "bet_type", "bet_type": "大", "amount": 100, "original_text": "大100"},
                    "reason": "您已经对 大 下过注了，不能重复投注"
                },
                {
                    "bet": {"type": "number", "number": "8", "amount": 50, "original_text": "数字8 押50"},
                    "reason": "积分余额不足"
                }
            ]
        },
        {
            "name": "部分成功",
            "bets": [
                {"type": "bet_type", "bet_type": "大", "amount": 100, "original_text": "大100"},
                {"type": "bet_type", "bet_type": "小", "amount": 200, "original_text": "小200"},
                {"type": "number", "number": "8", "amount": 50, "original_text": "数字8 押50"}
            ],
            "success_count": 1,
            "failed_bets": [
                {
                    "bet": {"type": "bet_type", "bet_type": "大", "amount": 100, "original_text": "大100"},
                    "reason": "您已经对 大 下过注了，不能重复投注"
                },
                {
                    "bet": {"type": "number", "number": "8", "amount": 50, "original_text": "数字8 押50"},
                    "reason": "当前没有进行中的开奖期"
                }
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"测试 {i}: {test_case['name']}")
        print("-" * 30)
        
        # 模拟发送反馈
        feedback = monitor._format_bet_feedback(
            test_case["bets"], 
            test_case["success_count"], 
            test_case["failed_bets"]
        )
        
        print(feedback)
        print()

def test_feedback_format():
    """测试反馈格式化"""
    print("🧪 测试反馈格式化")
    print("=" * 50)
    
    # 添加格式化方法到 BetMessageMonitor 类
    def _format_bet_feedback(self, bets, success_count, failed_bets):
        """格式化投注反馈（用于测试）"""
        total_bets = len(bets)
        failed_bets = failed_bets or []
        
        if success_count == 0:
            feedback = f"❌ 投注失败\n\n"
            feedback += f"📝 解析到 {total_bets} 个投注，但全部失败\n\n"
            
            # 显示每个失败投注的具体原因
            feedback += f"🔍 失败原因:\n"
            for failed_bet in failed_bets:
                bet = failed_bet["bet"]
                reason = failed_bet["reason"]
                
                # 格式化投注信息
                if bet["type"] == "bet_type":
                    bet_info = f"{bet['bet_type']} {bet['amount']}积分"
                else:
                    bet_info = f"数字{bet['number']} {bet['amount']}积分"
                
                feedback += f"   • {bet_info}: {reason}\n"
            
            feedback += f"\n💡 请检查投注格式和余额"
            
        elif success_count == total_bets:
            feedback = f"✅ 投注成功\n\n"
            feedback += f"📝 成功投注 {success_count} 个\n"
            feedback += f"💰 投注详情:\n"
            for bet in bets:
                if bet["type"] == "bet_type":
                    feedback += f"   • {bet['bet_type']}: {bet['amount']}积分\n"
                else:
                    feedback += f"   • 数字{bet['number']}: {bet['amount']}积分\n"
        else:
            feedback = f"⚠️ 部分投注成功\n\n"
            feedback += f"📝 成功: {success_count}/{total_bets}\n"
            
            # 显示成功的投注
            feedback += f"💰 成功投注:\n"
            for bet in bets:
                # 检查这个投注是否在失败列表中
                is_failed = any(fb["bet"] == bet for fb in failed_bets)
                if not is_failed:
                    if bet["type"] == "bet_type":
                        feedback += f"   • {bet['bet_type']}: {bet['amount']}积分\n"
                    else:
                        feedback += f"   • 数字{bet['number']}: {bet['amount']}积分\n"
            
            # 显示失败的投注和原因
            if failed_bets:
                feedback += f"\n❌ 失败投注:\n"
                for failed_bet in failed_bets:
                    bet = failed_bet["bet"]
                    reason = failed_bet["reason"]
                    
                    # 格式化投注信息
                    if bet["type"] == "bet_type":
                        bet_info = f"{bet['bet_type']} {bet['amount']}积分"
                    else:
                        bet_info = f"数字{bet['number']} {bet['amount']}积分"
                    
                    feedback += f"   • {bet_info}: {reason}\n"
        
        return feedback
    
    # 临时添加到类中
    BetMessageMonitor._format_bet_feedback = _format_bet_feedback
    
    test_bet_feedback()

if __name__ == "__main__":
    test_feedback_format() 