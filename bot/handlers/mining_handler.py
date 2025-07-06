"""
挖矿处理器
处理Telegram机器人的挖矿相关命令和交互
"""

from telethon import TelegramClient, events
from bot.common.mining_service import MiningService
from bot.common.uow import UoW
from bot.database.db import SessionFactory
import logging

logger = logging.getLogger(__name__)

# 全局变量用于存储服务实例
_mining_service = None

async def get_mining_service():
    """获取挖矿服务实例（异步，手动 new UoW）"""
    global _mining_service
    if _mining_service is None:
        async with SessionFactory() as session:
            uow = UoW(session)
            _mining_service = MiningService(uow)
    return _mining_service

async def show_mining_menu(message, telegram_id: int):
    """
    显示挖矿菜单界面（供 aiogram 调用）
    """
    try:
        mining_service = await get_mining_service()
        
        # 获取挖矿信息
        mining_info = await mining_service.get_mining_info(telegram_id)
        
        if not mining_info["success"]:
            await message.answer(f"❌ {mining_info['message']}")
            return
        
        # 构建挖矿界面消息
        message_text = _build_mining_interface_message(mining_info)
        
        # 构建挖矿菜单按钮
        keyboard = _build_mining_menu_keyboard(mining_info)
        
        try:
            # 尝试编辑消息
            await message.edit_text(message_text, reply_markup=keyboard)
        except Exception as edit_error:
            # 如果编辑失败，则发送新消息
            logger.info(f"无法编辑消息，发送新消息: {edit_error}")
            await message.answer(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"显示挖矿菜单失败: {e}")
        # 使用 answer 而不是 edit_text 来确保消息能发送
        await message.answer("❌ 系统错误，请稍后重试")

async def show_mining_cards(message, telegram_id: int, page: int = 1):
    """
    显示矿工卡选择界面（供 aiogram 调用）
    支持分页显示，每页显示5张矿工卡
    """
    try:
        mining_service = await get_mining_service()
        
        # 获取挖矿信息
        mining_info = await mining_service.get_mining_info(telegram_id)
        
        if not mining_info["success"]:
            await message.answer(f"❌ {mining_info['message']}")
            return
        
        # 获取用户的矿工卡列表（分页）
        cards_per_page = 5
        user_cards_result = await mining_service.get_user_mining_cards(
            telegram_id=telegram_id, 
            page=page, 
            limit=cards_per_page
        )
        
        if not user_cards_result["success"]:
            await message.answer(f"❌ {user_cards_result['message']}")
            return
        
        # 构建矿工卡选择界面消息
        message_text = _build_mining_cards_message(mining_info, user_cards_result)
        
        # 构建矿工卡选择按钮（分页）
        keyboard = _build_mining_cards_keyboard(
            mining_info["cards_info"], 
            user_cards_result,
            telegram_id=telegram_id
        )
        
        try:
            # 尝试编辑消息
            await message.edit_text(message_text, reply_markup=keyboard)
        except Exception as edit_error:
            # 如果编辑失败，则发送新消息
            logger.info(f"无法编辑消息，发送新消息: {edit_error}")
            await message.answer(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"显示矿工卡选择界面失败: {e}")
        await message.answer("❌ 系统错误，请稍后重试")

async def handle_mining_purchase_callback(callback_query, card_type: str):
    """
    处理购买矿工卡回调（供 aiogram 调用）
    """
    try:
        telegram_id = callback_query.from_user.id
        mining_service = await get_mining_service()
        
        # 执行购买
        result = await mining_service.purchase_mining_card(
            telegram_id=telegram_id,
            card_type=card_type
        )
        
        # 构建结果消息
        message_text = _build_purchase_result_message(result)
        
        # 添加返回按钮
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 返回挖矿菜单",
                        callback_data="mining_menu"
                    )
                ]
            ]
        )
        
        try:
            # 尝试编辑消息
            await callback_query.message.edit_text(message_text, reply_markup=keyboard)
        except Exception as edit_error:
            # 如果编辑失败，则发送新消息
            logger.info(f"无法编辑消息，发送新消息: {edit_error}")
            await callback_query.message.answer(message_text, reply_markup=keyboard)
            
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"处理购买矿工卡回调失败: {e}")
        await callback_query.answer("❌ 购买失败，请稍后重试")

async def show_pending_rewards(message, telegram_id: int, page: int = 1):
    """
    显示待领取奖励界面（供 aiogram 调用）
    """
    try:
        mining_service = await get_mining_service()
        
        # 计算偏移量
        limit = 10
        offset = (page - 1) * limit
        
        # 获取待领取奖励
        rewards_result = await mining_service.get_pending_rewards(telegram_id, limit=limit, offset=offset)
        
        if not rewards_result["success"]:
            await message.answer(f"❌ {rewards_result['message']}")
            return
        
        # 构建待领取奖励消息
        message_text = _build_pending_rewards_message(rewards_result)
        
        # 添加分页和领取按钮
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = _build_pending_rewards_keyboard(
            current_page=rewards_result["current_page"],
            total_pages=rewards_result["total_pages"],
            telegram_id=telegram_id,
            has_rewards=len(rewards_result["rewards"]) > 0
        )
        
        try:
            # 尝试编辑消息
            await message.edit_text(message_text, reply_markup=keyboard)
        except Exception as edit_error:
            # 如果编辑失败，则发送新消息
            logger.info(f"无法编辑消息，发送新消息: {edit_error}")
            await message.answer(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"显示待领取奖励失败: {e}")
        await message.answer("❌ 获取奖励失败，请稍后重试")

