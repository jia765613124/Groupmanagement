"""
多群组定时开奖任务
支持不同群组不同开奖间隔的自动开奖
"""

import asyncio
import logging
from datetime import datetime, timedelta
from bot.common.lottery_service import LotteryService
from bot.common.uow import UoW
from bot.database.db import SessionFactory
from bot.config.multi_game_config import MultiGameConfig
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

class LotteryScheduler:
    """多群组开奖调度器"""
    
    def __init__(self):
        self.is_running = False
        self.lottery_service = None
        self.multi_config = MultiGameConfig()
        self.group_draw_times = {}  # 记录每个群组的上次开奖时间
    
    def _get_notification_group_ids(self) -> list:
        """获取需要发送通知的群组ID列表"""
        import os
        group_ids_str = os.getenv("LOTTERY_NOTIFICATION_GROUPS", "")
        if group_ids_str:
            return [int(gid.strip()) for gid in group_ids_str.split(",") if gid.strip()]
        return []
    
    async def _get_lottery_service(self):
        """获取开奖服务实例"""
        if self.lottery_service is None:
            async with SessionFactory() as session:
                uow = UoW(session)
                self.lottery_service = LotteryService(uow)
        return self.lottery_service
    
    async def _send_draw_result(self, group_id: int, draw_result: dict):
        """发送开奖结果到指定群组"""
        try:
            from bot.misc import bot
            
            group_config = self.multi_config.get_group_config(group_id)
            if not group_config:
                logger.error(f"群组 {group_id} 未配置")
                return
            
            # 格式化开奖消息
            message = self._format_draw_message(group_id, draw_result)
            
            # 发送到群组及其通知群组
            notification_groups = group_config.notification_groups or [group_id]
            for target_group_id in notification_groups:
                try:
                    await bot.send_message(target_group_id, message, parse_mode="HTML")
                    logger.info(f"开奖结果已发送到群组 {target_group_id}")
                except Exception as e:
                    logger.error(f"发送开奖结果到群组 {target_group_id} 失败: {e}")
                    
        except Exception as e:
            logger.error(f"发送开奖结果失败: {e}")
    
    def _format_draw_message(self, group_id: int, draw_result: dict) -> str:
        """格式化开奖消息"""
        draw = draw_result["draw"]
        result = draw_result["result"]
        total_bets = draw_result["total_bets"]
        total_payout = draw_result["total_payout"]
        
        group_config = self.multi_config.get_group_config(group_id)
        game_config = self.multi_config.get_game_config(draw.game_type)
        
        message = f"🎲 <b>第 {draw.draw_number} 期开奖结果</b> 🎲\n\n"
        message += f"🏆 <b>开奖号码: {result}</b>\n\n"
        
        # 添加大小单双信息（简化版）
        if result in [1, 2, 3, 4]:
            message += "📊 <b>大小单双:</b> 小"
        elif result in [6, 7, 8, 9]:
            message += "📊 <b>大小单双:</b> 大"
        else:
            message += "📊 <b>大小单双:</b> 豹子"
        
        if result in [1, 3, 7, 9]:
            message += " 单"
        elif result in [2, 4, 6, 8]:
            message += " 双"
        else:
            message += " 豹子"
        
        message += f"\n\n📈 <b>本期统计:</b>\n"
        message += f"   总投注: {total_bets:,} 积分\n"
        message += f"   总派奖: {total_payout:,} 积分\n"
        
        # 计算盈亏
        profit = draw.profit  # 直接使用数据库中保存的盈亏值
        if profit > 0:
            message += f"   💰 盈利: +{profit:,} 积分"
        else:
            message += f"   💸 亏损: {profit:,} 积分"
        
        message += f"\n\n🎯 <b>下期投注即将开始...</b>"
        
        return message
    
    async def _send_new_draw_message(self, group_id: int, draw):
        """发送新一期开始投注消息（不显示按钮）"""
        try:
            logger.info(f"开始发送新一期开始投注消息，群组: {group_id}, 期号: {draw.draw_number}")
            from bot.misc import bot
            group_config = self.multi_config.get_group_config(group_id)
            if not group_config:
                logger.error(f"群组 {group_id} 未配置")
                return
            
            logger.info(f"群组配置获取成功: {group_config.group_name}, 游戏类型: {group_config.game_type}")
            
            # 获取开奖间隔
            game_config = self.multi_config.get_game_config(draw.game_type)
            interval = game_config.draw_interval if game_config else 5
            logger.info(f"游戏配置获取成功，开奖间隔: {interval}分钟")
            
            # 消息内容 - 不显示按钮，只提示用户通过消息投注
            message = (
                f"🎲 <b>第 {draw.draw_number} 期开始投注</b>\n\n"
                f"⏰ <b>投注时间:</b> {interval}分钟\n"
                f"💰 <b>投注方式:</b> 发送消息投注积分\n\n"
                f"📊 <b>投注类型与赔率:</b>\n"
                f"🔸 <b>大小单双:</b>\n"
                f"   小(1,2,3,4) 大(6,7,8,9) 单(1,3,7,9) 双(2,4,6,8) - 1.8倍\n\n"
                f"🔸 <b>组合投注:</b>\n"
                f"   小单(1,3) 小双(2,4) 大单(7,9) 大双(6,8) 豹子(0,5) - 3倍\n\n"
                f"🔸 <b>数字投注:</b>\n"
                f"   0-9任意数字 - 6倍\n\n"
                f"📝 <b>投注格式:</b>\n"
                f"• 大1000 小500 单200\n"
                f"• 小单100 大双200 豹子50\n"
                f"• 数字8 押100\n\n"
                f"💡 <b>示例:</b> 大1000 小单100 数字8 押100\n\n"
                f"🎯 <b>开奖时间:</b> {interval}分钟后"
            )
            logger.info(f"消息内容构建完成，长度: {len(message)} 字符")
            
            notification_groups = group_config.notification_groups or [group_id]
            logger.info(f"通知群组列表: {notification_groups}")
            
            for target_group_id in notification_groups:
                try:
                    logger.info(f"正在发送消息到群组 {target_group_id}...")
                    await bot.send_message(target_group_id, message, parse_mode="HTML")
                    logger.info(f"✅ 新一期开始投注消息已成功发送到群组 {target_group_id}")
                except Exception as e:
                    logger.error(f"❌ 发送新一期消息到群组 {target_group_id} 失败: {e}")
                    logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
        except Exception as e:
            logger.error(f"❌ 发送新一期开始投注消息失败: {e}")
            logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
    
    async def _create_new_draw(self, group_id: int):
        """为指定群组创建新的开奖期"""
        try:
            logger.info(f"开始为群组 {group_id} 创建新开奖期...")
            lottery_service = await self._get_lottery_service()
            group_config = self.multi_config.get_group_config(group_id)
            game_type = group_config.game_type if group_config else "lottery"
            logger.info(f"群组配置: {group_config.group_name if group_config else 'None'}, 游戏类型: {game_type}")
            
            # 新增：检查当前是否已有未开奖的期
            logger.info(f"检查群组 {group_id} 是否有未开奖期...")
            from bot.crud.lottery import lottery_draw as lottery_draw_crud
            current_draw = await lottery_draw_crud.get_current_draw(lottery_service.uow.session, group_id, game_type)
            if current_draw:
                logger.info(f"⚠️ 群组 {group_id} 已有未开奖期: {current_draw.draw_number}，状态: {current_draw.status}，不重复创建")
                return
            
            logger.info(f"群组 {group_id} 没有未开奖期，开始创建新期...")
            result = await lottery_service.create_new_draw(group_id, game_type)
            if result["success"]:
                logger.info(f"✅ 群组 {group_id} 创建新开奖期成功: {result['draw'].draw_number}")
                # 新增：发送新一期已开启消息和投注按钮
                logger.info(f"开始发送新一期已开启消息...")
                await self._send_new_draw_message(group_id, result['draw'])
            else:
                logger.error(f"❌ 群组 {group_id} 创建新开奖期失败: {result['message']}")
        except Exception as e:
            logger.error(f"❌ 群组 {group_id} 创建新开奖期异常: {e}")
            logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
    
    async def _draw_lottery(self, group_id: int):
        """为指定群组执行开奖"""
        try:
            logger.info(f"开始为群组 {group_id} 执行开奖...")
            
            # 添加重试逻辑
            max_retries = 3
            retry_count = 0
            
            while retry_count <= max_retries:
                try:
                    # 获取开奖服务
                    lottery_service = await self._get_lottery_service()
                    # 执行开奖
                    result = await lottery_service.draw_lottery(group_id=group_id)
                    
                    if result["success"]:
                        logger.info(f"✅ 群组 {group_id} 开奖完成: 结果={result['result']}, 总投注={result['total_bets']}, 总派奖={result['total_payout']}")
                        
                        # 发送开奖结果到群组
                        logger.info(f"开始发送开奖结果到群组 {group_id}...")
                        await self._send_draw_result(group_id, result)
                        
                        # 创建新的开奖期
                        logger.info(f"开始为群组 {group_id} 创建新开奖期...")
                        await self._create_new_draw(group_id)
                    else:
                        logger.error(f"❌ 群组 {group_id} 开奖失败: {result['message']}")
                    
                    # 成功执行，跳出循环
                    break
                    
                except Exception as e:
                    retry_count += 1
                    if "Lost connection" in str(e) and retry_count <= max_retries:
                        logger.warning(f"数据库连接丢失，正在进行第 {retry_count} 次重试（共 {max_retries} 次）...")
                        await asyncio.sleep(2 * retry_count)  # 延迟时间随重试次数增加
                    else:
                        if retry_count > max_retries:
                            logger.error(f"❌ 群组 {group_id} 开奖失败，已达到最大重试次数: {e}")
                        else:
                            logger.error(f"❌ 群组 {group_id} 开奖失败，非连接问题: {e}")
                        break
                
        except Exception as e:
            logger.error(f"❌ 群组 {group_id} 开奖异常: {e}")
            logger.error(f"错误详情: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"堆栈跟踪: {traceback.format_exc()}")
    
    async def _cleanup_expired_cashback(self):
        """清理过期的返水记录"""
        try:
            from bot.crud.lottery import lottery_bet
            
            async with SessionFactory() as session:
                expired_bets = await lottery_bet.get_expired_cashback(session)
                
                if expired_bets:
                    for bet in expired_bets:
                        await lottery_bet.update(
                            session=session,
                            db_obj=bet,
                            obj_in={"cashback_claimed": True, "remarks": "返水已过期"}
                        )
                    
                    logger.info(f"清理了 {len(expired_bets)} 条过期返水记录")
                    
        except Exception as e:
            logger.error(f"清理过期返水失败: {e}")
    
    def _should_draw_now(self, group_id: int) -> bool:
        """检查指定群组是否应该现在开奖"""
        group_config = self.multi_config.get_group_config(group_id)
        if not group_config or not group_config.auto_draw:
            logger.debug(f"群组 {group_id} 未配置或自动开奖已禁用")
            return False
        
        game_config = self.multi_config.get_game_config(group_config.game_type)
        if not game_config:
            logger.debug(f"群组 {group_id} 游戏类型 {group_config.game_type} 未配置")
            return False
        
        now = datetime.now()
        interval_minutes = game_config.draw_interval
        
        # 检查是否到了开奖时间
        should_draw = now.minute % interval_minutes == 0 and now.second < 10
        
        # 检查是否已经开过奖（避免重复开奖）
        last_draw_time = self.group_draw_times.get(group_id)
        if last_draw_time and (now - last_draw_time).total_seconds() < 60:
            logger.debug(f"群组 {group_id} 距离上次开奖时间过短，跳过")
            return False
        
        if should_draw:
            logger.info(f"🎯 群组 {group_id} 应该开奖: 当前时间={now.strftime('%H:%M:%S')}, 间隔={interval_minutes}分钟")
        
        return should_draw
    
    async def _check_and_draw(self):
        """检查所有群组并执行开奖"""
        enabled_groups = self.multi_config.get_enabled_groups()
        logger.debug(f"检查开奖: 当前启用的群组数量: {len(enabled_groups)}")
        
        for group_config in enabled_groups:
            logger.debug(f"检查群组 {group_config.group_id} ({group_config.group_name}) 是否需要开奖...")
            if self._should_draw_now(group_config.group_id):
                logger.info(f"🚀 群组 {group_config.group_id} ({group_config.group_name}) 开始执行定时开奖...")
                await self._draw_lottery(group_config.group_id)
                self.group_draw_times[group_config.group_id] = datetime.now()
                logger.info(f"✅ 群组 {group_config.group_id} 开奖完成，记录开奖时间")
            else:
                logger.debug(f"群组 {group_config.group_id} 暂不需要开奖")
    
    async def start(self):
        """启动多群组开奖调度器"""
        if self.is_running:
            logger.warning("⚠️ 开奖调度器已在运行")
            return
        
        self.is_running = True
        logger.info("🚀 多群组开奖调度器已启动")
        
        # 启动时为所有启用的群组创建第一个开奖期
        enabled_groups = self.multi_config.get_enabled_groups()
        logger.info(f"📋 启动时初始化: 找到 {len(enabled_groups)} 个启用的群组")
        for group_config in enabled_groups:
            logger.info(f"初始化群组: {group_config.group_id} ({group_config.group_name})")
            await self._create_new_draw(group_config.group_id)
        
        try:
            while self.is_running:
                try:
                    # 检查是否需要开奖
                    await self._check_and_draw()
                    
                    # 每小时清理一次过期返水
                    if datetime.now().minute == 0 and datetime.now().second < 10:
                        await self._cleanup_expired_cashback()
                    
                    # 等待1秒
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"开奖调度器循环异常: {e}")
                    await asyncio.sleep(5)  # 异常时等待5秒
                    
        except asyncio.CancelledError:
            logger.info("开奖调度器被取消")
        except Exception as e:
            logger.error(f"开奖调度器异常: {e}")
        finally:
            self.is_running = False
            logger.info("开奖调度器已停止")
    
    async def stop(self):
        """停止开奖调度器"""
        self.is_running = False
        logger.info("正在停止开奖调度器...")

