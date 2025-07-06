import asyncio
from datetime import date
from bot.database.db import SessionFactory
from bot.crud.mining import mining_card, mining_reward
from bot.common.uow import UoW
from bot.common.mining_service import MiningService

async def check_mining_status():
    print("检查挖矿系统状态...")
    
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        # 检查待处理的矿工卡
        pending_count = await mining_service.get_pending_cards_count()
        print(f"待处理矿工卡数量: {pending_count}")
        
        # 获取一些待处理的矿工卡
        cards = await mining_card.get_pending_cards_batch(session, 0, 5)
        print(f"获取到 {len(cards)} 张待处理矿工卡:")
        
        telegram_ids = set()
        for card in cards:
            telegram_ids.add(card.telegram_id)
            print(f"卡ID: {card.id}, 用户ID: {card.telegram_id}, 类型: {card.card_type}, "
                 f"剩余天数: {card.remaining_days}, 最后奖励时间: {card.last_reward_time}")
        
        # 检查奖励
        for telegram_id in telegram_ids:
            rewards = await mining_reward.get_pending_rewards(session, telegram_id=telegram_id)
            print(f"用户 {telegram_id} 待领取奖励数量: {len(rewards)}")
            
            for reward in rewards:
                print(f"奖励ID: {reward.id}, 卡ID: {reward.mining_card_id}, "
                     f"积分: {reward.reward_points}, 第{reward.reward_day}天, "
                     f"日期: {reward.reward_date}")
        
        # 尝试手动处理一下奖励
        print("\n尝试手动处理奖励...")
        result = await mining_service.process_daily_mining_rewards_batch(offset=0, limit=10)
        print(f"处理结果: {result}")

if __name__ == "__main__":
    asyncio.run(check_mining_status()) 