async def handle_claim_rewards_callback(callback_query):
    """
    处理领取奖励回调（供 aiogram 调用）
    """
    try:
        telegram_id = callback_query.from_user.id
        mining_service = await get_mining_service()
        
        # 执行领取奖励
        result = await mining_service.claim_all_rewards(telegram_id)
        
        # 构建结果消息
        message_text = _build_claim_result_message(result)
        
        # 添加返回按钮
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="🔙 返回挖矿菜单",
                        callback_data="mining_menu"
                    )
                ]
            ]
        )
        
        try:
            # 尝试编辑消息
            await callback_query.message.edit_text(message_text, reply_markup=keyboard)
        except Exception as edit_error:
            # 如果编辑失败，则发送新消息
            logger.info(f"无法编辑消息，发送新消息: {edit_error}")
            await callback_query.message.answer(message_text, reply_markup=keyboard)
            
        await callback_query.answer()
        
    except Exception as e:
        logger.error(f"处理领取奖励回调失败: {e}")
        await callback_query.answer("❌ 领取失败，请稍后重试")

async def show_mining_management(message, telegram_id: int, page: int = 1):
    """
    显示矿工卡管理界面（供 aiogram 调用）
    """
    try:
        mining_service = await get_mining_service()
        
        # 获取用户的矿工卡列表（分页）
        cards_per_page = 8
        user_cards_result = await mining_service.get_user_mining_cards(
            telegram_id=telegram_id, 
            page=page, 
            limit=cards_per_page
        )
        
        if not user_cards_result["success"]:
            await message.answer(f"❌ {user_cards_result['message']}")
            return
        
        # 构建管理界面消息
        message_text = _build_mining_management_message(user_cards_result)
        
        # 构建管理界面按钮
        keyboard = _build_mining_management_keyboard(user_cards_result, telegram_id)
        
        try:
            # 尝试编辑消息
            await message.edit_text(message_text, reply_markup=keyboard)
        except Exception as edit_error:
            # 如果编辑失败，则发送新消息
            logger.info(f"无法编辑消息，发送新消息: {edit_error}")
            await message.answer(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"显示矿工卡管理界面失败: {e}")
        await message.answer("❌ 系统错误，请稍后重试")

async def show_mining_history(message, telegram_id: int, page: int = 1):
    """
    显示挖矿历史界面（供 aiogram 调用）
    支持分页显示，每页显示10条历史记录
    """
    try:
        mining_service = await get_mining_service()
        
        # 获取挖矿历史记录
        history_result = await mining_service.get_mining_history(
            telegram_id=telegram_id, 
            page=page, 
            limit=10
        )
        
        if not history_result["success"]:
            await message.answer(f"❌ {history_result['message']}")
            return
        
        # 构建挖矿历史界面消息
        message_text = _build_mining_history_message(history_result)
        
        # 构建挖矿历史按钮（分页）
        keyboard = _build_mining_history_keyboard(history_result, telegram_id)
        
        try:
            # 尝试编辑消息
            await message.edit_text(message_text, reply_markup=keyboard)
        except Exception as edit_error:
            # 如果编辑失败，则发送新消息
            logger.info(f"无法编辑消息，发送新消息: {edit_error}")
            await message.answer(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"显示挖矿历史界面失败: {e}")
        await message.answer("❌ 系统错误，请稍后重试")

def _build_mining_interface_message(mining_info: dict) -> str:
    """构建挖矿界面消息"""
    wallet_balance = mining_info["wallet_balance"]
    pending_rewards = mining_info["pending_rewards"]
    pending_points = mining_info["pending_points"]
    
    message = f"⛏️ **挖矿系统**\n\n"
    message += f"💰 钱包余额: **{wallet_balance:.2f}U**\n"
    
    if pending_rewards > 0:
        message += f"🎁 待领取奖励: **{pending_rewards}** 笔\n"
        message += f"💎 待领取积分: **{pending_points:,}**\n\n"
    else:
        message += f"🎁 待领取奖励: **0** 笔\n\n"
    
    message += "**选择操作:**\n"
    message += "🔧 购买矿工卡 - 使用USDT购买矿工卡进行挖矿\n"
    message += "🎁 领取奖励 - 领取已挖取的积分奖励\n"
    message += "📊 挖矿统计 - 查看挖矿历史和统计信息\n"
    
    return message

