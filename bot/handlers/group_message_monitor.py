"""
群组消息监控处理器
监控群组中所有成员发送的消息，包括文本、图片、视频等
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ChatType
from aiogram.filters import Command

logger = logging.getLogger(__name__)

# 创建群组消息监控路由器
group_message_monitor_router = Router(name="group_message_monitor")

# 消息统计数据
message_stats = {
    "total_messages": 0,
    "group_messages": {},  # 按群组统计消息
    "user_messages": {},   # 按用户统计消息
    "message_types": {},   # 按消息类型统计
    "hourly_stats": {},    # 按小时统计
    "daily_stats": {},     # 按天统计
    "start_time": datetime.now()
}

class GroupMessageMonitor:
    """群组消息监控器"""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def log_message(self, message: Message, message_type: str, content: str):
        """记录消息"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_time = datetime.now()
        
        # 更新总消息数
        message_stats["total_messages"] += 1
        
        # 按群组统计
        if chat_id not in message_stats["group_messages"]:
            message_stats["group_messages"][chat_id] = {
                "total": 0,
                "users": set(),
                "types": {},
                "last_message": None
            }
        message_stats["group_messages"][chat_id]["total"] += 1
        message_stats["group_messages"][chat_id]["users"].add(user_id)
        message_stats["group_messages"][chat_id]["last_message"] = current_time
        
        # 按消息类型统计
        if message_type not in message_stats["group_messages"][chat_id]["types"]:
            message_stats["group_messages"][chat_id]["types"][message_type] = 0
        message_stats["group_messages"][chat_id]["types"][message_type] += 1
        
        # 按用户统计
        if user_id not in message_stats["user_messages"]:
            message_stats["user_messages"][user_id] = {
                "total": 0,
                "groups": set(),
                "types": {},
                "last_message": None
            }
        message_stats["user_messages"][user_id]["total"] += 1
        message_stats["user_messages"][user_id]["groups"].add(chat_id)
        message_stats["user_messages"][user_id]["last_message"] = current_time
        
        # 按消息类型统计
        if message_type not in message_stats["user_messages"][user_id]["types"]:
            message_stats["user_messages"][user_id]["types"][message_type] = 0
        message_stats["user_messages"][user_id]["types"][message_type] += 1
        
        # 全局消息类型统计
        if message_type not in message_stats["message_types"]:
            message_stats["message_types"][message_type] = 0
        message_stats["message_types"][message_type] += 1
        
        # 按小时统计
        hour_key = current_time.strftime("%Y-%m-%d %H:00")
        if hour_key not in message_stats["hourly_stats"]:
            message_stats["hourly_stats"][hour_key] = 0
        message_stats["hourly_stats"][hour_key] += 1
        
        # 按天统计
        day_key = current_time.strftime("%Y-%m-%d")
        if day_key not in message_stats["daily_stats"]:
            message_stats["daily_stats"][day_key] = 0
        message_stats["daily_stats"][day_key] += 1
        
        # 记录日志
        logger.info(
            f"群组消息 | 用户: {message.from_user.full_name} (ID: {user_id}) | "
            f"群组: {message.chat.title} (ID: {chat_id}) | "
            f"类型: {message_type} | "
            f"内容: {content[:100]}{'...' if len(content) > 100 else ''}"
        )

# 全局消息监控器实例
message_monitor = GroupMessageMonitor()

@group_message_monitor_router.message(
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})
)
async def monitor_group_messages(message: Message) -> None:
    """监控群组中的所有消息"""
    try:
        # 获取消息类型和内容
        message_type = "unknown"
        content = ""
        
        if message.text:
            message_type = "text"
            content = message.text
        elif message.photo:
            message_type = "photo"
            content = message.caption or "图片消息"
        elif message.video:
            message_type = "video"
            content = message.caption or "视频消息"
        elif message.audio:
            message_type = "audio"
            content = message.caption or "音频消息"
        elif message.voice:
            message_type = "voice"
            content = "语音消息"
        elif message.document:
            message_type = "document"
            content = f"文档: {message.document.file_name}"
        elif message.sticker:
            message_type = "sticker"
            content = f"贴纸: {message.sticker.emoji}"
        elif message.animation:
            message_type = "animation"
            content = message.caption or "动画消息"
        elif message.contact:
            message_type = "contact"
            content = f"联系人: {message.contact.first_name}"
        elif message.location:
            message_type = "location"
            content = "位置信息"
        elif message.poll:
            message_type = "poll"
            content = f"投票: {message.poll.question}"
        else:
            content = "其他类型消息"
        
        # 记录消息
        message_monitor.log_message(message, message_type, content)
        
    except Exception as e:
        logger.error(f"监控群组消息时出错: {e}")

