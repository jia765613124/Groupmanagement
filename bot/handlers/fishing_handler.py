"""
钓鱼处理器
处理Telegram机器人的钓鱼相关命令和交互
"""

from telethon import TelegramClient, events
from bot.common.fishing_service import FishingService
from bot.common.uow import UoW
from bot.database.db import SessionFactory
import logging

logger = logging.getLogger(__name__)

# 全局变量用于存储服务实例
_fishing_service = None

async def get_fishing_service():
    """获取钓鱼服务实例（异步，手动 new UoW）"""
    global _fishing_service
    if _fishing_service is None:
        async with SessionFactory() as session:
            uow = UoW(session)
            _fishing_service = FishingService(uow)
    return _fishing_service

async def show_fishing_rods(message, telegram_id: int):
    """
    显示钓鱼竿选择界面（供 aiogram 调用）
    """
    try:
        fishing_service = await get_fishing_service()
        
        # 获取钓鱼信息
        fishing_info = await fishing_service.get_fishing_info(telegram_id)
        
        if not fishing_info["success"]:
            await message.edit_text(f"❌ {fishing_info['message']}")
            return
        
        # 构建钓鱼界面消息
        message_text = _build_fishing_interface_message(fishing_info)
        
        # 构建钓鱼竿选择按钮
        keyboard = _build_fishing_keyboard(fishing_info["rods_info"])
        
        await message.edit_text(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"显示钓鱼竿选择界面失败: {e}")
        await message.edit_text("❌ 系统错误，请稍后重试")

async def show_fishing_history(message, telegram_id: int, page: int = 1):
    """
    显示钓鱼历史记录（供 aiogram 调用）
    """
    try:
        fishing_service = await get_fishing_service()
        
        # 计算偏移量
        limit = 10
        offset = (page - 1) * limit
        
        # 获取钓鱼历史
        history_result = await fishing_service.get_fishing_history(telegram_id, limit=limit, offset=offset)
        
        if not history_result["success"]:
            await message.edit_text(f"❌ {history_result['message']}")
            return
        
        # 构建历史记录消息
        message_text = _build_fishing_history_message(history_result)
        
        # 添加分页按钮
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = _build_fishing_history_keyboard(
            current_page=history_result["current_page"],
            total_pages=history_result["total_pages"],
            telegram_id=telegram_id
        )
        
        await message.edit_text(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"显示钓鱼历史记录失败: {e}")
        await message.edit_text("❌ 获取历史记录失败，请稍后重试")

async def handle_fishing_callback(callback_query, rod_type: str):
    """
    处理钓鱼回调（供 aiogram 调用）
    """
    try:
        telegram_id = callback_query.from_user.id
        fishing_service = await get_fishing_service()
        
        # 执行钓鱼
        from bot.config import get_config
        config = get_config()
        # 如果配置中有subscription_link则使用，否则使用默认值
        subscription_link = getattr(config, "subscription_link", "https://t.me/your_subscription")
        
        # 获取用户完整名称
        player_name = callback_query.from_user.full_name or f"用户{telegram_id}"
        
        result = await fishing_service.fish(
            telegram_id=telegram_id,
            rod_type=rod_type,
            subscription_link=subscription_link,
            player_name=player_name  # 传递用户名称
        )
        
        # 构建结果消息
        message_text = _build_fishing_result_message(result)
        
        # 如果有传说鱼通知，发送到群组并发红包
        if result.get("notification"):
            # 这里直接使用前面已经获取的玩家名称
            fish_points = result.get("points", 0)
            await _send_legendary_notification_aiogram(
                notification=result["notification"],
                fish_points=fish_points,
                player_name=player_name
            )
        
        # 添加继续钓鱼按钮
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🎣 继续钓鱼",
                        callback_data="fishing_menu"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="📊 查看记录",
                        callback_data="fishing_history"
                    )
                ]
            ]
        )
        
        try:
            await callback_query.message.edit_text(message_text, reply_markup=keyboard)
            await callback_query.answer()
        except Exception as e:
            logger.warning(f"无法更新钓鱼结果消息: {e}")
            # 尝试发送新消息而不是编辑
            try:
                await callback_query.message.reply(message_text, reply_markup=keyboard)
            except Exception as reply_error:
                logger.error(f"无法发送钓鱼结果消息: {reply_error}")
        
    except Exception as e:
        logger.error(f"处理钓鱼回调失败: {e}")
        try:
            await callback_query.answer("❌ 钓鱼失败，请稍后重试")
        except Exception as answer_error:
            logger.warning(f"无法显示钓鱼失败提示: {answer_error}")