def _build_mining_menu_keyboard(mining_info: dict):
    """构建挖矿菜单键盘（aiogram 版本）"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    # 购买矿工卡按钮
    buttons.append([InlineKeyboardButton(
        text="🔧 购买矿工卡",
        callback_data="mining_cards"
    )])
    
    # 管理矿工卡按钮
    buttons.append([InlineKeyboardButton(
        text="📊 管理矿工卡",
        callback_data="mining_management"
    )])
    
    # 领取奖励按钮（如果有待领取的奖励）
    if mining_info["pending_rewards"] > 0:
        buttons.append([InlineKeyboardButton(
            text=f"🎁 领取奖励 ({mining_info['pending_rewards']}笔)",
            callback_data="mining_rewards"
        )])
    
    # 添加挖矿历史按钮
    buttons.append([InlineKeyboardButton(
        text="📜 挖矿历史",
        callback_data="mining_history"
    )])
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回主菜单",
        callback_data="back_to_main"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_mining_cards_message(mining_info: dict, user_cards_result: dict) -> str:
    """构建矿工卡选择消息"""
    wallet_balance = mining_info["wallet_balance"]
    cards_info = mining_info["cards_info"]
    user_cards = user_cards_result.get("cards", [])
    total_cards = user_cards_result.get("total_count", 0)
    current_page = user_cards_result.get("current_page", 1)
    total_pages = user_cards_result.get("total_pages", 1)
    
    message = f"🔧 **购买矿工卡**\n\n"
    message += f"💰 钱包余额: **{wallet_balance:.2f}U**\n"
    message += f"📊 总矿工卡: **{total_cards}** 张\n\n"
    
    # 显示用户现有的矿工卡（当前页）
    if user_cards:
        message += "**您现有的矿工卡:**\n"
        for card in user_cards:
            status_emoji = "⛏️" if card["status"] == 1 else "✅" if card["status"] == 2 else "❌"
            message += f"{status_emoji} {card['card_type']}矿工卡\n"
            message += f"   💰 每日积分: {card['daily_points']:,}\n"
            message += f"   ⏰ 剩余天数: {card['remaining_days']}天\n"
            message += f"   💎 已获得: {card['earned_points']:,}积分\n"
            message += f"   📅 结束时间: {card['end_time'][:10]}\n\n"
    
    message += "**选择矿工卡类型:**\n"
    
    for card_type, info in cards_info.items():
        status_emoji = "✅" if info["can_purchase"] else "❌"
        message += f"{status_emoji} **{info['name']}**\n"
        message += f"   价格: {info['cost_usdt']:.2f}U\n"
        message += f"   每日积分: {info['daily_points']:,}\n"
        message += f"   持续天数: {info['duration_days']}天\n"
        message += f"   总积分: {info['total_points']:,}\n"
        message += f"   已拥有: {info['user_count']}/{info['max_cards']}张\n"
        message += f"   {info['description']}\n"
        
        if not info["can_purchase"]:
            if info["user_count"] >= info["max_cards"]:
                message += f"   ⚠️ 已达到最大数量限制\n"
            else:
                message += f"   ⚠️ 余额不足\n"
        
        message += "\n"
    
    if total_pages > 1:
        message += f"📄 第 {current_page} 页，共 {total_pages} 页\n\n"
    
    message += "💡 **小贴士:** 高级矿工卡每日挖取的积分更多！"
    
    return message

def _build_mining_cards_keyboard(cards_info: dict, user_cards_result: dict, telegram_id: int):
    """构建矿工卡选择键盘（aiogram 版本）"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    # 购买矿工卡按钮
    for card_type, info in cards_info.items():
        button_text = f"{info['name']} ({info['cost_usdt']:.2f}U)"
        if not info["can_purchase"]:
            button_text += " ❌"
        
        buttons.append([InlineKeyboardButton(
            text=button_text,
            callback_data=f"mining_purchase_{card_type}"
        )])
    
    # 分页按钮（如果用户矿工卡很多）
    current_page = user_cards_result.get("current_page", 1)
    total_pages = user_cards_result.get("total_pages", 1)
    
    if total_pages > 1:
        row = []
        
        # 上一页按钮
        if current_page > 1:
            row.append(InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"mining_cards_page_{telegram_id}_{current_page - 1}"
            ))
        
        # 页码信息
        row.append(InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="mining_cards_info"
        ))
        
        # 下一页按钮
        if current_page < total_pages:
            row.append(InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"mining_cards_page_{telegram_id}_{current_page + 1}"
            ))
        
        buttons.append(row)
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回挖矿菜单",
        callback_data="mining_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_purchase_result_message(result: dict) -> str:
    """构建购买结果消息"""
    if not result["success"]:
        return f"❌ {result['message']}"
    
    mining_card = result["mining_card"]
    
    message = f"✅ **购买成功！**\n\n"
    message += f"🎉 成功购买 **{mining_card['name']}**\n"
    message += f"💰 每日挖取: **{mining_card['daily_points']:,}** 积分\n"
    message += f"⏰ 持续天数: **{mining_card['total_days']}** 天\n"
    message += f"📅 开始时间: {mining_card['start_time'].strftime('%Y-%m-%d %H:%M')}\n"
    message += f"📅 结束时间: {mining_card['end_time'].strftime('%Y-%m-%d %H:%M')}\n\n"
    message += f"💡 **提示:** 矿工们会在每天自动挖取积分，您可以在第二天签到或手动领取奖励！"
    
    return message