def get_message_stats() -> Dict[str, Any]:
    """获取消息统计信息"""
    stats = message_stats.copy()
    
    # 转换set为list以便JSON序列化
    for chat_id, chat_data in stats["group_messages"].items():
        chat_data["users"] = list(chat_data["users"])
        if chat_data["last_message"]:
            chat_data["last_message"] = chat_data["last_message"].isoformat()
    
    for user_id, user_data in stats["user_messages"].items():
        user_data["groups"] = list(user_data["groups"])
        if user_data["last_message"]:
            user_data["last_message"] = user_data["last_message"].isoformat()
    
    # 计算运行时间
    stats["uptime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
    
    return stats

def format_message_stats() -> str:
    """格式化消息统计信息"""
    stats = get_message_stats()
    
    # 格式化运行时间
    uptime_seconds = stats["uptime_seconds"]
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours}小时{minutes}分钟{seconds}秒"
    
    # 获取最活跃的群组
    top_groups = sorted(
        stats["group_messages"].items(), 
        key=lambda x: x[1]["total"], 
        reverse=True
    )[:5]
    
    # 获取最活跃的用户
    top_users = sorted(
        stats["user_messages"].items(), 
        key=lambda x: x[1]["total"], 
        reverse=True
    )[:5]
    
    # 获取最常用的消息类型
    top_types = sorted(
        stats["message_types"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    message = f"📊 **群组消息监控统计**\n\n"
    message += f"⏱️ **运行时间:** {uptime_str}\n"
    message += f"📈 **总消息数:** {stats['total_messages']}\n"
    message += f"👥 **活跃群组数:** {len(stats['group_messages'])}\n"
    message += f"👤 **活跃用户数:** {len(stats['user_messages'])}\n\n"
    
    message += f"🔥 **最活跃群组:**\n"
    for chat_id, data in top_groups:
        message += f"• 群组{chat_id}: {data['total']}条消息 ({len(data['users'])}个用户)\n"
    
    message += f"\n👤 **最活跃用户:**\n"
    for user_id, data in top_users:
        message += f"• 用户{user_id}: {data['total']}条消息 ({len(data['groups'])}个群组)\n"
    
    message += f"\n📝 **消息类型分布:**\n"
    for msg_type, count in top_types:
        percentage = (count / stats['total_messages']) * 100 if stats['total_messages'] > 0 else 0
        message += f"• {msg_type}: {count}条 ({percentage:.1f}%)\n"
    
    return message

# 添加统计命令
@group_message_monitor_router.message(Command("msg_stats"))
async def show_message_stats_command(message: Message) -> None:
    """显示消息统计信息"""
    try:
        # 检查权限（仅管理员）
        from bot.config import get_config
        config = get_config()
        
        if message.from_user.id not in config.ADMIN_IDS:
            await message.reply("❌ 此命令仅限管理员使用")
            return
        
        stats_message = format_message_stats()
        await message.reply(stats_message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"显示消息统计信息失败: {e}")
        await message.reply("❌ 获取统计信息失败")

@group_message_monitor_router.message(Command("reset_msg_stats"))
async def reset_message_stats_command(message: Message) -> None:
    """重置消息统计信息"""
    try:
        # 检查权限（仅管理员）
        from bot.config import get_config
        config = get_config()
        
        if message.from_user.id not in config.ADMIN_IDS:
            await message.reply("❌ 此命令仅限管理员使用")
            return
        
        # 重置统计
        global message_stats
        message_stats = {
            "total_messages": 0,
            "group_messages": {},
            "user_messages": {},
            "message_types": {},
            "hourly_stats": {},
            "daily_stats": {},
            "start_time": datetime.now()
        }
        
        await message.reply("✅ 消息统计信息已重置")
        
    except Exception as e:
        logger.error(f"重置消息统计信息失败: {e}")
        await message.reply("❌ 重置统计信息失败")

@group_message_monitor_router.message(Command("group_activity"))
async def show_group_activity_command(message: Message) -> None:
    """显示当前群组活动统计"""
    try:
        chat_id = message.chat.id
        stats = get_message_stats()
        
        if chat_id not in stats["group_messages"]:
            await message.reply("❌ 该群组暂无消息记录")
            return
        
        group_data = stats["group_messages"][chat_id]
        
        # 获取该群组最活跃的用户
        group_users = []
        for user_id, user_data in stats["user_messages"].items():
            if chat_id in user_data["groups"]:
                group_users.append((user_id, user_data["total"]))
        
        top_group_users = sorted(group_users, key=lambda x: x[1], reverse=True)[:5]
        
        message_text = f"📊 **群组活动统计**\n\n"
        message_text += f"📝 **群组:** {message.chat.title}\n"
        message_text += f"📈 **总消息数:** {group_data['total']}\n"
        message_text += f"👥 **活跃用户数:** {len(group_data['users'])}\n\n"
        
        message_text += f"📝 **消息类型分布:**\n"
        for msg_type, count in group_data["types"].items():
            percentage = (count / group_data['total']) * 100
            message_text += f"• {msg_type}: {count}条 ({percentage:.1f}%)\n"
        
        message_text += f"\n👤 **最活跃用户:**\n"
        for user_id, count in top_group_users:
            message_text += f"• 用户{user_id}: {count}条消息\n"
        
        await message.reply(message_text, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"显示群组活动统计失败: {e}")
        await message.reply("❌ 获取群组活动统计失败") 