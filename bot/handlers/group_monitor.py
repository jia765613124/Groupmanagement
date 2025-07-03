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
from telethon import TelegramClient, events
from bot.utils.group_info import GroupInfoHelper

from bot.config import get_config

# 配置日志记录器
logger = logging.getLogger(__name__)
config = get_config()

# 创建群组监控路由器
group_router = Router(name="group_monitor")

class GroupMonitor:
    """群组监控器"""
    
    def __init__(self, client: TelegramClient):
        self.client = client
        self.group_helper = GroupInfoHelper(client)
        
        # 注册事件处理器
        self._register_handlers()
    
    def _register_handlers(self):
        """注册事件处理器"""
        
        @self.client.on(events.NewMessage(pattern=r'^/groupinfo$'))
        async def group_info_command(event):
            """群组信息命令处理器"""
            await self._handle_group_info_command(event)
        
        @self.client.on(events.NewMessage(pattern=r'^/mygroups$'))
        async def my_groups_command(event):
            """我的群组命令处理器"""
            await self._handle_my_groups_command(event)
        
        @self.client.on(events.NewMessage(pattern=r'^/searchgroup\s+(.+)$'))
        async def search_group_command(event):
            """搜索群组命令处理器"""
            await self._handle_search_group_command(event)
        
        @self.client.on(events.NewMessage(pattern=r'^/groupid$'))
        async def group_id_command(event):
            """获取当前群组ID命令处理器"""
            await self._handle_group_id_command(event)
    
    async def _handle_group_info_command(self, event):
        """处理群组信息命令"""
        try:
            # 检查权限（仅管理员）
            if not await self._check_admin_permission(event):
                await event.respond("❌ 此命令仅限管理员使用")
                return
            
            # 获取当前群组信息
            chat_id = event.chat_id
            group_info = await self.group_helper.get_chat_info(chat_id)
            
            if group_info:
                message = self.group_helper.format_group_info(group_info)
                await event.respond(message, parse_mode="Markdown")
            else:
                await event.respond("❌ 无法获取群组信息")
                
        except Exception as e:
            logger.error(f"处理群组信息命令失败: {e}")
            await event.respond("❌ 获取群组信息失败")
    
    async def _handle_my_groups_command(self, event):
        """处理我的群组命令"""
        try:
            # 检查权限（仅管理员）
            if not await self._check_admin_permission(event):
                await event.respond("❌ 此命令仅限管理员使用")
                return
            
            # 获取机器人所在的群组列表
            groups = await self.group_helper.get_my_groups()
            
            if groups:
                message = self.group_helper.format_group_list(groups, "机器人所在群组")
                await event.respond(message, parse_mode="Markdown")
            else:
                await event.respond("❌ 无法获取群组列表")
                
        except Exception as e:
            logger.error(f"处理我的群组命令失败: {e}")
            await event.respond("❌ 获取群组列表失败")
    
    async def _handle_search_group_command(self, event):
        """处理搜索群组命令"""
        try:
            # 检查权限（仅管理员）
            if not await self._check_admin_permission(event):
                await event.respond("❌ 此命令仅限管理员使用")
                return
            
            # 获取搜索关键词
            query = event.pattern_match.group(1).strip()
            
            if not query:
                await event.respond("❌ 请输入搜索关键词")
                return
            
            # 搜索群组
            results = await self.group_helper.search_groups(query)
            
            if results:
                message = self.group_helper.format_group_list(results, f"搜索结果: {query}")
                await event.respond(message, parse_mode="Markdown")
            else:
                await event.respond(f"❌ 未找到包含 '{query}' 的群组")
                
        except Exception as e:
            logger.error(f"处理搜索群组命令失败: {e}")
            await event.respond("❌ 搜索群组失败")
    
    async def _handle_group_id_command(self, event):
        """处理获取群组ID命令"""
        try:
            # 获取当前群组信息
            chat_id = event.chat_id
            group_info = await self.group_helper.get_chat_info(chat_id)
            
            if group_info:
                message = f"📋 **当前群组信息**\n\n"
                message += f"🆔 **群组ID:** `{group_info['id']}`\n"
                message += f"📝 **群组名称:** {group_info['title']}\n"
                
                if group_info.get('username'):
                    message += f"🔗 **用户名:** @{group_info['username']}\n"
                
                message += f"📊 **类型:** {group_info['type']}\n"
                
                # 添加配置示例
                message += f"\n🔧 **配置示例:**\n"
                message += f"```python\n"
                message += f"GroupConfig(\n"
                message += f"    group_id={group_info['id']},\n"
                message += f"    group_name=\"{group_info['title']}\",\n"
                message += f"    game_type=\"lottery\",\n"
                message += f"    enabled=True,\n"
                message += f"    admin_only=False,\n"
                message += f"    min_bet=1,\n"
                message += f"    max_bet=100000,\n"
                message += f"    auto_draw=True,\n"
                message += f"    notification_groups=[{group_info['id']}]\n"
                message += f"),\n"
                message += f"```"
                
                await event.respond(message, parse_mode="Markdown")
            else:
                await event.respond("❌ 无法获取群组信息")
                
        except Exception as e:
            logger.error(f"处理群组ID命令失败: {e}")
            await event.respond("❌ 获取群组ID失败")
    
    async def _check_admin_permission(self, event) -> bool:
        """检查管理员权限"""
        try:
            # 获取发送者信息
            sender = await event.get_sender()
            
            # 检查是否是机器人管理员
            if hasattr(sender, 'id'):
                # 这里可以添加管理员ID列表检查
                admin_ids = self._get_admin_ids()
                return sender.id in admin_ids
            
            return False
            
        except Exception as e:
            logger.error(f"检查管理员权限失败: {e}")
            return False
    
    def _get_admin_ids(self) -> list:
        """获取管理员ID列表"""
        # 从环境变量或配置文件获取管理员ID
        import os
        admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
        if admin_ids_str:
            return [int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()]
        return []

# 全局实例
group_monitor = None

async def get_group_monitor(client: TelegramClient) -> GroupMonitor:
    """获取群组监控器实例"""
    global group_monitor
    if group_monitor is None:
        group_monitor = GroupMonitor(client)
    return group_monitor

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