# 全局调度器实例
lottery_scheduler = LotteryScheduler()

async def start_lottery_scheduler():
    """启动开奖调度器"""
    await lottery_scheduler.start()

async def stop_lottery_scheduler():
    """停止开奖调度器"""
    await lottery_scheduler.stop()

# 手动开奖函数（用于测试或手动触发）
async def manual_draw(group_id: int = None):
    """手动开奖"""
    try:
        lottery_service = None
        async with SessionFactory() as session:
            uow = UoW(session)
            lottery_service = LotteryService(uow)
        
        if group_id:
            # 为指定群组开奖
            result = await lottery_service.draw_lottery(group_id=group_id)
            if result["success"]:
                logger.info(f"群组 {group_id} 手动开奖成功: {result['result']}")
                await lottery_scheduler._send_draw_result(group_id, result)
                await lottery_scheduler._create_new_draw(group_id)
            else:
                logger.error(f"群组 {group_id} 手动开奖失败: {result['message']}")
            return result
        else:
            # 为所有启用的群组开奖
            enabled_groups = lottery_scheduler.multi_config.get_enabled_groups()
            results = []
            for group_config in enabled_groups:
                result = await lottery_service.draw_lottery(group_id=group_config.group_id)
                if result["success"]:
                    logger.info(f"群组 {group_config.group_id} 手动开奖成功: {result['result']}")
                    await lottery_scheduler._send_draw_result(group_config.group_id, result)
                    await lottery_scheduler._create_new_draw(group_config.group_id)
                else:
                    logger.error(f"群组 {group_config.group_id} 手动开奖失败: {result['message']}")
                results.append(result)
            return results
            
    except Exception as e:
        logger.error(f"手动开奖异常: {e}")
        return {"success": False, "message": f"开奖异常: {e}"} 