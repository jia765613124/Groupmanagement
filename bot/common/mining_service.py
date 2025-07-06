"""
挖矿服务类
处理购买矿工卡、发放奖励、领取奖励等业务逻辑
"""

from typing import Dict, Optional, Tuple, List
from datetime import datetime, date, timedelta
from decimal import Decimal
from bot.config.mining_config import MiningConfig
from bot.crud.mining import mining_card, mining_reward, mining_statistics
from bot.crud.account import account as account_crud
from bot.crud.account_transaction import account_transaction as transaction_crud
from bot.common.uow import UoW
import logging

logger = logging.getLogger(__name__)

class MiningService:
    """挖矿服务类"""
    
    def __init__(self, uow: UoW):
        self.uow = uow
    
    async def can_purchase_mining_card(self, telegram_id: int, card_type: str) -> Tuple[bool, str]:
        """
        检查用户是否可以购买矿工卡
        
        Args:
            telegram_id: Telegram用户ID
            card_type: 矿工卡类型
            
        Returns:
            (是否可以购买, 错误信息)
        """
        try:
            # 获取矿工卡配置
            card_config = MiningConfig.get_mining_card(card_type)
            if not card_config:
                return False, "无效的矿工卡类型"
            
            # 检查用户钱包账户
            async with self.uow:
                wallet_account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    MiningConfig.ACCOUNT_TYPE_WALLET
                )
                
                if not wallet_account:
                    return False, "钱包账户不存在，请先创建账户"
                
                if wallet_account.status != 1:
                    return False, "钱包账户已被冻结，无法购买矿工卡"
                
                # 检查USDT余额
                cost_usdt = card_config.cost_usdt  # 已经是整数格式
                if wallet_account.available_amount < cost_usdt:
                    return False, f"USDT余额不足，需要{cost_usdt / 1000000:.2f}U，当前余额不足"
                
                # 检查同类型矿工卡数量限制
                active_count = await mining_card.get_active_cards_count_by_type(
                    self.uow.session,
                    telegram_id=telegram_id,
                    card_type=card_type
                )
                
                if active_count >= card_config.max_cards:
                    return False, f"已达到{card_config.name}最大使用数量限制({card_config.max_cards}张)"
                
                return True, ""
                
        except Exception as e:
            logger.error(f"检查购买矿工卡条件失败: {e}")
            return False, "系统错误，请稍后重试"
    
    async def purchase_mining_card(self, telegram_id: int, card_type: str) -> Dict:
        """
        购买矿工卡
        
        Args:
            telegram_id: Telegram用户ID
            card_type: 矿工卡类型
            
        Returns:
            购买结果字典
        """
        try:
            # 检查是否可以购买
            can_purchase, error_msg = await self.can_purchase_mining_card(telegram_id, card_type)
            if not can_purchase:
                return {
                    "success": False,
                    "message": error_msg,
                    "mining_card": None
                }
            
            # 获取矿工卡配置
            card_config = MiningConfig.get_mining_card(card_type)
            
            # 执行购买操作
            async with self.uow:
                # 获取用户钱包账户
                wallet_account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    MiningConfig.ACCOUNT_TYPE_WALLET
                )
                
                # 扣除USDT
                cost_usdt = card_config.cost_usdt  # 已经是整数格式
                wallet_account.available_amount -= cost_usdt
                wallet_account.total_amount -= cost_usdt
                await account_crud.update(
                    session=self.uow.session,
                    db_obj=wallet_account,
                    obj_in={"available_amount": wallet_account.available_amount, "total_amount": wallet_account.total_amount}
                )
                
                # 记录扣除交易
                await transaction_crud.create(
                    session=self.uow.session,
                    account_id=wallet_account.id,
                    telegram_id=telegram_id,
                    account_type=MiningConfig.ACCOUNT_TYPE_WALLET,
                    transaction_type=MiningConfig.TRANSACTION_TYPE_MINING_PURCHASE,
                    amount=-cost_usdt,
                    balance=wallet_account.available_amount,
                    remarks=f"购买{card_config.name}"
                )
                
                # 创建矿工卡记录
                start_time = datetime.now()
                end_time = start_time + timedelta(days=card_config.duration_days)
                
                mining_card_record = await mining_card.create_mining_card(
                    session=self.uow.session,
                    telegram_id=telegram_id,
                    card_type=card_type,
                    cost_usdt=cost_usdt,
                    daily_points=card_config.daily_points,
                    total_days=card_config.duration_days,
                    start_time=start_time,
                    end_time=end_time,
                    remarks=f"购买{card_config.name}"
                )
                
                # 更新统计信息
                await mining_statistics.update_statistics(
                    session=self.uow.session,
                    telegram_id=telegram_id,
                    card_type=card_type,
                    cost_usdt=cost_usdt,
                    earned_points=0
                )
                
                await self.uow.commit()
                
                return {
                    "success": True,
                    "message": f"成功购买{card_config.name}！",
                    "mining_card": {
                        "id": mining_card_record.id,
                        "name": card_config.name,
                        "daily_points": card_config.daily_points,
                        "total_days": card_config.duration_days,
                        "start_time": start_time,
                        "end_time": end_time
                    }
                }
                
        except Exception as e:
            logger.error(f"购买矿工卡失败: {e}")
            await self.uow.rollback()
            return {
                "success": False,
                "message": "购买失败，请稍后重试",
                "mining_card": None
            }
    
    async def get_mining_info(self, telegram_id: int) -> Dict:
        """
        获取挖矿相关信息
        
        Args:
            telegram_id: Telegram用户ID
            
        Returns:
            挖矿信息字典
        """
        try:
            async with self.uow:
                # 获取用户钱包账户
                wallet_account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    MiningConfig.ACCOUNT_TYPE_WALLET
                )
                
                if not wallet_account:
                    return {
                        "success": False,
                        "message": "钱包账户不存在，请先创建账户",
                        "wallet_balance": 0,
                        "cards_info": {},
                        "pending_rewards": 0
                    }
                
                # 获取所有矿工卡配置
                cards_info = MiningConfig.get_all_cards_display_info()
                
                # 获取用户各类型矿工卡数量
                summary = await mining_card.get_user_mining_summary(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                # 为每个矿工卡添加用户信息
                for card_type, info in cards_info.items():
                    user_summary = summary.get(card_type, {"count": 0, "total_points": 0, "earned_points": 0})
                    info["user_count"] = user_summary["count"]
                    info["user_total_points"] = user_summary["total_points"]
                    info["user_earned_points"] = user_summary["earned_points"]
                    info["can_purchase"] = user_summary["count"] < info["max_cards"]
                    info["remaining_slots"] = info["max_cards"] - user_summary["count"]
                
                # 获取待领取奖励数量
                pending_count = await mining_reward.get_pending_rewards_count(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                # 获取待领取总积分
                pending_points = await mining_reward.get_total_pending_points(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                return {
                    "success": True,
                    "message": "",
                    "wallet_balance": wallet_account.available_amount / 1000000,  # 转换为USDT显示
                    "cards_info": cards_info,
                    "pending_rewards": pending_count,
                    "pending_points": pending_points
                }
                
        except Exception as e:
            logger.error(f"获取挖矿信息失败: {e}")
            return {
                "success": False,
                "message": "获取信息失败，请稍后重试",
                "wallet_balance": 0,
                "cards_info": {},
                "pending_rewards": 0,
                "pending_points": 0
            }
    
    async def get_pending_rewards(self, telegram_id: int, limit: int = 10, offset: int = 0) -> Dict:
        """
        获取待领取的挖矿奖励
        
        Args:
            telegram_id: Telegram用户ID
            limit: 限制记录数量
            offset: 分页偏移量
            
        Returns:
            待领取奖励列表
        """
        try:
            async with self.uow:
                rewards = await mining_reward.get_pending_rewards(
                    self.uow.session,
                    telegram_id=telegram_id,
                    skip=offset,
                    limit=limit
                )
                
                total_count = await mining_reward.get_pending_rewards_count(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                total_points = await mining_reward.get_total_pending_points(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                reward_list = []
                for reward in rewards:
                    reward_list.append({
                        "id": reward.id,
                        "card_type": reward.card_type,
                        "reward_points": reward.reward_points,
                        "reward_day": reward.reward_day,
                        "reward_date": reward.reward_date.isoformat() if reward.reward_date else None,
                        "remarks": reward.remarks
                    })
                
                current_page = (offset // limit) + 1
                total_pages = (total_count + limit - 1) // limit
                
                return {
                    "success": True,
                    "message": "",
                    "rewards": reward_list,
                    "total_count": total_count,
                    "total_points": total_points,
                    "current_page": current_page,
                    "total_pages": total_pages
                }
                
        except Exception as e:
            logger.error(f"获取待领取奖励失败: {e}")
            return {
                "success": False,
                "message": "获取奖励失败，请稍后重试",
                "rewards": [],
                "total_count": 0,
                "total_points": 0,
                "current_page": 1,
                "total_pages": 0
            }
    
    async def claim_all_rewards(self, telegram_id: int) -> Dict:
        """
        领取所有待领取的挖矿奖励
        
        Args:
            telegram_id: Telegram用户ID
            
        Returns:
            领取结果字典
        """
        try:
            async with self.uow:
                # 获取所有待领取的奖励
                pending_rewards = await mining_reward.get_pending_rewards(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                if not pending_rewards:
                    return {
                        "success": False,
                        "message": "没有待领取的奖励",
                        "claimed_rewards": [],
                        "total_points": 0
                    }
                
                # 获取用户积分账户
                points_account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    MiningConfig.ACCOUNT_TYPE_POINTS
                )
                
                if not points_account:
                    return {
                        "success": False,
                        "message": "积分账户不存在，请先创建账户",
                        "claimed_rewards": [],
                        "total_points": 0
                    }
                
                # 计算总积分
                total_points = sum(reward.reward_points for reward in pending_rewards)
                
                # 增加积分
                points_account.available_amount += total_points
                points_account.total_amount += total_points
                await account_crud.update(
                    session=self.uow.session,
                    db_obj=points_account,
                    obj_in={"available_amount": points_account.available_amount, "total_amount": points_account.total_amount}
                )
                
                # 记录积分奖励交易
                await transaction_crud.create(
                    session=self.uow.session,
                    account_id=points_account.id,
                    telegram_id=telegram_id,
                    account_type=MiningConfig.ACCOUNT_TYPE_POINTS,
                    transaction_type=MiningConfig.TRANSACTION_TYPE_MINING_REWARD,
                    amount=total_points,
                    balance=points_account.available_amount,
                    remarks=f"领取挖矿奖励，共{len(pending_rewards)}笔"
                )
                
                # 标记奖励为已领取
                reward_ids = [reward.id for reward in pending_rewards]
                claimed_rewards = await mining_reward.claim_rewards(
                    self.uow.session,
                    telegram_id=telegram_id,
                    reward_ids=reward_ids
                )
                
                await self.uow.commit()
                
                return {
                    "success": True,
                    "message": f"成功领取{len(claimed_rewards)}笔挖矿奖励，共{total_points:,}积分！",
                    "claimed_rewards": [
                        {
                            "card_type": reward.card_type,
                            "reward_points": reward.reward_points,
                            "reward_day": reward.reward_day
                        }
                        for reward in claimed_rewards
                    ],
                    "total_points": total_points
                }
                
        except Exception as e:
            logger.error(f"领取挖矿奖励失败: {e}")
            await self.uow.rollback()
            return {
                "success": False,
                "message": "领取奖励失败，请稍后重试",
                "claimed_rewards": [],
                "total_points": 0
            }
    
    async def process_daily_mining_rewards(self, reward_date: date = None) -> Dict:
        """
        处理每日挖矿奖励发放
        
        Args:
            reward_date: 奖励日期，默认为今天
            
        Returns:
            处理结果字典
        """
        if reward_date is None:
            reward_date = date.today()
        
        try:
            async with self.uow:
                # 获取需要发放奖励的矿工卡
                cards_needing_reward = await mining_card.get_cards_needing_reward(
                    self.uow.session,
                    reward_date=reward_date
                )
                
                if not cards_needing_reward:
                    return {
                        "success": True,
                        "message": "没有需要发放奖励的矿工卡",
                        "processed_cards": 0,
                        "total_rewards": 0
                    }
                
                processed_cards = 0
                total_rewards = 0
                
                for card in cards_needing_reward:
                    try:
                        # 计算奖励天数
                        if card.last_reward_time is None:
                            # 第一次发放奖励
                            reward_day = 1
                        else:
                            # 计算距离上次奖励的天数
                            days_diff = (reward_date - card.last_reward_time.date()).days
                            if days_diff == 0:
                                continue  # 今天已经发放过了
                            reward_day = card.total_days - card.remaining_days + 1
                        
                        # 创建奖励记录
                        await mining_reward.create_mining_reward(
                            session=self.uow.session,
                            mining_card_id=card.id,
                            telegram_id=card.telegram_id,
                            card_type=card.card_type,
                            reward_points=card.daily_points,
                            reward_day=reward_day,
                            reward_date=datetime.combine(reward_date, datetime.min.time()),
                            remarks=f"{card.card_type}矿工卡第{reward_day}天奖励"
                        )
                        
                        # 更新矿工卡状态
                        new_earned_points = card.earned_points + card.daily_points
                        new_remaining_days = card.remaining_days - 1
                        new_status = 2 if new_remaining_days == 0 else 1  # 如果剩余天数为0，标记为已完成
                        
                        await mining_card.update_card_reward(
                            session=self.uow.session,
                            card_id=card.id,
                            earned_points=new_earned_points,
                            remaining_days=new_remaining_days,
                            last_reward_time=datetime.combine(reward_date, datetime.min.time()),
                            status=new_status
                        )
                        
                        processed_cards += 1
                        total_rewards += card.daily_points
                        
                    except Exception as e:
                        logger.error(f"处理矿工卡 {card.id} 奖励失败: {e}")
                        continue
                
                await self.uow.commit()
                
                return {
                    "success": True,
                    "message": f"成功处理{processed_cards}张矿工卡的奖励发放，共{total_rewards:,}积分",
                    "processed_cards": processed_cards,
                    "total_rewards": total_rewards
                }
                
        except Exception as e:
            logger.error(f"处理每日挖矿奖励失败: {e}")
            await self.uow.rollback()
            return {
                "success": False,
                "message": "处理挖矿奖励失败",
                "processed_cards": 0,
                "total_rewards": 0
            }
    
    async def get_user_mining_cards(self, telegram_id: int, page: int = 1, limit: int = 10):
        """获取用户的矿工卡列表（分页）"""
        try:
            # 直接使用导入的mining_card实例，而不是通过self.uow访问
            
            # 计算偏移量
            offset = (page - 1) * limit
            
            # 获取用户矿工卡列表
            cards = await mining_card.get_user_cards(
                session=self.uow.session,
                telegram_id=telegram_id,
                limit=limit,
                offset=offset
            )
            
            # 获取总数
            total_count = await mining_card.get_user_cards_count(
                session=self.uow.session,
                telegram_id=telegram_id
            )
            
            # 计算总页数
            total_pages = (total_count + limit - 1) // limit
            
            return {
                "success": True,
                "cards": cards,
                "total_count": total_count,
                "current_page": page,
                "total_pages": total_pages,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"获取用户矿工卡列表失败: {e}")
            return {
                "success": False,
                "message": f"获取矿工卡列表失败: {e}",
                "cards": [],
                "total_count": 0,
                "current_page": page,
                "total_pages": 0,
                "limit": limit
            }
    
    async def get_pending_cards_count(self):
        """获取需要处理的矿工卡总数"""
        try:
            count = await mining_card.get_pending_cards_count(session=self.uow.session)
            return count
        except Exception as e:
            logger.error(f"获取待处理矿工卡数量失败: {e}")
            return 0
    
    async def process_daily_mining_rewards_batch(self, offset: int = 0, limit: int = 100):
        """批量处理每日挖矿奖励"""
        try:
            # 获取需要处理的矿工卡（分页）
            pending_cards = await mining_card.get_pending_cards_batch(
                session=self.uow.session,
                offset=offset,
                limit=limit
            )
            
            if not pending_cards:
                return {
                    "success": True,
                    "message": "没有需要处理的矿工卡",
                    "processed_cards": 0,
                    "total_rewards": 0
                }
            
            processed_cards = 0
            total_rewards = 0
            
            for card in pending_cards:
                try:
                    # 处理单张矿工卡
                    card_result = await self._process_single_card(card)
                    
                    if card_result["success"]:
                        processed_cards += 1
                        total_rewards += card_result["reward_points"]
                        
                        # 更新矿工卡状态
                        await mining_card.update_card_status(
                            session=self.uow.session,
                            card_id=card.id,
                            earned_points=card_result["reward_points"],
                            last_reward_time=datetime.now()
                        )
                    
                except Exception as e:
                    logger.error(f"处理矿工卡 {card.id} 失败: {e}")
                    continue
            
            return {
                "success": True,
                "message": f"批量处理完成，处理 {processed_cards} 张矿工卡",
                "processed_cards": processed_cards,
                "total_rewards": total_rewards
            }
            
        except Exception as e:
            logger.error(f"批量处理每日挖矿奖励失败: {e}")
            return {
                "success": False,
                "message": f"批量处理失败: {e}",
                "processed_cards": 0,
                "total_rewards": 0
            }
    
    async def _process_single_card(self, card):
        """处理单张矿工卡"""
        try:
            # 计算奖励积分
            reward_points = card.daily_points
            
            # 创建奖励记录
            reward_record = await mining_reward.create_mining_reward(
                session=self.uow.session,
                mining_card_id=card.id,
                telegram_id=card.telegram_id,
                card_type=card.card_type,
                reward_points=reward_points,
                reward_day=card.total_days - card.remaining_days + 1,
                reward_date=datetime.now(),
                remarks=f"{card.card_type}矿工卡第{card.total_days - card.remaining_days + 1}天奖励"
            )
            
            return {
                "success": True,
                "reward_points": reward_points,
                "reward_record": reward_record
            }
            
        except Exception as e:
            logger.error(f"处理单张矿工卡失败: {e}")
            return {
                "success": False,
                "reward_points": 0,
                "error": str(e)
            }
    
    async def get_mining_history(self, telegram_id: int, page: int = 1, limit: int = 10) -> Dict:
        """
        获取挖矿历史记录（分页）
        
        Args:
            telegram_id: Telegram用户ID
            page: 页码（从1开始）
            limit: 每页记录数
            
        Returns:
            挖矿历史记录字典
        """
        try:
            async with self.uow:
                # 计算偏移量
                offset = (page - 1) * limit
                
                # 获取挖矿奖励历史
                rewards = await mining_reward.get_reward_history(
                    self.uow.session,
                    telegram_id=telegram_id,
                    skip=offset,
                    limit=limit
                )
                
                # 获取总记录数
                total_count = await mining_reward.get_reward_history_count(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                # 计算总页数
                total_pages = (total_count + limit - 1) // limit
                
                # 获取挖矿统计信息
                stats = await mining_statistics.get_or_create_statistics(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                # 转换为字典格式
                rewards_list = []
                for reward in rewards:
                    rewards_list.append({
                        "id": reward.id,
                        "mining_card_id": reward.mining_card_id,
                        "card_type": reward.card_type,
                        "reward_points": reward.reward_points,
                        "reward_day": reward.reward_day,
                        "reward_date": reward.reward_date.strftime('%Y-%m-%d %H:%M:%S'),
                        "status": reward.status,
                        "claimed_time": reward.claimed_time.strftime('%Y-%m-%d %H:%M:%S') if reward.claimed_time else None,
                        "remarks": reward.remarks
                    })
                
                # 构建统计信息
                statistics = {
                    "total_cards_purchased": stats.total_cards_purchased,
                    "total_cost_usdt": float(stats.total_cost_usdt) / 10000,  # 转换为USDT显示
                    "total_earned_points": stats.total_earned_points,
                    "bronze_cards": stats.bronze_cards,
                    "silver_cards": stats.silver_cards,
                    "gold_cards": stats.gold_cards,
                    "diamond_cards": stats.diamond_cards,
                    "last_mining_time": stats.last_mining_time.strftime('%Y-%m-%d %H:%M:%S') if stats.last_mining_time else None
                }
                
                return {
                    "success": True,
                    "message": "",
                    "rewards": rewards_list,
                    "statistics": statistics,
                    "total_count": total_count,
                    "current_page": page,
                    "total_pages": max(1, total_pages)
                }
                
        except Exception as e:
            logger.error(f"获取挖矿历史记录失败: {e}")
            return {
                "success": False,
                "message": "获取历史记录失败，请稍后重试",
                "rewards": [],
                "statistics": {},
                "total_count": 0,
                "current_page": page,
                "total_pages": 1
            } 