async def _send_legendary_notification_aiogram(notification: str, fish_points: int = 0, player_name: str = ""):
    """发送传说鱼通知到群组（aiogram 版本），并发红包"""
    try:
        # 这里需要配置群组ID，可以从配置文件或环境变量获取
        group_ids = _get_notification_group_ids()
        
        from bot.misc import bot
        sent_to_groups = []
        
        for group_id in group_ids:
            try:
                # 发送通知
                await bot.send_message(group_id, notification)
                sent_to_groups.append(group_id)
                
                # 如果有积分和玩家名，发放红包
                if fish_points > 0 and player_name:
                    from bot.handlers.red_packet_handler import create_red_packet_from_fishing
                    success, red_packet_id = await create_red_packet_from_fishing(
                        chat_id=group_id,
                        player_name=player_name,
                        fish_points=fish_points
                    )
                    if not success:
                        logger.error(f"在群组 {group_id} 创建钓鱼红包失败")
                    else:
                        logger.info(f"在群组 {group_id} 成功创建钓鱼红包: {red_packet_id}")
                
            except Exception as e:
                logger.error(f"发送传说鱼通知到群组 {group_id} 失败: {e}")
        
        return sent_to_groups
                
    except Exception as e:
        logger.error(f"发送传说鱼通知失败: {e}")
        return []

def _build_fishing_interface_message(fishing_info: dict) -> str:
    """构建钓鱼界面消息"""
    user_points = fishing_info["user_points"]
    rods_info = fishing_info["rods_info"]
    
    message = f"🎣 **钓鱼系统**\n\n"
    message += f"💰 当前积分: **{user_points:,}**\n\n"
    message += "**选择钓鱼竿:**\n"
    
    for rod_type, info in rods_info.items():
        status_emoji = "✅" if info["can_use"] else "❌"
        message += f"{status_emoji} **{info['name']}**\n"
        message += f"   消耗: {info['cost']:,} 积分\n"
        message += f"   最低收获: {info['min_points']:,} 积分\n"
        message += f"   {info['description']}\n"
        
        if not info["can_use"]:
            message += f"   ⚠️ 还差 {info['shortage']:,} 积分\n"
        
        message += "\n"
    
    message += "💡 **小贴士:** 高级钓鱼竿钓到大鱼的概率更高哦！"
    
    return message

