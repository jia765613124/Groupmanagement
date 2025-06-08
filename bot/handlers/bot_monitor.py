import logging
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated
from aiogram.enums import ChatMemberStatus
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, JOIN_TRANSITION, LEAVE_TRANSITION

from bot.config import get_config

# 配置日志记录器
logger = logging.getLogger(__name__)
config = get_config()

# 创建机器人监控路由器
bot_router = Router(name="bot_monitor")

@bot_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def handle_bot_join(event: ChatMemberUpdated) -> None:
    """处理机器人加入群组事件"""
    chat = event.chat
    logger.info(f"机器人被添加到群组: {chat.title} (ID: {chat.id})")
    notification = (
        f"🤖 机器人已被添加到新群组\n\n"
        f"群组：{chat.title}\n"
        f"群组ID：{chat.id}"
    )
    await notify_admins(event.bot, notification)

@bot_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=LEAVE_TRANSITION))
async def handle_bot_leave(event: ChatMemberUpdated) -> None:
    """处理机器人离开群组事件"""
    chat = event.chat
    logger.info(f"机器人被移出群组: {chat.title} (ID: {chat.id})")
    notification = (
        f"🤖 机器人已被移出群组\n\n"
        f"群组：{chat.title}\n"
        f"群组ID：{chat.id}"
    )
    await notify_admins(event.bot, notification)

@bot_router.my_chat_member(
    F.chat_member.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR,
    F.chat_member.old_chat_member.status != ChatMemberStatus.ADMINISTRATOR
)
async def handle_bot_admin(event: ChatMemberUpdated) -> None:
    """处理机器人成为管理员事件"""
    chat = event.chat
    logger.info(f"机器人被设为管理员: {chat.title} (ID: {chat.id})")
    notification = (
        f"🤖 机器人已被设为群组管理员\n\n"
        f"群组：{chat.title}\n"
        f"群组ID：{chat.id}"
    )
    await notify_admins(event.bot, notification)

@bot_router.my_chat_member(
    F.chat_member.old_chat_member.status == ChatMemberStatus.ADMINISTRATOR,
    F.chat_member.new_chat_member.status == ChatMemberStatus.MEMBER
)
async def handle_bot_admin_revoke(event: ChatMemberUpdated) -> None:
    """处理机器人被取消管理员事件"""
    chat = event.chat
    logger.info(f"机器人被取消管理员: {chat.title} (ID: {chat.id})")
    notification = (
        f"🤖 机器人已被取消群组管理员\n\n"
        f"群组：{chat.title}\n"
        f"群组ID：{chat.id}"
    )
    await notify_admins(event.bot, notification)

@bot_router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    F.old_chat_member.status == ChatMemberStatus.MEMBER,
    F.new_chat_member.status == ChatMemberStatus.ADMINISTRATOR
)
async def handle_bot_promote(event: ChatMemberUpdated) -> None:
    """处理机器人被提升为管理员事件"""
    try:
        chat = event.chat
        user = event.from_user
        
        # 记录事件
        logger.info(f"机器人被提升为管理员: {chat.title} (ID: {chat.id}) 由 {user.full_name} (ID: {user.id})")
        
        notification = (
            f"🤖 机器人被提升为管理员\n\n"
            f"群组：{chat.title}\n"
            f"群组ID：{chat.id}\n"
            f"操作者：{user.full_name}\n"
            f"操作者ID：{user.id}"
        )
        await notify_admins(event.bot, notification)
    except Exception as e:
        logger.error(f"处理机器人提升事件时出错: {e}")

@bot_router.my_chat_member(
    F.chat.type.in_({"group", "supergroup"}),
    F.old_chat_member.status == ChatMemberStatus.ADMINISTRATOR,
    F.new_chat_member.status == ChatMemberStatus.MEMBER
)
async def handle_bot_demote(event: ChatMemberUpdated) -> None:
    """处理机器人被取消管理员事件"""
    try:
        chat = event.chat
        user = event.from_user
        
        # 记录事件
        logger.info(f"机器人被取消管理员: {chat.title} (ID: {chat.id}) 由 {user.full_name} (ID: {user.id})")
        
        notification = (
            f"🤖 机器人被取消管理员\n\n"
            f"群组：{chat.title}\n"
            f"群组ID：{chat.id}\n"
            f"操作者：{user.full_name}\n"
            f"操作者ID：{user.id}"
        )
        await notify_admins(event.bot, notification)
    except Exception as e:
        logger.error(f"处理机器人降级事件时出错: {e}")

async def notify_admins(bot, notification: str) -> None:
    """通知所有管理员"""
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, notification)
        except Exception as e:
            logger.error(f"发送通知给管理员 {admin_id} 失败: {e}") 