import logging
import uuid
import random
from typing import List, Optional
from decimal import Decimal, ConversionSyntax, ROUND_HALF_UP, ROUND_DOWN
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from datetime import timezone

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, BotCommand, BotCommandScopeDefault, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext

from bot.config import get_config
from bot.states import Menu
from bot.misc import bot
from bot.telethon_client import telegram_client
from bot.database.db import SessionFactory
from bot.utils import sanitize_text
from bot.utils.wallet import generate_qr_code, validate_tron_address, check_recharge_status
from bot.crud import recharge_order, account, account_transaction # Import account CRUD and account_transaction
from bot.models.recharge_order import RechargeOrder # Import RechargeOrder model
from bot.models.account import Account # Import Account model
from sqlalchemy import select

logger = logging.getLogger(__name__)

config = get_config()
commands_router = Router()

# 配置钱包地址
WALLET_ADDRESS = "TC9wtcWAZzZ5squ5DB8x9UAQ1nYNP25RDW"

# 积分兑换率：1 USDT = ? 积分 (需要根据实际需求设置)
USDT_TO_POINTS_RATE = Decimal('1000.0') # 示例：1 USDT 兑换 1000 积分

# 基本命令（所有用户可见）
BASIC_COMMANDS = [
    BotCommand(command="start", description="开始使用"),
    BotCommand(command="balance", description="查看余额和积分余额"),
    BotCommand(command="recharge", description="充值USDT"),
    BotCommand(command="help", description="帮助信息")
]

# USDT 充值金额选项（单位：USDT）
RECHARGE_AMOUNTS = [1, 10, 50, 100]

# 存储等待链接的用户ID
waiting_for_link = set()

def get_lang_keyboard() -> InlineKeyboardMarkup:
    """创建语言设置键盘"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📲 点击安装中文语言包",
                    url="https://t.me/setlanguage/zh-hans-raw"
                )
            ]
        ]
    )
    return keyboard

def get_recharge_keyboard() -> InlineKeyboardMarkup:
    """创建USDT充值键盘，并包含兑换选项"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f"💰 {amount} USDT", callback_data=f"recharge_{amount}")
                for amount in RECHARGE_AMOUNTS[:2]
            ],
            [
                InlineKeyboardButton(text=f"💰 {amount} USDT", callback_data=f"recharge_{amount}")
                for amount in RECHARGE_AMOUNTS[2:]
            ],
            [
                InlineKeyboardButton(text="💳 自定义金额", callback_data="recharge_custom")
            ],
            [
                InlineKeyboardButton(text="🔄 USDT 兑换积分", callback_data="exchange_usdt_to_points") # 添加兑换按钮
            ]
        ]
    )
    return keyboard

def get_recharge_confirm_keyboard() -> InlineKeyboardMarkup:
    """创建充值确认界面的键盘"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 返回", callback_data="recharge_back")
            ]
        ]
    )
    return keyboard

async def setup_bot_commands():
    """
    设置机器人命令菜单
    """
    try:
        # 先删除所有现有命令
        await bot.delete_my_commands(scope=BotCommandScopeDefault())
        logger.info("已清理现有命令")

        # 设置基本命令（全局范围）
        await bot.set_my_commands(
            commands=BASIC_COMMANDS,
            scope=BotCommandScopeDefault()
        )
        logger.info("成功设置基本命令")
    except Exception as e:
        logger.error("设置机器人命令失败: %s", e, exc_info=True)
        raise


@commands_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    处理 /start 命令
    """
    logger.info(f"用户 {message.from_user.id} 发送了 /start 命令")
    await message.answer(
        "👋 欢迎使用USDT充值机器人！\n\n"
        "💰 使用 /balance 查看USDT余额\n"
        "💳 使用 /recharge 进行USDT充值\n"
        "❓ 使用 /help 获取帮助信息"
    )


