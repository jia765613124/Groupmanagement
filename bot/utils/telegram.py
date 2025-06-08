import re
from typing import Dict, Any, Optional

from aiogram.types import Message


def sanitize_text(text: Optional[str]) -> str:
    """清理文本中的特殊字符和实体标签"""
    if not text:
        return ""
    
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 移除特殊实体标签
    text = re.sub(r'telethon\.tl\.types\.[a-zA-Z]+', '', text)
    
    # 移除其他特殊字符
    text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
    
    return text.strip()


async def get_chat_info(message: Message) -> Optional[Dict[str, Any]]:
    """获取聊天信息"""
    try:
        chat = message.chat
        
        # 确定类型
        chat_type = "群组" if chat.type in ["group", "supergroup"] else "频道"
        
        # 获取基本信息
        info = {
            "id": chat.id,
            "type": chat_type,
            "title": chat.title,
            "username": chat.username,
            "description": getattr(chat, 'description', ''),
            "members_count": getattr(chat, 'members_count', 0),
            "public": not chat.has_private_forwards if hasattr(chat, 'has_private_forwards') else True
        }
        
        return info
    except Exception as e:
        print(f"获取聊天信息失败: {e}")
        return None 