"""
群组信息获取工具
提供获取Telegram群组ID和名称的方法
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from telethon import TelegramClient
from telethon.tl.types import Chat, Channel, User

logger = logging.getLogger(__name__)

class GroupInfoHelper:
    """群组信息获取助手"""
    
    def __init__(self, client: TelegramClient):
        self.client = client
        self._group_cache = {}  # 缓存群组信息
    
    async def get_chat_info(self, chat_id: int) -> Optional[Dict]:
        """获取聊天信息"""
        try:
            # 从缓存获取
            if chat_id in self._group_cache:
                return self._group_cache[chat_id]
            
            # 获取聊天实体
            entity = await self.client.get_entity(chat_id)
            
            if isinstance(entity, (Chat, Channel)):
                info = {
                    'id': entity.id,
                    'title': getattr(entity, 'title', ''),
                    'username': getattr(entity, 'username', ''),
                    'type': 'group' if isinstance(entity, Chat) else 'channel',
                    'participants_count': getattr(entity, 'participants_count', 0),
                    'verified': getattr(entity, 'verified', False),
                    'scam': getattr(entity, 'scam', False),
                    'fake': getattr(entity, 'fake', False),
                }
                
                # 缓存结果
                self._group_cache[chat_id] = info
                return info
            else:
                logger.warning(f"实体 {chat_id} 不是群组或频道")
                return None
                
        except Exception as e:
            logger.error(f"获取群组信息失败 {chat_id}: {e}")
            return None
    
    async def get_my_groups(self) -> List[Dict]:
        """获取机器人所在的群组列表"""
        try:
            groups = []
            
            # 获取对话列表
            async for dialog in self.client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    entity = dialog.entity
                    info = {
                        'id': entity.id,
                        'title': getattr(entity, 'title', ''),
                        'username': getattr(entity, 'username', ''),
                        'type': 'group' if dialog.is_group else 'channel',
                        'unread_count': dialog.unread_count,
                        'last_message_date': dialog.date.isoformat() if dialog.date else None,
                    }
                    groups.append(info)
            
            return groups
            
        except Exception as e:
            logger.error(f"获取群组列表失败: {e}")
            return []
    
    async def search_groups(self, query: str) -> List[Dict]:
        """搜索群组"""
        try:
            results = []
            
            # 搜索群组
            async for result in self.client.iter_dialogs():
                if (result.is_group or result.is_channel) and query.lower() in result.title.lower():
                    entity = result.entity
                    info = {
                        'id': entity.id,
                        'title': getattr(entity, 'title', ''),
                        'username': getattr(entity, 'username', ''),
                        'type': 'group' if result.is_group else 'channel',
                    }
                    results.append(info)
            
            return results
            
        except Exception as e:
            logger.error(f"搜索群组失败: {e}")
            return []
    
    def format_group_info(self, group_info: Dict) -> str:
        """格式化群组信息"""
        if not group_info:
            return "❌ 无法获取群组信息"
        
        info = f"📋 **群组信息**\n\n"
        info += f"🆔 **群组ID:** `{group_info['id']}`\n"
        info += f"📝 **群组名称:** {group_info['title']}\n"
        
        if group_info.get('username'):
            info += f"🔗 **用户名:** @{group_info['username']}\n"
        
        info += f"📊 **类型:** {group_info['type']}\n"
        
        if group_info.get('participants_count'):
            info += f"👥 **成员数:** {group_info['participants_count']:,}\n"
        
        # 状态信息
        status = []
        if group_info.get('verified'):
            status.append("✅ 认证")
        if group_info.get('scam'):
            status.append("⚠️ 诈骗")
        if group_info.get('fake'):
            status.append("❌ 虚假")
        
        if status:
            info += f"🏷️ **状态:** {' '.join(status)}\n"
        
        return info
    
    def format_group_list(self, groups: List[Dict], title: str = "群组列表") -> str:
        """格式化群组列表"""
        if not groups:
            return f"📋 **{title}**\n\n暂无群组"
        
        info = f"📋 **{title}** (共 {len(groups)} 个)\n\n"
        
        for i, group in enumerate(groups[:20], 1):  # 最多显示20个
            info += f"{i}. **{group['title']}**\n"
            info += f"   ID: `{group['id']}`\n"
            if group.get('username'):
                info += f"   用户名: @{group['username']}\n"
            info += f"   类型: {group['type']}\n\n"
        
        if len(groups) > 20:
            info += f"... 还有 {len(groups) - 20} 个群组"
        
        return info

# 全局实例
group_info_helper = None

async def get_group_info_helper(client: TelegramClient) -> GroupInfoHelper:
    """获取群组信息助手实例"""
    global group_info_helper
    if group_info_helper is None:
        group_info_helper = GroupInfoHelper(client)
    return group_info_helper

# 便捷函数
async def get_chat_info(client: TelegramClient, chat_id: int) -> Optional[Dict]:
    """获取聊天信息"""
    helper = await get_group_info_helper(client)
    return await helper.get_chat_info(chat_id)

async def get_my_groups(client: TelegramClient) -> List[Dict]:
    """获取机器人所在的群组列表"""
    helper = await get_group_info_helper(client)
    return await helper.get_my_groups()

async def search_groups(client: TelegramClient, query: str) -> List[Dict]:
    """搜索群组"""
    helper = await get_group_info_helper(client)
    return await helper.search_groups(query) 