import asyncio
from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.mining_service import MiningService

async def claim_rewards():
    print("领取挖矿奖励...")
    
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        # 指定用户ID
        telegram_id = 6657123296  # 请替换为您的实际ID
        
        # 领取所有奖励
        result = await mining_service.claim_all_rewards(telegram_id)
        
        print(f"领取结果: {result['success']}, 消息: {result['message']}")
        
        if result['success']:
            print(f"成功领取 {len(result['claimed_rewards'])} 个奖励")
            print(f"总积分: {result['total_points']}")
            
            for i, reward in enumerate(result['claimed_rewards']):
                print(f"奖励 {i+1}: 类型: {reward['card_type']}, 积分: {reward['reward_points']}")

if __name__ == "__main__":
    asyncio.run(claim_rewards()) 