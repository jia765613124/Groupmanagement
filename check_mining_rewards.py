import asyncio
from datetime import datetime, date
from bot.database.db import SessionFactory
from bot.crud.mining import mining_reward
from sqlalchemy import select
from bot.models.mining import MiningReward

async def check_mining_rewards():
    print("检查挖矿奖励...")
    
    async with SessionFactory() as session:
        # 查询所有奖励
        stmt = select(MiningReward)
        result = await session.execute(stmt)
        all_rewards = result.scalars().all()
        
        print(f"数据库中共有 {len(all_rewards)} 个奖励记录")
        
        for reward in all_rewards:
            status_text = "待领取" if reward.status == 1 else "已领取" if reward.status == 2 else "已取消"
            print(f"奖励ID: {reward.id}, 卡ID: {reward.mining_card_id}, 用户ID: {reward.telegram_id}")
            print(f"  类型: {reward.card_type}, 积分: {reward.reward_points}")
            print(f"  第{reward.reward_day}天, 日期: {reward.reward_date}")
            print(f"  状态: {status_text}")
            print(f"  领取时间: {reward.claimed_time}")
            print()
        
        # 查询特定用户的待领取奖励
        telegram_id = 6657123296  # 请替换为您的实际ID
        pending_rewards = await mining_reward.get_pending_rewards(
            session=session,
            telegram_id=telegram_id
        )
        
        print(f"用户 {telegram_id} 有 {len(pending_rewards)} 个待领取奖励:")
        
        for reward in pending_rewards:
            print(f"奖励ID: {reward.id}, 卡类型: {reward.card_type}, 积分: {reward.reward_points}")
            print(f"  第{reward.reward_day}天, 日期: {reward.reward_date}")
            print()
        
        # 计算总待领取积分
        total_points = await mining_reward.get_total_pending_points(
            session=session,
            telegram_id=telegram_id
        )
        
        print(f"用户 {telegram_id} 总待领取积分: {total_points}")

if __name__ == "__main__":
    asyncio.run(check_mining_rewards()) 