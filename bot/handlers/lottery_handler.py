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

# 全局变量用于存储服务实例
_lottery_service = None

async def get_lottery_service():
    """获取彩票服务实例（异步，手动 new UoW）"""
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

async def show_bets_page(message: Message, telegram_id: int, page: int, page_size: int = 5):
    """
    显示指定页面的投注记录
    
    Args:
        message: 消息对象
        telegram_id: 用户ID
        page: 页码（从1开始）
        page_size: 每页显示数量
    """
    try:
        lottery_service = await get_lottery_service()
        
        # 计算分页参数
        offset = (page - 1) * page_size
        
        # 获取用户投注历史（使用服务端分页）
        result = await lottery_service.get_user_bet_history(
            telegram_id=telegram_id,
            limit=page_size,
            offset=offset
        )
        
        if result["success"]:
            current_page_bets = result["history"]
            total_bets = result["total"]
            total_pages = result["total_pages"]
            current_page = result["current_page"]
            
            if not current_page_bets:
                await message.answer(
                    "📝 **投注记录**\n\n"
                    "您还没有任何投注记录。\n\n"
                    "💡 开始投注：\n"
                    "• 在群组中发送投注消息\n"
                    "• 格式：大1000 小单100 数字8 押100\n"
                    "• 支持大小单双、组合投注、数字投注"
                )
                return
            
            # 确保页码在有效范围内
            if page < 1:
                page = 1
            elif page > total_pages:
                page = total_pages
            
            # 构建投注记录消息
            message_text = _build_bets_message(current_page_bets, page, total_pages, page_size)
            
            # 添加统计信息
            stats_text = await _build_bets_stats(lottery_service, telegram_id, total_bets)
            message_text += stats_text
            
            # 创建分页键盘
            keyboard = _build_bets_keyboard(page, total_pages, telegram_id)
            
            # 发送或编辑消息
            try:
                # 尝试编辑消息（用于分页）
                await message.edit_text(message_text, parse_mode="Markdown", reply_markup=keyboard)
            except Exception as edit_error:
                # 如果编辑失败，发送新消息
                logger.warning(f"编辑消息失败，发送新消息: {edit_error}")
                await message.answer(message_text, parse_mode="Markdown", reply_markup=keyboard)
            
        else:
            await message.answer(f"❌ 获取投注记录失败: {result['message']}")
            
    except Exception as e:
        logger.error(f"获取投注记录失败: {e}")
        await message.answer("❌ 获取投注记录时发生错误，请稍后重试")

async def show_recent_draws(message: Message, limit: int = 10):
    """
    显示最近开奖记录
    
    Args:
        message: 消息对象
        limit: 显示记录数量
    """
    try:
        lottery_service = await get_lottery_service()
        
        # 获取最近开奖记录
        result = await lottery_service.get_recent_draws(limit=limit)
        
        if result["success"]:
            draws = result["history"]
            
            if not draws:
                await message.answer("📊 **开奖记录**\n\n暂无开奖记录。")
                return
            
            # 构建开奖记录消息
            message_text = _build_draws_message(draws)
            
            await message.answer(message_text, parse_mode="Markdown")
            
        else:
            await message.answer(f"❌ 获取开奖记录失败: {result['message']}")
            
    except Exception as e:
        logger.error(f"获取开奖记录失败: {e}")
        await message.answer("❌ 获取开奖记录时发生错误，请稍后重试")

def _build_bets_message(bets: list, page: int, total_pages: int, page_size: int) -> str:
    """构建投注记录消息"""
    message_text = f"📝 **您的投注记录** (第 {page}/{total_pages} 页)\n\n"
    
    for i, bet in enumerate(bets, 1):
        # 格式化时间
        created_time = bet["created_at"][5:16]  # 取 MM-DD HH:MM 部分
        
        # 格式化投注信息
        if bet["is_win"]:
            status = "✅ 中奖"
            win_info = f" +{bet['win_amount']}积分"
        else:
            status = "❌ 未中"
            win_info = ""
        
        message_text += (
            f"**{i}. {bet['bet_type']} {bet['bet_amount']}积分**\n"
            f"   期号: {bet['draw_number']}\n"
            f"   时间: {created_time}\n"
            f"   状态: {status}{win_info}\n\n"
        )
    
    message_text += f"📄 第 {page}/{total_pages} 页，每页 {page_size} 条记录\n\n"
    
    return message_text

