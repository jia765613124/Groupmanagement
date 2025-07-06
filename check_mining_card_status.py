import asyncio
from datetime import datetime, date
from bot.database.db import SessionFactory
from bot.crud.mining import mining_card

async def check_card_status():
    print("检查矿工卡状态...")
    
    async with SessionFactory() as session:
        # 获取最近创建的矿工卡
        cards = await mining_card.get_by_telegram_id(
            session=session,
            telegram_id=6657123296,  # 请替换为您的实际ID
            limit=5
        )
        
        print(f"找到 {len(cards)} 张矿工卡:")
        
        for card in cards:
            status_text = "挖矿中" if card.status == 1 else "已完成" if card.status == 2 else "已过期"
            print(f"卡ID: {card.id}, 类型: {card.card_type}, 状态: {status_text}")
            print(f"  每日积分: {card.daily_points}, 剩余天数: {card.remaining_days}/{card.total_days}")
            print(f"  已获得积分: {card.earned_points}/{card.total_points}")
            print(f"  开始时间: {card.start_time}")
            print(f"  结束时间: {card.end_time}")
            print(f"  最后奖励时间: {card.last_reward_time}")
            
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
            
            if not should_get_reward:
                if card.start_time.date() > today:
                    print(f"  原因: 矿工卡还未开始挖矿 (开始日期: {card.start_time.date()})")
                elif card.end_time.date() < today:
                    print(f"  原因: 矿工卡已结束挖矿 (结束日期: {card.end_time.date()})")
                elif card.last_reward_time and card.last_reward_time.date() >= today:
                    print(f"  原因: 今天已经获得过奖励 (最后奖励时间: {card.last_reward_time})")
                elif card.remaining_days <= 0:
                    print(f"  原因: 没有剩余天数")
                elif card.status != 1:
                    print(f"  原因: 矿工卡状态不是挖矿中")
            
            print()
        
        # 检查需要处理的矿工卡
        today = date.today()
        pending_cards = await mining_card.get_cards_needing_reward(
            session=session,
            reward_date=today
        )
        
        print(f"今天需要处理的矿工卡: {len(pending_cards)} 张")
        
        for card in pending_cards:
            print(f"卡ID: {card.id}, 类型: {card.card_type}, 用户ID: {card.telegram_id}")
            print(f"  剩余天数: {card.remaining_days}, 最后奖励时间: {card.last_reward_time}")

if __name__ == "__main__":
    asyncio.run(check_card_status()) 