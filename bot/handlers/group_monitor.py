"""群组监控处理器

处理群组中的各种事件：
1. 成员加入事件 (ChatMemberStatus.LEFT -> ChatMemberStatus.MEMBER)
2. 成员离开事件 (ChatMemberStatus.MEMBER -> ChatMemberStatus.LEFT)
3. 成员被提升为管理员 (ChatMemberStatus.MEMBER -> ChatMemberStatus.ADMINISTRATOR)
4. 成员被取消管理员 (ChatMemberStatus.ADMINISTRATOR -> ChatMemberStatus.MEMBER)
5. 机器人被添加 (ChatMemberStatus.LEFT -> ChatMemberStatus.MEMBER)
6. 机器人被移除 (ChatMemberStatus.MEMBER -> ChatMemberStatus.LEFT)
7. 机器人被提升为管理员 (ChatMemberStatus.MEMBER -> ChatMemberStatus.ADMINISTRATOR)
8. 机器人被取消管理员 (ChatMemberStatus.ADMINISTRATOR -> ChatMemberStatus.MEMBER)
"""

import logging
from typing import Annotated, TypeAlias
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, ChatMember
from aiogram.enums import ChatMemberStatus
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION

from bot.config import get_config

# 配置日志记录器
logger = logging.getLogger(__name__)
config = get_config()

# 创建群组监控路由器
group_router = Router(name="group_monitor")

async def check_bot_permissions(bot, chat_id: int) -> bool:
    """检查机器人是否具有必要的权限
    
    Args:
        bot: Bot 实例
        chat_id: 群组ID
        
    Returns:
        bool: 是否具有必要权限
    """
    try:
        # 获取机器人在群组中的状态
        bot_member = await bot.get_chat_member(chat_id, bot.id)
        
        # 检查是否是管理员
        if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
            logger.warning(f"机器人不是群组 {chat_id} 的管理员")
            return False
            
        return True
    except Exception as e:
        logger.error(f"检查机器人权限时出错: {e}")
        return False

@group_router.chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    F.old_chat_member.status == ChatMemberStatus.LEFT,
    F.new_chat_member.status == ChatMemberStatus.MEMBER
)
async def handle_member_join(event: ChatMemberUpdated) -> None:
    """处理成员加入群组事件"""
    try:
        chat = event.chat
        user = event.new_chat_member.user
        
        # 记录事件
        logger.info(f"成员加入群组: {user.full_name} (ID: {user.id}) 在群组 {chat.title} (ID: {chat.id})")
        
        # 检查机器人权限
        if not await check_bot_permissions(event.bot, chat.id):
            logger.warning(f"机器人没有足够的权限监控群组 {chat.id} 的成员加入事件")
            return
            
        notification = (
            f"👋 新成员加入群组\n\n"
            f"成员：{user.full_name}\n"
            f"用户ID：{user.id}\n"
            f"群组：{chat.title}\n"
            f"群组ID：{chat.id}"
        )
        await notify_admins(event.bot, notification)
    except Exception as e:
        logger.error(f"处理成员加入事件时出错: {e}")

@group_router.chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    F.old_chat_member.status == ChatMemberStatus.MEMBER,
    F.new_chat_member.status == ChatMemberStatus.LEFT
)
async def handle_member_leave(event: ChatMemberUpdated) -> None:
    """处理成员离开群组事件"""
    try:
        chat = event.chat
        user = event.new_chat_member.user
        
        # 记录事件
        logger.info(f"成员离开群组: {user.full_name} (ID: {user.id}) 从群组 {chat.title} (ID: {chat.id})")
        
        # 检查机器人权限
        if not await check_bot_permissions(event.bot, chat.id):
            logger.warning(f"机器人没有足够的权限监控群组 {chat.id} 的成员离开事件")
            return
            
        notification = (
            f"👋 成员离开群组\n\n"
            f"成员：{user.full_name}\n"
            f"用户ID：{user.id}\n"
            f"群组：{chat.title}\n"
            f"群组ID：{chat.id}"
        )
        await notify_admins(event.bot, notification)
    except Exception as e:
        logger.error(f"处理成员离开事件时出错: {e}")

@group_router.chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    F.old_chat_member.status == ChatMemberStatus.MEMBER,
    F.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR
)
async def handle_member_promote(event: ChatMemberUpdated) -> None:
    """处理成员被提升为管理员事件"""
    try:
        chat = event.chat
        user = event.new_chat_member.user
        
        # 记录事件
        logger.info(f"成员被提升为管理员: {user.full_name} (ID: {user.id}) 在群组 {chat.title} (ID: {chat.id})")
        
        # 检查机器人权限
        if not await check_bot_permissions(event.bot, chat.id):
            logger.warning(f"机器人没有足够的权限监控群组 {chat.id} 的管理员变更事件")
            return
            
        notification = (
            f"👑 成员被提升为管理员\n\n"
            f"成员：{user.full_name}\n"
            f"用户ID：{user.id}\n"
            f"群组：{chat.title}\n"
            f"群组ID：{chat.id}"
        )
        await notify_admins(event.bot, notification)
    except Exception as e:
        logger.error(f"处理成员提升事件时出错: {e}")

@group_router.chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    F.old_chat_member.status == ChatMemberStatus.ADMINISTRATOR,
    F.new_chat_member.status == ChatMemberStatus.MEMBER
)
async def handle_member_demote(event: ChatMemberUpdated) -> None:
    """处理成员被取消管理员事件"""
    try:
        chat = event.chat
        user = event.new_chat_member.user
        
        # 记录事件
        logger.info(f"成员被取消管理员: {user.full_name} (ID: {user.id}) 从群组 {chat.title} (ID: {chat.id})")
        
        # 检查机器人权限
        if not await check_bot_permissions(event.bot, chat.id):
            logger.warning(f"机器人没有足够的权限监控群组 {chat.id} 的管理员变更事件")
            return
            
        notification = (
            f"👑 成员被取消管理员\n\n"
            f"成员：{user.full_name}\n"
            f"用户ID：{user.id}\n"
            f"群组：{chat.title}\n"
            f"群组ID：{chat.id}"
        )
        await notify_admins(event.bot, notification)
    except Exception as e:
        logger.error(f"处理成员降级事件时出错: {e}")

async def notify_admins(bot, notification: str) -> None:
    """通知所有管理员"""
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, notification)
        except Exception as e:
            logger.error(f"发送通知给管理员 {admin_id} 失败: {e}") 