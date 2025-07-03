#!/usr/bin/env python3
"""
开奖系统测试文件
用于验证开奖逻辑的正确性
"""

import random
import asyncio
from datetime import datetime, timedelta
from bot.config.lottery_config import LotteryConfig

def test_lottery_config():
    """测试开奖配置"""
    print("=== 开奖配置测试 ===")
    
    # 测试投注类型信息
    print("\n1. 投注类型信息:")
    for bet_type, info in LotteryConfig.get_all_bet_types().items():
        print(f"   {bet_type}: {info.description} - 赔率{info.odds}倍 - 投注范围{info.min_bet:,}-{info.max_bet:,}U")
    
    # 测试数字投注配置
    print(f"\n2. 数字投注配置:")
    print(f"   赔率: {LotteryConfig.NUMBER_BET_ODDS}倍")
    print(f"   投注范围: {LotteryConfig.NUMBER_BET_MIN:,} - {LotteryConfig.NUMBER_BET_MAX:,} U")
    
    # 测试返水比例
    print(f"\n3. 返水配置:")
    print(f"   返水比例: {LotteryConfig.CASHBACK_RATE*100}%")
    
    # 测试开奖频率
    print(f"\n4. 开奖频率:")
    print(f"   开奖间隔: {LotteryConfig.DRAW_INTERVAL_MINUTES} 分钟")

def test_lottery_result_generation():
    """测试开奖结果生成"""
    print("\n=== 开奖结果生成测试 ===")
    
    test_count = 10000
    results = {}
    
    for _ in range(test_count):
        result = LotteryConfig.generate_lottery_result()
        results[result] = results.get(result, 0) + 1
    
    print(f"生成 {test_count} 次开奖结果:")
    for i in range(10):
        count = results.get(i, 0)
        percentage = count / test_count * 100
        print(f"   数字 {i}: {count} 次 ({percentage:.2f}%)")
    
    # 验证分布是否均匀
    expected_count = test_count / 10
    max_deviation = max(abs(count - expected_count) for count in results.values())
    max_deviation_percent = max_deviation / expected_count * 100
    
    print(f"\n最大偏差: {max_deviation_percent:.2f}%")
    if max_deviation_percent < 5:
        print("✅ 随机分布良好")
    else:
        print("⚠️  随机分布可能有问题")

def test_bet_win_check():
    """测试投注中奖检查"""
    print("\n=== 投注中奖检查测试 ===")
    
    # 测试大小单双
    print("1. 大小单双测试:")
    test_cases = [
        ("小", 1, True), ("小", 5, False), ("小", 9, False),
        ("大", 1, False), ("大", 5, False), ("大", 9, True),
        ("单", 1, True), ("单", 2, False), ("单", 9, True),
        ("双", 1, False), ("双", 2, True), ("双", 9, False),
    ]
    
    for bet_type, result, expected in test_cases:
        actual = LotteryConfig.check_bet_win(bet_type, 100, result)
        status = "✅" if actual == expected else "❌"
        print(f"   {status} {bet_type} vs {result}: 期望{expected}, 实际{actual}")
    
    # 测试组合投注
    print("\n2. 组合投注测试:")
    test_cases = [
        ("小单", 1, True), ("小单", 3, True), ("小单", 2, False),
        ("小双", 2, True), ("小双", 4, True), ("小双", 1, False),
        ("大单", 7, True), ("大单", 9, True), ("大单", 6, False),
        ("大双", 6, True), ("大双", 8, True), ("大双", 7, False),
        ("豹子", 0, True), ("豹子", 5, True), ("豹子", 1, False),
    ]
    
    for bet_type, result, expected in test_cases:
        actual = LotteryConfig.check_bet_win(bet_type, 100, result)
        status = "✅" if actual == expected else "❌"
        print(f"   {status} {bet_type} vs {result}: 期望{expected}, 实际{actual}")
    
    # 测试数字投注
    print("\n3. 数字投注测试:")
    for i in range(10):
        for j in range(10):
            expected = i == j
            actual = LotteryConfig.check_bet_win(str(i), 100, j)
            if expected != actual:
                print(f"   ❌ 数字{i} vs {j}: 期望{expected}, 实际{actual}")
    print("   ✅ 数字投注测试完成")

