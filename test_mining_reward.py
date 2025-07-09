"""
测试矿工卡奖励发放
模拟三天的奖励发放过程，验证剩余天数和结束时间是否正确同步
"""

import asyncio
import logging
from datetime import datetime, timedelta, date
from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.mining_service import MiningService
from bot.models.mining import MiningCard
from bot.crud.mining import mining_card, mining_reward

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试用户ID
TEST_USER_ID = 123456789
# 测试卡类型
TEST_CARD_TYPE = "白银"

async def create_test_mining_card():
    """创建测试用的矿工卡"""
    logger.info("创建测试矿工卡...")
    
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        # 获取现有的测试卡片
        existing_cards = await mining_card.get_user_cards(
            session=session,
            telegram_id=TEST_USER_ID,
            offset=0,
            limit=10
        )
        
        # 如果已有测试卡片，不需要再创建
        for card in existing_cards:
            if card['card_type'] == TEST_CARD_TYPE and card['status'] == 1:
                logger.info(f"已找到测试矿工卡: ID={card['id']}, 类型={card['card_type']}, 剩余天数={card['remaining_days']}")
                return card['id']
        
        # 没有找到测试卡片，创建一张新的
        logger.info(f"为测试用户 {TEST_USER_ID} 创建一张 {TEST_CARD_TYPE} 矿工卡")
        
        # 创建矿工卡记录
        now = datetime.now()
        duration_days = 3  # 三天有效期
        start_time = now
        end_time = start_time + timedelta(days=duration_days)
        
        # 日志记录创建的日期
        logger.info(f"创建矿工卡 - 开始时间: {start_time}, 结束时间: {end_time}, 持续天数: {duration_days}")
        
        # 创建测试矿工卡
        card = await mining_card.create_test_card(
            session=session,
            telegram_id=TEST_USER_ID,
            card_type=TEST_CARD_TYPE,
            cost_usdt=50000000,  # 假设成本是50 USDT
            daily_points=10000,  # 每日10000积分
            total_days=duration_days,
            start_time=start_time,
            end_time=end_time,
            remarks="测试卡"
        )
        
        await session.commit()
        logger.info(f"成功创建测试矿工卡: ID={card.id}")
        return card.id

async def simulate_reward_days(card_id: int, days: int):
    """模拟多天的奖励发放"""
    logger.info(f"准备模拟 {days} 天的奖励发放...")
    
    # 获取初始矿工卡状态
    async with SessionFactory() as session:
        card = await mining_card.get(session, card_id)
        if not card:
            logger.error(f"找不到ID为 {card_id} 的矿工卡")
            return
            
        # 记录初始状态
        logger.info(f"初始状态: 卡ID={card.id}, 剩余天数={card.remaining_days}, 结束时间={card.end_time}, 已获得积分={card.earned_points}")
        logger.info(f"详细信息: 开始时间={card.start_time}, 总天数={card.total_days}, 每日积分={card.daily_points}")
        
        # 检查初始状态是否一致
        expected_end_time = card.start_time + timedelta(days=card.remaining_days)
        if expected_end_time != card.end_time:
            logger.warning(f"初始状态不一致! 基于剩余天数计算的结束时间: {expected_end_time}, 实际结束时间: {card.end_time}")
    
    # 模拟每天发放奖励
    for i in range(days):
        # 使用当前日期作为处理日期，但年份设置为2025年以匹配测试数据
        current_date = datetime.now().replace(year=2025)
        # 反转日期顺序，使第1天是最早的日期，第N天是最晚的日期
        process_date = current_date - timedelta(days=(days-1-i))
        date_str = process_date.strftime('%Y-%m-%d')
        
        logger.info(f"-- 第 {i+1} 天 ({date_str}) --")
        
        # 在每次循环中使用新的会话，避免会话过期问题
        async with SessionFactory() as session:
            # 重新获取最新的矿工卡状态
            card = await mining_card.get(session, card_id)
            if not card:
                logger.error(f"找不到ID为 {card_id} 的矿工卡")
                continue
                
            logger.info(f"处理前: 开始时间={card.start_time}, 剩余天数={card.remaining_days}, 结束时间={card.end_time}")
            
            # 创建服务实例
            uow = UoW(session)
            mining_service = MiningService(uow)
            
            # 处理当天的挖矿奖励
            result = await mining_service.process_daily_mining_rewards(process_date)
            logger.info(f"奖励处理结果: {result}")
            
            # 重新获取更新后的矿工卡状态
            card = await mining_card.get(session, card_id)
            if card:
                logger.info(f"处理后: 开始时间={card.start_time}, 剩余天数={card.remaining_days}, 结束时间={card.end_time}, 已获得积分={card.earned_points}")
                
                # 检查更新后的状态是否一致
                expected_end_time = card.start_time + timedelta(days=card.remaining_days)
                if expected_end_time != card.end_time:
                    logger.warning(f"更新后状态不一致! 基于剩余天数计算的结束时间: {expected_end_time}, 实际结束时间: {card.end_time}")
            else:
                logger.warning(f"处理后找不到ID为 {card_id} 的矿工卡")
            
            # 获取该卡的奖励记录
            rewards = await mining_reward.get_card_rewards(session, card_id=card_id)
            logger.info(f"当前奖励记录数: {len(rewards)}")
            for reward in rewards:
                logger.info(f"奖励记录: ID={reward.id}, 积分={reward.reward_points}, 时间={reward.created_at}")
                
        # 等待一小段时间，避免处理太快
        await asyncio.sleep(0.5)

