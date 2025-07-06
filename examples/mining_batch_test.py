"""
挖矿批量处理测试脚本
测试大量矿工卡的批量处理性能
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入项目模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.mining_service import MiningService
from bot.tasks.mining_scheduler import process_mining_rewards_manual
from bot.crud.mining import mining_card, mining_reward, mining_statistics
from bot.crud.account import account as account_crud
from bot.crud.account_transaction import account_transaction as transaction_crud

async def create_test_cards(telegram_id: int, num_cards: int = 100):
    """创建测试矿工卡"""
    logger.info(f"开始创建 {num_cards} 张测试矿工卡...")
    
    card_types = ["Bronze", "Silver", "Gold", "Diamond"]
    card_configs = {
        "Bronze": {"cost_usdt": 1000, "daily_points": 10, "total_days": 30},
        "Silver": {"cost_usdt": 5000, "daily_points": 50, "total_days": 30},
        "Gold": {"cost_usdt": 10000, "daily_points": 100, "total_days": 30},
        "Diamond": {"cost_usdt": 50000, "daily_points": 500, "total_days": 30}
    }
    
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        created_count = 0
        for i in range(num_cards):
            try:
                # 随机选择卡类型
                card_type = random.choice(card_types)
                config = card_configs[card_type]
                
                # 随机设置开始时间（过去30天内）
                days_ago = random.randint(0, 30)
                start_time = date.today() - timedelta(days=days_ago)
                end_time = start_time + timedelta(days=config["total_days"])
                
                # 创建矿工卡记录
                mining_card_record = await mining_card.create_mining_card(
                    session=session,
                    telegram_id=telegram_id,
                    card_type=card_type,
                    cost_usdt=config["cost_usdt"],
                    daily_points=config["daily_points"],
                    total_days=config["total_days"],
                    start_time=start_time,
                    end_time=end_time,
                    remarks=f"测试卡 #{i+1}"
                )
                
                created_count += 1
                if created_count % 10 == 0:
                    logger.info(f"已创建 {created_count} 张矿工卡...")
                
            except Exception as e:
                logger.error(f"创建矿工卡失败: {e}")
                continue
        
        await session.commit()
        logger.info(f"测试矿工卡创建完成，成功创建 {created_count} 张")
        return created_count

async def test_batch_processing():
    """测试批量处理功能"""
    logger.info("开始测试批量处理功能...")
    
    # 测试用户ID
    test_telegram_id = 123456789
    
    # 1. 创建测试数据
    await create_test_cards(test_telegram_id, 100)
    
    # 2. 测试不同批次大小的处理性能
    batch_sizes = [50, 100, 200, 500]
    
    for batch_size in batch_sizes:
        logger.info(f"\n测试批次大小: {batch_size}")
        logger.info("=" * 50)
        
        start_time = datetime.now()
        
        # 执行批量处理
        result = await process_mining_rewards_manual(
            reward_date=date.today(),
            batch_size=batch_size
        )
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        if result["success"]:
            logger.info(f"批次大小 {batch_size} 处理结果:")
            logger.info(f"  处理矿工卡: {result['processed_cards']} 张")
            logger.info(f"  发放积分: {result['total_rewards']:,}")
            logger.info(f"  总耗时: {total_time:.2f} 秒")
            if result['processed_cards'] > 0:
                avg_time = total_time / result['processed_cards']
                logger.info(f"  平均每张卡: {avg_time:.3f} 秒")
        else:
            logger.error(f"批次大小 {batch_size} 处理失败: {result['message']}")
        
        # 等待一下再进行下一轮测试
        await asyncio.sleep(2)

async def test_scheduler_performance():
    """测试调度器性能"""
    logger.info("\n开始测试调度器性能...")
    logger.info("=" * 50)
    
    # 模拟调度器的批量处理
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        
        # 获取待处理卡数量
        total_cards = await mining_service.get_pending_cards_count()
        logger.info(f"待处理矿工卡总数: {total_cards}张")
        
        if total_cards == 0:
            logger.info("没有待处理的矿工卡")
            return
        
        # 模拟调度器处理
        start_time = datetime.now()
        batch_size = 100
        
        processed_total = 0
        total_rewards = 0
        batch_count = 0
        
        for offset in range(0, total_cards, batch_size):
            batch_count += 1
            batch_start = datetime.now()
            
            # 处理当前批次
            batch_result = await mining_service.process_daily_mining_rewards_batch(
                offset=offset,
                limit=batch_size
            )
            
            if batch_result["success"]:
                processed_total += batch_result["processed_cards"]
                total_rewards += batch_result["total_rewards"]
                
                batch_time = (datetime.now() - batch_start).total_seconds()
                logger.info(f"批次 {batch_count}: "
                          f"处理 {batch_result['processed_cards']} 张卡, "
                          f"发放 {batch_result['total_rewards']:,} 积分, "
                          f"耗时 {batch_time:.2f} 秒")
            else:
                logger.error(f"批次 {batch_count} 失败: {batch_result['message']}")
            
            # 批次间休息
            await asyncio.sleep(1)
        
        # 总统计
        total_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"\n调度器性能测试完成:")
        logger.info(f"  总处理卡数: {processed_total} 张")
        logger.info(f"  总发放积分: {total_rewards:,}")
        logger.info(f"  总耗时: {total_time:.2f} 秒")
        if processed_total > 0:
            avg_time = total_time / processed_total
            logger.info(f"  平均每张卡: {avg_time:.3f} 秒")

async def main():
    """主函数"""
    logger.info("挖矿批量处理性能测试")
    logger.info("=" * 60)
    
    try:
        # 测试批量处理
        await test_batch_processing()
        
        # 测试调度器性能
        await test_scheduler_performance()
        
        logger.info("\n所有测试完成！")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 