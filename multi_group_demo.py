#!/usr/bin/env python3
"""
多群组游戏系统演示脚本
展示不同群组运行不同游戏的功能
"""

import asyncio
import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.config.multi_game_config import MultiGameConfig, GroupConfig

def demo_multi_group_system():
    """演示多群组游戏系统"""
    print("🎲 多群组游戏系统演示")
    print("=" * 50)
    
    # 创建多游戏配置管理器
    config = MultiGameConfig()
    
    # 1. 显示所有游戏类型
    print("\n1. 可用游戏类型:")
    for game_type, game_config in config.game_configs.items():
        print(f"   🎮 {game_type}: {game_config.name}")
        print(f"      描述: {game_config.description}")
        print(f"      开奖间隔: {game_config.draw_interval}分钟")
        print(f"      返水比例: {game_config.cashback_rate * 100}%")
        print()
    
    # 2. 显示所有群组配置
    print("\n2. 群组配置:")
    for group_id, group_config in config.group_configs.items():
        game_config = config.get_game_config(group_config.game_type)
        print(f"   📱 群组: {group_config.group_name} (ID: {group_id})")
        print(f"      游戏类型: {group_config.game_type} ({game_config.name})")
        print(f"      状态: {'✅ 启用' if group_config.enabled else '❌ 禁用'}")
        print(f"      权限: {'👑 仅管理员' if group_config.admin_only else '👥 所有用户'}")
        print(f"      投注范围: {group_config.min_bet} - {group_config.max_bet:,} U")
        print(f"      自动开奖: {'✅ 是' if group_config.auto_draw else '❌ 否'}")
        print()
    
    # 3. 演示不同群组的游戏信息
    print("\n3. 各群组游戏信息:")
    for group_id, group_config in config.group_configs.items():
        print(f"\n📱 **{group_config.group_name}** (ID: {group_id})")
        print("-" * 40)
        game_info = config.format_game_info(group_id)
        print(game_info)
    
    # 4. 演示投注验证
    print("\n4. 投注验证演示:")
    test_cases = [
        (-1001234567890, "小", 1000),  # 正常投注
        (-1001234567890, "5", 500),    # 数字投注
        (-1001234567891, "大", 100),   # 快速开奖群组
        (-1001234567892, "豹子", 50),  # 高赔率群组
        (-1001234567890, "小", 0),     # 金额过小
        (-1001234567890, "小", 200000), # 金额过大
        (-1001234567890, "无效", 1000), # 无效投注类型
    ]
    
    for group_id, bet_type, bet_amount in test_cases:
        is_valid, message = config.validate_bet(group_id, bet_type, bet_amount)
        group_name = config.get_group_config(group_id).group_name if config.get_group_config(group_id) else "未知群组"
        status = "✅" if is_valid else "❌"
        print(f"   {status} 群组{group_name}: {bet_type} {bet_amount}U - {message}")
    
    # 5. 演示赔率计算
    print("\n5. 赔率计算演示:")
    test_odds = [
        (-1001234567890, "小", 1000),  # 经典开奖
        (-1001234567890, "5", 1000),   # 数字投注
        (-1001234567891, "大", 1000),  # 快速开奖
        (-1001234567892, "豹子", 1000), # 高赔率
    ]
    
    for group_id, bet_type, bet_amount in test_odds:
        group_config = config.get_group_config(group_id)
        game_type = group_config.game_type
        odds = config.get_bet_odds(bet_type, game_type)
        win_amount = config.calculate_win_amount(bet_type, bet_amount, game_type)
        cashback = config.calculate_cashback(bet_amount, game_type)
        
        print(f"   📊 群组{group_config.group_name}: {bet_type} {bet_amount}U")
        print(f"      赔率: {odds}倍")
        print(f"      中奖金额: {win_amount}U")
        print(f"      返水金额: {cashback}U")
        print()
    
    # 6. 演示期号生成
    print("\n6. 期号生成演示:")
    for group_id, group_config in config.group_configs.items():
        draw_number = config.generate_draw_number(group_id, group_config.game_type)
        print(f"   📅 群组{group_config.group_name}: {draw_number}")
    
    # 7. 演示下次开奖时间
    print("\n7. 下次开奖时间:")
    for group_id, group_config in config.group_configs.items():
        try:
            next_draw = config.get_next_draw_time(group_id)
            print(f"   ⏰ 群组{group_config.group_name}: {next_draw.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"   ❌ 群组{group_config.group_name}: {e}")
    
    # 8. 演示开奖结果生成
    print("\n8. 开奖结果生成演示:")
    for i in range(10):
        result = config.generate_secure_result()
        print(f"   🎲 第{i+1}次开奖: {result}")
    
    # 9. 演示中奖检查
    print("\n9. 中奖检查演示:")
    test_results = [
        (1, "小", True),   # 1是小
        (1, "大", False),  # 1不是大
        (1, "单", True),   # 1是单
        (1, "双", False),  # 1不是双
        (1, "1", True),    # 数字1中奖
        (1, "5", False),   # 数字5不中奖
        (5, "豹子", True), # 5是豹子
        (0, "豹子", True), # 0是豹子
    ]
    
    for result, bet_type, expected in test_results:
        is_win = config.check_bet_win(bet_type, result, "lottery")
        status = "✅" if is_win == expected else "❌"
        print(f"   {status} 开奖{result} 投注{bet_type}: 期望{expected}, 实际{is_win}")
    
    # 10. 演示群组管理
    print("\n10. 群组管理演示:")
    
    # 添加新群组
    new_group = GroupConfig(
        group_id=-1001234567893,
        group_name="测试群组",
        game_type="fast_lottery",
        enabled=True,
        admin_only=False,
        min_bet=1,
        max_bet=10000,
        auto_draw=True,
        notification_groups=[-1001234567893]
    )
    config.add_group_config(new_group)
    print(f"   ✅ 添加新群组: {new_group.group_name}")
    
    # 更新群组配置
    config.update_group_config(-1001234567893, max_bet=50000, admin_only=True)
    updated_group = config.get_group_config(-1001234567893)
    print(f"   ✅ 更新群组配置: 最大投注{updated_group.max_bet}U, 仅管理员{updated_group.admin_only}")
    
    # 获取特定游戏类型的群组
    lottery_groups = config.get_groups_by_game_type("lottery")
    print(f"   📊 经典开奖群组数量: {len(lottery_groups)}")
    
    fast_groups = config.get_groups_by_game_type("fast_lottery")
    print(f"   📊 快速开奖群组数量: {len(fast_groups)}")
    
    high_groups = config.get_groups_by_game_type("high_odds")
    print(f"   📊 高赔率群组数量: {len(high_groups)}")
    
    print("\n🎉 多群组游戏系统演示完成！")

if __name__ == "__main__":
    demo_multi_group_system() 