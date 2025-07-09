"""
挖矿系统CRUD操作
包含矿工卡和挖矿奖励的数据访问层
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from decimal import Decimal
import logging

from bot.crud.base import CRUDBase
from bot.models.mining import MiningCard, MiningReward, MiningStatistics

logger = logging.getLogger(__name__)

class CRUDMiningCard(CRUDBase[MiningCard]):
    async def create_mining_card(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        card_type: str,
        cost_usdt: Decimal,
        daily_points: int,
        total_days: int,
        start_time: datetime,
        end_time: datetime,
        remarks: Optional[str] = None
    ) -> MiningCard:
        """创建矿工卡记录"""
        mining_card_data = {
            "telegram_id": telegram_id,
            "card_type": card_type,
            "cost_usdt": cost_usdt,
            "daily_points": daily_points,
            "total_days": total_days,
            "remaining_days": total_days,
            "total_points": daily_points * total_days,
            "earned_points": 0,
            "status": 1,  # 挖矿中
            "start_time": start_time,
            "end_time": end_time,
            "last_reward_time": None,
            "remarks": remarks
        }
        return await super().create(session=session, obj_in=mining_card_data)

    async def create_test_card(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        card_type: str,
        cost_usdt: int,
        daily_points: int,
        total_days: int,
        start_time: datetime,
        end_time: datetime,
        remarks: str = ""
    ) -> MiningCard:
        """创建测试用矿工卡"""
        card_data = {
            "telegram_id": telegram_id,
            "card_type": card_type,
            "cost_usdt": cost_usdt,
            "daily_points": daily_points,
            "total_days": total_days,
            "remaining_days": total_days,
            "earned_points": 0,
            "status": 1,  # 1=有效
            "start_time": start_time,
            "end_time": end_time,
            "last_reward_time": None,
            "remarks": remarks
        }
        
        card = MiningCard(**card_data)
        session.add(card)
        await session.flush()
        return card

    async def get_by_telegram_id(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        status: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MiningCard]:
        """获取用户的矿工卡记录"""
        conditions = [MiningCard.telegram_id == telegram_id]
        if status is not None:
            conditions.append(MiningCard.status == status)
        
        stmt = select(MiningCard).where(*conditions).order_by(
            MiningCard.created_at.desc()
        ).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_active_cards_by_type(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        card_type: str
    ) -> List[MiningCard]:
        """获取用户指定类型的活跃矿工卡"""
        stmt = select(MiningCard).where(
            MiningCard.telegram_id == telegram_id,
            MiningCard.card_type == card_type,
            MiningCard.status == 1  # 挖矿中
        ).order_by(MiningCard.created_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_active_cards_count_by_type(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        card_type: str
    ) -> int:
        """获取用户指定类型的活跃矿工卡数量"""
        stmt = select(func.count(MiningCard.id)).where(
            MiningCard.telegram_id == telegram_id,
            MiningCard.card_type == card_type,
            MiningCard.status == 1  # 挖矿中
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    async def get_cards_needing_reward(
        self,
        session: AsyncSession,
        *,
        reward_date: date
    ) -> List[MiningCard]:
        """获取需要发放奖励的矿工卡"""
        stmt = select(MiningCard).where(
            and_(
                MiningCard.status == 1,  # 挖矿中
                MiningCard.remaining_days > 0,  # 还有剩余天数
                func.date(MiningCard.start_time) <= reward_date,  # 已开始（使用func.date转换为日期）
                func.date(MiningCard.end_time) >= reward_date,  # 未结束（使用func.date转换为日期）
                or_(
                    MiningCard.last_reward_time.is_(None),  # 从未发放过奖励
                    func.date(MiningCard.last_reward_time) < reward_date  # 上次奖励日期早于今天
                ),
                MiningCard.is_deleted == False  # 确保未被删除
            )
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_cards_needing_reward_batch(self, session: AsyncSession, reward_date: date, offset: int = 0, limit: int = 100) -> List[MiningCard]:
        """
        批量获取需要发放奖励的矿工卡
        
        Args:
            session: 数据库会话
            reward_date: 奖励日期
            offset: 偏移量
            limit: 限制数量
            
        Returns:
            需要发放奖励的矿工卡列表
        """
        from sqlalchemy import func, or_
        
        try:
            stmt = (
                select(MiningCard)
                .where(
                    MiningCard.status == 1,  # 挖矿中
                    MiningCard.remaining_days > 0,  # 还有剩余天数
                    func.date(MiningCard.start_time) <= reward_date,  # 已开始
                    func.date(MiningCard.end_time) >= reward_date,  # 未结束
                    or_(
                        MiningCard.last_reward_time.is_(None),  # 从未发放过奖励
                        func.date(MiningCard.last_reward_time) < reward_date  # 上次奖励日期早于今天
                    )
                )
                .order_by(MiningCard.id)
                .offset(offset)
                .limit(limit)
            )
            
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"批量获取需要发放奖励的矿工卡失败: {e}")
            return []

    async def update_card_reward(
        self,
        session: AsyncSession,
        *,
        card_id: int,
        earned_points: int,
        remaining_days: int,
        last_reward_time: datetime,
        status: Optional[int] = None
    ) -> MiningCard:
        """更新矿工卡奖励信息"""
        update_data = {
            "remaining_days": remaining_days,
            "earned_points": earned_points,
            "last_reward_time": last_reward_time
        }
        
        if status is not None:
            update_data["status"] = status
            
        card = await self.update(
            session=session,
            db_obj=await self.get(session, card_id),
            obj_in=update_data,
            exclude_fields=["start_time"]  # 排除start_time字段，确保它不会被更新
        )
        return card
    
    async def update_card_reward_with_end_time(
        self,
        session: AsyncSession,
        *,
        card_id: int,
        earned_points: int,
        remaining_days: int,
        end_time: datetime,
        last_reward_time: datetime,
        status: Optional[int] = None
    ) -> MiningCard:
        """更新矿工卡奖励信息（包括结束时间）"""
        update_data = {
            "remaining_days": remaining_days,
            "earned_points": earned_points,
            "end_time": end_time,
            "last_reward_time": last_reward_time
        }
        
        if status is not None:
            update_data["status"] = status
            
        card = await self.update(
            session=session,
            db_obj=await self.get(session, card_id),
            obj_in=update_data,
            exclude_fields=["start_time"]  # 排除start_time字段，确保它不会被更新
        )
        return card

    async def update_card_dates(
        self,
        session: AsyncSession,
        *,
        card_id: int,
        end_time: datetime,
        remaining_days: int
    ) -> MiningCard:
        """专门用于更新矿工卡的结束时间和剩余天数"""
        update_data = {
            "end_time": end_time,
            "remaining_days": remaining_days
        }
        
        # 获取矿工卡对象
        db_obj = await self.get(session, card_id)
        if not db_obj:
            raise ValueError(f"找不到ID为{card_id}的矿工卡")
            
        return await super().update(
            session=session,
            db_obj=db_obj,
            obj_in=update_data
        )

    async def get_active_cards(
        self,
        session: AsyncSession
    ) -> List[MiningCard]:
        """获取所有状态为挖矿中的矿工卡"""
        stmt = select(MiningCard).where(
            MiningCard.status == 1,  # 挖矿中
            MiningCard.is_deleted == False
        )
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update_last_reward_time(
        self,
        session: AsyncSession,
        *,
        card_id: int,
        last_reward_time: datetime
    ) -> MiningCard:
        """更新矿工卡的最后奖励时间"""
        update_data = {
            "last_reward_time": last_reward_time
        }
        
        # 获取矿工卡对象
        db_obj = await self.get(session, card_id)
        if not db_obj:
            raise ValueError(f"找不到ID为{card_id}的矿工卡")
            
        return await super().update(
            session=session,
            db_obj=db_obj,
            obj_in=update_data
        )

    async def get_user_mining_summary(
        self,
        session: AsyncSession,
        *,
        telegram_id: int
    ) -> Dict[str, Any]:
        """获取用户挖矿汇总信息"""
        # 统计各类型矿工卡数量
        stmt = select(
            MiningCard.card_type,
            func.count(MiningCard.id).label('count'),
            func.sum(MiningCard.total_points).label('total_points'),
            func.sum(MiningCard.earned_points).label('earned_points')
        ).where(
            MiningCard.telegram_id == telegram_id
        ).group_by(MiningCard.card_type)
        
        result = await session.execute(stmt)
        summary = {}
        
        for row in result:
            summary[row.card_type] = {
                "count": row.count,
                "total_points": row.total_points or 0,
                "earned_points": row.earned_points or 0
            }
        
        return summary

    async def get_user_cards(self, session, telegram_id: int, limit: int = 10, offset: int = 0):
        """获取用户的矿工卡列表（分页）"""
        try:
            query = select(self.model).where(
                self.model.telegram_id == telegram_id,
                self.model.is_deleted == False
            ).order_by(
                self.model.created_at.desc()
            ).limit(limit).offset(offset)
            
            result = await session.execute(query)
            cards = result.scalars().all()
            
            # 转换为字典格式
            cards_list = []
            for card in cards:
                cards_list.append({
                    "id": card.id,
                    "telegram_id": card.telegram_id,
                    "card_type": card.card_type,
                    "cost_usdt": card.cost_usdt,
                    "daily_points": card.daily_points,
                    "total_days": card.total_days,
                    "remaining_days": card.remaining_days,
                    "total_points": card.total_points,
                    "earned_points": card.earned_points,
                    "status": card.status,
                    "start_time": card.start_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "end_time": card.end_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "last_reward_time": card.last_reward_time.strftime('%Y-%m-%d %H:%M:%S') if card.last_reward_time else None,
                    "remarks": card.remarks
                })
            
            return cards_list
            
        except Exception as e:
            logger.error(f"获取用户矿工卡列表失败: {e}")
            return []
    
    async def get_user_cards_count(self, session, telegram_id: int):
        """获取用户的矿工卡总数"""
        try:
            query = select(func.count(self.model.id)).where(
                self.model.telegram_id == telegram_id,
                self.model.is_deleted == False
            )
            
            result = await session.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"获取用户矿工卡总数失败: {e}")
            return 0

    async def get_pending_cards_count(self, session):
        """获取需要处理的矿工卡数量"""
        try:
            today = date.today()
            query = select(func.count(self.model.id)).where(
                self.model.status == 1,  # 挖矿中
                self.model.remaining_days > 0,  # 还有剩余天数
                func.date(self.model.start_time) <= today,  # 已经开始（使用func.date转换为日期）
                func.date(self.model.end_time) >= today,  # 还未结束（使用func.date转换为日期）
                or_(
                    self.model.last_reward_time.is_(None),
                    func.date(self.model.last_reward_time) < today
                ),  # 今天还没发奖励
                self.model.is_deleted == False
            )
            
            result = await session.execute(query)
            count = result.scalar()
            
            return count or 0
            
        except Exception as e:
            logger.error(f"获取待处理矿工卡数量失败: {e}")
            return 0
    
    async def get_pending_cards_batch(self, session, offset: int = 0, limit: int = 100):
        """获取需要处理的矿工卡批次"""
        try:
            today = date.today()
            query = select(self.model).where(
                self.model.status == 1,  # 挖矿中
                self.model.remaining_days > 0,  # 还有剩余天数
                func.date(self.model.start_time) <= today,  # 已经开始（使用func.date转换为日期）
                func.date(self.model.end_time) >= today,  # 还未结束（使用func.date转换为日期）
                or_(
                    self.model.last_reward_time.is_(None),
                    func.date(self.model.last_reward_time) < today
                ),  # 今天还没发奖励
                self.model.is_deleted == False
            ).order_by(
                self.model.created_at.asc()  # 按创建时间升序，先处理早的
            ).limit(limit).offset(offset)
            
            result = await session.execute(query)
            cards = result.scalars().all()
            
            return cards
            
        except Exception as e:
            logger.error(f"获取待处理矿工卡批次失败: {e}")
            return []
    
    async def update_card_status(self, session, card_id: int, earned_points: int, last_reward_time: datetime):
        """更新矿工卡状态"""
        try:
            # 获取矿工卡
            card = await self.get(session, card_id)
            if not card:
                return False
            
            # 更新已获得积分
            card.earned_points += earned_points
            
            # 更新最后奖励时间
            card.last_reward_time = last_reward_time
            
            # 减少剩余天数
            card.remaining_days -= 1
            
            # 更新结束时间，与剩余天数保持同步
            if card.remaining_days > 0:
                card.end_time = datetime.now() + timedelta(days=card.remaining_days)
            
            # 如果剩余天数为0，标记为已完成
            if card.remaining_days <= 0:
                card.status = 2  # 已完成
                card.remaining_days = 0
                card.end_time = datetime.now()  # 结束时间设为当前时间
            
            # 保存更新
            await session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"更新矿工卡状态失败: {e}")
            await session.rollback()
            return False


class CRUDMiningReward(CRUDBase[MiningReward]):
    async def create_mining_reward(
        self,
        session: AsyncSession,
        *,
        mining_card_id: int,
        telegram_id: int,
        card_type: str,
        reward_points: int,
        reward_day: int,
        reward_date: datetime,
        remarks: Optional[str] = None
    ) -> MiningReward:
        """创建挖矿奖励记录"""
        reward_data = {
            "mining_card_id": mining_card_id,
            "telegram_id": telegram_id,
            "card_type": card_type,
            "reward_points": reward_points,
            "reward_day": reward_day,
            "reward_date": reward_date,
            "status": 1,  # 待领取
            "claimed_time": None,
            "remarks": remarks
        }
        return await super().create(session=session, obj_in=reward_data)

    async def create_reward(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        card_id: int,
        card_type: str,
        reward_points: int,
        reward_day: int,
        reward_date: date,
        remarks: Optional[str] = None
    ) -> MiningReward:
        """创建挖矿奖励记录（新版方法）"""
        reward_data = {
            "mining_card_id": card_id,
            "telegram_id": telegram_id,
            "card_type": card_type,
            "reward_points": reward_points,
            "reward_day": reward_day,
            "reward_date": datetime.combine(reward_date, datetime.min.time()),
            "status": 1,  # 待领取
            "claimed_time": None,
            "remarks": remarks
        }
        return await super().create(session=session, obj_in=reward_data)

    async def get_pending_rewards(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[MiningReward]:
        """获取待领取的挖矿奖励"""
        stmt = select(MiningReward).where(
            MiningReward.telegram_id == telegram_id,
            MiningReward.status == 1  # 待领取
        ).order_by(MiningReward.reward_date.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_pending_rewards_count(
        self,
        session: AsyncSession,
        *,
        telegram_id: int
    ) -> int:
        """获取待领取的挖矿奖励数量"""
        stmt = select(func.count(MiningReward.id)).where(
            MiningReward.telegram_id == telegram_id,
            MiningReward.status == 1  # 待领取
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    async def get_total_pending_points(
        self,
        session: AsyncSession,
        *,
        telegram_id: int
    ) -> int:
        """获取待领取的总积分"""
        stmt = select(func.sum(MiningReward.reward_points)).where(
            MiningReward.telegram_id == telegram_id,
            MiningReward.status == 1  # 待领取
        )
        result = await session.execute(stmt)
        return result.scalar() or 0

    async def claim_rewards(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        reward_ids: List[int]
    ) -> List[MiningReward]:
        """领取挖矿奖励"""
        stmt = select(MiningReward).where(
            MiningReward.id.in_(reward_ids),
            MiningReward.telegram_id == telegram_id,
            MiningReward.status == 1  # 待领取
        )
        result = await session.execute(stmt)
        rewards = result.scalars().all()
        
        # 更新奖励状态为已领取
        for reward in rewards:
            reward.status = 2  # 已领取
            reward.claimed_time = datetime.now()
        
        await session.commit()
        return rewards

    async def get_reward_history(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[MiningReward]:
        """获取挖矿奖励历史"""
        stmt = select(MiningReward).where(
            MiningReward.telegram_id == telegram_id
        ).order_by(MiningReward.reward_date.desc()).offset(skip).limit(limit)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_reward_history_count(
        self,
        session: AsyncSession,
        *,
        telegram_id: int
    ) -> int:
        """获取挖矿奖励历史总数"""
        stmt = select(func.count(MiningReward.id)).where(
            MiningReward.telegram_id == telegram_id
        )
        result = await session.execute(stmt)
        return result.scalar() or 0


class CRUDMiningStatistics(CRUDBase[MiningStatistics]):
    async def get_or_create_statistics(
        self,
        session: AsyncSession,
        *,
        telegram_id: int
    ) -> MiningStatistics:
        """获取或创建用户挖矿统计"""
        stmt = select(MiningStatistics).where(
            MiningStatistics.telegram_id == telegram_id
        )
        result = await session.execute(stmt)
        stats = result.scalar_one_or_none()
        
        if not stats:
            stats_data = {
                "telegram_id": telegram_id,
                "total_cards_purchased": 0,
                "total_cost_usdt": Decimal('0'),
                "total_earned_points": 0,
                "bronze_cards": 0,
                "silver_cards": 0,
                "gold_cards": 0,
                "diamond_cards": 0,
                "last_mining_time": None
            }
            stats = await super().create(session=session, obj_in=stats_data)
        
        return stats

    async def update_statistics(
        self,
        session: AsyncSession,
        *,
        telegram_id: int,
        card_type: str,
        cost_usdt: Decimal,
        earned_points: int
    ) -> MiningStatistics:
        """更新挖矿统计"""
        stats = await self.get_or_create_statistics(session, telegram_id=telegram_id)
        
        # 更新统计信息
        stats.total_cards_purchased += 1
        stats.total_cost_usdt += cost_usdt
        stats.total_earned_points += earned_points
        stats.last_mining_time = datetime.now()
        
        # 更新对应类型的矿工卡数量
        if card_type == "青铜":
            stats.bronze_cards += 1
        elif card_type == "白银":
            stats.silver_cards += 1
        elif card_type == "黄金":
            stats.gold_cards += 1
        elif card_type == "钻石":
            stats.diamond_cards += 1
        
        await session.commit()
        return stats


# 创建CRUD实例
mining_card = CRUDMiningCard(MiningCard)
mining_reward = CRUDMiningReward(MiningReward)
mining_statistics = CRUDMiningStatistics(MiningStatistics) 