def test_win_amount_calculation():
    """测试中奖金额计算"""
    print("\n=== 中奖金额计算测试 ===")
    
    bet_amount = 1000
    
    # 测试大小单双
    print("1. 大小单双中奖金额:")
    for bet_type in ["小", "大", "单", "双"]:
        win_amount = LotteryConfig.calculate_win_amount(bet_type, bet_amount)
        expected = int(bet_amount * LotteryConfig.get_bet_type_info(bet_type).odds)
        status = "✅" if win_amount == expected else "❌"
        print(f"   {status} {bet_type}: {bet_amount}U -> {win_amount}U (期望{expected}U)")
    
    # 测试组合投注
    print("\n2. 组合投注中奖金额:")
    for bet_type in ["小单", "小双", "大单", "大双", "豹子"]:
        win_amount = LotteryConfig.calculate_win_amount(bet_type, bet_amount)
        expected = int(bet_amount * LotteryConfig.get_bet_type_info(bet_type).odds)
        status = "✅" if win_amount == expected else "❌"
        print(f"   {status} {bet_type}: {bet_amount}U -> {win_amount}U (期望{expected}U)")
    
    # 测试数字投注
    print("\n3. 数字投注中奖金额:")
    for i in range(10):
        win_amount = LotteryConfig.calculate_win_amount(str(i), bet_amount)
        expected = int(bet_amount * LotteryConfig.NUMBER_BET_ODDS)
        status = "✅" if win_amount == expected else "❌"
        print(f"   {status} 数字{i}: {bet_amount}U -> {win_amount}U (期望{expected}U)")

def test_cashback_calculation():
    """测试返水计算"""
    print("\n=== 返水计算测试 ===")
    
    test_amounts = [100, 1000, 10000, 100000]
    
    for amount in test_amounts:
        cashback = LotteryConfig.calculate_cashback(amount)
        expected = int(amount * LotteryConfig.CASHBACK_RATE)
        status = "✅" if cashback == expected else "❌"
        print(f"   {status} 投注{amount:,}U -> 返水{cashback}U (期望{expected}U)")

def test_next_draw_time():
    """测试下次开奖时间计算"""
    print("\n=== 下次开奖时间测试 ===")
    
    # 直接测试当前时间的下次开奖时间
    next_draw = LotteryConfig.get_next_draw_time()
    now = datetime.now()
    
    print(f"   当前时间: {now.strftime('%H:%M:%S')}")
    print(f"   下次开奖: {next_draw.strftime('%H:%M:%S')}")
    
    # 计算时间差
    time_diff = next_draw - now
    minutes_diff = time_diff.total_seconds() / 60
    
    print(f"   时间差: {minutes_diff:.1f} 分钟")
    
    if 0 <= minutes_diff <= 5:
        print("   ✅ 下次开奖时间计算正确")
    else:
        print("   ⚠️  下次开奖时间可能有问题")

def test_message_formatting():
    """测试消息格式化"""
    print("\n=== 消息格式化测试 ===")
    
    # 测试开奖消息格式化
    print("1. 开奖消息格式化:")
    message = LotteryConfig.format_draw_message(
        draw_number="202401011000",
        result=7,
        total_bets=50000,
        total_payout=30000
    )
    print(message)
    
    print("\n2. 投注界面格式化:")
    message = LotteryConfig.format_bet_interface()
    print(message)

def test_probability_analysis():
    """测试概率分析"""
    print("\n=== 概率分析测试 ===")
    
    test_count = 100000
    
    # 统计各种投注类型的中奖概率
    bet_types = ["小", "大", "单", "双", "小单", "小双", "大单", "大双", "豹子"]
    
    for bet_type in bet_types:
        wins = 0
        for _ in range(test_count):
            result = LotteryConfig.generate_lottery_result()
            if LotteryConfig.check_bet_win(bet_type, 100, result):
                wins += 1
        
        win_rate = wins / test_count * 100
        expected_rate = len(LotteryConfig.get_bet_type_info(bet_type).numbers) / 10 * 100
        
        print(f"   {bet_type}: {win_rate:.2f}% (期望{expected_rate:.2f}%)")
    
    # 数字投注概率
    wins = 0
    for _ in range(test_count):
        result = LotteryConfig.generate_lottery_result()
        if LotteryConfig.check_bet_win("5", 100, result):
            wins += 1
    
    win_rate = wins / test_count * 100
    expected_rate = 10.0  # 1/10 = 10%
    print(f"   数字投注: {win_rate:.2f}% (期望{expected_rate:.2f}%)")

def main():
    """主测试函数"""
    print("🎲 开奖系统测试开始\n")
    
    # 设置随机种子以确保测试结果可重现
    random.seed(42)
    
    test_lottery_config()
    test_lottery_result_generation()
    test_bet_win_check()
    test_win_amount_calculation()
    test_cashback_calculation()
    test_next_draw_time()
    test_message_formatting()
    test_probability_analysis()
    
    print("\n✅ 开奖系统测试完成")

if __name__ == "__main__":
    main() 