def _build_pending_rewards_message(rewards_result: dict) -> str:
    """构建待领取奖励消息"""
    rewards = rewards_result["rewards"]
    total_count = rewards_result["total_count"]
    total_points = rewards_result["total_points"]
    current_page = rewards_result["current_page"]
    total_pages = rewards_result["total_pages"]
    
    if not rewards:
        return "🎁 **待领取奖励**\n\n暂无待领取的挖矿奖励"
    
    message = f"🎁 **待领取奖励** (共 {total_count} 笔，{total_points:,} 积分)\n\n"
    
    for reward in rewards:
        message += f"⛏️ {reward['card_type']}矿工卡\n"
        message += f"   💰 奖励积分: {reward['reward_points']:,}\n"
        message += f"   📅 第{reward['reward_day']}天奖励\n"
        message += f"   🕐 {reward['reward_date'][:10]}\n\n"
    
    if total_pages > 1:
        message += f"📄 第 {current_page} 页，共 {total_pages} 页"
    
    return message

def _build_pending_rewards_keyboard(current_page: int, total_pages: int, telegram_id: int, has_rewards: bool):
    """构建待领取奖励分页键盘"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    # 领取所有奖励按钮
    if has_rewards:
        buttons.append([InlineKeyboardButton(
            text="🎁 领取所有奖励",
            callback_data="mining_claim_all"
        )])
    
    # 分页按钮
    if total_pages > 1:
        row = []
        
        # 上一页按钮
        if current_page > 1:
            row.append(InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"mining_rewards_page_{telegram_id}_{current_page - 1}"
            ))
        
        # 页码信息
        row.append(InlineKeyboardButton(
                text=f"📄 {current_page}/{total_pages}",
                callback_data="mining_rewards_info"
            ))
        
        # 下一页按钮
        if current_page < total_pages:
            row.append(InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"mining_rewards_page_{telegram_id}_{current_page + 1}"
            ))
        
        buttons.append(row)
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回挖矿菜单",
        callback_data="mining_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_claim_result_message(result: dict) -> str:
    """构建领取结果消息"""
    if not result["success"]:
        return f"❌ {result['message']}"
    
    claimed_rewards = result["claimed_rewards"]
    total_points = result["total_points"]
    
    message = f"🎉 **领取成功！**\n\n"
    message += f"✅ 成功领取 **{len(claimed_rewards)}** 笔挖矿奖励\n"
    message += f"💰 总积分: **{total_points:,}**\n\n"
    
    if claimed_rewards:
        message += "**领取详情:**\n"
        for reward in claimed_rewards:
            message += f"⛏️ {reward['card_type']}矿工卡 - 第{reward['reward_day']}天 - {reward['reward_points']:,}积分\n"
    
    return message

def _build_mining_management_message(user_cards_result: dict) -> str:
    """构建矿工卡管理消息"""
    user_cards = user_cards_result.get("cards", [])
    total_cards = user_cards_result.get("total_count", 0)
    current_page = user_cards_result.get("current_page", 1)
    total_pages = user_cards_result.get("total_pages", 1)
    
    message = f"📊 **矿工卡管理**\n\n"
    message += f"📈 总矿工卡: **{total_cards}** 张\n\n"
    
    if not user_cards:
        message += "暂无矿工卡，快去购买吧！\n\n"
    else:
        message += "**您的矿工卡:**\n"
        for i, card in enumerate(user_cards, 1):
            status_emoji = "⛏️" if card["status"] == 1 else "✅" if card["status"] == 2 else "❌"
            status_text = "挖矿中" if card["status"] == 1 else "已完成" if card["status"] == 2 else "已过期"
            
            message += f"{i}. {status_emoji} **{card['card_type']}矿工卡** ({status_text})\n"
            message += f"   💰 每日积分: {card['daily_points']:,}\n"
            message += f"   ⏰ 剩余天数: {card['remaining_days']}天\n"
            message += f"   💎 已获得: {card['earned_points']:,}积分\n"
            message += f"   📅 结束时间: {card['end_time'][:10]}\n\n"
    
    if total_pages > 1:
        message += f"📄 第 {current_page} 页，共 {total_pages} 页\n\n"
    
    return message

def _build_mining_management_keyboard(user_cards_result: dict, telegram_id: int):
    """构建矿工卡管理键盘"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    # 分页按钮
    current_page = user_cards_result.get("current_page", 1)
    total_pages = user_cards_result.get("total_pages", 1)
    
    if total_pages > 1:
        row = []
        
        # 上一页按钮
        if current_page > 1:
            row.append(InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"mining_manage_page_{telegram_id}_{current_page - 1}"
            ))
        
        # 页码信息
        row.append(InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="mining_manage_info"
        ))
        
        # 下一页按钮
        if current_page < total_pages:
            row.append(InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"mining_manage_page_{telegram_id}_{current_page + 1}"
            ))
        
        buttons.append(row)
    
    # 功能按钮
    buttons.append([
        InlineKeyboardButton(
            text="🔧 购买新矿工卡",
            callback_data="mining_cards"
        ),
        InlineKeyboardButton(
            text="🎁 领取奖励",
            callback_data="mining_rewards"
        )
    ])
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回挖矿菜单",
        callback_data="mining_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_mining_history_message(history_result: dict) -> str:
    """构建挖矿历史消息"""
    rewards = history_result["rewards"]
    statistics = history_result["statistics"]
    total_count = history_result["total_count"]
    current_page = history_result["current_page"]
    total_pages = history_result["total_pages"]
    
    message = f"📜 **挖矿历史记录**\n\n"
    
    # 添加统计信息
    message += f"📊 **挖矿统计**\n"
    message += f"💰 总花费: **{statistics['total_cost_usdt']:.2f}U**\n"
    message += f"💎 总获得积分: **{statistics['total_earned_points']:,}**\n"
    message += f"🔧 总购买矿工卡: **{statistics['total_cards_purchased']}** 张\n"
    message += f"🟤 青铜矿工卡: **{statistics['bronze_cards']}** 张\n"
    message += f"⚪ 白银矿工卡: **{statistics['silver_cards']}** 张\n"
    message += f"🟡 黄金矿工卡: **{statistics['gold_cards']}** 张\n"
    message += f"💎 钻石矿工卡: **{statistics['diamond_cards']}** 张\n"
    
    if statistics.get('last_mining_time'):
        message += f"⏰ 最后挖矿时间: {statistics['last_mining_time'][:10]}\n\n"
    else:
        message += "\n"
    
    # 添加奖励历史记录
    if not rewards:
        message += "暂无挖矿历史记录\n\n"
    else:
        message += f"**历史记录** (共 {total_count} 条)\n\n"
        
        for i, reward in enumerate(rewards, 1):
            status_emoji = "✅" if reward["status"] == 2 else "⏳"
            status_text = "已领取" if reward["status"] == 2 else "待领取"
            
            message += f"{i}. {status_emoji} {reward['card_type']}矿工卡\n"
            message += f"   💰 奖励积分: {reward['reward_points']:,}\n"
            message += f"   📅 第{reward['reward_day']}天奖励\n"
            message += f"   🕐 奖励日期: {reward['reward_date'][:10]}\n"
            
            if reward["status"] == 2 and reward["claimed_time"]:
                message += f"   ✅ 领取时间: {reward['claimed_time'][:10]}\n"
            
            message += f"   📝 状态: {status_text}\n\n"
    
    if total_pages > 1:
        message += f"📄 第 {current_page} 页，共 {total_pages} 页"
    
    return message