@commands_router.message(Command("help"))
async def command_help_handler(message: Message, state: FSMContext):
    """
    处理 /help 命令
    """
    await state.set_state(Menu.help)
    help_text = (
        "🤖 机器人帮助信息\n\n"
        "1. /start - 开始使用机器人\n"
        "2. /balance - 查看USDT余额和积分余额\n"
        "3. /recharge - 充值USDT (也包含兑换积分入口)\n"
        "4. /help - 显示此帮助信息\n"
        "5. /exchange - 兑换积分到钱包\n"
        "6. /check_recharge - 批量查询充值状态\n\n" # 更新帮助信息
        "💡 充值说明：\n"
        "- 仅支持USDT-TRC20\n"
        "- 最小充值金额：1 USDT\n"
        "- 请确保使用TRC20网络转账\n"
        "\n如需更多帮助，请联系客服。"
    )
    await message.answer(help_text)
    await state.clear()


@commands_router.message(Command("lang"))
async def command_lang_handler(message: Message, state: FSMContext):
    """
    处理 /lang 命令
    所有用户都可以使用此命令
    """
    await state.set_state(Menu.lang)
    await message.answer(
        "🌏 欢迎使用！\n\n"
        "🌏 请先安装中文语言包：\n"
        "1️⃣ 点击下方按钮\n"
        "2️⃣ 在弹出窗口中点击「Change」即可",
        reply_markup=get_lang_keyboard()
    )


@commands_router.message(Command("balance"))
async def command_balance_handler(message: Message):
    """处理 /balance 命令"""
    try:
        async with SessionFactory() as session:
            telegram_id = message.from_user.id
            
            # 从数据库获取用户所有账户
            user_accounts = await account.get_by_telegram_id(session=session, telegram_id=telegram_id)
            
            积分_balance = Decimal('0.00')
            钱包_balance = Decimal('0.00')
            
            # 遍历账户，区分积分和钱包余额
            for acc in user_accounts:
                if acc.account_type == 1: # 假设 1 是积分账户类型
                    积分_balance = Decimal(str(acc.available_amount)) # 假设积分是整数
                elif acc.account_type == 2: # 假设 2 是钱包账户类型 (USDT)
                    # 正确换算为 USDT，保留3位小数
                    钱包_balance = (Decimal(str(acc.available_amount)) / Decimal('1000000')).quantize(Decimal('0.1'), rounding=ROUND_DOWN)

            await message.answer(
                f"您的账户余额：\n\n"
                f"💰 积分余额：{积分_balance} 积分\n"
                f"💳 钱包余额：{钱包_balance} USDT\n\n"
                "使用 /recharge 命令进行充值"
            )
    except Exception as e:
        logger.error(f"查询余额失败: {e}", exc_info=True)
        await message.answer("❌ 查询余额失败，请稍后重试")


@commands_router.message(Command("recharge"))
async def command_recharge_handler(message: Message):
    """处理 /recharge 命令"""
    await message.answer(
        "💳 USDT充值\n\n"
        "请选择充值金额：\n"
        "💡 仅支持USDT-TRC20网络\n"
        "⚠️ 请确保使用TRC20网络转账\n"
        "💰 最小充值金额：1 USDT",
        reply_markup=get_recharge_keyboard()
    )


