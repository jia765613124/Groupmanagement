"""
挖矿调度器
处理每日挖矿奖励的定时任务
支持大量矿工卡的批量处理
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from bot.database.db import SessionFactory
from bot.common.uow import UoW
from bot.common.mining_service import MiningService

logger = logging.getLogger(__name__)

class MiningScheduler:
    """挖矿调度器"""
    
    def __init__(self):
        self.is_running = False
        self.task = None
        self.batch_size = 100  # 每批处理的矿工卡数量
        self.max_retries = 3   # 最大重试次数
        self.retry_delay = 60  # 重试延迟（秒）
    
    async def start(self):
        """启动挖矿调度器"""
        if self.is_running:
            logger.warning("挖矿调度器已经在运行中")
            return
        
        self.is_running = True
        logger.info("挖矿调度器已启动")
        
        # 启动定时任务
        self.task = asyncio.create_task(self._run_scheduler())
    
    async def stop(self):
        """停止挖矿调度器"""
        if not self.is_running:
            logger.warning("挖矿调度器未在运行")
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logger.info("挖矿调度器已停止")
    
    async def _run_scheduler(self):
        """运行调度器主循环"""
        while self.is_running:
            try:
                # 处理每日挖矿奖励
                await self._process_daily_rewards_batch()
                
                # 等待到下一个整点
                await self._wait_until_next_hour()
                
            except asyncio.CancelledError:
                logger.info("挖矿调度器被取消")
                break
            except Exception as e:
                logger.error(f"挖矿调度器运行错误: {e}")
                # 等待5分钟后重试
                await asyncio.sleep(300)
    
    async def _process_daily_rewards_batch(self):
        """批量处理每日挖矿奖励"""
        start_time = datetime.now()
        logger.info("开始批量处理每日挖矿奖励...")
        
        try:
            async with SessionFactory() as session:
                uow = UoW(session)
                mining_service = MiningService(uow)
                
                # 获取需要处理的矿工卡总数
                total_cards = await mining_service.get_pending_cards_count()
                logger.info(f"需要处理的矿工卡总数: {total_cards}张")
                
                if total_cards == 0:
                    logger.info("没有需要处理的矿工卡")
                    return
                
                # 分批处理
                processed_total = 0
                total_rewards = 0
                batch_count = 0
                
                for offset in range(0, total_cards, self.batch_size):
                    batch_count += 1
                    batch_start = datetime.now()
                    
                    logger.info(f"处理第 {batch_count} 批 (偏移量: {offset}, 大小: {self.batch_size})")
                    
                    # 处理当前批次
                    batch_result = await self._process_batch(
                        mining_service, 
                        offset, 
                        self.batch_size
                    )
                    
                    if batch_result["success"]:
                        processed_total += batch_result["processed_cards"]
                        total_rewards += batch_result["total_rewards"]
                        
                        batch_time = (datetime.now() - batch_start).total_seconds()
                        logger.info(f"第 {batch_count} 批处理完成: "
                                  f"处理 {batch_result['processed_cards']} 张卡, "
                                  f"发放 {batch_result['total_rewards']:,} 积分, "
                                  f"耗时 {batch_time:.2f} 秒")
                    else:
                        logger.error(f"第 {batch_count} 批处理失败: {batch_result['message']}")
                    
                    # 批次间短暂休息，避免数据库压力过大
                    await asyncio.sleep(1)
                
                # 处理完成统计
                total_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"批量处理完成: "
                          f"总共处理 {processed_total} 张矿工卡, "
                          f"发放 {total_rewards:,} 积分, "
                          f"总耗时 {total_time:.2f} 秒, "
                          f"平均每张卡 {total_time/processed_total:.3f} 秒")
                
        except Exception as e:
            logger.error(f"批量处理每日挖矿奖励失败: {e}")
    
    async def _process_batch(self, mining_service, offset: int, limit: int):
        """处理一批矿工卡"""
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # 处理指定批次的矿工卡
                result = await mining_service.process_daily_mining_rewards_batch(
                    offset=offset,
                    limit=limit
                )
                
                return result
                
            except Exception as e:
                retry_count += 1
                logger.warning(f"批次处理失败 (重试 {retry_count}/{self.max_retries}): {e}")
                
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"批次处理最终失败: {e}")
                    return {
                        "success": False,
                        "message": f"批次处理失败: {e}",
                        "processed_cards": 0,
                        "total_rewards": 0
                    }
    
    async def _wait_until_next_hour(self):
        """等待到下一个整点"""
        now = datetime.now()
        next_hour = now.replace(minute=0, second=0, microsecond=0)
        if next_hour <= now:
            next_hour = next_hour.replace(hour=next_hour.hour + 1)
        
        wait_seconds = (next_hour - now).total_seconds()
        logger.info(f"等待到下一个整点: {next_hour.strftime('%Y-%m-%d %H:%M:%S')} (等待{wait_seconds:.0f}秒)")
        
        await asyncio.sleep(wait_seconds)

# 全局调度器实例
_mining_scheduler = None

async def start_mining_scheduler():
    """启动挖矿调度器"""
    global _mining_scheduler
    if _mining_scheduler is None:
        _mining_scheduler = MiningScheduler()
    
    await _mining_scheduler.start()

async def stop_mining_scheduler():
    """停止挖矿调度器"""
    global _mining_scheduler
    if _mining_scheduler:
        await _mining_scheduler.stop()
        _mining_scheduler = None

async def process_mining_rewards_manual(reward_date: date = None, batch_size: int = 100):
    """手动处理挖矿奖励（用于测试或手动触发）"""
    start_time = datetime.now()
    logger.info("开始手动处理挖矿奖励...")
    
    try:
        async with SessionFactory() as session:
            uow = UoW(session)
            mining_service = MiningService(uow)
            
            # 获取需要处理的矿工卡总数
            total_cards = await mining_service.get_pending_cards_count()
            logger.info(f"需要处理的矿工卡总数: {total_cards}张")
            
            if total_cards == 0:
                logger.info("没有需要处理的矿工卡")
                return {
                    "success": True,
                    "message": "没有需要处理的矿工卡",
                    "processed_cards": 0,
                    "total_rewards": 0
                }
            
            # 分批处理
            processed_total = 0
            total_rewards = 0
            batch_count = 0
            
            for offset in range(0, total_cards, batch_size):
                batch_count += 1
                batch_start = datetime.now()
                
                logger.info(f"处理第 {batch_count} 批 (偏移量: {offset}, 大小: {batch_size})")
                
                # 处理当前批次
                batch_result = await mining_service.process_daily_mining_rewards_batch(
                    offset=offset,
                    limit=batch_size
                )
                
                if batch_result["success"]:
                    processed_total += batch_result["processed_cards"]
                    total_rewards += batch_result["total_rewards"]
                    
                    batch_time = (datetime.now() - batch_start).total_seconds()
                    logger.info(f"第 {batch_count} 批处理完成: "
                              f"处理 {batch_result['processed_cards']} 张卡, "
                              f"发放 {batch_result['total_rewards']:,} 积分, "
                              f"耗时 {batch_time:.2f} 秒")
                else:
                    logger.error(f"第 {batch_count} 批处理失败: {batch_result['message']}")
                
                # 批次间短暂休息
                await asyncio.sleep(1)
            
            # 处理完成统计
            total_time = (datetime.now() - start_time).total_seconds()
            result = {
                "success": True,
                "message": f"手动处理完成，总共处理 {processed_total} 张矿工卡，发放 {total_rewards:,} 积分",
                "processed_cards": processed_total,
                "total_rewards": total_rewards,
                "total_time": total_time
            }
            
            logger.info(f"手动处理完成: "
                      f"总共处理 {processed_total} 张矿工卡, "
                      f"发放 {total_rewards:,} 积分, "
                      f"总耗时 {total_time:.2f} 秒")
            
            return result
                
    except Exception as e:
        logger.error(f"手动处理挖矿奖励失败: {e}")
        return {
            "success": False,
            "message": f"处理失败: {e}",
            "processed_cards": 0,
            "total_rewards": 0
        }

# 使用示例
if __name__ == "__main__":
    async def main():
        """主函数"""
        print("挖矿调度器示例")
        print("="*40)
        
        # 启动调度器
        print("启动挖矿调度器...")
        await start_mining_scheduler()
        
        # 运行一段时间
        print("调度器运行中，按 Ctrl+C 停止...")
        try:
            await asyncio.sleep(3600)  # 运行1小时
        except KeyboardInterrupt:
            print("\n收到停止信号")
        
        # 停止调度器
        print("停止挖矿调度器...")
        await stop_mining_scheduler()
        
        print("调度器已停止")
    
    # 运行示例
    asyncio.run(main()) 