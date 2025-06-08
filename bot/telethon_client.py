import logging
import os
from typing import List, Optional, Dict, Any

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User, ChatParticipantAdmin, ChatParticipantCreator, ChannelParticipantCreator
from telethon.tl.functions.channels import GetFullChannelRequest, JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest, DeleteChatUserRequest
from telethon.tl.types import ChannelParticipantsAdmins
from telethon.errors import ChannelPrivateError, ChatAdminRequiredError, UsernameNotOccupiedError, UsernameInvalidError

from bot.config import get_config

# 设置日志级别为 WARNING，只显示警告和错误信息
logging.getLogger('telethon').setLevel(logging.WARNING)
logging.getLogger('aiogram').setLevel(logging.WARNING)
logging.getLogger('watchfiles').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 只显示重要信息
config = get_config()

class TelegramClientManager:
    """Telegram 客户端管理器"""
    
    def __init__(self):
        """初始化客户端"""
        # 使用现有的会话文件
        self.session_path = os.path.join("sessions", "+8618516300397", "telegram_session.session")
        self.client = TelegramClient(
            session=self.session_path,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            device_model='MacOS',
            system_version='Sonoma',
            app_version='1.0.0'
        )
    
    async def connect(self) -> None:
        """连接客户端"""
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                logger.error("Telethon 会话未授权")
                raise RuntimeError("Telethon 会话未授权")
            logger.info("Telethon 客户端连接成功")
        except Exception as e:
            logger.error(f"连接 Telethon 客户端失败: {e}")
            raise
    
    async def disconnect(self) -> None:
        """断开客户端连接"""
        try:
            await self.client.disconnect()
            logger.info("Telethon 客户端已断开连接")
        except Exception as e:
            logger.error(f"断开 Telethon 客户端连接失败: {e}")
            raise
    
    async def get_channel_info(self, link: str) -> Optional[Dict[str, Any]]:
        """
        获取频道或群组基本信息（仅获取公开信息，不加入）
        
        Args:
            link: 频道/群组链接或用户名
            
        Returns:
            频道/群组基本信息字典，如果获取失败返回None
        """
        try:
            # 处理链接格式
            if link.startswith('https://t.me/'):
                username = link.split('/')[3]
            else:
                username = link.lstrip('@')
            
            # 获取实体
            try:
                entity = await self.client.get_entity(username)
            except Exception as e:
                error_msg = str(e)
                if "wait of" in error_msg and "seconds is required" in error_msg:
                    logger.error(f"获取实体失败: 触发Telegram速率限制，需要等待一段时间后重试")
                    raise Exception("触发Telegram速率限制，请稍后再试")
                else:
                    logger.error(f"获取实体失败: {e}")
                    raise Exception(f"获取频道/群组信息失败: {e}")
            
            if isinstance(entity, (Channel, Chat)):
                # 判断类型
                if isinstance(entity, Channel):
                    entity_type = "频道" if getattr(entity, 'broadcast', False) else "群组"
                else:
                    entity_type = "群组"
                
                # 获取基本信息
                basic_info = {
                    "id": entity.id,
                    "title": entity.title,
                    "username": getattr(entity, 'username', None),
                    "type": entity_type,
                    "is_private": getattr(entity, 'broadcast', False),
                    "is_verified": getattr(entity, 'verified', False),
                    "is_scam": getattr(entity, 'scam', False),
                    "is_fake": getattr(entity, 'fake', False),
                    "date": getattr(entity, 'date', None),
                    "restricted": getattr(entity, 'restricted', False),
                    "restriction_reason": getattr(entity, 'restriction_reason', None),
                    "participants_count": 0  # 默认值
                }
                
                # 尝试获取成员数量（不加入）
                try:
                    if isinstance(entity, Channel):
                        # 对于频道，直接获取完整信息
                        full = await self.client(GetFullChannelRequest(entity))
                        if full and hasattr(full, 'full_chat'):
                            basic_info["participants_count"] = getattr(full.full_chat, 'participants_count', 0)
                    else:
                        # 对于群组，尝试获取完整信息
                        full = await self.client(GetFullChatRequest(entity.id))
                        if full and hasattr(full, 'full_chat'):
                            basic_info["participants_count"] = getattr(full.full_chat, 'participants_count', 0)
                except Exception as e:
                    logger.warning(f"获取成员数量失败: {e}")
                    # 保持默认值0
                
                return basic_info
                
        except Exception as e:
            logger.error(f"获取信息失败: {e}")
            return None
    
    async def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """
        获取群组成员列表
        
        Args:
            group_id: 群组ID
            
        Returns:
            成员信息列表
        """
        try:
            members = []
            async for member in self.client.iter_participants(group_id):
                if isinstance(member, User):
                    members.append({
                        "id": member.id,
                        "first_name": member.first_name,
                        "last_name": member.last_name,
                        "username": member.username,
                        "is_bot": member.bot,
                        "is_verified": member.verified,
                        "is_scam": member.scam,
                        "is_fake": member.fake,
                        "status": member.status,
                        "last_online": member.last_online,
                        "phone": member.phone,
                        "access_hash": member.access_hash
                    })
            return members
        except (ValueError, ChannelPrivateError, ChatAdminRequiredError) as e:
            logger.error(f"获取群组成员列表失败: {e}")
            return []
    
    async def get_channel_info_by_id(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        通过ID获取频道或群组信息（仅获取公开信息，不加入）
        
        Args:
            channel_id: 频道/群组ID
            
        Returns:
            频道/群组信息字典，如果获取失败返回None
        """
        try:
            # 获取实体
            try:
                entity = await self.client.get_entity(channel_id)
            except Exception as e:
                logger.error(f"获取实体失败: {e}")
                return None
            
            if isinstance(entity, (Channel, Chat)):
                # 判断类型
                if isinstance(entity, Channel):
                    entity_type = "频道" if getattr(entity, 'broadcast', False) else "群组"
                else:
                    entity_type = "群组"
                
                # 获取基本信息
                info = {
                    "id": entity.id,
                    "title": entity.title,
                    "username": getattr(entity, 'username', None),
                    "type": entity_type,
                    "is_private": getattr(entity, 'broadcast', False),
                    "is_verified": getattr(entity, 'verified', False),
                    "is_scam": getattr(entity, 'scam', False),
                    "is_fake": getattr(entity, 'fake', False),
                    "date": getattr(entity, 'date', None),
                    "restricted": getattr(entity, 'restricted', False),
                    "restriction_reason": getattr(entity, 'restriction_reason', None),
                    "participants_count": 0  # 默认值
                }
                
                # 尝试获取成员数量（不加入）
                try:
                    if isinstance(entity, Channel):
                        # 对于频道，直接获取完整信息
                        full = await self.client(GetFullChannelRequest(entity))
                        if full and hasattr(full, 'full_chat'):
                            info["participants_count"] = getattr(full.full_chat, 'participants_count', 0)
                    else:
                        # 对于群组，尝试获取完整信息
                        full = await self.client(GetFullChatRequest(entity.id))
                        if full and hasattr(full, 'full_chat'):
                            info["participants_count"] = getattr(full.full_chat, 'participants_count', 0)
                except Exception as e:
                    logger.warning(f"获取成员数量失败: {e}")
                    # 保持默认值0
                
                return info
                
        except Exception as e:
            logger.error(f"获取信息失败: {e}")
            return None

# 创建全局客户端管理器实例
telegram_client = TelegramClientManager() 