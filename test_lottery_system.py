#!/usr/bin/env python3
"""
开奖系统测试脚本
测试多群组开奖系统的基本功能
"""

import asyncio
import logging
from datetime import datetime

from bot.config.multi_game_config import MultiGameConfig
from bot.common.lottery_service import LotteryService
from bot.common.uow import UoW
from bot.database.db import SessionFactory

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_multi_game_config():
    """测试多群组游戏配置"""
    print("🔧 测试多群组游戏配置...")
    
    config = MultiGameConfig()
    
    # 测试游戏配置
    game_types = ["lottery", "fast_lottery", "high_odds"]
    for game_type in game_types:
        game_config = config.get_game_config(game_type)
        if game_config:
            print(f"✅ 游戏类型 {game_type}: {game_config.name}")
            print(f"   描述: {game_config.description}")
            print(f"   开奖间隔: {game_config.draw_interval} 分钟")
            print(f"   返水比例: {game_config.cashback_rate * 100}%")
        else:
            print(f"❌ 游戏类型 {game_type} 未找到")
    
    # 测试群组配置
    enabled_groups = config.get_enabled_groups()
    print(f"\n📊 启用的群组数量: {len(enabled_groups)}")
    
    for group in enabled_groups:
        print(f"✅ 群组 {group.group_id}: {group.group_name}")
        print(f"   游戏类型: {group.game_type}")
        print(f"   投注范围: {group.min_bet} - {group.max_bet:,} U")
        print(f"   自动开奖: {'是' if group.auto_draw else '否'}")
    
    print("\n" + "="*50)

async def test_lottery_service():
    """测试开奖服务"""
    print("🎲 测试开奖服务...")
    
    try:
        async with SessionFactory() as session:
            uow = UoW(session)
            lottery_service = LotteryService(uow)
            
            # 测试创建开奖期
            config = MultiGameConfig()
            enabled_groups = config.get_enabled_groups()
            
            if enabled_groups:
                test_group = enabled_groups[0]
                print(f"📝 为群组 {test_group.group_id} 创建开奖期...")
                
                result = await lottery_service.create_new_draw(group_id=test_group.group_id, game_type=test_group.game_type)
                if result["success"]:
                    print(f"✅ 创建开奖期成功: {result['draw'].draw_number}")
                    
                    # 测试投注
                    print(f"💰 测试投注...")
                    bet_result = await lottery_service.place_bet(
                        group_id=test_group.group_id,
                        telegram_id=123456789,  # 测试用户ID
                        bet_type="小",
                        bet_amount=100
                    )
                    
                    if bet_result["success"]:
                        print(f"✅ 投注成功: {bet_result['bet'].bet_type} {bet_result['bet'].bet_amount} U")
                    else:
                        print(f"❌ 投注失败: {bet_result['message']}")
                    
                    # 测试开奖
                    print(f"🎯 测试开奖...")
                    draw_result = await lottery_service.draw_lottery(group_id=test_group.group_id)
                    if draw_result["success"]:
                        print(f"✅ 开奖成功: {draw_result['result']}")
                        print(f"   总投注: {draw_result['total_bets']:,} U")
                        print(f"   总派奖: {draw_result['total_payout']:,} U")
                    else:
                        print(f"❌ 开奖失败: {draw_result['message']}")
                else:
                    print(f"❌ 创建开奖期失败: {result['message']}")
            else:
                print("⚠️ 没有启用的群组配置")
                
    except Exception as e:
        print(f"❌ 测试开奖服务失败: {e}")
        logger.error(f"测试开奖服务失败: {e}", exc_info=True)
    
    print("\n" + "="*50)

async def test_game_info_formatting():
    """测试游戏信息格式化"""
    print("📝 测试游戏信息格式化...")
    
    config = MultiGameConfig()
    enabled_groups = config.get_enabled_groups()
    
    if enabled_groups:
        test_group = enabled_groups[0]
        game_info = config.format_game_info(test_group.group_id)
        print(f"📊 群组 {test_group.group_id} 的游戏信息:")
        print(game_info)
    else:
        print("⚠️ 没有启用的群组配置")
    
    print("\n" + "="*50)

async def test_bet_validation():
    """测试投注验证"""
    print("✅ 测试投注验证...")
    
    config = MultiGameConfig()
    enabled_groups = config.get_enabled_groups()
    
    if enabled_groups:
        test_group = enabled_groups[0]
        
        # 测试有效投注
        test_cases = [
            ("小", 100),
            ("大", 500),
            ("单", 1000),
            ("5", 50),  # 数字投注
        ]
        
        for bet_type, bet_amount in test_cases:
            is_valid, message = config.validate_bet(test_group.group_id, bet_type, bet_amount)
            status = "✅" if is_valid else "❌"
            print(f"{status} {bet_type} {bet_amount}U: {message}")
        
        # 测试无效投注
        invalid_cases = [
            ("小", 0),  # 金额太小
            ("大", 999999),  # 金额太大
            ("无效", 100),  # 无效投注类型
        ]
        
        print("\n测试无效投注:")
        for bet_type, bet_amount in invalid_cases:
            is_valid, message = config.validate_bet(test_group.group_id, bet_type, bet_amount)
            status = "✅" if is_valid else "❌"
            print(f"{status} {bet_type} {bet_amount}U: {message}")
    else:
        print("⚠️ 没有启用的群组配置")
    
    print("\n" + "="*50)

async def main():
    """主测试函数"""
    print("🚀 开始测试多群组开奖系统...")
    print("="*50)
    
    # 测试配置
    await test_multi_game_config()
    
    # 测试游戏信息格式化
    await test_game_info_formatting()
    
    # 测试投注验证
    await test_bet_validation()
    
    # 测试开奖服务
    await test_lottery_service()
    
    print("🎉 测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 