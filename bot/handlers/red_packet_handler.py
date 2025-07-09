"""
红包处理器
处理红包相关命令和回调
"""

from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.common.red_packet_service import RedPacketService
from bot.common.uow import UoW
from bot.database.db import SessionFactory
import logging

logger = logging.getLogger(__name__)

# 全局变量用于存储服务实例
_red_packet_service = None

async def get_red_packet_service():
    """获取红包服务实例（异步，手动 new UoW）"""
    global _red_packet_service
    if _red_packet_service is None:
        async with SessionFactory() as session:
            uow = UoW(session)
            _red_packet_service = RedPacketService(uow)
    return _red_packet_service

# 创建路由器
red_packet_router = Router()

# 红包相关回调数据前缀
RED_PACKET_GRAB_PREFIX = "grab_red_packet_"
RED_PACKET_INFO_PREFIX = "red_packet_info_"

async def create_red_packet_from_fishing(chat_id: int, player_name: str, fish_points: int):
    """
    从钓鱼成功创建红包
    
    Args:
        chat_id: 群组ID
        player_name: 玩家名称
        fish_points: 钓到的积分
    
    Returns:
        是否成功创建红包
    """
    try:
        red_packet_service = await get_red_packet_service()
        
        # 生成红包ID
        import time
        red_packet_id = f"rp_system_{int(time.time())}"
        
        # 计算红包个数：每10000积分1个红包，最少3个，最多20个
        total_num = max(3, min(20, fish_points // 10000))
        
        # 直接创建系统红包，不需要扣除账户积分
        red_packet_service._red_packets[red_packet_id] = {
            "amount": fish_points,
            "total_num": total_num,
            "remaining_num": total_num,
            "remaining_amount": fish_points,
            "participants": [],
            "created_at": time.time(),
            "message_id": 0,
            "chat_id": chat_id,
            "sender_id": 0,  # 0表示系统
            "sender_name": f"🤖 系统代 {player_name}"
        }
        
        # 设置红包过期任务
        import asyncio
        asyncio.create_task(red_packet_service._expire_red_packet(red_packet_id))
        
        # 构建红包消息
        message = _build_red_packet_message(
            red_packet_id=red_packet_id,
            amount=fish_points,
            total_num=total_num,
            sender_name=f"🤖 系统代 {player_name}",
            description=f"恭喜 {player_name} 钓鱼成功，赶紧抢红包！"
        )
        
        # 构建红包按钮
        keyboard = _build_red_packet_keyboard(red_packet_id)
        
        # 发送红包消息
        from bot.misc import bot
        sent_message = await bot.send_message(
            chat_id=chat_id,
            text=message,
            reply_markup=keyboard
        )
        
        # 更新红包消息ID
        red_packet_service._red_packets[red_packet_id]["message_id"] = sent_message.message_id
        
        return True, red_packet_id
        
    except Exception as e:
        logger.error(f"创建钓鱼红包失败: {e}")
        return False, None

@red_packet_router.callback_query(lambda c: c.data.startswith(RED_PACKET_GRAB_PREFIX))
async def grab_red_packet_callback(callback_query: types.CallbackQuery):
    """
    处理抢红包回调
    """
    try:
        # 解析红包ID
        red_packet_id = callback_query.data[len(RED_PACKET_GRAB_PREFIX):]
        telegram_id = callback_query.from_user.id
        user_name = callback_query.from_user.full_name
        
        logger.info(f"用户 {user_name} (ID: {telegram_id}) 尝试抢红包: {red_packet_id}")
        
        # 抢红包
        red_packet_service = await get_red_packet_service()
        result = await red_packet_service.grab_red_packet(
            telegram_id=telegram_id,
            red_packet_id=red_packet_id,
            user_name=user_name
        )
        
        if not result["success"]:
            logger.warning(f"用户 {user_name} (ID: {telegram_id}) 抢红包失败: {result['message']}")
            try:
                await callback_query.answer(result["message"])
            except Exception as e:
                logger.warning(f"无法显示抢红包失败提示: {e}")
            return
        
        # 显示抢到的金额
        logger.info(f"用户 {user_name} (ID: {telegram_id}) 成功抢到红包: {result['amount']} 积分")
        try:
            await callback_query.answer(f"🎉 抢到了 {result['amount']:,} 积分！积分已添加到您的账户")
        except Exception as e:
            logger.warning(f"无法显示抢红包成功提示: {e}")
        
        # 如果是最后一个红包，更新红包消息
        if result["is_last"]:
            # 获取红包信息
            info_result = red_packet_service.get_red_packet_info(red_packet_id)
            if info_result["success"]:
                info = info_result["info"]
                
                # 构建红包结果消息
                message = _build_red_packet_result_message(
                    sender_name=info["sender_name"],
                    amount=info["amount"],
                    total_num=info["total_num"],
                    participants=info["participants"],
                    best_grabber=info["best_grabber"]
                )
                
                # 更新红包消息
                try:
                    await callback_query.message.edit_text(
                        text=message
                    )
                except Exception as e:
                    logger.warning(f"无法更新红包消息: {e}")
        
    except Exception as e:
        logger.error(f"处理抢红包回调失败: {e}")
        try:
            await callback_query.answer("❌ 抢红包失败，请稍后重试")
        except Exception as answer_error:
            logger.warning(f"无法显示错误提示: {answer_error}")

@red_packet_router.callback_query(lambda c: c.data.startswith(RED_PACKET_INFO_PREFIX))
async def red_packet_info_callback(callback_query: types.CallbackQuery):
    """
    处理红包详情回调
    """
    try:
        # 解析红包ID
        red_packet_id = callback_query.data[len(RED_PACKET_INFO_PREFIX):]
        
        # 获取红包信息
        red_packet_service = await get_red_packet_service()
        result = red_packet_service.get_red_packet_info(red_packet_id)
        
        if not result["success"]:
            try:
                await callback_query.answer(result["message"])
            except Exception as e:
                logger.warning(f"无法显示红包详情失败提示: {e}")
            return
        
        info = result["info"]
        
        # 构建红包详情消息
        message = _build_red_packet_detail_message(
            sender_name=info["sender_name"],
            amount=info["amount"],
            total_num=info["total_num"],
            participants=info["participants"]
        )
        
        # 回复详情消息
        try:
            await callback_query.message.reply(message)
            await callback_query.answer()
        except Exception as e:
            logger.warning(f"无法发送红包详情消息: {e}")
        
    except Exception as e:
        logger.error(f"处理红包详情回调失败: {e}")
        try:
            await callback_query.answer("❌ 获取红包详情失败，请稍后重试")
        except Exception as answer_error:
            logger.warning(f"无法显示错误提示: {answer_error}")

def _build_red_packet_message(red_packet_id: str, amount: int, total_num: int, sender_name: str, description: str = "") -> str:
    """
    构建红包消息
    """
    message = f"🧧 **{sender_name} 发了一个红包**\n\n"
    message += f"💰 总金额: **{amount:,}** 积分\n"
    message += f"👥 红包个数: **{total_num}** 个\n\n"
    
    if description:
        message += f"{description}\n\n"
    
    message += f"**点击下方按钮抢红包**\n"
    message += f"💡 积分将直接增加到您的账户中"
    
    return message

def _build_red_packet_keyboard(red_packet_id: str) -> InlineKeyboardMarkup:
    """构建红包按钮"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🧧 抢红包",
                    callback_data=f"{RED_PACKET_GRAB_PREFIX}{red_packet_id}"
                )
            ]
        ]
    )

def _build_red_packet_result_message(sender_name: str, amount: int, total_num: int, participants: list, best_grabber: dict = None) -> str:
    """构建红包结果消息"""
    message = f"🧧 **红包已抢完**\n\n"
    message += f"👤 {sender_name}\n"
    message += f"💰 总金额: **{amount:,}** 积分\n"
    message += f"👥 抢到人数: **{len(participants)}** 人\n"
    message += f"✅ 积分已添加到各用户账户\n\n"
    
    # 添加抢红包记录
    message += "**抢红包记录**\n"
    for i, p in enumerate(participants):
        message += f"{i+1}. {p['name']}: {p['amount']:,} 积分\n"
    
    if best_grabber:
        message += f"\n🥇 **手气最佳: {best_grabber['name']}** ({best_grabber['amount']:,} 积分)"
    
    return message

def _build_red_packet_detail_message(sender_name: str, amount: int, total_num: int, participants: list) -> str:
    """构建红包详情消息"""
    message = f"🧧 **红包详情**\n\n"
    message += f"👤 {sender_name}\n"
    message += f"💰 总金额: **{amount:,}** 积分\n"
    message += f"👥 抢到人数: **{len(participants)}** 人\n\n"
    
    message += "**抢红包记录**\n"
    
    for i, p in enumerate(participants):
        message += f"{i+1}. {p['name']}: {p['amount']:,} 积分\n"
    
    return message 

def _build_red_packet_expired_message(sender_name: str, amount: int, total_num: int, remaining_num: int, participants: list, best_grabber: dict = None) -> str:
    """构建红包过期消息"""
    message = f"🧧 **红包已过期**\n\n"
    message += f"👤 {sender_name}\n"
    message += f"💰 总金额: **{amount:,}** 积分\n"
    
    # 计算已抢和剩余
    grabbed_num = total_num - remaining_num
    
    # 计算已抢金额
    grabbed_amount = 0
    for p in participants:
        grabbed_amount += p["amount"]
    
    # 剩余金额 = 总金额 - 已抢金额
    remaining_amount = amount - grabbed_amount
    
    message += f"👥 已抢: **{grabbed_num}** 个，剩余: **{remaining_num}** 个\n"
    message += f"💵 已抢: **{grabbed_amount:,}** 积分"
    
    if remaining_num > 0:
        message += f"，剩余 **{remaining_amount:,}** 积分已退还\n"
    else:
        message += f"\n"
    
    # 如果有人抢了红包，显示记录
    if participants:
        message += f"\n**抢红包记录**\n"
        for i, p in enumerate(participants):
            message += f"{i+1}. {p['name']}: {p['amount']:,} 积分\n"
        
        if best_grabber:
            message += f"\n🥇 **手气最佳: {best_grabber['name']}** ({best_grabber['amount']:,} 积分)"
    else:
        message += f"\n💔 **没有人抢到红包**"
    
    return message 