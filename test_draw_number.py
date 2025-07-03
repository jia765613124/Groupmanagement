#!/usr/bin/env python3
"""
测试新的期号生成逻辑
"""

import asyncio
from datetime import datetime
import random

def test_lottery_service_draw_number():
    """测试 LotteryService 的期号生成"""
    from bot.common.lottery_service import LotteryService
    from bot.common.uow import UoW
    from bot.database.db import SessionFactory
    
    print("🎲 测试 LotteryService 期号生成...")
    
    # 创建服务实例
    service = LotteryService(None)  # 不需要 UoW 来测试期号生成
    
    # 生成多个期号测试
    for i in range(5):
        draw_number = service.generate_draw_number()
        print(f"   期号 {i+1}: {draw_number}")
        
        # 验证格式：应该是17位数字（年月日时分秒+3位随机数）
        if len(draw_number) == 17 and draw_number.isdigit():
            print(f"   ✅ 格式正确")
        else:
            print(f"   ❌ 格式错误")

def test_multi_config_draw_number():
    """测试 MultiGameConfig 的期号生成"""
    from bot.config.multi_game_config import MultiGameConfig
    
    print("\n🎲 测试 MultiGameConfig 期号生成...")
    
    config = MultiGameConfig()
    
    # 测试群组
    test_group_id = -1002882701368
    test_game_type = "lottery"
    
    # 生成多个期号测试
    for i in range(5):
        try:
            draw_number = config.generate_draw_number(test_group_id, test_game_type)
            print(f"   期号 {i+1}: {draw_number}")
            
            # 验证格式：应该是17位数字（年月日时分秒+3位随机数）
            if len(draw_number) == 17 and draw_number.isdigit():
                print(f"   ✅ 格式正确")
            else:
                print(f"   ❌ 格式错误")
                
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")

def test_draw_number_uniqueness():
    """测试期号唯一性"""
    from bot.common.lottery_service import LotteryService
    
    print("\n🎲 测试期号唯一性...")
    
    service = LotteryService(None)
    draw_numbers = set()
    
    # 生成100个期号，检查是否有重复
    for i in range(100):
        draw_number = service.generate_draw_number()
        if draw_number in draw_numbers:
            print(f"   ❌ 发现重复期号: {draw_number}")
            return False
        draw_numbers.add(draw_number)
    
    print(f"   ✅ 100个期号全部唯一")
    return True

async def main():
    """主函数"""
    print("🚀 期号生成测试开始")
    print("=" * 50)
    
    # 测试 LotteryService 期号生成
    test_lottery_service_draw_number()
    
    # 测试 MultiGameConfig 期号生成
    test_multi_config_draw_number()
    
    # 测试期号唯一性
    test_draw_number_uniqueness()
    
    print("\n" + "=" * 50)
    print("✅ 期号生成测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 