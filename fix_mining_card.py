"""
修复矿工卡日期问题
将矿工卡的结束时间和剩余天数同步更新为正确值
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import update, select
from sqlalchemy.sql import text
from bot.database.db import SessionFactory
from bot.models.mining import MiningCard

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def fix_mining_card_dates():
    """修复矿工卡日期计算错误"""
    logger.info("开始修复矿工卡日期问题...")
    
    async with SessionFactory() as session:
        # 获取所有状态为"挖矿中"的矿工卡 (status=1)
        stmt = select(MiningCard).where(MiningCard.status == 1)
        result = await session.execute(stmt)
        active_cards = result.scalars().all()
        
        logger.info(f"找到 {len(active_cards)} 张状态为挖矿中的矿工卡")
        
        fixed_count = 0
        for card in active_cards:
            logger.info(f"检查卡ID: {card.id}, 类型: {card.card_type}")
            logger.info(f"  开始时间: {card.start_time}")
            logger.info(f"  结束时间: {card.end_time}")
            logger.info(f"  总天数: {card.total_days}, 剩余天数: {card.remaining_days}")
            
            # 检查是否使用了远期日期（2025年）
            is_future_date = False
            if card.start_time.year >= 2025:
                is_future_date = True
                logger.warning(f"  发现异常未来日期: {card.start_time}，将修正")
            
            # 如果是未来日期，重置为当前时间
            if is_future_date:
                # 保存原始总天数和剩余天数的比例
                remaining_ratio = card.remaining_days / card.total_days if card.total_days > 0 else 0
                
                # 重置开始时间为当前时间
                card.start_time = datetime.now()
                
                # 重新计算结束时间
                card.end_time = card.start_time + timedelta(days=card.total_days)
                
                # 如果有剩余天数比例，按比例重置剩余天数
                if remaining_ratio > 0:
                    card.remaining_days = int(card.total_days * remaining_ratio)
                
                logger.info(f"  已重置时间 - 开始: {card.start_time}, 结束: {card.end_time}, 剩余天数: {card.remaining_days}")
                fixed_count += 1
                continue
            
            # 计算正确的结束时间：应该是开始时间加上总天数
            correct_end_time = card.start_time + timedelta(days=card.total_days)
            
            # 计算正确的剩余天数：应该是结束时间减去现在的天数
            days_remaining = max(0, (card.end_time - datetime.now()).days)
            
            # 如果日期不正确，进行修复
            if abs((correct_end_time - card.end_time).total_seconds()) > 3600 or card.remaining_days != days_remaining:
                logger.info(f"  需要修复:")
                logger.info(f"  原结束时间: {card.end_time} -> 修正为: {correct_end_time}")
                logger.info(f"  原剩余天数: {card.remaining_days} -> 修正为: {days_remaining}")
                
                # 直接更新对象
                card.end_time = correct_end_time
                card.remaining_days = days_remaining
                
                fixed_count += 1
        
        # 提交所有更改
        await session.commit()
        
        logger.info(f"完成修复! 共修复 {fixed_count} 张矿工卡")

if __name__ == "__main__":
    asyncio.run(fix_mining_card_dates()) 