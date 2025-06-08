import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.filters import Command

# 配置日志记录器
logger = logging.getLogger(__name__)

# 创建消息路由器
message_router = Router()

# 保留命令监控处理器
@message_router.message(
    F.chat.type == ChatType.PRIVATE,
    F.text.startswith('/')
)
async def monitor_commands(message: Message) -> None:
    """监控命令消息"""
    user = message.from_user
    logger.info(
        "收到私聊命令 | 用户: %s (ID: %s) | 命令: %s",
        user.full_name,
        user.id,
        message.text
    ) 