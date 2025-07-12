import logging
import datetime
from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from bot.common.uow import UoW
from bot.database.db import SessionFactory
from bot.models.tg_user_group import User
from bot.models.account import Account
from bot.models.account_transaction import AccountTransaction
from bot.crud.account import account
from bot.crud.sign_in_record import sign_in_record
from bot.config import get_config

logger = logging.getLogger(__name__)
checkin_router = Router()
config = get_config()

# 积分账户类型
POINT_ACCOUNT_TYPE = 1
# 现金账户类型
CASH_ACCOUNT_TYPE = 2
# 每次签到积分
CHECKIN_POINTS = 100
# 签到交易类型
CHECKIN_TRANSACTION_TYPE = 4

# 连续签到奖励规则
CONTINUOUS_CHECKIN_RULES = [
    {"days": 3, "bonus": 200, "description": "连续签到3天"},
    {"days": 7, "bonus": 500, "description": "连续签到7天"},
    {"days": 14, "bonus": 1000, "description": "连续签到14天"},
    {"days": 21, "bonus": 1500, "description": "连续签到21天"},
    {"days": 30, "bonus": 2000, "description": "连续签到1个月"},
    {"days": 60, "bonus": 5000, "description": "连续签到2个月"},
    {"days": 90, "bonus": 8000, "description": "连续签到3个月"},
    {"days": 180, "bonus": 20000, "description": "连续签到半年"},
    {"days": 365, "bonus": 50000, "description": "连续签到一年"},
]

def get_bonus_description(continuous_days: int) -> str:
    """根据连续签到天数获取奖励描述"""
    for rule in CONTINUOUS_CHECKIN_RULES:
        if continuous_days == rule["days"]:
            return rule["description"]
    return f"连续签到{continuous_days}天"

def is_allowed_group(chat_id: int) -> bool:
    """检查群组是否允许签到"""
    if not config.checkin_allowed_groups:
        # 如果没有配置允许的群组，则默认允许所有群组
        return True
    
    allowed_groups = [int(group_id.strip()) for group_id in config.checkin_allowed_groups.split(',') if group_id.strip()]
    return chat_id in allowed_groups

