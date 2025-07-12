import logging
from typing import Any
from contextlib import asynccontextmanager
import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.types import ErrorEvent, Update, BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from dishka import make_async_container
from dishka.integrations.aiogram import setup_dishka
from fastapi import FastAPI
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable

from bot.config import get_config
from bot.handlers.commands import commands_router, setup_bot_commands
from bot.handlers.message_monitor import message_router
from bot.handlers.group_monitor import group_router
from bot.handlers.bot_monitor import bot_router
from bot.handlers.lottery_handler import lottery_router  # 导入开奖处理器
from bot.handlers.group_message_monitor import group_message_monitor_router  # 导入群组消息监控器
from bot.handlers.text_message_monitor import text_message_monitor_router  # 导入文字消息监控器
from bot.handlers.bet_message_monitor import bet_message_monitor_router  # 导入投注消息监控器
from bot.handlers.red_packet_handler import red_packet_router  # 导入红包处理器
from bot.handlers.checkin_handler import checkin_router  # 导入签到处理器
from bot.ioc import DepsProvider
from bot.misc import bot, dp
from bot.tasks.lottery_scheduler import start_lottery_scheduler, stop_lottery_scheduler  # 导入开奖调度器
from bot.tasks.mining_scheduler import start_mining_scheduler, stop_mining_scheduler  # 导入挖矿调度器
from bot.utils import setup_logging
from bot.states import Menu

# 获取配置并设置日志
config = get_config()
setup_logging(config)
logger = logging.getLogger(__name__)

# 创建主路由器
main_router = Router()


def register_routers(router: Router):
    """注册所有路由器"""
    logger.info("Registering routers")
    # 注册所有路由器，按优先级排序
    router.include_router(checkin_router)  # 签到处理器放在最前面
    router.include_router(bet_message_monitor_router)  # 投注消息监控
    router.include_router(text_message_monitor_router)  # 文字消息监控
    router.include_router(group_message_monitor_router)  # 群组消息监控
    router.include_router(group_router)       # 群组成员监控
    router.include_router(bot_router)         # 机器人状态监控
    router.include_router(lottery_router)     # 开奖处理器
    router.include_router(red_packet_router)  # 红包处理器
    router.include_router(commands_router)    # 命令路由器
    router.include_router(message_router)     # 消息监控放在最后
    logger.info("Routers registered successfully")


@main_router.error()
async def error_handler(event: ErrorEvent):
    """
    错误处理函数
    当发生错误时，记录错误
    """
    logger.error("Error occurred: %s", event.exception, exc_info=event.exception)


async def setup_dispatcher(dp: Dispatcher):
    """
    设置调度器
    初始化依赖注入容器，设置路由器
    """
    logger.info("Admin IDs: %s", config.ADMIN_IDS)
    # 先设置依赖注入
    container = make_async_container(DepsProvider())
    setup_dishka(container=container, router=dp)
    dp.include_router(main_router)
    
    register_routers(dp)


async def start_pooling():
    """
    启动轮询模式
    设置调度器并开始轮询消息
    """
    
    await setup_dispatcher(dp)
    
    try:
        # 设置机器人命令菜单
        await setup_bot_commands()
        logger.info("Bot commands setup successfully")
    except Exception as e:
        logger.warning(f"Failed to setup bot commands: {e}")
        # 继续运行，不因为命令设置失败而停止

    # 启动开奖调度器
    try:
        asyncio.create_task(start_lottery_scheduler())
        logger.info("Started lottery scheduler task")
    except Exception as e:
        logger.error(f"Failed to start lottery scheduler: {e}")

    # 启动挖矿调度器
    try:
        asyncio.create_task(start_mining_scheduler())
        logger.info("Started mining scheduler task")
    except Exception as e:
        logger.error(f"Failed to start mining scheduler: {e}")

    await dp.start_polling(bot, skip_updates=True)


async def setup_webhook(bot: Bot):
    """
    设置Webhook模式
    设置调度器并配置Webhook
    """
    
    await setup_dispatcher(dp)
    
    try:
        # 设置机器人命令菜单
        await setup_bot_commands()
        logger.info("Bot commands setup successfully")
    except Exception as e:
        logger.warning(f"Failed to setup bot commands: {e}")

    # 启动开奖调度器
    try:
        asyncio.create_task(start_lottery_scheduler())
        logger.info("Started lottery scheduler task")
    except Exception as e:
        logger.error(f"Failed to start lottery scheduler: {e}")

    # 启动挖矿调度器
    try:
        asyncio.create_task(start_mining_scheduler())
        logger.info("Started mining scheduler task")
    except Exception as e:
        logger.error(f"Failed to start mining scheduler: {e}")

    await bot.set_webhook(config.WEBHOOK_URL, secret_token=config.BOT_SECRET_TOKEN)