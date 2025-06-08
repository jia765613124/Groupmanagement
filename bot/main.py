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
from bot.ioc import DepsProvider
from bot.misc import bot, dp
from bot.tasks.recharge_checker import start_recharge_checker  # 导入定时任务
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
    router.include_router(group_router)       # 群组成员监控放在最前面
    router.include_router(bot_router)         # 机器人状态监控
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
    # 设置机器人命令菜单
    await setup_bot_commands()

    # 启动充值检查定时任务
    # asyncio.create_task(start_recharge_checker())
    # logger.info("Started recharge checker task")

    await dp.start_polling(bot, skip_updates=True)


async def setup_webhook(bot: Bot):
    """
    设置Webhook模式
    设置调度器并配置Webhook
    """
    
    await setup_dispatcher(dp)
    # 设置机器人命令菜单
    await setup_bot_commands()

    # # 启动充值检查定时任务
    # asyncio.create_task(start_recharge_checker())
    logger.info("Started recharge checker task")

    await bot.set_webhook(config.WEBHOOK_URL, secret_token=config.BOT_SECRET_TOKEN)