async def _build_bets_stats(lottery_service, telegram_id: int, total_bets: int) -> str:
    """构建投注统计信息"""
    try:
        # 获取所有投注记录来计算统计
        stats_result = await lottery_service.get_user_bet_history(
            telegram_id=telegram_id,
            limit=1000,  # 获取足够多的数据来计算统计
            offset=0
        )
        
        if stats_result["success"]:
            all_bets_for_stats = stats_result["history"]
            total_bet_amount = sum(bet["bet_amount"] for bet in all_bets_for_stats)
            total_win_amount = sum(bet["win_amount"] for bet in all_bets_for_stats if bet["is_win"])
            win_count = sum(1 for bet in all_bets_for_stats if bet["is_win"])
        else:
            # 如果获取统计失败，返回空统计
            total_bet_amount = 0
            total_win_amount = 0
            win_count = 0
        
        win_rate = (win_count / total_bets * 100) if total_bets > 0 else 0
        
        stats_text = (
            f"📊 **统计信息**\n"
            f"总投注: {total_bets} 次\n"
            f"总投注金额: {total_bet_amount:,} 积分\n"
            f"中奖次数: {win_count} 次\n"
            f"总中奖金额: {total_win_amount:,} 积分\n"
            f"胜率: {win_rate:.1f}%"
        )
        
        return stats_text
        
    except Exception as e:
        logger.error(f"构建投注统计失败: {e}")
        return "📊 **统计信息**\n获取统计信息失败"

def _build_draws_message(draws: list) -> str:
    """构建开奖记录消息"""
    message_text = "📊 **最近开奖记录**\n\n"
    
    for i, draw in enumerate(draws, 1):
        # 格式化时间
        draw_time = draw["draw_time"][5:16]  # 取 MM-DD HH:MM 部分
        
        # 格式化结果
        result_text = f"结果: {draw['result']}"
        
        # 格式化统计信息
        profit_text = f"盈利: {draw['profit']:,} 积分" if draw['profit'] >= 0 else f"亏损: {abs(draw['profit']):,} 积分"
        
        message_text += (
            f"**{i}. 第 {draw['draw_number']} 期**\n"
            f"   {result_text}\n"
            f"   投注总额: {draw['total_bets']:,} 积分\n"
            f"   派奖总额: {draw['total_payout']:,} 积分\n"
            f"   {profit_text}\n"
            f"   开奖时间: {draw_time}\n\n"
        )
    
    return message_text

def _build_bets_keyboard(page: int, total_pages: int, telegram_id: int) -> InlineKeyboardMarkup:
    """构建投注记录分页键盘"""
    keyboard_buttons = []
    
    # 上一页按钮
    if page > 1:
        keyboard_buttons.append(
            InlineKeyboardButton(
                text="⬅️ 上一页",
                callback_data=f"bets_page_{telegram_id}_{page-1}"
            )
        )
    
    # 下一页按钮
    if page < total_pages:
        keyboard_buttons.append(
            InlineKeyboardButton(
                text="下一页 ➡️",
                callback_data=f"bets_page_{telegram_id}_{page+1}"
            )
        )
    
    # 如果只有一页，显示刷新按钮
    if total_pages <= 1:
        keyboard_buttons.append(
            InlineKeyboardButton(
                text="🔄 刷新",
                callback_data=f"bets_page_{telegram_id}_1"
            )
        )
    
    return InlineKeyboardMarkup(inline_keyboard=[keyboard_buttons]) 