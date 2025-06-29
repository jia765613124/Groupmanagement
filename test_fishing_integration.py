#!/usr/bin/env python3
"""
钓鱼功能集成测试
测试钓鱼功能与命令系统的集成
"""

import asyncio
import logging
from unittest.mock import Mock, AsyncMock
from aiogram.types import Message, CallbackQuery, User, Chat
from bot.handlers.commands import fish_command_handler, fishing_menu_callback, fishing_history_callback
from bot.handlers.fishing_handler import show_fishing_rods, show_fishing_history, handle_fishing_callback

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fish_command():
    """测试 /fish 命令"""
    print("🧪 测试 /fish 命令...")
    
    # 创建模拟消息
    mock_message = Mock(spec=Message)
    mock_message.from_user = Mock(spec=User)
    mock_message.from_user.id = 123456789
    mock_message.answer = AsyncMock()
    
    try:
        await fish_command_handler(mock_message)
        print("✅ /fish 命令测试通过")
    except Exception as e:
        print(f"❌ /fish 命令测试失败: {e}")

async def test_fishing_menu_callback():
    """测试钓鱼菜单回调"""
    print("🧪 测试钓鱼菜单回调...")
    
    # 创建模拟回调查询
    mock_callback = Mock(spec=CallbackQuery)
    mock_callback.from_user = Mock(spec=User)
    mock_callback.from_user.id = 123456789
    mock_callback.message = Mock(spec=Message)
    mock_callback.message.edit_text = AsyncMock()
    mock_callback.answer = AsyncMock()
    mock_callback.data = "fishing_menu"
    
    try:
        await fishing_menu_callback(mock_callback)
        print("✅ 钓鱼菜单回调测试通过")
    except Exception as e:
        print(f"❌ 钓鱼菜单回调测试失败: {e}")

async def test_fishing_history_callback():
    """测试钓鱼历史回调"""
    print("🧪 测试钓鱼历史回调...")
    
    # 创建模拟回调查询
    mock_callback = Mock(spec=CallbackQuery)
    mock_callback.from_user = Mock(spec=User)
    mock_callback.from_user.id = 123456789
    mock_callback.message = Mock(spec=Message)
    mock_callback.message.edit_text = AsyncMock()
    mock_callback.answer = AsyncMock()
    mock_callback.data = "fishing_history"
    
    try:
        await fishing_history_callback(mock_callback)
        print("✅ 钓鱼历史回调测试通过")
    except Exception as e:
        print(f"❌ 钓鱼历史回调测试失败: {e}")

async def test_fishing_rod_callback():
    """测试钓鱼竿选择回调"""
    print("🧪 测试钓鱼竿选择回调...")
    
    # 创建模拟回调查询
    mock_callback = Mock(spec=CallbackQuery)
    mock_callback.from_user = Mock(spec=User)
    mock_callback.from_user.id = 123456789
    mock_callback.message = Mock(spec=Message)
    mock_callback.message.edit_text = AsyncMock()
    mock_callback.answer = AsyncMock()
    mock_callback.data = "fish_basic"
    
    try:
        # 这里需要导入 fishing_rod_callback 函数
        from bot.handlers.commands import fishing_rod_callback
        await fishing_rod_callback(mock_callback)
        print("✅ 钓鱼竿选择回调测试通过")
    except Exception as e:
        print(f"❌ 钓鱼竿选择回调测试失败: {e}")

async def test_fishing_service_functions():
    """测试钓鱼服务函数"""
    print("🧪 测试钓鱼服务函数...")
    
    # 创建模拟消息
    mock_message = Mock(spec=Message)
    mock_message.edit_text = AsyncMock()
    
    try:
        # 测试显示钓鱼竿
        await show_fishing_rods(mock_message, 123456789)
        print("✅ 显示钓鱼竿函数测试通过")
    except Exception as e:
        print(f"❌ 显示钓鱼竿函数测试失败: {e}")
    
    try:
        # 测试显示钓鱼历史
        await show_fishing_history(mock_message, 123456789)
        print("✅ 显示钓鱼历史函数测试通过")
    except Exception as e:
        print(f"❌ 显示钓鱼历史函数测试失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始钓鱼功能集成测试...\n")
    
    # 运行所有测试
    await test_fish_command()
    print()
    
    await test_fishing_menu_callback()
    print()
    
    await test_fishing_history_callback()
    print()
    
    await test_fishing_rod_callback()
    print()
    
    await test_fishing_service_functions()
    print()
    
    print("🎉 钓鱼功能集成测试完成！")

if __name__ == "__main__":
    asyncio.run(main()) 