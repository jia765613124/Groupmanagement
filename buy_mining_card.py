import asyncio
from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.mining_service import MiningService
from bot.crud.account import account as account_crud
from bot.models.account import Account

async def buy_mining_card(telegram_id, card_type):
    print(f"为用户 {telegram_id} 购买 {card_type} 矿工卡...")
    
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        # 先检查钱包余额
        wallet_account = await account_crud.get_by_telegram_id_and_type(
            session, telegram_id=telegram_id, account_type=2  # 钱包账户
        )
        
        if wallet_account:
            print(f"钱包余额: {wallet_account.available_amount / 1000000:.2f}U")
        else:
            print("钱包账户不存在，将创建账户")
            # 创建钱包账户
            wallet_account = await account_crud.create(
                session=session,
                obj_in={
                    "telegram_id": telegram_id,
                    "account_type": 2,  # 钱包账户
                    "total_amount": 10000000,  # 10U
                    "available_amount": 10000000,
                    "frozen_amount": 0,
                    "status": 1,  # 正常
                    "remarks": "测试账户"
                }
            )
            print(f"已创建钱包账户，余额: {wallet_account.available_amount / 1000000:.2f}U")
        
        # 检查积分账户
        points_account = await account_crud.get_by_telegram_id_and_type(
            session, telegram_id=telegram_id, account_type=1  # 积分账户
        )
        
        if not points_account:
            print("积分账户不存在，将创建账户")
            # 创建积分账户
            points_account = await account_crud.create(
                session=session,
                obj_in={
                    "telegram_id": telegram_id,
                    "account_type": 1,  # 积分账户
                    "total_amount": 0,
                    "available_amount": 0,
                    "frozen_amount": 0,
                    "status": 1,  # 正常
                    "remarks": "测试账户"
                }
            )
            print("已创建积分账户")
        
        # 检查是否可以购买
        can_purchase, message = await mining_service.can_purchase_mining_card(
            telegram_id=telegram_id,
            card_type=card_type
        )
        
        print(f"可以购买: {can_purchase}, 消息: {message}")
        
        if can_purchase:
            # 执行购买
            result = await mining_service.purchase_mining_card(
                telegram_id=telegram_id,
                card_type=card_type
            )
            
            print(f"购买结果: {result['success']}, 消息: {result['message']}")
            
            if result['success']:
                print(f"购买成功! 矿工卡ID: {result['mining_card']['id']}")
                print(f"矿工卡类型: {result['mining_card']['name']}")
                print(f"每日积分: {result['mining_card']['daily_points']}")
                print(f"持续天数: {result['mining_card']['total_days']}")
                print(f"开始时间: {result['mining_card']['start_time']}")
                print(f"结束时间: {result['mining_card']['end_time']}")
        else:
            print(f"无法购买矿工卡: {message}")

if __name__ == "__main__":
    # 替换为您的Telegram ID
    telegram_id = 6657123296  # 请替换为您的实际ID
    card_type = "青铜"  # 青铜、白银、黄金、钻石
    asyncio.run(buy_mining_card(telegram_id, card_type)) 