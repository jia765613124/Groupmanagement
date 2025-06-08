import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_DOWN
from typing import List, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.db import SessionFactory
from bot.crud import recharge_order, account, account_transaction
from bot.models.recharge_order import RechargeOrder
from bot.models.account import Account
from bot.utils.wallet import check_recharge_status
from bot.misc import bot
from bot.config import get_config

config = get_config()
logger = logging.getLogger(__name__)

async def check_pending_recharges():
    """
    检查所有待处理的充值订单，并更新状态
    """
    logger.info("开始检查待处理的充值订单...")
    
    async with SessionFactory() as session:
        try:
            # 获取所有待处理且未过期的订单
            stmt = select(RechargeOrder).where(
                and_(
                    RechargeOrder.status == 1,
                    RechargeOrder.expire_time > datetime.now(timezone.utc)  # 使用 UTC 时间比较
                )
            )
            result = await session.execute(stmt)
            pending_orders = result.scalars().all()

            if not pending_orders:
                logger.info("没有找到待处理的充值订单")
                return

            logger.info(f"找到 {len(pending_orders)} 个待处理的充值订单")

            # 计算过去一小时的时间范围（中国大陆时区，转为UTC）
            china_tz = ZoneInfo('Asia/Shanghai')
            # 获取当前中国时区时间
            now_china = datetime.now(china_tz)
            # 设置结束时间为当前时间的整秒
            end_time = now_china.replace(microsecond=0)
            # 设置开始时间为一小时前
            start_time = end_time - timedelta(hours=1)
            
            # 转换为 UTC 时间并格式化为 ISO 8601 格式
            min_timestamp = start_time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            max_timestamp = end_time.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            
            logger.info(f"中国时区时间范围: {start_time} - {end_time}")
            logger.info(f"UTC 时间范围: {min_timestamp} - {max_timestamp}")
            
            # 获取交易记录
            transactions = await check_recharge_status(
                address=config.WALLET_ADDRESS,
                start_timestamp=min_timestamp,
                end_timestamp=max_timestamp
            )
            logger.info(f"获取到 {len(transactions)} 笔交易记录")

            # 处理每个待处理订单
            for order in pending_orders:
                await process_pending_order(session, order, transactions)

        except Exception as e:
            logger.error(f"检查待处理充值订单时发生错误: {str(e)}", exc_info=True)
            await session.rollback()
        finally:
            await session.close()

async def process_pending_order(session: AsyncSession, order: RechargeOrder, transactions: List[dict]):
    """
    处理单个待处理订单
    """
    logger.info(f"处理订单 {order.order_no} (金额: {order.amount} USDT)")
    
    try:
        for tx in transactions:
            # 检查 tx_hash 是否已被其他订单使用
            tx_hash = tx.get('tx_hash')
            if not tx_hash:
                continue
            # 查询是否有其他订单已用此 tx_hash
            stmt = select(RechargeOrder).where(RechargeOrder.tx_hash == tx_hash)
            result = await session.execute(stmt)
            existing_order = result.scalar_one_or_none()
            if existing_order:
                logger.info(f"交易哈希 {tx_hash} 已被订单 {existing_order.order_no} 使用，跳过。")
                continue

            if not await is_valid_transaction(tx, order):
                continue

            # 更新订单状态
            order.status = RechargeOrder.Status.COMPLETED  # 使用枚举值 3 表示已完成
            order.tx_hash = tx_hash
            order.paid_at = datetime.now(timezone.utc)  # 使用 UTC 时间记录支付时间
            
            # 更新用户余额
            await update_user_balance(session, order.telegram_id, Decimal(str(order.amount)))
            
            # 通知用户
            await notify_user(order)
            
            await session.commit()
            logger.info(f"订单 {order.order_no} 处理完成")
            return

        logger.info(f"订单 {order.order_no} 未找到匹配的充值交易")
            
    except Exception as e:
        logger.error(f"处理订单 {order.order_no} 时发生错误: {str(e)}", exc_info=True)
        await session.rollback()

async def is_valid_transaction(tx: dict, order: RechargeOrder) -> bool:
    """
    验证交易是否有效且匹配订单
    """
    tx_amount = tx.get('amount')
    if tx_amount is None:
        logger.warning(f"跳过交易 {tx.get('tx_hash')} - 金额为空")
        return False

    # 比较交易金额与订单金额（允许 0.01 USDT 的误差）
    if abs(float(tx_amount) - float(order.amount)) <= 0.01:
        logger.info(f"找到匹配的充值交易: {tx.get('tx_hash')} (金额: {tx_amount} USDT)")
        return True
    
    logger.debug(f"交易 {tx.get('tx_hash')} 金额 {tx_amount} USDT 与订单金额 {order.amount} USDT 不匹配")
    return False

