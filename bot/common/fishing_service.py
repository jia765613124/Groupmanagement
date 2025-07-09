"""
钓鱼服务类
处理钓鱼相关的业务逻辑
"""

from typing import Dict, Optional, Tuple
from bot.config.fishing_config import FishingConfig
from bot.crud.account import account as account_crud
from bot.crud.account_transaction import account_transaction as transaction_crud
from bot.common.uow import UoW
import logging

logger = logging.getLogger(__name__)

class FishingService:
    """钓鱼服务类"""
    
    # 钓鱼相关交易类型常量
    TRANSACTION_TYPE_FISHING_COST = 20  # 钓鱼费用
    TRANSACTION_TYPE_FISHING_REWARD = 21  # 钓鱼奖励
    TRANSACTION_TYPE_FISHING_LEGENDARY = 22  # 传说鱼奖励
    
    # 账户类型常量
    ACCOUNT_TYPE_POINTS = 1  # 积分账户
    
    def __init__(self, uow: UoW):
        self.uow = uow
    
    async def can_fish(self, telegram_id: int, rod_type: str) -> Tuple[bool, str]:
        """
        检查用户是否可以钓鱼
        
        Args:
            telegram_id: Telegram用户ID
            rod_type: 钓鱼竿类型
            
        Returns:
            (是否可以钓鱼, 错误信息)
        """
        try:
            # 获取钓鱼竿信息
            rod_info = FishingConfig.get_rod_info(rod_type)
            if not rod_info:
                return False, "无效的钓鱼竿类型"
            
            # 检查用户积分账户
            async with self.uow:
                account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    self.ACCOUNT_TYPE_POINTS
                )
                
                if not account:
                    return False, "积分账户不存在，请先创建账户"
                
                if account.status != 1:
                    return False, "账户已被冻结，无法进行钓鱼"
                
                if account.available_amount < rod_info["cost"]:
                    return False, f"积分不足，需要{rod_info['cost']}积分，当前只有{account.available_amount}积分"
                
                return True, ""
                
        except Exception as e:
            logger.error(f"检查钓鱼条件失败: {e}")
            return False, "系统错误，请稍后重试"
    
    async def fish(self, telegram_id: int, rod_type: str, subscription_link: str = "") -> Dict:
        """
        执行钓鱼操作
        
        Args:
            telegram_id: Telegram用户ID
            rod_type: 钓鱼竿类型
            subscription_link: 订阅号链接，用于传说鱼通知
            
        Returns:
            钓鱼结果字典
        """
        try:
            # 检查是否可以钓鱼
            can_fish, error_msg = await self.can_fish(telegram_id, rod_type)
            if not can_fish:
                return {
                    "success": False,
                    "message": error_msg,
                    "fish": None,
                    "points": 0,
                    "is_legendary": False,
                    "notification": None
                }
            
            # 获取钓鱼竿信息
            rod_info = FishingConfig.get_rod_info(rod_type)
            
            # 执行钓鱼操作
            async with self.uow:
                # 获取用户积分账户
                account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    self.ACCOUNT_TYPE_POINTS
                )
                
                # 扣除钓鱼费用
                account.available_amount -= rod_info["cost"]
                account.total_amount -= rod_info["cost"]
                await account_crud.update(
                    session=self.uow.session,
                    db_obj=account,
                    obj_in={"available_amount": account.available_amount, "total_amount": account.total_amount}
                )
                
                # 记录扣除交易
                await transaction_crud.create(
                    session=self.uow.session,
                    account_id=account.id,
                    telegram_id=telegram_id,
                    account_type=self.ACCOUNT_TYPE_POINTS,
                    transaction_type=self.TRANSACTION_TYPE_FISHING_COST,
                    amount=-rod_info["cost"],
                    balance=account.available_amount,
                    remarks=f"使用{rod_info['name']}钓鱼"
                )
                
                # 获取钓鱼结果
                fishing_result = FishingConfig.get_fishing_result(rod_type)
                
                if fishing_result["success"]:
                    # 钓鱼成功，增加积分
                    earned_points = fishing_result["points"]
                    account.available_amount += earned_points
                    account.total_amount += earned_points
                    await account_crud.update(
                        session=self.uow.session,
                        db_obj=account,
                        obj_in={"available_amount": account.available_amount, "total_amount": account.total_amount}
                    )
                    
                    # 确定交易类型
                    transaction_type = (
                        self.TRANSACTION_TYPE_FISHING_LEGENDARY 
                        if fishing_result["is_legendary"] 
                        else self.TRANSACTION_TYPE_FISHING_REWARD
                    )
                    
                    # 记录获得积分交易
                    await transaction_crud.create(
                        session=self.uow.session,
                        account_id=account.id,
                        telegram_id=telegram_id,
                        account_type=self.ACCOUNT_TYPE_POINTS,
                        transaction_type=transaction_type,
                        amount=earned_points,
                        balance=account.available_amount,
                        remarks=f"钓到{fishing_result['fish'].name}"
                    )
                    
                    # 如果是传说鱼，生成通知消息
                    notification = None
                    if fishing_result["is_legendary"]:
                        notification = FishingConfig.format_legendary_notification(
                            player_name=account.remarks or f"用户{telegram_id}",
                            fish_name=fishing_result["fish"].name,
                            fish_points=earned_points,  # 传入实际积分
                            subscription_link=subscription_link
                        )
                    
                    fishing_result["notification"] = notification
                    
                await self.uow.commit()
                
                return fishing_result
                
        except Exception as e:
            logger.error(f"钓鱼操作失败: {e}")
            await self.uow.rollback()
            return {
                "success": False,
                "message": "钓鱼失败，请稍后重试",
                "fish": None,
                "points": 0,
                "is_legendary": False,
                "notification": None
            }
    
    async def get_fishing_info(self, telegram_id: int) -> Dict:
        """
        获取钓鱼相关信息
        
        Args:
            telegram_id: Telegram用户ID
            
        Returns:
            钓鱼信息字典
        """
        try:
            async with self.uow:
                account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    self.ACCOUNT_TYPE_POINTS
                )
                
                if not account:
                    return {
                        "success": False,
                        "message": "积分账户不存在，请先创建账户",
                        "user_points": 0,
                        "rods_info": {}
                    }
                
                rods_info = FishingConfig.get_all_rods_info()
                
                # 为每个钓鱼竿添加是否可用的信息
                for rod_type, info in rods_info.items():
                    info["can_use"] = account.available_amount >= info["cost"]
                    info["shortage"] = max(0, info["cost"] - account.available_amount)
                
                return {
                    "success": True,
                    "message": "",
                    "user_points": account.available_amount,
                    "rods_info": rods_info
                }
                
        except Exception as e:
            logger.error(f"获取钓鱼信息失败: {e}")
            return {
                "success": False,
                "message": "获取信息失败，请稍后重试",
                "user_points": 0,
                "rods_info": {}
            }
    
    async def get_fishing_history(self, telegram_id: int, limit: int = 10, offset: int = 0) -> Dict:
        """
        获取钓鱼历史记录
        
        Args:
            telegram_id: Telegram用户ID
            limit: 限制记录数量
            offset: 分页偏移量
            
        Returns:
            钓鱼历史记录
        """
        try:
            async with self.uow:
                # 获取用户的积分账户
                account = await account_crud.get_by_telegram_id_and_type(
                    self.uow.session, 
                    telegram_id, 
                    self.ACCOUNT_TYPE_POINTS
                )
                
                if not account:
                    return {
                        "success": False,
                        "message": "积分账户不存在",
                        "history": [],
                        "total": 0,
                        "current_page": 1,
                        "total_pages": 0
                    }
                
                # 使用新的CRUD方法获取钓鱼相关的交易记录
                transactions = await transaction_crud.get_fishing_transactions(
                    self.uow.session,
                    telegram_id=telegram_id,
                    skip=offset,
                    limit=limit
                )
                
                # 获取总数
                total_count = await transaction_crud.get_fishing_transactions_count(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                history = []
                for trans in transactions:
                    history.append({
                        "id": trans.id,
                        "amount": trans.amount,
                        "type": trans.transaction_type,
                        "description": trans.remarks or "钓鱼交易",
                        "created_at": trans.created_at.isoformat() if trans.created_at else None
                    })
                
                current_page = (offset // limit) + 1
                total_pages = (total_count + limit - 1) // limit
                
                return {
                    "success": True,
                    "message": "",
                    "history": history,
                    "total": total_count,
                    "current_page": current_page,
                    "total_pages": total_pages
                }
                
        except Exception as e:
            logger.error(f"获取钓鱼历史失败: {e}")
            return {
                "success": False,
                "message": "获取历史记录失败",
                "history": [],
                "total": 0,
                "current_page": 1,
                "total_pages": 0
            } 