async def verify_rewards(card_id: int):
    """
    验证所有奖励是否正确记录
    
    Args:
        card_id: 矿工卡ID
    """
    async with SessionFactory() as session:
        # 获取卡片
        card = await mining_card.get(session, card_id)
        
        # 获取所有相关奖励记录
        rewards = await mining_reward.get_card_rewards(session, card_id=card_id)
        
        logger.info(f"卡片 {card_id} 的奖励记录:")
        for reward in rewards:
            logger.info(f"第 {reward.reward_day} 天 - 日期: {reward.reward_date} - 积分: {reward.reward_points} - 状态: {reward.status}")
        
        # 验证奖励天数是否符合卡片总天数
        total_days = card.total_days
        if len(rewards) != total_days:
            logger.error(f"奖励记录数量 ({len(rewards)}) 与卡片总天数 ({total_days}) 不一致!")
        else:
            logger.info(f"奖励记录数量 ({len(rewards)}) 与卡片总天数一致")
        
        # 验证奖励天数是否连续
        days_set = {r.reward_day for r in rewards}
        expected_days = set(range(1, total_days + 1))
        if days_set != expected_days:
            logger.error(f"奖励天数不连续! 实际: {sorted(days_set)}, 期望: {sorted(expected_days)}")
        else:
            logger.info("奖励天数连续性检查通过")
        
        # 验证总积分是否正确
        total_reward_points = sum(r.reward_points for r in rewards)
        if total_reward_points != card.earned_points:
            logger.error(f"总积分不一致! 奖励记录总和: {total_reward_points}, 卡片记录: {card.earned_points}")
        else:
            logger.info(f"总积分一致性检查通过: {total_reward_points}")

async def test_single_card():
    """测试单张卡片的奖励发放"""
    logger.info("=== 开始测试单张矿工卡奖励发放 ===")
    
    try:
        # 1. 创建测试矿工卡
        card_id = await create_test_mining_card()
        
        # 2. 模拟三天奖励发放
        await simulate_reward_days(card_id, days=3)
        
        # 3. 验证所有奖励记录
        await verify_rewards(card_id)
        
        logger.info("单张卡片测试完成!")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def main():
    """主测试函数"""
    logger.info("=== 开始测试矿工卡奖励发放 ===")
    
    try:
        # 测试单张卡片
        await test_single_card()
        
        logger.info("测试完成!")
        
    except Exception as e:
        logger.error(f"测试过程中出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 