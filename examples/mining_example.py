"""
挖矿系统使用示例
演示如何购买矿工卡、领取奖励等操作
"""

import asyncio
from datetime import datetime, date
from decimal import Decimal
from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.mining_service import MiningService
from bot.config.mining_config import MiningConfig

async def example_mining_operations():
    """挖矿系统操作示例"""
    
    # 示例用户ID
    telegram_id = 123456789
    
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        print("=== 挖矿系统示例 ===\n")
        
        # 1. 获取挖矿信息
        print("1. 获取挖矿信息")
        mining_info = await mining_service.get_mining_info(telegram_id)
        if mining_info["success"]:
            print(f"   钱包余额: {mining_info['wallet_balance']:.2f}U")
            print(f"   待领取奖励: {mining_info['pending_rewards']}笔")
            print(f"   待领取积分: {mining_info['pending_points']:,}")
            
            print("\n   矿工卡信息:")
            for card_type, info in mining_info["cards_info"].items():
                print(f"   {info['name']}: 已拥有{info['user_count']}/{info['max_cards']}张")
        else:
            print(f"   获取失败: {mining_info['message']}")
        
        print("\n" + "="*50 + "\n")
        
        # 2. 购买矿工卡示例
        print("2. 购买矿工卡示例")
        card_types = ["青铜", "白银", "黄金", "钻石"]
        
        for card_type in card_types:
            print(f"\n   尝试购买{card_type}矿工卡:")
            
            # 检查是否可以购买
            can_purchase, error_msg = await mining_service.can_purchase_mining_card(telegram_id, card_type)
            if can_purchase:
                print(f"   ✅ 可以购买{card_type}矿工卡")
                
                # 执行购买
                result = await mining_service.purchase_mining_card(telegram_id, card_type)
                if result["success"]:
                    print(f"   ✅ 购买成功: {result['message']}")
                    mining_card = result["mining_card"]
                    print(f"   📅 开始时间: {mining_card['start_time']}")
                    print(f"   📅 结束时间: {mining_card['end_time']}")
                else:
                    print(f"   ❌ 购买失败: {result['message']}")
            else:
                print(f"   ❌ 无法购买: {error_msg}")
        
        print("\n" + "="*50 + "\n")
        
        # 3. 查看待领取奖励
        print("3. 查看待领取奖励")
        rewards_result = await mining_service.get_pending_rewards(telegram_id)
        if rewards_result["success"]:
            print(f"   待领取奖励: {rewards_result['total_count']}笔")
            print(f"   总积分: {rewards_result['total_points']:,}")
            
            if rewards_result["rewards"]:
                print("\n   奖励详情:")
                for reward in rewards_result["rewards"][:5]:  # 只显示前5个
                    print(f"   ⛏️ {reward['card_type']}矿工卡 - 第{reward['reward_day']}天 - {reward['reward_points']:,}积分")
                
                if len(rewards_result["rewards"]) > 5:
                    print(f"   ... 还有{len(rewards_result['rewards']) - 5}笔奖励")
            else:
                print("   暂无待领取的奖励")
        else:
            print(f"   获取失败: {rewards_result['message']}")
        
        print("\n" + "="*50 + "\n")
        
        # 4. 领取奖励示例
        print("4. 领取奖励示例")
        if rewards_result["success"] and rewards_result["total_count"] > 0:
            claim_result = await mining_service.claim_all_rewards(telegram_id)
            if claim_result["success"]:
                print(f"   ✅ 领取成功: {claim_result['message']}")
                print(f"   💰 总积分: {claim_result['total_points']:,}")
                
                if claim_result["claimed_rewards"]:
                    print("\n   领取详情:")
                    for reward in claim_result["claimed_rewards"]:
                        print(f"   ⛏️ {reward['card_type']}矿工卡 - 第{reward['reward_day']}天 - {reward['reward_points']:,}积分")
            else:
                print(f"   ❌ 领取失败: {claim_result['message']}")
        else:
            print("   没有待领取的奖励")
        
        print("\n" + "="*50 + "\n")
        
        # 5. 处理每日挖矿奖励示例
        print("5. 处理每日挖矿奖励示例")
        process_result = await mining_service.process_daily_mining_rewards()
        if process_result["success"]:
            print(f"   ✅ 处理成功: {process_result['message']}")
            print(f"   📊 处理矿工卡: {process_result['processed_cards']}张")
            print(f"   💰 发放积分: {process_result['total_rewards']:,}")
        else:
            print(f"   ❌ 处理失败: {process_result['message']}")

async def example_mining_config():
    """挖矿配置示例"""
    print("=== 挖矿配置示例 ===\n")
    
    # 获取所有矿工卡配置
    cards_info = MiningConfig.get_all_cards_display_info()
    
    print("矿工卡配置:")
    for card_type, info in cards_info.items():
        print(f"\n{info['name']}:")
        print(f"  价格: {info['cost_usdt']:.2f}U")
        print(f"  每日积分: {info['daily_points']:,}")
        print(f"  持续天数: {info['duration_days']}天")
        print(f"  总积分: {info['total_points']:,}")
        print(f"  最大数量: {info['max_cards']}张")
        print(f"  描述: {info['description']}")
    
    print("\n" + "="*50 + "\n")
    
    # 计算收益示例
    print("收益计算示例:")
    for card_type in ["青铜", "白银", "黄金", "钻石"]:
        total_points = MiningConfig.calculate_total_points(card_type)
        card_info = MiningConfig.get_mining_card(card_type)
        if card_info:
            cost_usdt = card_info.cost_usdt
            daily_points = card_info.daily_points
            
            print(f"\n{card_info.name}:")
            print(f"  投入: {cost_usdt / 10000:.2f}U")
            print(f"  产出: {total_points:,}积分")
            print(f"  每日产出: {daily_points:,}积分")
            print(f"  投资回报率: {total_points / (cost_usdt * 10000):.2f}倍")

async def main():
    """主函数"""
    print("挖矿系统示例程序")
    print("注意: 请确保数据库已正确配置并运行了迁移脚本")
    print("="*60 + "\n")
    
    try:
        # 运行配置示例
        await example_mining_config()
        
        # 运行操作示例（需要数据库支持）
        # await example_mining_operations()
        
    except Exception as e:
        print(f"示例运行失败: {e}")
        print("请检查数据库连接和配置")

if __name__ == "__main__":
    asyncio.run(main()) 