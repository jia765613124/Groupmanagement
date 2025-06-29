#!/usr/bin/env python3
"""
钓鱼系统使用示例
展示如何在Telegram机器人中集成钓鱼功能
"""

import asyncio
import os
from telethon import TelegramClient
from bot.handlers.fishing_handler import FishingHandler
from bot.common.uow import UnitOfWork
from bot.ioc import get_container

# 配置信息 (实际使用时应该从环境变量或配置文件读取)
API_ID = os.getenv("TELEGRAM_API_ID", "your_api_id")
API_HASH = os.getenv("TELEGRAM_API_HASH", "your_api_hash")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "your_bot_token")

# 设置环境变量
os.environ["FISHING_NOTIFICATION_GROUPS"] = "-1001234567890,-1001987654321"  # 替换为实际的群组ID
os.environ["SUBSCRIPTION_LINK"] = "https://t.me/your_subscription"  # 替换为实际的订阅号链接

async def main():
    """主函数"""
    print("🎣 启动钓鱼机器人...")
    
    # 创建Telegram客户端
    client = TelegramClient('fishing_bot_session', API_ID, API_HASH)
    
    try:
        # 启动客户端
        await client.start(bot_token=BOT_TOKEN)
        print("✅ Telegram客户端启动成功")
        
        # 初始化依赖注入容器
        container = get_container()
        
        # 注册钓鱼处理器
        fishing_handler = FishingHandler(client)
        print("✅ 钓鱼处理器注册成功")
        
        # 显示机器人信息
        me = await client.get_me()
        print(f"🤖 机器人信息: {me.first_name} (@{me.username})")
        print(f"🆔 机器人ID: {me.id}")
        
        print("\n📋 可用命令:")
        print("  /fishing - 打开钓鱼界面")
        print("  /fishing_history - 查看钓鱼历史")
        
        print("\n🎯 钓鱼系统特性:")
        print("  • 三种钓鱼竿: 初级(1000积分)、中级(3000积分)、高级(5000积分)")
        print("  • 四类鱼类: 一类鱼(75%)、二类鱼(15%)、三类鱼(4.9%)、四类鱼(0.1%)")
        print("  • 传说鱼通知: 钓到传说鱼时自动发送全服公告")
        print("  • 钓鱼失败: 5%概率鱼竿损坏")
        
        print("\n🚀 机器人运行中... (按 Ctrl+C 停止)")
        
        # 保持机器人运行
        await client.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
    finally:
        await client.disconnect()
        print("👋 机器人已停止")

def show_fishing_config():
    """显示钓鱼配置信息"""
    from bot.config.fishing_config import FishingConfig
    
    print("📊 钓鱼系统配置信息:")
    print("=" * 50)
    
    # 钓鱼竿信息
    print("\n🎣 钓鱼竿配置:")
    for rod_type, info in FishingConfig.get_all_rods_info().items():
        print(f"  {rod_type}:")
        print(f"    名称: {info['name']}")
        print(f"    消耗: {info['cost']:,} 积分")
        print(f"    最低收获: {info['min_points']:,} 积分")
        print(f"    描述: {info['description']}")
    
    # 鱼类分类信息
    print("\n🐟 鱼类分类:")
    for category_name, category in FishingConfig.FISH_CATEGORIES.items():
        print(f"  {category_name} (概率: {category.probability*100:.1f}%):")
        for fish in category.fishes:
            print(f"    • {fish.name}: {fish.points:,} 积分 - {fish.description}")
    
    # 失败概率
    print(f"\n❌ 钓鱼失败概率: {FishingConfig.FAILURE_PROBABILITY*100:.1f}%")
    
    # 概率总和验证
    total_prob = sum(cat.probability for cat in FishingConfig.FISH_CATEGORIES.values())
    total_prob += FishingConfig.FAILURE_PROBABILITY
    print(f"📈 总概率: {total_prob*100:.1f}%")
    
    if abs(total_prob - 1.0) < 0.001:
        print("✅ 概率配置正确")
    else:
        print("⚠️  概率配置可能有问题")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "config":
        # 显示配置信息
        show_fishing_config()
    else:
        # 启动机器人
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\n👋 用户中断，机器人已停止")
        except Exception as e:
            print(f"❌ 运行错误: {e}") 