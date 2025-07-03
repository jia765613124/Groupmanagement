#!/usr/bin/env python3
"""
手动开奖测试脚本
用于测试开奖功能和消息发送
"""

import asyncio
import logging
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_manual_draw():
    """测试手动开奖"""
    try:
        from bot.tasks.lottery_scheduler import manual_draw
        from bot.config.multi_game_config import MultiGameConfig
        
        print("🎲 开始测试手动开奖...")
        
        # 获取群组配置
        config = MultiGameConfig()
        enabled_groups = config.get_enabled_groups()
        
        if not enabled_groups:
            print("❌ 没有启用的群组配置")
            return
        
        test_group = enabled_groups[0]
        print(f"📝 测试群组: {test_group.group_name} (ID: {test_group.group_id})")
        
        # 执行手动开奖
        print("🎯 执行手动开奖...")
        result = await manual_draw(test_group.group_id)
        
        if result["success"]:
            print(f"✅ 手动开奖成功!")
            print(f"   开奖结果: {result['result']}")
            print(f"   总投注: {result['total_bets']:,} U")
            print(f"   总派奖: {result['total_payout']:,} U")
            print(f"   盈亏: {result['profit']:,} U")
        else:
            print(f"❌ 手动开奖失败: {result['message']}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.error(f"测试失败: {e}", exc_info=True)

async def test_message_sending():
    """测试消息发送功能"""
    try:
        from bot.tasks.lottery_scheduler import lottery_scheduler
        from bot.config.multi_game_config import MultiGameConfig
        
        print("\n📨 测试消息发送功能...")
        
        # 获取群组配置
        config = MultiGameConfig()
        enabled_groups = config.get_enabled_groups()
        
        if not enabled_groups:
            print("❌ 没有启用的群组配置")
            return
        
        test_group = enabled_groups[0]
        print(f"📝 测试群组: {test_group.group_name} (ID: {test_group.group_id})")
        
        # 模拟开奖结果
        mock_result = {
            "success": True,
            "draw": type('MockDraw', (), {
                'draw_number': '202507020830_TEST',
                'game_type': 'lottery'
            })(),
            "result": 7,
            "total_bets": 5000,
            "total_payout": 3000,
            "profit": 2000
        }
        
        # 测试发送消息
        print("📤 发送测试消息...")
        await lottery_scheduler._send_draw_result(test_group.group_id, mock_result)
        print("✅ 消息发送测试完成")
        
    except Exception as e:
        print(f"❌ 消息发送测试失败: {e}")
        logger.error(f"消息发送测试失败: {e}", exc_info=True)

async def main():
    """主函数"""
    print("🚀 开奖系统测试开始")
    print("=" * 50)
    
    # 测试手动开奖
    await test_manual_draw()
    
    # 测试消息发送
    await test_message_sending()
    
    print("\n" + "=" * 50)
    print("✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(main()) 