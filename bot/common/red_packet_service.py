"""
红包服务类
处理钓鱼成功后的红包发放和抢红包逻辑
"""

from typing import Dict, List, Optional, Tuple
import random
import logging
import time
import asyncio
from bot.crud.account import account as account_crud
from bot.crud.account_transaction import account_transaction as transaction_crud
from bot.common.uow import UoW
from bot.database.db import SessionFactory

logger = logging.getLogger(__name__)

class RedPacketService:
    """红包服务类"""
    
    # 红包相关交易类型常量
    TRANSACTION_TYPE_RED_PACKET_SEND = 50  # 发送红包
    TRANSACTION_TYPE_RED_PACKET_RECEIVE = 51  # 抢到红包
    
    # 账户类型常量
    ACCOUNT_TYPE_POINTS = 1  # 积分账户
    
    # 红包过期时间（秒）
    RED_PACKET_EXPIRE_TIME = 300  # 5分钟
    
    # 全局红包缓存
    # 格式: {red_packet_id: {amount, total_num, remaining_num, remaining_amount, participants, created_at, message_id, chat_id}}
    _red_packets = {}
    
    def __init__(self, uow: UoW):
        self.uow = uow
    
    async def create_red_packet(self, telegram_id: int, amount: int, chat_id: int, message_id: int = 0) -> Dict:
        """
        创建红包
        
        Args:
            telegram_id: 发红包用户的Telegram ID
            amount: 红包总金额
            chat_id: 群组ID
            message_id: 消息ID
            
        Returns:
            红包信息字典
        """
        try:
            # 检查用户积分是否足够
            async with self.uow:
                account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    self.ACCOUNT_TYPE_POINTS
                )
                
                if not account:
                    return {
                        "success": False,
                        "message": "积分账户不存在",
                        "red_packet_id": None
                    }
                
                if account.status != 1:
                    return {
                        "success": False,
                        "message": "账户已被冻结，无法发红包",
                        "red_packet_id": None
                    }
                
                if account.available_amount < amount:
                    return {
                        "success": False,
                        "message": f"积分不足，需要{amount}积分，当前只有{account.available_amount}积分",
                        "red_packet_id": None
                    }
                
                # 计算红包个数：每10000积分1个红包，最少1个，最多20个
                total_num = max(1, min(20, amount // 10000))
                
                # 生成红包ID
                red_packet_id = f"rp_{telegram_id}_{int(time.time())}"
                
                # 扣除用户积分
                account.available_amount -= amount
                account.total_amount -= amount
                await account_crud.update(
                    session=self.uow.session,
                    db_obj=account,
                    obj_in={"available_amount": account.available_amount, "total_amount": account.total_amount}
                )
                
                # 记录发红包交易
                await transaction_crud.create(
                    session=self.uow.session,
                    account_id=account.id,
                    telegram_id=telegram_id,
                    account_type=self.ACCOUNT_TYPE_POINTS,
                    transaction_type=self.TRANSACTION_TYPE_RED_PACKET_SEND,
                    amount=-amount,
                    balance=account.available_amount,
                    remarks=f"发放钓鱼红包 {amount} 积分"
                )
                
                # 创建红包
                self._red_packets[red_packet_id] = {
                    "amount": amount,
                    "total_num": total_num,
                    "remaining_num": total_num,
                    "remaining_amount": amount,
                    "participants": [],
                    "created_at": time.time(),
                    "message_id": message_id,
                    "chat_id": chat_id,
                    "sender_id": telegram_id,
                    "sender_name": account.remarks or f"用户{telegram_id}"
                }
                
                await self.uow.commit()
                
                # 设置红包过期任务
                asyncio.create_task(self._expire_red_packet(red_packet_id))
                
                return {
                    "success": True,
                    "message": "红包创建成功",
                    "red_packet_id": red_packet_id,
                    "total_num": total_num,
                    "amount": amount
                }
                
        except Exception as e:
            logger.error(f"创建红包失败: {e}")
            await self.uow.rollback()
            return {
                "success": False,
                "message": "创建红包失败，请稍后重试",
                "red_packet_id": None
            }
    
    async def grab_red_packet(self, telegram_id: int, red_packet_id: str, user_name: str = "") -> Dict:
        """
        抢红包 - 检查用户是否有积分账户并更新用户积分，但不记录交易
        
        Args:
            telegram_id: 抢红包用户的Telegram ID
            red_packet_id: 红包ID
            user_name: 用户名
            
        Returns:
            抢红包结果字典
        """
        try:
            # 检查红包是否存在
            if red_packet_id not in self._red_packets:
                return {
                    "success": False,
                    "message": "红包不存在或已过期",
                    "amount": 0
                }
            
            red_packet = self._red_packets[red_packet_id]
            
            # 检查红包是否已被抢光
            if red_packet["remaining_num"] <= 0:
                return {
                    "success": False,
                    "message": "红包已被抢光",
                    "amount": 0
                }
            
            # 检查用户是否已经抢过
            if telegram_id in [p["telegram_id"] for p in red_packet["participants"]]:
                return {
                    "success": False,
                    "message": "你已经抢过这个红包了",
                    "amount": 0
                }
            
            # 检查是否是自己发的红包
            if telegram_id == red_packet["sender_id"] and red_packet["sender_id"] != 0:
                return {
                    "success": False,
                    "message": "不能抢自己发的红包",
                    "amount": 0
                }
            
            # 检查用户是否有积分账户
            from bot.crud.account import account as account_crud
            account = await account_crud.get_by_telegram_id_and_type(
                session=self.uow.session,
                telegram_id=telegram_id,
                account_type=self.ACCOUNT_TYPE_POINTS
            )
            
            if not account:
                return {
                    "success": False,
                    "message": "你没有积分账户，无法抢红包",
                    "amount": 0
                }
            
            # 计算抢到的金额
            grabbed_amount = self._calculate_red_packet_amount(
                remaining_amount=red_packet["remaining_amount"],
                remaining_num=red_packet["remaining_num"]
            )
            
            # 更新红包信息
            red_packet["remaining_num"] -= 1
            red_packet["remaining_amount"] -= grabbed_amount
            red_packet["participants"].append({
                "telegram_id": telegram_id,
                "name": user_name or f"用户{telegram_id}",
                "amount": grabbed_amount,
                "time": time.time()
            })
            
            # 更新用户积分账户
            account.available_amount += grabbed_amount
            account.total_amount += grabbed_amount
            
            await account_crud.update(
                session=self.uow.session,
                db_obj=account,
                obj_in={"available_amount": account.available_amount, "total_amount": account.total_amount}
            )
            
            # 日志记录
            logger.info(f"用户 {user_name or telegram_id} 抢到红包 {red_packet_id}，金额: {grabbed_amount} 积分")
            
            # 提交事务
            await self.uow.commit()
            
            # 获取红包状态
            is_last = red_packet["remaining_num"] == 0
            
            return {
                "success": True,
                "message": "抢红包成功",
                "amount": grabbed_amount,
                "is_last": is_last,
                "sender_name": red_packet["sender_name"],
                "total_amount": red_packet["amount"],
                "total_num": red_packet["total_num"]
            }
                
        except Exception as e:
            logger.error(f"抢红包失败: {e}")
            return {
                "success": False,
                "message": "抢红包失败，请稍后重试",
                "amount": 0
            }
    
    def get_red_packet_info(self, red_packet_id: str) -> Dict:
        """
        获取红包信息
        
        Args:
            red_packet_id: 红包ID
            
        Returns:
            红包信息字典
        """
        if red_packet_id not in self._red_packets:
            return {
                "success": False,
                "message": "红包不存在或已过期",
                "info": None
            }
        
        red_packet = self._red_packets[red_packet_id]
        
        # 获取手气最佳
        best_grabber = None
        if red_packet["participants"]:
            # 按照抢到金额排序，获取手气最佳
            best_grabber = max(red_packet["participants"], key=lambda x: x["amount"])
            
            # 按照抢红包时间排序参与者列表
            sorted_participants = sorted(red_packet["participants"], key=lambda x: x["time"])
        else:
            sorted_participants = []
        
        return {
            "success": True,
            "message": "获取红包信息成功",
            "info": {
                "sender_name": red_packet["sender_name"],
                "sender_id": red_packet["sender_id"],
                "amount": red_packet["amount"],
                "total_num": red_packet["total_num"],
                "remaining_num": red_packet["remaining_num"],
                "remaining_amount": red_packet["remaining_amount"],
                "participants": sorted_participants,
                "best_grabber": best_grabber,
                "created_at": red_packet["created_at"],
                "message_id": red_packet["message_id"],
                "chat_id": red_packet["chat_id"]
            }
        }
    
    def _calculate_red_packet_amount(self, remaining_amount: int, remaining_num: int) -> int:
        """计算红包金额（使用微信红包算法）"""
        if remaining_num == 1:
            return remaining_amount
        
        # 最小金额为1积分
        min_amount = 1
        # 最大金额为剩余平均值的2倍
        max_amount = min(remaining_amount - min_amount * (remaining_num - 1), int(remaining_amount * 2 / remaining_num))
        
        # 随机计算
        amount = random.randint(min_amount, max(min_amount, max_amount))
        
        return amount
    
    async def _expire_red_packet(self, red_packet_id: str):
        """红包过期处理"""
        await asyncio.sleep(self.RED_PACKET_EXPIRE_TIME)
        
        if red_packet_id in self._red_packets:
            red_packet = self._red_packets[red_packet_id]
            
            # 如果还有剩余金额，且不是系统发放的红包，退回给发送者
            if red_packet["remaining_amount"] > 0 and red_packet["sender_id"] != 0:
                try:
                    async with SessionFactory() as session:
                        uow = UoW(session)
                        
                        # 获取发送者账户
                        account = await account_crud.get_by_telegram_id_and_type(
                            uow.session, 
                            red_packet["sender_id"], 
                            self.ACCOUNT_TYPE_POINTS
                        )
                        
                        if account:
                            # 更新账户
                            account.available_amount += red_packet["remaining_amount"]
                            account.total_amount += red_packet["remaining_amount"]
                            await account_crud.update(
                                session=uow.session,
                                db_obj=account,
                                obj_in={"available_amount": account.available_amount, "total_amount": account.total_amount}
                            )
                            
                            # 记录退回交易
                            await transaction_crud.create(
                                session=uow.session,
                                account_id=account.id,
                                telegram_id=red_packet["sender_id"],
                                account_type=self.ACCOUNT_TYPE_POINTS,
                                transaction_type=self.TRANSACTION_TYPE_RED_PACKET_SEND,
                                amount=red_packet["remaining_amount"],
                                balance=account.available_amount,
                                remarks=f"红包过期退回 {red_packet['remaining_amount']} 积分"
                            )
                            
                            await uow.commit()
                            
                except Exception as e:
                    logger.error(f"红包过期退回失败: {e}")
            
            # 更新红包消息，显示过期信息和抢红包记录
            try:
                if red_packet["message_id"] > 0 and red_packet["chat_id"] != 0:
                    from bot.misc import bot
                    from bot.handlers.red_packet_handler import _build_red_packet_expired_message
                    
                    # 获取红包信息
                    red_packet_info = self.get_red_packet_info(red_packet_id)
                    if red_packet_info["success"]:
                        info = red_packet_info["info"]
                        
                        # 构建红包过期消息
                        message = _build_red_packet_expired_message(
                            sender_name=info["sender_name"],
                            amount=info["amount"],
                            total_num=info["total_num"],
                            remaining_num=info["remaining_num"],
                            participants=info["participants"],
                            best_grabber=info["best_grabber"]
                        )
                        
                        # 更新红包消息
                        await bot.edit_message_text(
                            chat_id=red_packet["chat_id"],
                            message_id=red_packet["message_id"],
                            text=message
                        )
            except Exception as e:
                logger.error(f"更新过期红包消息失败: {e}")
            
            # 从缓存中删除红包
            del self._red_packets[red_packet_id] 