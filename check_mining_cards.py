import asyncio
from bot.database.db import SessionFactory
from bot.crud.mining import mining_card, mining_reward

async def check_user_mining_cards(telegram_id):
    print(f"检查用户 {telegram_id} 的矿工卡...")
    
    async with SessionFactory() as session:
        # 获取用户的所有矿工卡
        cards = await mining_card.get_by_telegram_id(session, telegram_id=telegram_id)
        print(f"用户拥有 {len(cards)} 张矿工卡:")
        
        for card in cards:
            status_text = "挖矿中" if card.status == 1 else "已完成" if card.status == 2 else "已过期"
            print(f"卡ID: {card.id}, 类型: {card.card_type}, 状态: {status_text}")
            print(f"  每日积分: {card.daily_points}, 剩余天数: {card.remaining_days}/{card.total_days}")
            print(f"  已获得积分: {card.earned_points}/{card.total_points}")
            print(f"  开始时间: {card.start_time}, 结束时间: {card.end_time}")
            print(f"  最后奖励时间: {card.last_reward_time}")
            print()
        
        # 获取用户的待领取奖励
        rewards = await mining_reward.get_pending_rewards(session, telegram_id=telegram_id)
        print(f"用户有 {len(rewards)} 个待领取奖励:")
        
        for reward in rewards:
            print(f"奖励ID: {reward.id}, 卡ID: {reward.mining_card_id}")
            print(f"  类型: {reward.card_type}, 积分: {reward.reward_points}")
            print(f"  第{reward.reward_day}天, 日期: {reward.reward_date}")
            print()

if __name__ == "__main__":
    # 替换为您的Telegram ID
    telegram_id = 6657123296  # 请替换为您的实际ID
    asyncio.run(check_user_mining_cards(telegram_id)) 