def _build_mining_history_keyboard(history_result: dict, telegram_id: int):
    """构建挖矿历史分页键盘"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    buttons = []
    
    # 分页按钮
    current_page = history_result["current_page"]
    total_pages = history_result["total_pages"]
    
    if total_pages > 1:
        row = []
        
        # 上一页按钮
        if current_page > 1:
            row.append(InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"mining_history_page_{telegram_id}_{current_page - 1}"
            ))
        
        # 页码信息
        row.append(InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="mining_history_info"
        ))
        
        # 下一页按钮
        if current_page < total_pages:
            row.append(InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"mining_history_page_{telegram_id}_{current_page + 1}"
            ))
        
        buttons.append(row)
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回挖矿菜单",
        callback_data="mining_menu"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# 保留原有的 Telethon 处理器类（如果需要的话）
class MiningHandler:
    """挖矿处理器（Telethon 版本）"""
    
    def __init__(self, client: TelegramClient):
        self.client = client
        self.mining_service = None
        
        # 注册事件处理器
        self._register_handlers()
    
    async def _get_mining_service(self):
        """获取挖矿服务实例"""
        if self.mining_service is None:
            async with SessionFactory() as session:
                uow = UoW(session)
                self.mining_service = MiningService(uow)
        return self.mining_service

    def _register_handlers(self):
        """注册事件处理器"""
        
        @self.client.on(events.NewMessage(pattern=r'^/mining$'))
        async def mining_command(event):
            """挖矿命令处理器"""
            await self._handle_mining_command(event)
        
        @self.client.on(events.CallbackQuery(pattern=r'^mining_(.+)$'))
        async def mining_callback(event):
            """挖矿回调处理器"""
            await self._handle_mining_callback(event)
    
    async def _handle_mining_command(self, event):
        """处理挖矿命令"""
        try:
            telegram_id = event.sender_id
            
            # 获取挖矿信息
            mining_service = await self._get_mining_service()
            mining_info = await mining_service.get_mining_info(telegram_id)
            
            if not mining_info["success"]:
                await event.respond(f"❌ {mining_info['message']}")
                return
            
            # 构建挖矿界面消息
            message = self._build_mining_interface_message(mining_info)
            
            # 构建挖矿菜单按钮
            keyboard = self._build_mining_menu_keyboard(mining_info)
            
            await event.respond(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"处理挖矿命令失败: {e}")
            await event.respond("❌ 系统错误，请稍后重试")
    
    async def _handle_mining_callback(self, event):
        """处理挖矿回调"""
        try:
            telegram_id = event.sender_id
            callback_data = event.data.decode()
            
            if callback_data.startswith("mining_cards"):
                await self._handle_mining_cards_callback(event)
            elif callback_data.startswith("mining_purchase_"):
                card_type = callback_data.split('_')[2]
                await self._handle_purchase_callback(event, card_type)
            elif callback_data.startswith("mining_rewards"):
                await self._handle_rewards_callback(event)
            elif callback_data.startswith("mining_claim_all"):
                await self._handle_claim_callback(event)
            elif callback_data.startswith("mining_history"):
                await self._handle_history_callback(event)
            else:
                await event.answer("未知的回调操作")
            
        except Exception as e:
            logger.error(f"处理挖矿回调失败: {e}")
            await event.answer("❌ 操作失败，请稍后重试")
    
    async def _handle_mining_cards_callback(self, event):
        """处理矿工卡选择回调"""
        try:
            telegram_id = event.sender_id
            
            # 获取挖矿信息
            mining_service = await self._get_mining_service()
            mining_info = await mining_service.get_mining_info(telegram_id)
            
            if not mining_info["success"]:
                await event.answer(f"❌ {mining_info['message']}")
                return
            
            # 获取用户的矿工卡列表（分页）
            cards_per_page = 5
            user_cards_result = await mining_service.get_user_mining_cards(
                telegram_id=telegram_id, 
                page=1, 
                limit=cards_per_page
            )
            
            if not user_cards_result["success"]:
                await event.answer(f"❌ {user_cards_result['message']}")
                return
            
            # 构建矿工卡选择界面消息
            message = self._build_mining_cards_message(mining_info, user_cards_result)
            
            # 构建矿工卡选择按钮（分页）
            keyboard = self._build_mining_cards_keyboard(
                mining_info["cards_info"], 
                user_cards_result,
                telegram_id=telegram_id
            )
            
            await event.edit(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"处理矿工卡选择回调失败: {e}")
            await event.answer("❌ 系统错误，请稍后重试")
    
    async def _handle_purchase_callback(self, event, card_type: str):
        """处理购买回调"""
        try:
            telegram_id = event.sender_id
            
            # 执行购买
            mining_service = await self._get_mining_service()
            result = await mining_service.purchase_mining_card(
                telegram_id=telegram_id,
                card_type=card_type
            )
            
            # 构建结果消息
            message = self._build_purchase_result_message(result)
            
            await event.answer(message)
            
        except Exception as e:
            logger.error(f"处理购买回调失败: {e}")
            await event.answer("❌ 购买失败，请稍后重试")
    
    async def _handle_rewards_callback(self, event):
        """处理奖励回调"""
        try:
            telegram_id = event.sender_id
            
            # 获取待领取奖励
            mining_service = await self._get_mining_service()
            rewards_result = await mining_service.get_pending_rewards(telegram_id)
            
            if not rewards_result["success"]:
                await event.answer(f"❌ {rewards_result['message']}")
                return
            
            # 构建待领取奖励消息
            message = self._build_pending_rewards_message(rewards_result)
            
            await event.edit(message)
            
        except Exception as e:
            logger.error(f"处理奖励回调失败: {e}")
            await event.answer("❌ 获取奖励失败，请稍后重试")
    
    async def _handle_claim_callback(self, event):
        """处理领取回调"""
        try:
            telegram_id = event.sender_id
            
            # 执行领取奖励
            mining_service = await self._get_mining_service()
            result = await mining_service.claim_all_rewards(telegram_id)
            
            # 构建结果消息
            message = self._build_claim_result_message(result)
            
            await event.answer(message)
            
        except Exception as e:
            logger.error(f"处理领取回调失败: {e}")
            await event.answer("❌ 领取失败，请稍后重试")
    
    async def _handle_history_callback(self, event):
        """处理挖矿历史回调"""
        try:
            telegram_id = event.sender_id
            
            # 获取挖矿历史记录
            mining_service = await self._get_mining_service()
            history_result = await mining_service.get_mining_history(
                telegram_id=telegram_id, 
                page=1, 
                limit=10
            )
            
            if not history_result["success"]:
                await event.answer(f"❌ {history_result['message']}")
                return
            
            # 构建挖矿历史界面消息
            message = self._build_mining_history_message(history_result)
            
            # 构建挖矿历史按钮（分页）
            keyboard = self._build_mining_history_keyboard(history_result, telegram_id)
            
            await event.edit(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"处理挖矿历史回调失败: {e}")
            await event.answer("❌ 获取历史记录失败，请稍后重试")
    
    def _build_mining_interface_message(self, mining_info: dict) -> str:
        """构建挖矿界面消息"""
        wallet_balance = mining_info["wallet_balance"]
        pending_rewards = mining_info["pending_rewards"]
        pending_points = mining_info["pending_points"]
        
        message = f"⛏️ **挖矿系统**\n\n"
        message += f"💰 钱包余额: **{wallet_balance:.2f}U**\n"
        
        if pending_rewards > 0:
            message += f"🎁 待领取奖励: **{pending_rewards}** 笔\n"
            message += f"💎 待领取积分: **{pending_points:,}**\n\n"
        else:
            message += f"🎁 待领取奖励: **0** 笔\n\n"
        
        message += "**选择操作:**\n"
        message += "🔧 购买矿工卡 - 使用USDT购买矿工卡进行挖矿\n"
        message += "🎁 领取奖励 - 领取已挖取的积分奖励\n"
        message += "📊 挖矿统计 - 查看挖矿历史和统计信息\n"
        
        return message
    
    def _build_mining_menu_keyboard(self, mining_info: dict):
        """构建挖矿菜单键盘"""
        from telethon.tl.types import KeyboardButtonCallback
        
        buttons = []
        
        # 购买矿工卡按钮
        buttons.append([KeyboardButtonCallback(
            text="🔧 购买矿工卡",
            data="mining_cards".encode()
        )])
        
        # 管理矿工卡按钮
        buttons.append([KeyboardButtonCallback(
            text="📊 管理矿工卡",
            data="mining_management".encode()
        )])
        
        # 领取奖励按钮（如果有待领取的奖励）
        if mining_info["pending_rewards"] > 0:
            buttons.append([KeyboardButtonCallback(
                text=f"🎁 领取奖励 ({mining_info['pending_rewards']}笔)",
                data="mining_rewards".encode()
            )])
        
        # 添加挖矿历史按钮
        buttons.append([KeyboardButtonCallback(
            text="📜 挖矿历史",
            data="mining_history".encode()
        )])
        
        return buttons
    
    def _build_mining_cards_message(self, mining_info: dict, user_cards_result: dict) -> str:
        """构建矿工卡选择消息"""
        wallet_balance = mining_info["wallet_balance"]
        cards_info = mining_info["cards_info"]
        
        message = f"🔧 **购买矿工卡**\n\n"
        message += f"💰 钱包余额: **{wallet_balance:.2f}U**\n\n"
        message += "**选择矿工卡类型:**\n"
        
        for card_type, info in cards_info.items():
            status_emoji = "✅" if info["can_purchase"] else "❌"
            message += f"{status_emoji} **{info['name']}**\n"
            message += f"   价格: {info['cost_usdt']}U\n"
            message += f"   每日积分: {info['daily_points']:,}\n"
            message += f"   持续天数: {info['duration_days']}天\n"
            message += f"   总积分: {info['total_points']:,}\n"
            message += f"   已拥有: {info['user_count']}/{info['max_cards']}张\n"
            message += f"   {info['description']}\n"
            
            if not info["can_purchase"]:
                if info["user_count"] >= info["max_cards"]:
                    message += f"   ⚠️ 已达到最大数量限制\n"
                else:
                    message += f"   ⚠️ 余额不足\n"
            
            message += "\n"
        
        message += "💡 **小贴士:** 高级矿工卡每日挖取的积分更多！"
        
        return message
    
    def _build_mining_cards_keyboard(self, cards_info: dict, user_cards_result: dict, telegram_id: int):
        """构建矿工卡选择键盘"""
        from telethon.tl.types import KeyboardButtonCallback
        
        buttons = []
        
        for card_type, info in cards_info.items():
            button_text = f"{info['name']} ({info['cost_usdt']:.2f}U)"
            if not info["can_purchase"]:
                button_text += " ❌"
            
            buttons.append([KeyboardButtonCallback(
                text=button_text,
                data=f"mining_purchase_{card_type}".encode()
            )])
        
        # 返回按钮
        buttons.append([KeyboardButtonCallback(
            text="🔙 返回挖矿菜单",
            data="mining_menu".encode()
        )])
        
        return buttons
    
    def _build_purchase_result_message(self, result: dict) -> str:
        """构建购买结果消息"""
        if not result["success"]:
            return f"❌ {result['message']}"
        
        mining_card = result["mining_card"]
        
        message = f"✅ **购买成功！**\n\n"
        message += f"🎉 成功购买 **{mining_card['name']}**\n"
        message += f"💰 每日挖取: **{mining_card['daily_points']:,}** 积分\n"
        message += f"⏰ 持续天数: **{mining_card['total_days']}** 天\n"
        message += f"📅 开始时间: {mining_card['start_time'].strftime('%Y-%m-%d %H:%M')}\n"
        message += f"📅 结束时间: {mining_card['end_time'].strftime('%Y-%m-%d %H:%M')}\n\n"
        message += f"💡 **提示:** 矿工们会在每天自动挖取积分，您可以在第二天签到或手动领取奖励！"
        
        return message
    
    def _build_pending_rewards_message(self, rewards_result: dict) -> str:
        """构建待领取奖励消息"""
        rewards = rewards_result["rewards"]
        total_count = rewards_result["total_count"]
        total_points = rewards_result["total_points"]
        
        if not rewards:
            return "🎁 **待领取奖励**\n\n暂无待领取的挖矿奖励"
        
        message = f"🎁 **待领取奖励** (共 {total_count} 笔，{total_points:,} 积分)\n\n"
        
        for reward in rewards:
            message += f"⛏️ {reward['card_type']}矿工卡\n"
            message += f"   💰 奖励积分: {reward['reward_points']:,}\n"
            message += f"   📅 第{reward['reward_day']}天奖励\n"
            message += f"   🕐 {reward['reward_date'][:10]}\n\n"
        
        return message
    
    def _build_claim_result_message(self, result: dict) -> str:
        """构建领取结果消息"""
        if not result["success"]:
            return f"❌ {result['message']}"
        
        claimed_rewards = result["claimed_rewards"]
        total_points = result["total_points"]
        
        message = f"🎉 **领取成功！**\n\n"
        message += f"✅ 成功领取 **{len(claimed_rewards)}** 笔挖矿奖励\n"
        message += f"💰 总积分: **{total_points:,}**\n\n"
        
        if claimed_rewards:
            message += "**领取详情:**\n"
            for reward in claimed_rewards:
                message += f"⛏️ {reward['card_type']}矿工卡 - 第{reward['reward_day']}天 - {reward['reward_points']:,}积分\n"
        
        return message
    
    def _build_mining_history_message(self, history_result: dict) -> str:
        """构建挖矿历史消息"""
        rewards = history_result["rewards"]
        statistics = history_result["statistics"]
        total_count = history_result["total_count"]
        current_page = history_result["current_page"]
        total_pages = history_result["total_pages"]
        
        message = f"📜 **挖矿历史记录**\n\n"
        
        # 添加统计信息
        message += f"📊 **挖矿统计**\n"
        message += f"💰 总花费: **{statistics['total_cost_usdt']:.2f}U**\n"
        message += f"💎 总获得积分: **{statistics['total_earned_points']:,}**\n"
        message += f"🔧 总购买矿工卡: **{statistics['total_cards_purchased']}** 张\n"
        message += f"🟤 青铜矿工卡: **{statistics['bronze_cards']}** 张\n"
        message += f"⚪ 白银矿工卡: **{statistics['silver_cards']}** 张\n"
        message += f"🟡 黄金矿工卡: **{statistics['gold_cards']}** 张\n"
        message += f"💎 钻石矿工卡: **{statistics['diamond_cards']}** 张\n"
        
        if statistics.get('last_mining_time'):
            message += f"⏰ 最后挖矿时间: {statistics['last_mining_time'][:10]}\n\n"
        else:
            message += "\n"
        
        # 添加奖励历史记录
        if not rewards:
            message += "暂无挖矿历史记录\n\n"
        else:
            message += f"**历史记录** (共 {total_count} 条)\n\n"
            
            for i, reward in enumerate(rewards, 1):
                status_emoji = "✅" if reward["status"] == 2 else "⏳"
                status_text = "已领取" if reward["status"] == 2 else "待领取"
                
                message += f"{i}. {status_emoji} {reward['card_type']}矿工卡\n"
                message += f"   💰 奖励积分: {reward['reward_points']:,}\n"
                message += f"   📅 第{reward['reward_day']}天奖励\n"
                message += f"   🕐 奖励日期: {reward['reward_date'][:10]}\n"
                
                if reward["status"] == 2 and reward["claimed_time"]:
                    message += f"   ✅ 领取时间: {reward['claimed_time'][:10]}\n"
                
                message += f"   📝 状态: {status_text}\n\n"
        
        if total_pages > 1:
            message += f"📄 第 {current_page} 页，共 {total_pages} 页"
        
        return message
    
    def _build_mining_history_keyboard(self, history_result: dict, telegram_id: int):
        """构建挖矿历史分页键盘"""
        from telethon.tl.types import KeyboardButtonCallback
        
        buttons = []
        
        # 分页按钮
        current_page = history_result["current_page"]
        total_pages = history_result["total_pages"]
        
        if total_pages > 1:
            row = []
            
            # 上一页按钮
            if current_page > 1:
                row.append(KeyboardButtonCallback(
                    text="⬅️ 上一页",
                    data=f"mining_history_page_{telegram_id}_{current_page - 1}".encode()
                ))
            
            # 页码信息
            row.append(KeyboardButtonCallback(
                text=f"📄 {current_page}/{total_pages}",
                data="mining_history_info".encode()
            ))
            
            # 下一页按钮
            if current_page < total_pages:
                row.append(KeyboardButtonCallback(
                    text="下一页 ➡️",
                    data=f"mining_history_page_{telegram_id}_{current_page + 1}".encode()
                ))
            
            buttons.append(row)
        
        # 返回按钮
        buttons.append([KeyboardButtonCallback(
            text="🔙 返回挖矿菜单",
            data="mining_menu".encode()
        )])
        
        return buttons 