@commands_router.callback_query(F.data.startswith("recharge_") & (F.data != "recharge_back"))
async def handle_recharge_callback(callback_query: CallbackQuery, state: FSMContext):
    """处理充值回调"""
    try:
        amount_str = callback_query.data.split("_")[1]
        if amount_str == "custom":
            await state.set_state(Menu.waiting_for_amount)
            await callback_query.message.edit_text(
                "💳 请输入充值金额（USDT）：\n\n"
                "💡 仅支持USDT-TRC20网络\n"
                "⚠️ 请确保使用TRC20网络转账\n"
                "💰 最小充值金额：1 USDT\n\n"
                "输入 /cancel 可以取消操作"
            )
        else:
            try:
                logger.info(f"Attempting to convert amount_str: {amount_str} from callback_data: {callback_query.data}")
                base_amount = Decimal(amount_str).quantize(Decimal('0.0'), rounding=ROUND_HALF_UP) # 基础金额保留一位小数
                if base_amount < 1:
                    await callback_query.answer("❌ 最小充值金额为1 USDT", show_alert=True)
                    return
                
                # 生成随机两位小数并转换为三位小数的Decimal
                random_last_two = Decimal(str(random.randint(0, 99)).zfill(2)) / 1000 # 0.0XX
                final_amount = (base_amount + random_last_two).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP) # 确保最终三位小数
                
                # 生成唯一订单号
                order_no = f"RECHARGE-{uuid.uuid4().hex[:12].upper()}-{int(datetime.now().timestamp())}"
                
                # 使用中国时区创建过期时间
                china_tz = ZoneInfo('Asia/Shanghai')
                now_china = datetime.now(china_tz)
                expire_time = now_china + timedelta(minutes=30)  # 订单有效期30分钟
                # 转换为 UTC 时间存储
                expire_time_utc = expire_time.astimezone(timezone.utc)

                # 计算积分 (这里简单示例，实际逻辑可能更复杂)
                points = int(final_amount) # 例如，每充值1 USDT获得1积分
                bonus_points = 0

                # 获取用户Telegram ID
                telegram_id = callback_query.from_user.id
                # TODO: 获取用户或群组ID (如果需要)
                user_id = None # 根据你的用户管理逻辑获取
                group_id = 0 # 如果在群组中使用，这里需要获取群组ID

                # 创建订单
                async with SessionFactory() as session:
                    order_data = {
                        "order_no": order_no,
                        "group_id": group_id,
                        "user_id": user_id,
                        "telegram_id": telegram_id,
                        "amount": final_amount,
                        "coin_type": RechargeOrder.CoinType.USDT_TRC20, # 假设都是TRC20
                        "points": points,
                        "bonus_points": bonus_points,
                        "address": WALLET_ADDRESS,
                        "tx_hash": None,
                        "status": RechargeOrder.Status.PENDING,
                        "expire_time": expire_time_utc,  # 使用 UTC 时间存储
                        "remarks": None
                    }
                    new_order = await recharge_order.create(session=session, obj_in=order_data)
                    logger.info(f"Created recharge order: {new_order.order_no} with amount {new_order.amount} for user {telegram_id}")
                
                # 生成二维码 (使用最终金额)
                qr_image, qr_content = generate_qr_code(WALLET_ADDRESS, float(final_amount))
                
                # 构建充值信息文本 (使用最终金额和订单号)
                recharge_message_text = (
                    "🪙 您正在使用 TRC20 付款\n\n"
                    f"订单号: {order_no}\n"
                    f"付款金额:\n{final_amount} U\n\n"
                    "支持货币:USDT 💰\n\n"
                    f"收款地址(TRC20):\n`{WALLET_ADDRESS}`\n\n"
                    "👇 点击复制钱包地址, 可重复充值!\n"
                    "⚠️ 上面地址和二维码不一致, 请不要付款!\n\n"
                    "提示:\n"
                    f"- 请务必转账精确金额: {final_amount} USDT\n"
                    "- 对上述地址 充值后, 经过3次网络确认, 充值成功!\n"
                    "- 请耐心等待, 充值成功后 Bot 会通知您!\n"
                    f"\n订单过期时间: {expire_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)"
                )
                
                # 发送二维码图片和充值信息
                await callback_query.message.answer_photo(
                    BufferedInputFile(qr_image, filename="recharge_qr.png"),
                    caption=recharge_message_text,
                    parse_mode="Markdown",
                    reply_markup=get_recharge_confirm_keyboard() # 添加返回按钮
                )
                
                # 删除之前的充值金额选择消息
                await callback_query.message.delete()
                
            except ValueError:
                await callback_query.answer("❌ 无效的金额", show_alert=True)
                return
            except ConversionSyntax as e:
                logger.error(f"Decimal conversion failed for callback data: {callback_query.data}, amount string: {amount_str}. Error: {e}", exc_info=True)
                await callback_query.answer("❌ 处理失败，请稍后重试", show_alert=True)
    except Exception as e:
        logger.error(f"处理充值回调失败: {e}", exc_info=True)
        await callback_query.answer("❌ 处理失败，请稍后重试", show_alert=True)


