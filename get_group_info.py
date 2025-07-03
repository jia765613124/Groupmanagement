#!/usr/bin/env python3
"""
群组信息获取脚本
用于获取Telegram群组的ID和名称
"""

import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.tl.types import Chat, Channel

# 从环境变量获取API凭据
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

async def get_group_info():
    """获取群组信息"""
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        print("❌ 请设置环境变量：")
        print("   TELEGRAM_API_ID")
        print("   TELEGRAM_API_HASH") 
        print("   TELEGRAM_BOT_TOKEN")
        return
    
    # 创建客户端
    client = TelegramClient('group_info_session', int(API_ID), API_HASH)
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        print("✅ 已连接到Telegram")
        
        # 获取所有对话
        print("\n📋 正在获取群组列表...")
        groups = []
        channels = []
        
        async for dialog in client.iter_dialogs():
            if dialog.is_group:
                groups.append({
                    'id': dialog.entity.id,
                    'title': dialog.entity.title,
                    'username': getattr(dialog.entity, 'username', ''),
                    'participants_count': getattr(dialog.entity, 'participants_count', 0)
                })
            elif dialog.is_channel:
                channels.append({
                    'id': dialog.entity.id,
                    'title': dialog.entity.title,
                    'username': getattr(dialog.entity, 'username', ''),
                    'participants_count': getattr(dialog.entity, 'participants_count', 0)
                })
        
        # 显示群组信息
        print(f"\n🎯 **群组列表** (共 {len(groups)} 个)")
        print("=" * 50)
        
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group['title']}")
            print(f"   ID: {group['id']}")
            if group['username']:
                print(f"   用户名: @{group['username']}")
            if group['participants_count']:
                print(f"   成员数: {group['participants_count']:,}")
            print()
        
        # 显示频道信息
        if channels:
            print(f"📺 **频道列表** (共 {len(channels)} 个)")
            print("=" * 50)
            
            for i, channel in enumerate(channels, 1):
                print(f"{i}. {channel['title']}")
                print(f"   ID: {channel['id']}")
                if channel['username']:
                    print(f"   用户名: @{channel['username']}")
                if channel['participants_count']:
                    print(f"   成员数: {channel['participants_count']:,}")
                print()
        
        # 生成配置代码
        print("🔧 **配置代码**")
        print("=" * 50)
        print("在 multi_game_config.py 中添加群组配置：")
        print()
        
        for group in groups[:5]:  # 只显示前5个群组
            print(f"GroupConfig(")
            print(f"    group_id={group['id']},")
            print(f"    group_name=\"{group['title']}\",")
            print(f"    game_type=\"lottery\",")
            print(f"    enabled=True,")
            print(f"    admin_only=False,")
            print(f"    min_bet=1,")
            print(f"    max_bet=100000,")
            print(f"    auto_draw=True,")
            print(f"    notification_groups=[{group['id']}]")
            print(f"),")
            print()
        
        if len(groups) > 5:
            print(f"... 还有 {len(groups) - 5} 个群组")
        
    except Exception as e:
        print(f"❌ 获取群组信息失败: {e}")
    
    finally:
        await client.disconnect()

async def get_specific_group_info(group_id: int):
    """获取特定群组信息"""
    if not all([API_ID, API_HASH, BOT_TOKEN]):
        print("❌ 请设置环境变量")
        return
    
    client = TelegramClient('group_info_session', int(API_ID), API_HASH)
    
    try:
        await client.start(bot_token=BOT_TOKEN)
        
        # 获取特定群组信息
        entity = await client.get_entity(group_id)
        
        if isinstance(entity, (Chat, Channel)):
            print(f"📋 **群组详细信息**")
            print("=" * 50)
            print(f"🆔 群组ID: {entity.id}")
            print(f"📝 群组名称: {entity.title}")
            print(f"🔗 用户名: @{getattr(entity, 'username', '无')}")
            print(f"📊 类型: {'群组' if isinstance(entity, Chat) else '频道'}")
            print(f"👥 成员数: {getattr(entity, 'participants_count', '未知')}")
            print(f"✅ 认证: {'是' if getattr(entity, 'verified', False) else '否'}")
            print(f"⚠️ 诈骗: {'是' if getattr(entity, 'scam', False) else '否'}")
            print(f"❌ 虚假: {'是' if getattr(entity, 'fake', False) else '否'}")
        else:
            print(f"❌ 实体 {group_id} 不是群组或频道")
    
    except Exception as e:
        print(f"❌ 获取群组信息失败: {e}")
    
    finally:
        await client.disconnect()

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 获取特定群组信息
        try:
            group_id = int(sys.argv[1])
            asyncio.run(get_specific_group_info(group_id))
        except ValueError:
            print("❌ 群组ID必须是数字")
    else:
        # 获取所有群组信息
        asyncio.run(get_group_info())

if __name__ == "__main__":
    main() 