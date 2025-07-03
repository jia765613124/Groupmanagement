#!/usr/bin/env python3
"""
开奖系统演示脚本
展示如何启动和使用开奖系统
"""

import asyncio
import logging
import os
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def demo_lottery_system():
    """演示开奖系统"""
    print("🎲 开奖系统演示开始")
    print("=" * 50)
    
    # 1. 导入开奖系统组件
    from bot.config.lottery_config import LotteryConfig
    from bot.tasks.lottery_scheduler import manual_draw
    
    # 2. 显示系统配置
    print("\n📊 系统配置:")
    print(f"   开奖频率: 每 {LotteryConfig.DRAW_INTERVAL_MINUTES} 分钟")
    print(f"   返水比例: {LotteryConfig.CASHBACK_RATE*100}%")
    print(f"   投注类型数量: {len(LotteryConfig.get_all_bet_types())}")
    
    # 3. 显示投注类型
    print("\n🎯 投注类型:")
    for bet_type, info in LotteryConfig.get_all_bet_types().items():
        print(f"   {bet_type}: {info.description} (赔率{info.odds}倍)")
    
    # 4. 测试开奖结果生成
    print("\n🎲 测试开奖结果生成:")
    for i in range(5):
        result = LotteryConfig.generate_lottery_result()
        print(f"   第{i+1}次开奖: {result}")
    
    # 5. 测试投注中奖检查
    print("\n✅ 测试投注中奖检查:")
    test_bets = [
        ("小", 1, True), ("小", 5, False),
        ("大", 9, True), ("大", 1, False),
        ("单", 7, True), ("单", 2, False),
        ("双", 8, True), ("双", 1, False),
    ]
    
    for bet_type, result, expected in test_bets:
        actual = LotteryConfig.check_bet_win(bet_type, 100, result)
        status = "✅" if actual == expected else "❌"
        print(f"   {status} {bet_type} vs {result}: {actual}")
    
    # 6. 测试中奖金额计算
    print("\n💰 测试中奖金额计算:")
    bet_amount = 1000
    for bet_type in ["小", "小单", "0"]:
        win_amount = LotteryConfig.calculate_win_amount(bet_type, bet_amount)
        print(f"   {bet_type}: {bet_amount}U -> {win_amount}U")
    
    # 7. 显示消息格式化
    print("\n📝 开奖消息示例:")
    message = LotteryConfig.format_draw_message(
        draw_number="202401011000",
        result=7,
        total_bets=50000,
        total_payout=30000
    )
    print(message)
    
    print("\n" + "=" * 50)
    print("🎲 开奖系统演示完成")
    print("\n💡 使用说明:")
    print("1. 设置环境变量 LOTTERY_NOTIFICATION_GROUPS 配置群组ID")
    print("2. 运行数据库迁移脚本创建相关表")
    print("3. 在机器人启动时调用 start_lottery_scheduler()")
    print("4. 注册 LotteryHandler 处理用户命令")
    print("5. 系统将每5分钟自动开奖并发送结果到群组")

def setup_environment():
    """设置环境变量"""
    print("🔧 设置环境变量...")
    
    # 设置示例群组ID（需要替换为实际的群组ID）
    os.environ["LOTTERY_NOTIFICATION_GROUPS"] = "-1001234567890,-1001987654321"
    
    # 设置数据库连接（如果需要）
    os.environ["DATABASE_URL"] = "mysql+pymysql://user:password@localhost/dbname"
    
    print("✅ 环境变量设置完成")

def show_usage_instructions():
    """显示使用说明"""
    print("\n📖 使用说明:")
    print("=" * 50)
    
    print("\n1. 环境配置:")
    print("   export LOTTERY_NOTIFICATION_GROUPS='-1001234567890,-1001987654321'")
    print("   export DATABASE_URL='mysql+pymysql://user:password@localhost/dbname'")
    
    print("\n2. 数据库迁移:")
    print("   mysql -u user -p database < migrations/lottery_tables.sql")
    
    print("\n3. 在机器人代码中集成:")
    print("   from bot.tasks.lottery_scheduler import start_lottery_scheduler")
    print("   from bot.handlers.lottery_handler import LotteryHandler")
    print("   ")
    print("   # 启动开奖调度器")
    print("   asyncio.create_task(start_lottery_scheduler())")
    print("   ")
    print("   # 注册开奖处理器")
    print("   lottery_handler = LotteryHandler(client)")
    
    print("\n4. 用户命令:")
    print("   /lottery - 显示投注界面")
    print("   /lottery_history - 查看开奖历史")
    print("   /bet <类型> <金额> - 下注")
    print("   /cashback - 领取返水")
    
    print("\n5. 测试系统:")
    print("   python test_lottery.py")

async def main():
    """主函数"""
    try:
        # 设置环境
        setup_environment()
        
        # 运行演示
        await demo_lottery_system()
        
        # 显示使用说明
        show_usage_instructions()
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 