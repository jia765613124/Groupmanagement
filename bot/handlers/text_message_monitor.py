"""
文字消息监控处理器
专门监控群组中的文字消息，并提供处理功能
"""

import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from aiogram.filters import Command

logger = logging.getLogger(__name__)

# 创建文字消息监控路由器
text_message_monitor_router = Router(name="text_message_monitor")

# 文字消息统计数据
text_message_stats = {
    "total_text_messages": 0,
    "group_text_messages": {},  # 按群组统计文字消息
    "user_text_messages": {},   # 按用户统计文字消息
    "keyword_stats": {},        # 关键词统计
    "message_length_stats": {}, # 消息长度统计
    "start_time": datetime.now()
}

class TextMessageMonitor:
    """文字消息监控器"""
    
    def __init__(self):
        self.start_time = datetime.now()
        # 定义关键词列表（可以根据需要修改）
        self.keywords = [
            "你好", "大家好", "谢谢", "再见", "欢迎",
            "问题", "帮助", "支持", "信息", "通知",
            "重要", "紧急", "注意", "提醒", "更新"
        ]
        
        # 定义敏感词列表（可以根据需要修改）
        self.sensitive_words = [
            "垃圾", "广告", "诈骗", "色情", "暴力",
            "政治", "敏感", "违法", "违规", "不当"
        ]
    
    def log_text_message(self, message: Message, content: str):
        """记录文字消息"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_time = datetime.now()
        
        # 更新总文字消息数
        text_message_stats["total_text_messages"] += 1
        
        # 按群组统计
        if chat_id not in text_message_stats["group_text_messages"]:
            text_message_stats["group_text_messages"][chat_id] = {
                "total": 0,
                "users": set(),
                "keywords": {},
                "sensitive_count": 0,
                "last_message": None
            }
        text_message_stats["group_text_messages"][chat_id]["total"] += 1
        text_message_stats["group_text_messages"][chat_id]["users"].add(user_id)
        text_message_stats["group_text_messages"][chat_id]["last_message"] = current_time
        
        # 按用户统计
        if user_id not in text_message_stats["user_text_messages"]:
            text_message_stats["user_text_messages"][user_id] = {
                "total": 0,
                "groups": set(),
                "keywords": {},
                "sensitive_count": 0,
                "last_message": None
            }
        text_message_stats["user_text_messages"][user_id]["total"] += 1
        text_message_stats["user_text_messages"][user_id]["groups"].add(chat_id)
        text_message_stats["user_text_messages"][user_id]["last_message"] = current_time
        
        # 消息长度统计
        message_length = len(content)
        if message_length not in text_message_stats["message_length_stats"]:
            text_message_stats["message_length_stats"][message_length] = 0
        text_message_stats["message_length_stats"][message_length] += 1
        
        # 关键词检测
        found_keywords = self.detect_keywords(content)
        for keyword in found_keywords:
            # 全局关键词统计
            if keyword not in text_message_stats["keyword_stats"]:
                text_message_stats["keyword_stats"][keyword] = 0
            text_message_stats["keyword_stats"][keyword] += 1
            
            # 群组关键词统计
            if keyword not in text_message_stats["group_text_messages"][chat_id]["keywords"]:
                text_message_stats["group_text_messages"][chat_id]["keywords"][keyword] = 0
            text_message_stats["group_text_messages"][chat_id]["keywords"][keyword] += 1
            
            # 用户关键词统计
            if keyword not in text_message_stats["user_text_messages"][user_id]["keywords"]:
                text_message_stats["user_text_messages"][user_id]["keywords"][keyword] = 0
            text_message_stats["user_text_messages"][user_id]["keywords"][keyword] += 1
        
        # 敏感词检测
        sensitive_words_found = self.detect_sensitive_words(content)
        if sensitive_words_found:
            text_message_stats["group_text_messages"][chat_id]["sensitive_count"] += 1
            text_message_stats["user_text_messages"][user_id]["sensitive_count"] += 1
        
        # 记录日志
        log_message = (
            f"文字消息 | 用户: {message.from_user.full_name} (ID: {user_id}) | "
            f"群组: {message.chat.title} (ID: {chat_id}) | "
            f"长度: {message_length} | "
            f"内容: {content[:100]}{'...' if len(content) > 100 else ''}"
        )
        
        if found_keywords:
            log_message += f" | 关键词: {', '.join(found_keywords)}"
        
        if sensitive_words_found:
            log_message += f" | 敏感词: {', '.join(sensitive_words_found)}"
        
        logger.info(log_message)
        
        return {
            "keywords": found_keywords,
            "sensitive_words": sensitive_words_found,
            "message_length": message_length
        }
    
    def detect_keywords(self, content: str) -> List[str]:
        """检测关键词"""
        found_keywords = []
        for keyword in self.keywords:
            if keyword in content:
                found_keywords.append(keyword)
        return found_keywords
    
    def detect_sensitive_words(self, content: str) -> List[str]:
        """检测敏感词"""
        found_sensitive = []
        for word in self.sensitive_words:
            if word in content:
                found_sensitive.append(word)
        return found_sensitive
    
    def add_keyword(self, keyword: str):
        """添加关键词"""
        if keyword not in self.keywords:
            self.keywords.append(keyword)
            logger.info(f"添加关键词: {keyword}")
    
    def add_sensitive_word(self, word: str):
        """添加敏感词"""
        if word not in self.sensitive_words:
            self.sensitive_words.append(word)
            logger.info(f"添加敏感词: {word}")
    
    def remove_keyword(self, keyword: str):
        """移除关键词"""
        if keyword in self.keywords:
            self.keywords.remove(keyword)
            logger.info(f"移除关键词: {keyword}")
    
    def remove_sensitive_word(self, word: str):
        """移除敏感词"""
        if word in self.sensitive_words:
            self.sensitive_words.remove(word)
            logger.info(f"移除敏感词: {word}")

# 全局文字消息监控器实例
text_monitor = TextMessageMonitor()

@text_message_monitor_router.message(
    F.text,
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP})
)
async def monitor_text_messages(message: Message) -> None:
    """监控群组中的文字消息"""
    try:
        content = message.text.strip()
        
        # 跳过空消息
        if not content:
            return
        
        # 记录文字消息
        analysis_result = text_monitor.log_text_message(message, content)
        
        # 这里可以添加您的文字消息处理逻辑
        await process_text_message(message, content, analysis_result)
        
    except Exception as e:
        logger.error(f"监控文字消息时出错: {e}")

async def process_text_message(message: Message, content: str, analysis_result: Dict[str, Any]):
    """处理文字消息"""
    try:
        # 示例处理逻辑，您可以根据需要修改
        
        # 1. 敏感词处理
        if analysis_result["sensitive_words"]:
            logger.warning(f"检测到敏感词: {analysis_result['sensitive_words']}")
            # 可以在这里添加自动删除、警告等处理
        
        # 2. 关键词响应
        if analysis_result["keywords"]:
            logger.info(f"检测到关键词: {analysis_result['keywords']}")
            # 可以在这里添加自动回复等处理
        
        # 3. 长消息处理
        if analysis_result["message_length"] > 500:
            logger.info("检测到长消息")
            # 可以在这里添加长消息的特殊处理
        
        # 4. 链接检测
        if "http" in content or "www." in content:
            logger.info("检测到链接")
            # 可以在这里添加链接处理逻辑
        
        # 5. 表情符号检测
        emoji_pattern = re.compile(r'[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+')
        emojis = emoji_pattern.findall(content)
        if emojis:
            logger.info(f"检测到表情符号: {emojis}")
        
        # 6. 数字检测
        numbers = re.findall(r'\d+', content)
        if numbers:
            logger.info(f"检测到数字: {numbers}")
        
        # 7. 英文单词检测
        english_words = re.findall(r'\b[a-zA-Z]+\b', content)
        if english_words:
            logger.info(f"检测到英文单词: {english_words}")
        
    except Exception as e:
        logger.error(f"处理文字消息时出错: {e}")

def get_text_message_stats() -> Dict[str, Any]:
    """获取文字消息统计信息"""
    stats = text_message_stats.copy()
    
    # 转换set为list以便JSON序列化
    for chat_id, chat_data in stats["group_text_messages"].items():
        chat_data["users"] = list(chat_data["users"])
        if chat_data["last_message"]:
            chat_data["last_message"] = chat_data["last_message"].isoformat()
    
    for user_id, user_data in stats["user_text_messages"].items():
        user_data["groups"] = list(user_data["groups"])
        if user_data["last_message"]:
            user_data["last_message"] = user_data["last_message"].isoformat()
    
    # 计算运行时间
    stats["uptime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
    
    return stats

def format_text_message_stats() -> str:
    """格式化文字消息统计信息"""
    stats = get_text_message_stats()
    
    # 格式化运行时间
    uptime_seconds = stats["uptime_seconds"]
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    uptime_str = f"{hours}小时{minutes}分钟{seconds}秒"
    
    # 获取最活跃的群组
    top_groups = sorted(
        stats["group_text_messages"].items(), 
        key=lambda x: x[1]["total"], 
        reverse=True
    )[:5]
    
    # 获取最活跃的用户
    top_users = sorted(
        stats["user_text_messages"].items(), 
        key=lambda x: x[1]["total"], 
        reverse=True
    )[:5]
    
    # 获取最常用的关键词
    top_keywords = sorted(
        stats["keyword_stats"].items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:5]
    
    message = f"📝 **文字消息监控统计**\n\n"
    message += f"⏱️ **运行时间:** {uptime_str}\n"
    message += f"📈 **总文字消息数:** {stats['total_text_messages']}\n"
    message += f"👥 **活跃群组数:** {len(stats['group_text_messages'])}\n"
    message += f"👤 **活跃用户数:** {len(stats['user_text_messages'])}\n\n"
    
    message += f"🔥 **最活跃群组:**\n"
    for chat_id, data in top_groups:
        message += f"• 群组{chat_id}: {data['total']}条消息 ({len(data['users'])}个用户)\n"
    
    message += f"\n👤 **最活跃用户:**\n"
    for user_id, data in top_users:
        message += f"• 用户{user_id}: {data['total']}条消息 ({len(data['groups'])}个群组)\n"
    
    if top_keywords:
        message += f"\n🔑 **最常用关键词:**\n"
        for keyword, count in top_keywords:
            percentage = (count / stats['total_text_messages']) * 100 if stats['total_text_messages'] > 0 else 0
            message += f"• {keyword}: {count}次 ({percentage:.1f}%)\n"
    
    return message

# 添加统计命令
@text_message_monitor_router.message(Command("text_stats"))
async def show_text_stats_command(message: Message) -> None:
    """显示文字消息统计信息"""
    try:
        # 检查权限（仅管理员）
        from bot.config import get_config
        config = get_config()
        
        if message.from_user.id not in config.ADMIN_IDS:
            await message.reply("❌ 此命令仅限管理员使用")
            return
        
        stats_message = format_text_message_stats()
        await message.reply(stats_message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"显示文字消息统计信息失败: {e}")
        await message.reply("❌ 获取统计信息失败")

@text_message_monitor_router.message(Command("add_keyword"))
async def add_keyword_command(message: Message) -> None:
    """添加关键词"""
    try:
        # 检查权限（仅管理员）
        from bot.config import get_config
        config = get_config()
        
        if message.from_user.id not in config.ADMIN_IDS:
            await message.reply("❌ 此命令仅限管理员使用")
            return
        
        # 解析命令参数
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ 请提供关键词，格式: /add_keyword 关键词")
            return
        
        keyword = args[1]
        text_monitor.add_keyword(keyword)
        await message.reply(f"✅ 已添加关键词: {keyword}")
        
    except Exception as e:
        logger.error(f"添加关键词失败: {e}")
        await message.reply("❌ 添加关键词失败")

@text_message_monitor_router.message(Command("add_sensitive"))
async def add_sensitive_word_command(message: Message) -> None:
    """添加敏感词"""
    try:
        # 检查权限（仅管理员）
        from bot.config import get_config
        config = get_config()
        
        if message.from_user.id not in config.ADMIN_IDS:
            await message.reply("❌ 此命令仅限管理员使用")
            return
        
        # 解析命令参数
        args = message.text.split()
        if len(args) < 2:
            await message.reply("❌ 请提供敏感词，格式: /add_sensitive 敏感词")
            return
        
        word = args[1]
        text_monitor.add_sensitive_word(word)
        await message.reply(f"✅ 已添加敏感词: {word}")
        
    except Exception as e:
        logger.error(f"添加敏感词失败: {e}")
        await message.reply("❌ 添加敏感词失败") 