@commands_router.message(Menu.waiting_for_amount)
async def handle_custom_amount(message: Message, state: FSMContext):
    """处理自定义充值金额"""
    try:
        amount_input = message.text.strip()

        # 只允许整数或一位小数
        import re
        if not re.match(r'^\d+(\.\d)?$', amount_input):
            await message.answer("❌ 请输入整数或最多一位小数的金额（如 1 或 1.2）")
            return

        # 检查是否为有效数字
        try:
            base_amount = Decimal(amount_input)
        except Exception:
            await message.answer("❌ 请输入有效的金额（数字）")
            return

        if base_amount < 1:
            await message.answer("❌ 最小充值金额为1 USDT")
            return
        
        # 生成随机两位小数并转换为三位小数的Decimal
        random_last_two = Decimal(str(random.randint(0, 99)).zfill(2)) / 1000 # 0.0XX
        final_amount = (base_amount + random_last_two).quantize(Decimal('0.000'), rounding=ROUND_HALF_UP) # 确保最终三位小数
        
        # 生成唯一订单号
        order_no = f"RECHARGE-{uuid.uuid4().hex[:12].upper()}-{int(datetime.now().timestamp())}"
        
        # 使用中国时区创建过期时间
        china_tz = ZoneInfo('Asia/Shanghai')
        now_china = datetime.now(china_tz)
        expire_time = now_china + timedelta(minutes=30)  # 订单有效期30分钟
        # 转换为 UTC 时间存储
        expire_time_utc = expire_time.astimezone(timezone.utc)

        # 计算积分 (这里简单示例，实际逻辑可能更复杂)
        points = int(final_amount) # 例如，每充值1 USDT获得1积分
        bonus_points = 0

        # 获取用户Telegram ID
        telegram_id = message.from_user.id
        # TODO: 获取用户或群组ID (如果需要)
        user_id = None # 根据你的用户管理逻辑获取
        group_id = 0 # 如果在群组中使用，这里需要获取群组ID

        # 创建订单
        async with SessionFactory() as session:
            order_data = {
                "order_no": order_no,
                "group_id": group_id,
                "user_id": user_id,
                "telegram_id": telegram_id,
                "amount": final_amount,
                "coin_type": RechargeOrder.CoinType.USDT_TRC20, # 假设都是TRC20
                "points": points,
                "bonus_points": bonus_points,
                "address": WALLET_ADDRESS,
                "tx_hash": None,
                "status": RechargeOrder.Status.PENDING,
                "expire_time": expire_time_utc,  # 使用 UTC 时间存储
                "remarks": None
            }
            new_order = await recharge_order.create(session=session, obj_in=order_data)
            logger.info(f"Created recharge order: {new_order.order_no} with amount {new_order.amount} for user {telegram_id}")
        
        # 生成二维码 (使用最终金额)
        qr_image, qr_content = generate_qr_code(WALLET_ADDRESS, float(final_amount))
        
        # 构建充值信息文本 (使用最终金额和订单号)
        recharge_message_text = (
            "🪙 您正在使用 TRC20 付款\n\n"
            f"订单号: {order_no}\n"
            f"付款金额:\n{final_amount} U\n\n"
            "支持货币:USDT 💰\n\n"
            f"收款地址(TRC20):\n`{WALLET_ADDRESS}`\n\n"
            "👇 点击复制钱包地址, 可重复充值!\n"
            "⚠️ 上面地址和二维码不一致, 请不要付款!\n\n"
            "提示:\n"
            f"- 请务必转账精确金额: {final_amount} USDT\n"
            "- 对上述地址 充值后, 经过3次网络确认, 充值成功!\n"
            "- 请耐心等待, 充值成功后 Bot 会通知您!\n"
            f"\n订单过期时间: {expire_time.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)"
        )
        
        # 发送二维码图片和充值信息
        await message.answer_photo(
            BufferedInputFile(qr_image, filename="recharge_qr.png"),
            caption=recharge_message_text,
            parse_mode="Markdown",
            reply_markup=get_recharge_confirm_keyboard() # 添加返回按钮
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ 请输入有效的金额")
    except Exception as e:
        logger.error(f"处理自定义金额失败: {e}", exc_info=True)
        await message.answer("❌ 处理失败，请稍后重试")
        await state.clear()


@commands_router.message(Command("cancel"))
async def command_cancel_handler(message: Message, state: FSMContext):
    """处理 /cancel 命令"""
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer("✅ 已取消当前操作")
    else:
        await message.answer("❌ 没有正在进行的操作")


@commands_router.callback_query(F.data == "recharge_back")
async def handle_recharge_back(callback_query: CallbackQuery, state: FSMContext):
    """处理充值确认界面的返回按钮"""
    await state.clear()
    await callback_query.message.delete()
    await command_recharge_handler(callback_query.message)
    await callback_query.answer()


@commands_router.callback_query(F.data == "exchange_usdt_to_points")
async def handle_exchange_usdt_to_points_callback(callback_query: CallbackQuery, state: FSMContext):
    """
    处理 USDT 兑换积分按钮回调
    """
    await state.set_state(Menu.waiting_for_usdt_exchange_amount) # 设置等待 USDT 兑换数量状态
    await callback_query.message.edit_text(
        f"🔄 USDT 兑换积分\n\n"
        f"当前兑换率：1 USDT = {USDT_TO_POINTS_RATE} 积分\n\n"
        "请回复您想用于兑换的 USDT 数量 (整数或小数)。\n\n"
        "输入 /cancel 可以取消操作"
    )
    await callback_query.answer()


@commands_router.message(Menu.waiting_for_usdt_exchange_amount)
async def handle_usdt_exchange_amount(message: Message, state: FSMContext):
    """
    处理用户输入的 USDT 兑换数量
    """
    try:
        amount_str = message.text.strip()
        try:
            # 确保输入是有效的数字，并限制小数位数
            usdt_amount = Decimal(amount_str).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        except Exception:
            await message.answer("❌ 请输入有效的 USDT 数量（最多两位小数）")
            return

        if usdt_amount <= 0:
            await message.answer("❌ 兑换数量必须大于0")
            return
            
        # 计算获得的积分数量（向下取整）
        points_to_gain = (usdt_amount * USDT_TO_POINTS_RATE).quantize(Decimal('1'), rounding=ROUND_DOWN)

        async with SessionFactory() as session:
            telegram_id = message.from_user.id
            
            # 获取用户钱包账户 (account_type = 2)
            wallet_account = await account.get_by_telegram_id_and_type(session=session, telegram_id=telegram_id, account_type=2)
            # 获取用户积分账户 (account_type = 1)
            points_account = await account.get_by_telegram_id_and_type(session=session, telegram_id=telegram_id, account_type=1)

            if not wallet_account:
                await message.answer("❌ 未找到您的钱包账户，请联系客服。")
                await state.clear()
                return
                
            if not points_account:
                await message.answer("❌ 未找到您的积分账户，请联系客服。")
                await state.clear()
                return

            # 将钱包余额转换为 USDT（6位小数）
            wallet_available_usdt = Decimal(str(wallet_account.available_amount)) / Decimal('1000000')
            wallet_available_usdt = wallet_available_usdt.quantize(Decimal('0.01'), rounding=ROUND_DOWN)

            if wallet_available_usdt < usdt_amount:
                await message.answer(f"❌ 您的钱包余额不足，当前可用余额：{wallet_available_usdt} USDT")
                await state.clear()
                return

            try:
                # 执行兑换：扣除钱包余额，增加积分余额
                # 将 USDT 转换为存储单位（6位小数）
                usdt_to_deduct_stored = int((usdt_amount * Decimal('1000000')).quantize(Decimal('1'), rounding=ROUND_DOWN))
                wallet_account.available_amount -= usdt_to_deduct_stored
                wallet_account.total_amount -= usdt_to_deduct_stored
                
                # 积分直接使用整数存储
                points_to_gain_stored = int(points_to_gain)
                points_account.available_amount += points_to_gain_stored
                points_account.total_amount += points_to_gain_stored

                # 记录钱包账户交易（消费）
                await account_transaction.create(
                    session=session,
                    account_id=wallet_account.id,
                    telegram_id=telegram_id,
                    account_type=2,  # 钱包账户
                    transaction_type=2,  # 消费
                    amount=-usdt_to_deduct_stored,  # 负数表示支出
                    balance=wallet_account.available_amount,
                    remarks=f"兑换积分 {points_to_gain_stored}"
                )

                # 记录积分账户交易（奖励）
                await account_transaction.create(
                    session=session,
                    account_id=points_account.id,
                    telegram_id=telegram_id,
                    account_type=1,  # 积分账户
                    transaction_type=3,  # 充值
                    amount=points_to_gain_stored,
                    balance=points_account.available_amount,
                    remarks=f"USDT兑换 {usdt_amount} USDT"
                )

                await session.commit()

                # 查询更新后的余额以回复用户
                await session.refresh(wallet_account)
                await session.refresh(points_account)
                
                # 转换回显示格式
                updated_wallet_balance = (Decimal(str(wallet_account.available_amount)) / Decimal('1000000')).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
                updated_points_balance = Decimal(str(points_account.available_amount))

                await message.answer(
                    f"✅ 兑换成功！\n\n"
                    f"用 {usdt_amount} USDT 成功兑换了 {points_to_gain_stored} 积分。\n\n"
                    f"您的最新余额：\n"
                    f"💰 积分余额：{updated_points_balance} 积分\n"
                    f"💳 钱包余额：{updated_wallet_balance} USDT"
                )

            except Exception as e:
                logger.error(f"更新账户余额失败: {e}", exc_info=True)
                await session.rollback()
                await message.answer("❌ 兑换失败，请稍后重试")
                return

        await state.clear()

    except ValueError:
        await message.answer("❌ 请输入有效的 USDT 数量（数字格式）")
    except Exception as e:
        logger.error(f"处理 USDT 兑换积分失败: {e}", exc_info=True)
        await message.answer("❌ 兑换失败，请稍后重试")
        await state.clear()


@commands_router.message(Command("check_recharge"))
async def command_check_recharge_handler(message: Message, state: FSMContext):
    """
    处理 /check_recharge 命令，检查充值状态
    """
    await state.set_state(Menu.waiting_for_amount)  # 复用现有的等待金额输入状态
    await message.answer(
        "请输入您要查询的充值金额（USDT）：\n\n"
        "💡 请输入精确的充值金额，包括小数点后的数字\n"
        "⚠️ 系统将检查最近的交易\n"
        "输入 /cancel 可以取消操作"
    )

@commands_router.message(Menu.waiting_for_amount, F.text.regexp(r"^\d+(\.\d+)?$"))
async def handle_recharge_check(message: Message, state: FSMContext):
    """
    处理充值状态检查
    """
    try:
        amount_str = message.text.strip()
        try:
            amount = float(amount_str)
        except ValueError:
            await message.answer("❌ 请输入有效的金额")
            return

        if amount <= 0:
            await message.answer("❌ 金额必须大于 0")
            return

        # 获取充值状态
        transactions = check_recharge_status(WALLET_ADDRESS, amount)
        
        if not transactions:
            await message.answer(
                f"❌ 未找到金额为 {amount} USDT 的充值交易\n\n"
                "可能的原因：\n"
                "1. 交易尚未完成\n"
                "2. 交易金额不匹配\n"
                "3. 交易尚未被确认\n\n"
                "请确认：\n"
                "1. 是否已完成转账\n"
                "2. 转账金额是否准确\n"
                "3. 是否使用了 TRC20 网络"
            )
        else:
            # 找到匹配的交易
            reply_text = f"✅ 找到 {len(transactions)} 笔匹配的充值交易：\n\n"
            for tx in transactions:
                reply_text += (
                    f"交易哈希：`{tx['tx_hash']}`\n"
                    f"金额：{Decimal(str(tx['amount'])).quantize(Decimal('0.1'), rounding=ROUND_DOWN)} USDT\n"
                    f"时间：{datetime.fromtimestamp(tx['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S')}\n"
                    "---\n"
                )
            await message.answer(reply_text, parse_mode="Markdown")

        await state.clear()

    except Exception as e:
        logger.error(f"检查充值状态失败: {e}", exc_info=True)
        await message.answer("❌ 检查充值状态失败，请稍后重试")
        await state.clear()


