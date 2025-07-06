import asyncio
from datetime import datetime, date
from bot.database.db import SessionFactory
from bot.crud.mining import mining_card
from sqlalchemy import select, update
from bot.models.mining import MiningCard

async def fix_mining_cards():
    print("修复矿工卡问题...")
    
    async with SessionFactory() as session:
        # 检查数据库中的矿工卡
        stmt = select(MiningCard)
        result = await session.execute(stmt)
        all_cards = result.scalars().all()
        
        print(f"数据库中共有 {len(all_cards)} 张矿工卡")
        
        for card in all_cards:
            print(f"卡ID: {card.id}, 类型: {card.card_type}, 用户ID: {card.telegram_id}")
            print(f"  状态: {card.status}, 剩余天数: {card.remaining_days}/{card.total_days}")
            print(f"  开始时间: {card.start_time}, 结束时间: {card.end_time}")
            print(f"  最后奖励时间: {card.last_reward_time}")
            print(f"  is_deleted: {card.is_deleted}")
            
            # 检查是否应该获得奖励
            today = date.today()
            should_get_reward = (
                card.status == 1 and
                card.remaining_days > 0 and
                card.start_time.date() <= today and
                card.end_time.date() >= today and
                (card.last_reward_time is None or card.last_reward_time.date() < today)
            )
            
            print(f"  今天应该获得奖励: {should_get_reward}")
            
            if should_get_reward and card.is_deleted:
                print(f"  需要修复: 卡ID {card.id} 应该获得奖励但被标记为已删除")
                # 修复is_deleted字段
                card.is_deleted = False
                await session.commit()
                print(f"  已修复: 卡ID {card.id} is_deleted 已设置为 False")
            
            print()
        
        # 再次检查需要处理的矿工卡
        today = date.today()
        pending_cards = await mining_card.get_pending_cards_batch(
            session=session,
            offset=0,
            limit=100
        )
        
        print(f"修复后，今天需要处理的矿工卡: {len(pending_cards)} 张")
        
        for card in pending_cards:
            print(f"卡ID: {card.id}, 类型: {card.card_type}, 用户ID: {card.telegram_id}")
            print(f"  剩余天数: {card.remaining_days}, 最后奖励时间: {card.last_reward_time}")
            print()

if __name__ == "__main__":
    asyncio.run(fix_mining_cards()) 