import asyncio
from datetime import datetime
from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.mining_service import MiningService
from bot.tasks.mining_scheduler import process_mining_rewards_manual

async def process_rewards():
    print("开始手动处理挖矿奖励...")
    start_time = datetime.now()
    
    # 使用挖矿调度器的手动处理函数
    result = await process_mining_rewards_manual()
    
    print(f"处理结果: {result}")
    print(f"总耗时: {(datetime.now() - start_time).total_seconds():.2f}秒")
    
    # 检查处理后的用户奖励
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        # 查询一个用户的待领取奖励（使用我们刚才创建矿工卡的用户ID）
        telegram_id = 6657123296  # 请替换为您的实际ID
        rewards_result = await mining_service.get_pending_rewards(telegram_id)
        
        print(f"\n用户 {telegram_id} 的待领取奖励:")
        print(f"总数: {rewards_result['total_count']}")
        print(f"总积分: {rewards_result['total_points']}")
        
        for reward in rewards_result['rewards']:
            print(f"奖励ID: {reward['id']}, 卡类型: {reward['card_type']}")
            print(f"  积分: {reward['reward_points']}, 第{reward['reward_day']}天")
            print(f"  日期: {reward['reward_date']}")

if __name__ == "__main__":
    asyncio.run(process_rewards()) 