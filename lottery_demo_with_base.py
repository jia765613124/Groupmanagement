#!/usr/bin/env python3
"""
开奖系统演示脚本（使用更新后的基类）
展示开奖系统的完整功能
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.config.lottery_config import LotteryConfig
from bot.models.lottery import LotteryDraw, LotteryBet, LotteryCashback
from bot.common.lottery_service import LotteryService
from bot.common.uow import UoW
from bot.database.db import SessionFactory

async def demo_lottery_system():
    """演示开奖系统功能"""
    print("🎲 开奖系统演示（使用更新后的基类）")
    print("=" * 50)
    
    # 创建配置
    config = LotteryConfig()
    
    # 创建服务
    async with SessionFactory() as session:
        uow = UoW(session)
        lottery_service = LotteryService(uow, config)
        
        # 1. 创建新一期开奖
        print("\n1. 创建新一期开奖")
        draw_result = await lottery_service.create_draw()
        if draw_result["success"]:
            draw = draw_result["draw"]
            print(f"✅ 创建开奖期号: {draw.draw_number}")
            print(f"   开奖时间: {draw.draw_time}")
            print(f"   状态: {'进行中' if draw.status == 1 else '已开奖'}")
        else:
            print(f"❌ 创建开奖失败: {draw_result['message']}")
            return
        
        # 2. 模拟用户投注
        print("\n2. 模拟用户投注")
        telegram_id = 123456789
        
        # 投注大小单双
        bet_result1 = await lottery_service.place_bet(
            telegram_id=telegram_id,
            draw_number=draw.draw_number,
            bet_type="小",
            bet_amount=1000
        )
        if bet_result1["success"]:
            bet1 = bet_result1["bet"]
            print(f"✅ 投注成功: {bet1.bet_type} {bet1.bet_amount}U")
            print(f"   赔率: {bet1.odds}倍")
            print(f"   返水金额: {bet1.cashback_amount}U")
        else:
            print(f"❌ 投注失败: {bet_result1['message']}")
        
        # 投注数字
        bet_result2 = await lottery_service.place_bet(
            telegram_id=telegram_id,
            draw_number=draw.draw_number,
            bet_type="5",
            bet_amount=500
        )
        if bet_result2["success"]:
            bet2 = bet_result2["bet"]
            print(f"✅ 投注成功: 数字{bet2.bet_type} {bet2.bet_amount}U")
            print(f"   赔率: {bet2.odds}倍")
            print(f"   返水金额: {bet2.cashback_amount}U")
        else:
            print(f"❌ 投注失败: {bet_result2['message']}")
        
        # 3. 执行开奖
        print("\n3. 执行开奖")
        draw_result = await lottery_service.draw(draw.draw_number)
        if draw_result["success"]:
            result = draw_result["result"]
            print(f"✅ 开奖成功: 号码 {result}")
            
            # 显示投注结果
            bets_result = await lottery_service.get_bets_by_draw(draw.draw_number)
            if bets_result["success"]:
                for bet in bets_result["bets"]:
                    status = "中奖" if bet.is_win else "未中奖"
                    win_text = f"中奖 {bet.win_amount}U" if bet.is_win else "未中奖"
                    print(f"   投注{bet.bet_type}: {status} - {win_text}")
        else:
            print(f"❌ 开奖失败: {draw_result['message']}")
        
        # 4. 查看用户投注历史
        print("\n4. 查看用户投注历史")
        history_result = await lottery_service.get_user_bet_history(telegram_id, limit=10)
        if history_result["success"]:
            history = history_result["history"]
            print(f"✅ 找到 {len(history)} 条投注记录")
            for record in history:
                status = "中奖" if record["is_win"] else "未中奖"
                win_text = f"中奖 {record['win_amount']}U" if record["is_win"] else "未中奖"
                print(f"   期号{record['draw_number']} 投注{record['bet_type']}: {status} - {win_text}")
        else:
            print(f"❌ 获取历史失败: {history_result['message']}")
        
        # 5. 查看可领取的返水
        print("\n5. 查看可领取的返水")
        cashback_result = await lottery_service.get_user_cashback(telegram_id)
        if cashback_result["success"]:
            cashback = cashback_result["cashback"]
            if cashback > 0:
                print(f"✅ 可领取返水: {cashback}U")
                
                # 领取返水
                claim_result = await lottery_service.claim_cashback(telegram_id)
                if claim_result["success"]:
                    print(f"✅ 返水领取成功: {claim_result['amount']}U")
                else:
                    print(f"❌ 返水领取失败: {claim_result['message']}")
            else:
                print("ℹ️ 暂无可领取的返水")
        else:
            print(f"❌ 获取返水失败: {cashback_result['message']}")
        
        # 6. 查看开奖统计
        print("\n6. 查看开奖统计")
        stats_result = await lottery_service.get_draw_statistics(draw.draw_number)
        if stats_result["success"]:
            stats = stats_result["statistics"]
            print(f"✅ 期号 {draw.draw_number} 统计:")
            print(f"   总投注: {stats['total_bets']}U")
            print(f"   总派奖: {stats['total_payout']}U")
            print(f"   盈亏: {stats['profit']}U")
            print(f"   投注人数: {stats['bet_count']}人")
        else:
            print(f"❌ 获取统计失败: {stats_result['message']}")
        
        # 7. 显示模型字段信息
        print("\n7. 模型字段信息")
        print("✅ 所有模型都继承自 Base 类，包含以下通用字段:")
        print("   - created_at: 创建时间")
        print("   - updated_at: 更新时间") 
        print("   - deleted_at: 删除时间")
        print("   - is_deleted: 是否删除")
        
        # 显示具体模型字段
        print("\n📋 模型字段详情:")
        
        # LotteryDraw 字段
        draw_fields = [col.name for col in LotteryDraw.__table__.columns]
        print(f"   LotteryDraw: {', '.join(draw_fields)}")
        
        # LotteryBet 字段
        bet_fields = [col.name for col in LotteryBet.__table__.columns]
        print(f"   LotteryBet: {', '.join(bet_fields)}")
        
        # LotteryCashback 字段
        cashback_fields = [col.name for col in LotteryCashback.__table__.columns]
        print(f"   LotteryCashback: {', '.join(cashback_fields)}")
    
    print("\n🎉 开奖系统演示完成！")

if __name__ == "__main__":
    # 设置环境变量（如果需要）
    os.environ.setdefault("DATABASE_URL", "mysql+aiomysql://user:password@localhost/lottery_db")
    
    # 运行演示
    asyncio.run(demo_lottery_system()) 