def _build_fishing_keyboard(rods_info: dict):
    """构建钓鱼键盘（aiogram 版本）"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    for rod_type, info in rods_info.items():
        button_text = f"{info['name']} ({info['cost']:,}积分)"
        if not info["can_use"]:
            button_text += " ❌"
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"fish_{rod_type}"
        )])
    
    # 添加返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回主菜单",
        callback_data="back_to_main"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_fishing_result_message(result: dict) -> str:
    """构建钓鱼结果消息"""
    if not result["success"]:
        return f"❌ {result['message']}"
    
    fish = result["fish"]
    points = result["points"]
    
    message = f"🎣 **钓鱼结果**\n\n"
    
    if result["is_legendary"]:
        message += f"🌟 **传说鱼！** 🌟\n"
        message += f"🎉 恭喜钓到了 **{fish.name}**！\n"
        message += f"💰 获得积分: **{points:,}**\n"
        message += f"💎 {fish.description}\n"
        message += f"\n🏆 全服公告已发送！"
    else:
        message += f"🐟 钓到了 **{fish.name}**\n"
        message += f"💰 获得积分: **{points:,}**\n"
        message += f"💬 {fish.description}"
    
    return message

def _build_fishing_history_keyboard(current_page: int, total_pages: int, telegram_id: int):
    """构建钓鱼历史分页键盘"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    # 分页按钮
    if total_pages > 1:
        row = []
        
        # 上一页按钮
        if current_page > 1:
            row.append(InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"fishing_history_page_{telegram_id}_{current_page - 1}"
            ))
        
        # 页码信息
        row.append(InlineKeyboardButton(
                text=f"📄 {current_page}/{total_pages}",
                callback_data="fishing_history_info"
            ))
        
        # 下一页按钮
        if current_page < total_pages:
            row.append(InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"fishing_history_page_{telegram_id}_{current_page + 1}"
            ))
        
        buttons.append(row)
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回钓鱼菜单",
        callback_data="fishing_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_fishing_history_message(history_result: dict) -> str:
    """构建钓鱼历史消息"""
    history = history_result["history"]
    total = history_result["total"]
    current_page = history_result["current_page"]
    total_pages = history_result["total_pages"]
    
    if not history:
        return "📝 **钓鱼历史**\n\n暂无钓鱼记录"
    
    message = f"📝 **钓鱼历史** (共 {total} 条记录)\n\n"
    
    for record in history:
        # 根据交易类型确定emoji和描述
        if record["type"] == 20:  # 钓鱼费用
            emoji = "🎣"
            action = "钓鱼费用"
        elif record["type"] == 21:  # 钓鱼奖励
            emoji = "🐟"
            action = "钓鱼奖励"
        elif record["type"] == 22:  # 传说鱼奖励
            emoji = "🌟"
            action = "传说鱼奖励"
        else:
            emoji = "💰"
            action = "钓鱼交易"
        
        amount = record["amount"]
        amount_text = f"-{abs(amount):,}" if amount < 0 else f"+{amount:,}"
        
        message += f"{emoji} {record['description']}\n"
        message += f"   {amount_text} 积分\n"
        message += f"   {record['created_at'][:19]}\n\n"
    
    if total_pages > 1:
        message += f"📄 第 {current_page} 页，共 {total_pages} 页"
    
    return message

def _get_notification_group_ids() -> list:
    """获取需要发送通知的群组ID列表"""
    # 从配置中获取群组ID
    from bot.config import get_config
    config = get_config()
    group_ids_str = config.fishing_notification_groups
    if group_ids_str:
        return [int(gid.strip()) for gid in group_ids_str.split(",") if gid.strip()]
    return []