@checkin_router.message(F.text.casefold() == "签到")
async def handle_checkin(message: Message) -> None:
    """处理签到命令"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if message.chat.type not in ["group", "supergroup"]:
            logger.info(f"用户 {user_id} 尝试在非群组中签到")
            return
        
        # 检查群组是否允许签到
        if not is_allowed_group(chat_id):
            logger.info(f"用户 {user_id} 尝试在非允许的群组 {chat_id} 中签到")
            await message.reply("⚠️ 本群组不支持签到功能")
            return
            
        logger.info(f"用户 {user_id} 在群组 {chat_id} 中签到")
        
        async with SessionFactory() as session:
            uow = UoW(session)
            async with uow.session.begin():
                # 1. 获取或创建用户
                user = await get_or_create_user(uow.session, message)
                
                # 2. 获取或创建账户
                point_account = await get_or_create_account(uow.session, user_id, user.id, POINT_ACCOUNT_TYPE)
                cash_account = await get_or_create_account(uow.session, user_id, user.id, CASH_ACCOUNT_TYPE)
                
                # 3. 检查今天是否已经签到
                today = datetime.date.today()
                has_checked = await sign_in_record.get_by_telegram_id_and_date_any_group(
                    uow.session, user_id, today
                )
                
                if has_checked:
                    # 已经在任意群组签到过了
                    await message.reply(f"您今天已经签到过了，每天只能签到一次！\n当前积分：{point_account.available_amount}")
                    return
                
                # 4. 计算连续签到天数
                continuous_days = await sign_in_record.calculate_continuous_days_across_groups(
                    uow.session, user_id, today
                )
                
                # 5. 创建签到记录
                record = await sign_in_record.create_sign_in(
                    uow.session, 
                    chat_id, 
                    user.id, 
                    user_id, 
                    CHECKIN_POINTS, 
                    continuous_days, 
                    today
                )
                
                # 6. 计算特殊奖励积分
                bonus_points = 0
                bonus_description = ""
                
                # 查找符合条件的最高奖励等级
                for rule in sorted(CONTINUOUS_CHECKIN_RULES, key=lambda x: x["days"], reverse=True):
                    if continuous_days == rule["days"]:
                        bonus_points = rule["bonus"]
                        bonus_description = rule["description"]
                        break
                
                # 7. 更新账户积分（基础积分 + 连续签到奖励 + 特殊奖励）
                total_points = record.total_points + bonus_points
                point_account.total_amount += total_points
                point_account.available_amount += total_points
                
                # 7.1 创建签到交易记录
                transaction = AccountTransaction(
                    account_id=point_account.id,
                    user_id=user.id,
                    telegram_id=user_id,
                    account_type=POINT_ACCOUNT_TYPE,
                    transaction_type=CHECKIN_TRANSACTION_TYPE,
                    amount=total_points,
                    balance=point_account.available_amount,
                    group_id=chat_id,
                    remarks=f"签到奖励 (连续{continuous_days}天)"
                )
                uow.session.add(transaction)
                
                # 8. 组织回复消息
                reply_msg = f"✅ 签到成功！\n获得 {CHECKIN_POINTS} 基础积分\n"
                
                # 添加连续签到奖励信息
                if record.bonus_points > 0:
                    # 计算当前是一周内的第几天
                    day_in_week = ((continuous_days - 1) % 7) + 1
                    reply_msg += f"🔄 连续签到奖励：{record.bonus_points} 积分 (第{day_in_week}天)\n"
                
                # 添加特殊奖励信息
                if bonus_points > 0:
                    reply_msg += f"🎁 {bonus_description}，额外奖励：{bonus_points} 积分\n"
                
                reply_msg += f"当前积分：{point_account.available_amount}"
                
                await message.reply(reply_msg)
    except Exception as e:
        logger.error(f"签到处理失败: {e}", exc_info=True)
        await message.reply("❌ 签到失败，请稍后再试")

@checkin_router.message(F.text.casefold() == "查询积分")
async def handle_query_points(message: Message) -> None:
    """处理查询积分命令"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if message.chat.type not in ["group", "supergroup"]:
            logger.info(f"用户 {user_id} 尝试在非群组中查询积分")
            return
        
        # 检查群组是否允许签到（查询积分也限制在允许签到的群组中）
        if not is_allowed_group(chat_id):
            logger.info(f"用户 {user_id} 尝试在非允许的群组 {chat_id} 中查询积分")
            await message.reply("⚠️ 本群组不支持积分功能")
            return
            
        logger.info(f"用户 {user_id} 在群组 {chat_id} 中查询积分")
        
        async with SessionFactory() as session:
            uow = UoW(session)
            async with uow.session.begin():
                # 获取用户积分账户
                point_account = await account.get_by_telegram_id_and_type(uow.session, user_id, POINT_ACCOUNT_TYPE)
                
                if not point_account:
                    await message.reply("您还没有积分账户，请先签到开通")
                    return
                
                # 获取用户现金账户
                cash_account = await account.get_by_telegram_id_and_type(uow.session, user_id, CASH_ACCOUNT_TYPE)
                cash_amount = cash_account.available_amount if cash_account else 0
                # 格式化钱包余额，除以1000000并保留2位小数
                wallet_balance = f"{cash_amount / 1000000:.2f}U" if cash_amount else "0.00U"
                
                # 获取连续签到记录
                today = datetime.date.today()
                
                # 获取用户今日是否已签到
                today_record = await sign_in_record.get_by_telegram_id_and_date_any_group(
                    uow.session, user_id, today
                )
                
                if today_record:
                    continuous_days = today_record.continuous_days
                    sign_status = "✅ 今日已签到"
                else:
                    continuous_days = 0  # 如果今天没签到，连续天数显示为0
                    sign_status = "❌ 今日未签到"
                
                await message.reply(
                    f"👤 用户：{message.from_user.first_name}\n"
                    f"🔢 积分余额：{point_account.available_amount}\n"
                    f"💰 钱包余额：{wallet_balance}\n"
                    f"📅 连续签到：{continuous_days}天\n"
                    f"📝 状态：{sign_status}"
                )
    except Exception as e:
        logger.error(f"查询积分处理失败: {e}", exc_info=True)
        await message.reply("❌ 查询失败，请稍后再试")

# 辅助函数

async def get_or_create_user(session, message) -> User:
    """获取或创建用户"""
    user = await session.scalar(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    
    if not user:
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code,
            is_premium=getattr(message.from_user, 'is_premium', False),
            join_source=2,  # 来自群组
            source_group_id=message.chat.id
        )
        session.add(user)
        await session.flush()
        
    return user

async def get_or_create_account(session, telegram_id: int, user_id: int, account_type: int) -> Account:
    """获取或创建账户"""
    account_obj = await account.get_by_telegram_id_and_type(session, telegram_id, account_type)
    
    if not account_obj:
        account_obj = Account(
            user_id=user_id,
            telegram_id=telegram_id,
            account_type=account_type,
            total_amount=0,
            available_amount=0,
            frozen_amount=0,
            status=1  # 正常
        )
        session.add(account_obj)
        await session.flush()
        
    return account_obj 