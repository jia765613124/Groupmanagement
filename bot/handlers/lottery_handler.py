"""
多群组开奖处理器
处理Telegram机器人的开奖相关命令和交互
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from bot.config.multi_game_config import MultiGameConfig
from bot.common.lottery_service import LotteryService
from bot.common.uow import UoW
from bot.database.db import SessionFactory

logger = logging.getLogger(__name__)

# 全局配置实例
_multi_config = MultiGameConfig()

# 创建aiogram路由器
lottery_router = Router(name="lottery")

async def get_lottery_service():
    """获取开奖服务实例"""
    async with SessionFactory() as session:
        uow = UoW(session)
        return LotteryService(uow)

@lottery_router.message(Command("lottery"))
async def lottery_command(message: Message):
    """开奖命令处理器"""
    try:
        group_id = message.chat.id
        
        # 获取群组配置
        group_config = _multi_config.get_group_config(group_id)
        if not group_config:
            await message.reply("❌ 该群组未配置开奖游戏")
            return
        
        if not group_config.enabled:
            await message.reply("❌ 该群组的开奖游戏已禁用")
            return
        
        # 构建开奖信息消息
        message_text = _multi_config.format_game_info(group_id)
        
        # 构建投注按钮
        keyboard = _build_lottery_keyboard(group_id)
        
        await message.reply(message_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"处理开奖命令失败: {e}")
        await message.reply("❌ 系统错误，请稍后重试")

@lottery_router.callback_query(F.data.startswith("lottery_"))
async def lottery_callback(callback: CallbackQuery):
    """处理开奖相关的回调查询"""
    try:
        data = callback.data
        logger.info(f"收到开奖回调: {data}")
        
        parts = data.split("_")
        if len(parts) < 3:
            logger.error(f"回调数据格式错误: {data}")
            await callback.answer("❌ 无效的操作")
            return
        
        action = parts[1]
        
        # 根据不同的action类型解析group_id
        if action == "bet" and len(parts) >= 4:
            # 格式: lottery_bet_type_{group_id}_{bet_type} 或 lottery_bet_amount_{group_id}_{bet_type}_{amount}
            sub_action = parts[2]  # 'type' 或 'amount'
            group_id = int(parts[3])
            
            if sub_action == "type":
                # 格式: lottery_bet_type_{group_id}_{bet_type}
                if len(parts) >= 5:
                    bet_type = parts[4]
                    logger.info(f"解析投注类型回调: action={action}, sub_action={sub_action}, group_id={group_id}, bet_type={bet_type}")
                else:
                    logger.error(f"投注类型回调数据格式错误: {data}")
                    await callback.answer("❌ 无效的投注类型")
                    return
            elif sub_action == "amount":
                # 格式: lottery_bet_amount_{group_id}_{bet_type}_{amount}
                if len(parts) >= 7:
                    bet_type = parts[4]
                    bet_amount = int(parts[5])
                    logger.info(f"解析投注金额回调: action={action}, sub_action={sub_action}, group_id={group_id}, bet_type={bet_type}, amount={bet_amount}")
                else:
                    logger.error(f"投注金额回调数据格式错误: {data}")
                    await callback.answer("❌ 无效的投注金额")
                    return
            else:
                logger.error(f"未知的投注子操作: {sub_action}")
                await callback.answer("❌ 无效的操作")
                return
        else:
            # 格式: lottery_{action}_{group_id}_...
            group_id = int(parts[2])
            logger.info(f"解析回调: action={action}, group_id={group_id}")
        
        if action == "menu":
            # 显示主菜单
            message = f"🎲 **彩票游戏**\n\n欢迎来到彩票游戏！\n请选择您要进行的操作："
            keyboard = _build_lottery_keyboard(group_id)
            if (
                callback.message.text == message and
                getattr(callback.message.reply_markup, "inline_keyboard", None) == getattr(keyboard, "inline_keyboard", None)
            ):
                await callback.answer("已是当前内容")
                return
            await callback.message.edit_text(message, reply_markup=keyboard)
        
        elif action == "bet":
            # 显示投注类型选择
            message = _build_bet_interface_message(group_id)
            keyboard = _build_bet_keyboard(group_id)
            if (
                callback.message.text == message and
                getattr(callback.message.reply_markup, "inline_keyboard", None) == getattr(keyboard, "inline_keyboard", None)
            ):
                await callback.answer("已是当前内容")
                return
            await callback.message.edit_text(message, reply_markup=keyboard)
        
        elif action == "bet":
            # 处理投注相关的回调
            if sub_action == "type":
                logger.info(f"选择投注类型: {bet_type}")
                if bet_type == "number":
                    message = f"🎲 **数字投注**\n\n请选择您要投注的数字 (0-9):"
                    keyboard = _build_number_bet_keyboard(group_id)
                else:
                    message = _build_bet_interface_message(group_id, bet_type)
                    keyboard = _build_bet_keyboard(group_id, bet_type)
                if (
                    callback.message.text == message and
                    getattr(callback.message.reply_markup, "inline_keyboard", None) == getattr(keyboard, "inline_keyboard", None)
                ):
                    await callback.answer("已是当前内容")
                    return
                await callback.message.edit_text(message, reply_markup=keyboard)
            elif sub_action == "amount":
                telegram_id = callback.from_user.id
                logger.info(f"处理投注: 用户={telegram_id}, 群组={group_id}, 类型={bet_type}, 金额={bet_amount}")
                is_valid, error_msg = _multi_config.validate_bet(group_id, bet_type, bet_amount)
                if not is_valid:
                    logger.warning(f"投注验证失败: 用户={telegram_id}, 错误={error_msg}")
                    await callback.answer(f"❌ {error_msg}")
                    return
                logger.info(f"投注验证通过，开始执行投注...")
                lottery_service = await get_lottery_service()
                result = await lottery_service.place_bet(
                    group_id=group_id,
                    telegram_id=telegram_id,
                    bet_type=bet_type,
                    bet_amount=bet_amount
                )
                logger.info(f"投注结果: 成功={result['success']}, 消息={result.get('message', 'N/A')}")
                message = _build_bet_result_message(result)
                await callback.message.edit_text(message)
        else:
            logger.warning(f"未知的回调action: {action}, 数据: {data}")
        
        await callback.answer()
        
    except Exception as e:
        if "message is not modified" in str(e):
            # 忽略这个错误
            pass
        else:
            logger.error(f"处理开奖回调失败: {e}")
            await callback.answer("❌ 操作失败，请稍后重试")

def _build_lottery_keyboard(group_id: int):
    """构建开奖主菜单键盘"""
    buttons = [
        [InlineKeyboardButton(
            text="🎲 开始投注",
            callback_data=f"lottery_bet_{group_id}"
        )],
        [InlineKeyboardButton(
            text="📊 游戏规则",
            callback_data=f"lottery_rules_{group_id}"
        )],
        [InlineKeyboardButton(
            text="💰 我的余额",
            callback_data=f"lottery_balance_{group_id}"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_bet_interface_message(group_id: int, bet_type: str = None):
    """构建投注界面消息"""
    group_config = _multi_config.get_group_config(group_id)
    game_config = _multi_config.get_game_config(group_config.game_type)
    
    message = f"🎲 **{game_config.name} - 投注界面**\n\n"
    
    if bet_type:
        odds = _multi_config.get_bet_odds(bet_type, group_config.game_type)
        message += f"📝 **投注类型:** {bet_type}\n"
        message += f"📈 **赔率:** {odds}倍\n\n"
        message += "💰 **请选择投注金额:**\n"
    else:
        message += "📝 **请选择投注类型:**\n"
    
    return message

def _build_bet_keyboard(group_id: int, bet_type: str = None):
    """构建投注键盘"""
    group_config = _multi_config.get_group_config(group_id)
    game_config = _multi_config.get_game_config(group_config.game_type)
    
    buttons = []
    
    if bet_type:
        # 显示投注金额选项
        amounts = [1, 5, 10, 50, 100, 500, 1000, 5000]
        for i in range(0, len(amounts), 2):
            row = []
            row.append(InlineKeyboardButton(
                text=f"{amounts[i]}U",
                callback_data=f"lottery_bet_amount_{group_id}_{bet_type}_{amounts[i]}"
            ))
            if i + 1 < len(amounts):
                row.append(InlineKeyboardButton(
                    text=f"{amounts[i+1]}U",
                    callback_data=f"lottery_bet_amount_{group_id}_{bet_type}_{amounts[i+1]}"
                ))
            buttons.append(row)
    else:
        # 显示投注类型选项
        for bet_type_name in game_config.bet_types.keys():
            odds = game_config.bet_types[bet_type_name]["odds"]
            buttons.append([InlineKeyboardButton(
                text=f"{bet_type_name} ({odds}倍)",
                callback_data=f"lottery_bet_type_{group_id}_{bet_type_name}"
            )])
        
        # 数字投注
        buttons.append([InlineKeyboardButton(
            text=f"数字投注 ({game_config.number_odds}倍)",
            callback_data=f"lottery_bet_type_{group_id}_number"
        )])
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回",
        callback_data=f"lottery_menu_{group_id}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_number_bet_keyboard(group_id: int):
    """构建数字投注键盘"""
    buttons = []
    
    # 数字按钮 (0-9)
    for i in range(0, 10, 2):
        row = []
        row.append(InlineKeyboardButton(
            text=str(i),
            callback_data=f"lottery_bet_type_{group_id}_{i}"
        ))
        if i + 1 < 10:
            row.append(InlineKeyboardButton(
                text=str(i + 1),
                callback_data=f"lottery_bet_type_{group_id}_{i + 1}"
            ))
        buttons.append(row)
    
    # 返回按钮
    buttons.append([InlineKeyboardButton(
        text="🔙 返回",
        callback_data=f"lottery_bet_{group_id}"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def _build_bet_result_message(result: dict):
    """构建投注结果消息"""
    if result["success"]:
        message = f"✅ **投注成功!**\n\n"
        message += f"📝 **投注类型:** {result['bet_type']}\n"
        message += f"💰 **投注金额:** {result['bet_amount']:,} U\n"
        message += f"📈 **赔率:** {result['odds']}倍\n"
        message += f"🎯 **预期收益:** {result['expected_win']:,} U\n\n"
        message += f"📊 **期号:** {result['draw_number']}\n"
        message += f"⏰ **开奖时间:** {result['draw_time']}\n\n"
        message += "🎲 祝您好运！"
    else:
        message = f"❌ **投注失败**\n\n"
        message += f"💬 **原因:** {result['message']}\n\n"
        message += "请检查余额或投注参数后重试。"
    
    return message 