# 保留原有的 Telethon 处理器类（如果需要的话）
class FishingHandler:
    """钓鱼处理器（Telethon 版本）"""
    
    def __init__(self, client: TelegramClient):
        self.client = client
        self.fishing_service = None
        
        # 注册事件处理器
        self._register_handlers()
    
    async def _get_fishing_service(self):
        """获取钓鱼服务实例"""
        if self.fishing_service is None:
            async with SessionFactory() as session:
                uow = UoW(session)
                self.fishing_service = FishingService(uow)
        return self.fishing_service

    def _register_handlers(self):
        """注册事件处理器"""
        
        @self.client.on(events.NewMessage(pattern=r'^/fishing$'))
        async def fishing_command(event):
            """钓鱼命令处理器"""
            await self._handle_fishing_command(event)
        
        @self.client.on(events.CallbackQuery(pattern=r'^fish_(.+)$'))
        async def fishing_callback(event):
            """钓鱼回调处理器"""
            await self._handle_fishing_callback(event)
        
        @self.client.on(events.NewMessage(pattern=r'^/fishing_history$'))
        async def fishing_history_command(event):
            """钓鱼历史命令处理器"""
            await self._handle_fishing_history_command(event)
    
    async def _handle_fishing_command(self, event):
        """处理钓鱼命令"""
        try:
            telegram_id = event.sender_id
            
            # 获取钓鱼信息
            fishing_service = await self._get_fishing_service()
            fishing_info = await fishing_service.get_fishing_info(telegram_id)
            
            if not fishing_info["success"]:
                await event.respond(f"❌ {fishing_info['message']}")
                return
            
            # 构建钓鱼界面消息
            message = self._build_fishing_interface_message(fishing_info)
            
            # 构建钓鱼竿选择按钮
            keyboard = self._build_fishing_keyboard(fishing_info["rods_info"])
            
            await event.respond(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"处理钓鱼命令失败: {e}")
            await event.respond("❌ 系统错误，请稍后重试")
    
    async def _handle_fishing_callback(self, event):
        """处理钓鱼回调"""
        try:
            telegram_id = event.sender_id
            rod_type = event.data.decode().split('_')[1]
            
            # 执行钓鱼
            fishing_service = await self._get_fishing_service()
            
            # 从配置获取订阅链接
            from bot.config import get_config
            config = get_config()
            # 如果配置中有subscription_link则使用，否则使用默认值
            subscription_link = getattr(config, "subscription_link", "https://t.me/your_subscription")
            
            # 获取用户名称
            from telethon.utils import get_display_name
            player_name = get_display_name(await event.get_sender()) or f"用户{telegram_id}"
            
            result = await fishing_service.fish(
                telegram_id=telegram_id,
                rod_type=rod_type,
                subscription_link=subscription_link,
                player_name=player_name  # 传递用户名称
            )
            
            # 构建结果消息
            message = self._build_fishing_result_message(result)
            
            # 如果有传说鱼通知，发送到群组并发红包
            if result.get("notification"):
                # 这里直接使用前面已经获取的玩家名称
                fish_points = result.get("points", 0)
                await self._send_legendary_notification(
                    notification=result["notification"],
                    fish_points=fish_points,
                    player_name=player_name
                )
            
            await event.answer(message)
            
        except Exception as e:
            logger.error(f"处理钓鱼回调失败: {e}")
            await event.answer("❌ 钓鱼失败，请稍后重试")
    
    async def _handle_fishing_history_command(self, event):
        """处理钓鱼历史命令"""
        try:
            telegram_id = event.sender_id
            
            # 获取钓鱼历史
            fishing_service = await self._get_fishing_service()
            history_result = await fishing_service.get_fishing_history(telegram_id, limit=10)
            
            if not history_result["success"]:
                await event.respond(f"❌ {history_result['message']}")
                return
            
            # 构建历史记录消息
            message = self._build_fishing_history_message(history_result)
            
            await event.respond(message)
            
        except Exception as e:
            logger.error(f"处理钓鱼历史命令失败: {e}")
            await event.respond("❌ 获取历史记录失败，请稍后重试")
    
    def _build_fishing_interface_message(self, fishing_info: dict) -> str:
        """构建钓鱼界面消息"""
        user_points = fishing_info["user_points"]
        rods_info = fishing_info["rods_info"]
        
        message = f"🎣 **钓鱼系统**\n\n"
        message += f"💰 当前积分: **{user_points:,}**\n\n"
        message += "**选择钓鱼竿:**\n"
        
        for rod_type, info in rods_info.items():
            status_emoji = "✅" if info["can_use"] else "❌"
            message += f"{status_emoji} **{info['name']}**\n"
            message += f"   消耗: {info['cost']:,} 积分\n"
            message += f"   最低收获: {info['min_points']:,} 积分\n"
            message += f"   {info['description']}\n"
            
            if not info["can_use"]:
                message += f"   ⚠️ 还差 {info['shortage']:,} 积分\n"
            
            message += "\n"
        
        message += "💡 **小贴士:** 高级钓鱼竿钓到大鱼的概率更高哦！"
        
        return message
    
    def _build_fishing_keyboard(self, rods_info: dict):
        """构建钓鱼键盘"""
        from telethon.tl.types import KeyboardButtonCallback
        
        buttons = []
        
        for rod_type, info in rods_info.items():
            button_text = f"{info['name']} ({info['cost']:,}积分)"
            if not info["can_use"]:
                button_text += " ❌"
            
            buttons.append([KeyboardButtonCallback(
                text=button_text,
                data=f"fish_{rod_type}".encode()
            )])
        
        return buttons
    
    def _build_fishing_result_message(self, result: dict) -> str:
        """构建钓鱼结果消息"""
        if not result["success"]:
            return f"❌ {result['message']}"
        
        fish = result["fish"]
        points = result["points"]
        
        message = f"🎣 **钓鱼结果**\n\n"
        
        if result["is_legendary"]:
            message += f"🌟 **传说鱼！** 🌟\n"
            message += f"🎉 恭喜钓到了 **{fish.name}**！\n"
            message += f"💰 获得积分: **{points:,}**\n"
            message += f"💎 {fish.description}\n"
            message += f"\n🏆 全服公告已发送！"
        else:
            message += f"🐟 钓到了 **{fish.name}**\n"
            message += f"💰 获得积分: **{points:,}**\n"
            message += f"💬 {fish.description}"
        
        return message
    
    def _build_fishing_history_message(self, history_result: dict) -> str:
        """构建钓鱼历史消息"""
        history = history_result["history"]
        total = history_result["total"]
        current_page = history_result["current_page"]
        total_pages = history_result["total_pages"]
        
        if not history:
            return "📝 **钓鱼历史**\n\n暂无钓鱼记录"
        
        message = f"📝 **钓鱼历史** (共 {total} 条记录)\n\n"
        
        for record in history:
            # 根据交易类型确定emoji和描述
            if record["type"] == 20:  # 钓鱼费用
                emoji = "🎣"
                action = "钓鱼费用"
            elif record["type"] == 21:  # 钓鱼奖励
                emoji = "🐟"
                action = "钓鱼奖励"
            elif record["type"] == 22:  # 传说鱼奖励
                emoji = "🌟"
                action = "传说鱼奖励"
            else:
                emoji = "💰"
                action = "钓鱼交易"
            
            amount = record["amount"]
            amount_text = f"-{abs(amount):,}" if amount < 0 else f"+{amount:,}"
            
            message += f"{emoji} {record['description']}\n"
            message += f"   {amount_text} 积分\n"
            message += f"   {record['created_at'][:19]}\n\n"
        
        if total_pages > 1:
            message += f"📄 第 {current_page} 页，共 {total_pages} 页"
        
        return message
    
    async def _send_legendary_notification(self, notification: str, fish_points: int = 0, player_name: str = ""):
        """发送传说鱼通知到群组，并发红包"""
        try:
            # 这里需要配置群组ID，可以从配置文件或环境变量获取
            group_ids = self._get_notification_group_ids()
            sent_to_groups = []
            
            for group_id in group_ids:
                try:
                    # 发送通知
                    await self.client.send_message(group_id, notification)
                    sent_to_groups.append(group_id)
                    
                    # 如果有积分和玩家名，发放红包
                    if fish_points > 0 and player_name:
                        # 使用aiogram发红包，需要导入aiogram相关函数
                        from bot.handlers.red_packet_handler import create_red_packet_from_fishing
                        success, red_packet_id = await create_red_packet_from_fishing(
                            chat_id=group_id,
                            player_name=player_name,
                            fish_points=fish_points
                        )
                        if not success:
                            logger.error(f"在群组 {group_id} 创建钓鱼红包失败")
                        else:
                            logger.info(f"在群组 {group_id} 成功创建钓鱼红包: {red_packet_id}")
                    
                except Exception as e:
                    logger.error(f"发送传说鱼通知到群组 {group_id} 失败: {e}")
            
            return sent_to_groups
                    
        except Exception as e:
            logger.error(f"发送传说鱼通知失败: {e}")
            return []
    
    def _get_notification_group_ids(self) -> list:
        """获取需要发送通知的群组ID列表"""
        # 从配置中获取群组ID
        from bot.config import get_config
        config = get_config()
        group_ids_str = config.fishing_notification_groups
        if group_ids_str:
            return [int(gid.strip()) for gid in group_ids_str.split(",") if gid.strip()]
        return [] 