def split_amount_and_fee(amount_usdt: Decimal):
    # 到账部分：保留一位小数，向下截断
    amount_to_wallet = amount_usdt.quantize(Decimal('0.1'), rounding=ROUND_DOWN)
    # 手续费：剩余部分
    fee = amount_usdt - amount_to_wallet
    return amount_to_wallet, fee

async def update_user_balance(session: AsyncSession, telegram_id: int, amount_usdt: Decimal):
    """
    更新用户的钱包账户余额
    """
    logger.info(f"更新用户 {telegram_id} 的钱包余额: {amount_usdt} USDT")
    try:
        # 查找或创建钱包账户
        wallet_account = await account.get_by_telegram_id_and_type(
            session=session, 
            telegram_id=telegram_id, 
            account_type=2
        )

        if not wallet_account:
            wallet_account = await create_wallet_account(session, telegram_id)

        # 到账部分保留两位小数，手续费为最后两位
        amount_to_wallet, fee = split_amount_and_fee(amount_usdt)
        amount_in_smallest_unit = int(amount_to_wallet * Decimal('1000000'))
        logger.info(f"充值到账部分: {amount_to_wallet}，存入最小单位: {amount_in_smallest_unit}")
        wallet_account.total_amount += amount_in_smallest_unit
        wallet_account.available_amount += amount_in_smallest_unit
        wallet_account.updated_at = datetime.utcnow()
        logger.info(f"用户 {telegram_id} 的钱包余额已更新，到账 {amount_to_wallet} USDT，手续费 {fee} USDT，当前 available_amount: {wallet_account.available_amount}")
        
        # 记录充值交易
        await account_transaction.create(
            session=session,
            account_id=wallet_account.id,
            telegram_id=telegram_id,
            account_type=2,  # 钱包账户
            transaction_type=1,  # 充值
            amount=amount_in_smallest_unit,
            balance=wallet_account.available_amount,
            remarks=f"USDT充值 {amount_to_wallet} USDT"
        )
        
    except Exception as e:
        logger.error(f"更新用户 {telegram_id} 钱包余额时发生错误: {str(e)}", exc_info=True)
        raise

async def create_wallet_account(session: AsyncSession, telegram_id: int) -> Account:
    """
    创建新的钱包账户
    """
    wallet_account_data = {
        "telegram_id": telegram_id,
        "account_type": 2,
        "total_amount": 0,
        "available_amount": 0,
        "frozen_amount": 0,
        "status": 1,
        "remarks": "Auto-created wallet account"
    }
    return await account.create(session=session, obj_in=wallet_account_data)

async def notify_user(order: RechargeOrder):
    """
    通知用户充值完成
    """
    max_retries = 3
    retry_delay = 5  # 秒
    
    for attempt in range(max_retries):
        try:
            amount_str = f"{Decimal(order.amount).quantize(Decimal('0.1'), rounding=ROUND_DOWN)}"
            message_text = (
                "✅ 充值成功！\n\n"
                f"订单号: {order.order_no}\n"
                f"充值金额: {amount_str} USDT\n"
                f"交易哈希: `{order.tx_hash}`\n\n"
                "您的钱包余额已更新。"
            )
            await bot.send_message(order.telegram_id, message_text, parse_mode="Markdown")
            logger.info(f"已发送充值成功通知给用户 {order.telegram_id}")
            return  # 发送成功，退出函数
            
        except Exception as e:
            if attempt < max_retries - 1:  # 如果不是最后一次尝试
                logger.warning(f"发送充值成功通知给用户 {order.telegram_id} 失败 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
                await asyncio.sleep(retry_delay)  # 等待一段时间后重试
            else:  # 最后一次尝试失败
                logger.error(f"发送充值成功通知给用户 {order.telegram_id} 最终失败: {str(e)}", exc_info=True)
                # 这里不抛出异常，因为通知失败不应该影响充值流程
                return

async def start_recharge_checker():
    """
    启动定期充值检查任务
    """
    logger.info("启动充值检查任务...")
    while True:
        try:
            await check_pending_recharges()
        except Exception as e:
            logger.error(f"充值检查任务发生错误: {str(e)}", exc_info=True)
        finally:
            await asyncio.sleep(60)  # 每60秒检查一次 

def format_usdt_balance(available_amount: int) -> str:
    usdt = Decimal(available_amount) / Decimal('1000000')
    usdt = usdt.quantize(Decimal('0.001'), rounding=ROUND_DOWN)  # 保留3位小数，且不进位
    return f"{usdt} USDT" 