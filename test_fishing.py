#!/usr/bin/env python3
"""
钓鱼系统测试文件
用于验证钓鱼逻辑的正确性
"""

import random
from bot.config.fishing_config import FishingConfig

def test_fishing_config():
    """测试钓鱼配置"""
    print("=== 钓鱼配置测试 ===")
    
    # 测试钓鱼竿信息
    print("\n1. 钓鱼竿信息:")
    for rod_type, info in FishingConfig.get_all_rods_info().items():
        print(f"   {rod_type}: {info['name']} - 消耗{info['cost']}积分 - 最低收获{info['min_points']}积分")
    
    # 测试鱼类分类
    print("\n2. 鱼类分类:")
    for category_name, category in FishingConfig.FISH_CATEGORIES.items():
        print(f"   {category_name} (概率: {category.probability*100:.1f}%):")
        for fish in category.fishes:
            print(f"     - {fish.name}: {fish.points}积分 - {fish.description}")

def test_fishing_probability():
    """测试钓鱼概率"""
    print("\n=== 钓鱼概率测试 ===")
    
    rod_types = ["初级", "中级", "高级"]
    test_count = 10000
    
    for rod_type in rod_types:
        print(f"\n{rod_type}钓鱼竿测试 ({test_count}次):")
        
        results = {
            "成功": 0,
            "失败": 0,
            "一类鱼": 0,
            "二类鱼": 0,
            "三类鱼": 0,
            "四类鱼": 0
        }
        
        total_points = 0
        legendary_count = 0
        
        for _ in range(test_count):
            result = FishingConfig.get_fishing_result(rod_type)
            
            if result["success"]:
                results["成功"] += 1
                fish = result["fish"]
                results[fish.category] += 1
                total_points += result["points"]
                
                if result["is_legendary"]:
                    legendary_count += 1
            else:
                results["失败"] += 1
        
        # 计算概率
        success_rate = results["成功"] / test_count * 100
        failure_rate = results["失败"] / test_count * 100
        
        print(f"  成功率: {success_rate:.2f}%")
        print(f"  失败率: {failure_rate:.2f}%")
        print(f"  平均收益: {total_points/test_count:.0f}积分")
        print(f"  传说鱼次数: {legendary_count}")
        
        # 各类鱼概率
        for category in ["一类鱼", "二类鱼", "三类鱼", "四类鱼"]:
            if results[category] > 0:
                prob = results[category] / test_count * 100
                print(f"  {category}: {prob:.2f}%")

def test_fish_distribution():
    """测试鱼类分布"""
    print("\n=== 鱼类分布测试 ===")
    
    rod_types = ["初级", "中级", "高级"]
    test_count = 1000
    
    for rod_type in rod_types:
        print(f"\n{rod_type}钓鱼竿鱼类分布:")
        
        fish_counts = {}
        
        for _ in range(test_count):
            result = FishingConfig.get_fishing_result(rod_type)
            if result["success"]:
                fish_name = result["fish"].name
                fish_counts[fish_name] = fish_counts.get(fish_name, 0) + 1
        
        # 按积分排序显示
        sorted_fishes = sorted(fish_counts.items(), key=lambda x: x[1], reverse=True)
        for fish_name, count in sorted_fishes:
            prob = count / test_count * 100
            print(f"  {fish_name}: {count}次 ({prob:.2f}%)")

def test_expected_value():
    """测试期望值"""
    print("\n=== 期望值测试 ===")
    
    rod_types = ["初级", "中级", "高级"]
    test_count = 10000
    
    for rod_type in rod_types:
        print(f"\n{rod_type}钓鱼竿期望值分析:")
        
        rod_info = FishingConfig.get_rod_info(rod_type)
        cost = rod_info["cost"]
        
        total_earned = 0
        success_count = 0
        
        for _ in range(test_count):
            result = FishingConfig.get_fishing_result(rod_type)
            if result["success"]:
                total_earned += result["points"]
                success_count += 1
        
        avg_earned = total_earned / test_count
        success_rate = success_count / test_count
        expected_value = avg_earned - cost
        
        print(f"  钓鱼成本: {cost}积分")
        print(f"  平均收获: {avg_earned:.0f}积分")
        print(f"  期望值: {expected_value:.0f}积分")
        print(f"  成功率: {success_rate*100:.2f}%")
        
        if expected_value > 0:
            print(f"  ✅ 正期望值，理论上有利可图")
        else:
            print(f"  ❌ 负期望值，理论上会亏损")

def test_legendary_fish_notification():
    """测试传说鱼通知"""
    print("\n=== 传说鱼通知测试 ===")
    
    # 模拟传说鱼通知
    player_name = "测试玩家"
    fish_name = "金鱼"
    subscription_link = "https://t.me/test_subscription"
    
    notification = FishingConfig.format_legendary_notification(
        player_name=player_name,
        fish_name=fish_name,
        subscription_link=subscription_link
    )
    
    print(f"通知消息: {notification}")

def main():
    """主测试函数"""
    print("🎣 钓鱼系统测试开始\n")
    
    # 设置随机种子以确保测试结果可重现
    random.seed(42)
    
    test_fishing_config()
    test_fishing_probability()
    test_fish_distribution()
    test_expected_value()
    test_legendary_fish_notification()
    
    print("\n✅ 钓鱼系统测试完成")

if __name__ == "__main__":
    main() 