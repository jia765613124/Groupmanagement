"""
开奖服务类
处理开奖、投注、结算等业务逻辑
"""

from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from bot.config.lottery_config import LotteryConfig
from bot.crud.lottery import lottery_draw, lottery_bet, lottery_cashback
from bot.crud.account import account as account_crud
from bot.crud.account_transaction import account_transaction as account_transaction_crud
from bot.common.uow import UoW
import logging
from bot.config.multi_game_config import MultiGameConfig

logger = logging.getLogger(__name__)

class LotteryService:
    """彩票服务"""
    
    # 账户类型
    ACCOUNT_TYPE_POINTS = 1  # 积分账户
    
    # 交易类型
    TRANSACTION_TYPE_LOTTERY_BET = 30  # 开奖投注
    TRANSACTION_TYPE_LOTTERY_WIN = 31  # 开奖中奖
    TRANSACTION_TYPE_LOTTERY_CASHBACK = 32  # 开奖返水
    
    def __init__(self, uow: UoW):
        self.uow = uow
        self.multi_config = MultiGameConfig()
        
    def generate_draw_number(self) -> str:
        """生成期号"""
        import random
        now = datetime.now()
        # 格式: YYYYMMDDHHMMSSffffff + 3位随机数
        timestamp = now.strftime("%Y%m%d%H%M%S%f")  # 20位
        random_num = f"{random.randint(100, 999)}"  # 3位
        return f"{timestamp}{random_num}"
    
    async def create_new_draw(self, group_id: int, game_type: str) -> Dict:
        """为指定群组和游戏类型创建新的开奖期"""
        try:
            # 生成期号（年月日时分秒+随机数）
            draw_number = self.generate_draw_number()
            draw_time = datetime.now()
            
            # 检查是否已存在
            existing_draw = await lottery_draw.get_by_draw_number(self.uow.session, game_type, draw_number)
            if existing_draw:
                return {
                    "success": False,
                    "message": "期号已存在"
                }
            
            # 创建新期
            draw_data = {
                "group_id": group_id,
                "game_type": game_type,
                "draw_number": draw_number,
                "result": 0,  # 暂时为0，开奖时更新
                "total_bets": 0,
                "total_payout": 0,
                "profit": 0,
                "status": 1,  # 进行中
                "draw_time": draw_time,
                "remarks": "新开奖期"
            }
            
            new_draw = await lottery_draw.create(self.uow.session, obj_in=draw_data)
            
            return {
                "success": True,
                "draw": new_draw,
                "message": f"第 {draw_number} 期已创建"
            }
            
        except Exception as e:
            logger.error(f"创建新开奖期失败: {e}")
            return {
                "success": False,
                "message": "创建开奖期失败"
            }
    
    async def place_bet(self, group_id: int, telegram_id: int, bet_type: str, bet_amount: int) -> Dict:
        """下注"""
        try:
            # 获取当前期
            current_draw = await lottery_draw.get_current_draw(self.uow.session, group_id, "lottery")
            if not current_draw:
                return {
                    "success": False,
                    "message": "当前没有进行中的开奖期"
                }
            
            # 检查投注类型是否有效
            bet_type_info = LotteryConfig.get_bet_type_info(bet_type)
            if not bet_type_info and not (bet_type.isdigit() and 0 <= int(bet_type) <= 9):
                return {
                    "success": False,
                    "message": "无效的投注类型"
                }
            
            # 检查投注金额
            if bet_type_info:
                if bet_amount < bet_type_info.min_bet or bet_amount > bet_type_info.max_bet:
                    return {
                        "success": False,
                        "message": f"投注积分必须在 {bet_type_info.min_bet:,} - {bet_type_info.max_bet:,} 积分之间"
                    }
                odds = bet_type_info.odds
            else:
                # 数字投注
                if bet_amount < LotteryConfig.NUMBER_BET_MIN or bet_amount > LotteryConfig.NUMBER_BET_MAX:
                    return {
                        "success": False,
                        "message": f"数字投注积分必须在 {LotteryConfig.NUMBER_BET_MIN:,} - {LotteryConfig.NUMBER_BET_MAX:,} 积分之间"
                    }
                odds = LotteryConfig.NUMBER_BET_ODDS
            
            # 检查用户积分
            account = await account_crud.get_by_telegram_id_and_type(
                self.uow.session, 
                telegram_id, 
                self.ACCOUNT_TYPE_POINTS
            )
            
            if not account or account.available_amount < bet_amount:
                return {
                    "success": False,
                    "message": "积分余额不足"
                }
            
            # 检查是否已经下过相同类型的注
            existing_bet = await lottery_bet.get_by_user_draw_bet_type(
                self.uow.session,
                group_id=group_id,
                draw_number=current_draw.draw_number,
                telegram_id=telegram_id,
                bet_type=bet_type
            )
            
            if existing_bet:
                return {
                    "success": False,
                    "message": f"您已经对 {bet_type} 下过注了，不能重复投注"
                }
            
            # 执行投注
            async with self.uow:
                # 扣除积分
                account.available_amount -= bet_amount
                account.total_amount -= bet_amount
                await account_crud.update(
                    session=self.uow.session,
                    db_obj=account,
                    obj_in={"available_amount": account.available_amount, "total_amount": account.total_amount}
                )
                
                # 记录扣除交易
                await account_transaction_crud.create(
                    self.uow.session,
                    obj_in={
                        "account_id": account.id,
                        "telegram_id": telegram_id,
                        "account_type": self.ACCOUNT_TYPE_POINTS,
                        "transaction_type": self.TRANSACTION_TYPE_LOTTERY_BET,
                        "amount": -bet_amount,
                        "balance": account.available_amount,
                        "remarks": f"开奖投注 {bet_type} {bet_amount}积分"
                    }
                )
                
                # 创建投注记录
                cashback_amount = LotteryConfig.calculate_cashback(bet_amount)
                cashback_expire_time = datetime.now() + timedelta(hours=24)
                
                bet_data = {
                    "group_id": group_id,
                    "game_type": "lottery",
                    "draw_number": current_draw.draw_number,
                    "telegram_id": telegram_id,
                    "bet_type": bet_type,
                    "bet_amount": bet_amount,
                    "odds": odds,
                    "is_win": False,
                    "win_amount": 0,
                    "cashback_amount": cashback_amount,
                    "cashback_claimed": False,
                    "cashback_expire_time": cashback_expire_time,
                    "status": 1,  # 投注中
                    "remarks": f"投注 {bet_type}"
                }
                
                bet_record = await lottery_bet.create(self.uow.session, obj_in=bet_data)
                
                # 更新开奖期总投注金额
                current_draw.total_bets += bet_amount
                await lottery_draw.update(
                    session=self.uow.session,
                    db_obj=current_draw,
                    obj_in={"total_bets": current_draw.total_bets}
                )
                
                await self.uow.commit()
                
                return {
                    "success": True,
                    "bet": bet_record,
                    "message": f"投注成功！期号: {current_draw.draw_number}, 投注: {bet_type}, 积分: {bet_amount}"
                }
                
        except Exception as e:
            logger.error(f"下注失败: {e}")
            return {
                "success": False,
                "message": "下注失败，请稍后重试"
            }
    
    async def draw_lottery(self, group_id: int) -> Dict:
        """开奖"""
        try:
            # 获取当前期
            current_draw = await lottery_draw.get_current_draw(self.uow.session, group_id, "lottery")
            if not current_draw:
                return {
                    "success": False,
                    "message": "没有进行中的开奖期"
                }
            
            # 生成开奖结果
            result = self.multi_config.generate_secure_result()
            logger.info(f"为期号 {current_draw.draw_number} 生成开奖结果: {result}")
            
            # 获取该期所有投注
            bets = await lottery_bet.get_by_draw_number(self.uow.session, group_id, "lottery", current_draw.draw_number)
            logger.info(f"期号 {current_draw.draw_number} 共有 {len(bets)} 个投注")
            
            total_payout = 0
            
            async with self.uow:
                # 更新开奖结果
                await lottery_draw.update(
                    session=self.uow.session,
                    db_obj=current_draw,
                    obj_in={
                        "result": result,
                        "status": 2,  # 已开奖
                        "draw_time": datetime.now()
                    }
                )
                
                # 结算所有投注
                for bet in bets:
                    # 检查是否中奖
                    is_win = False
                    win_amount = 0
                    
                    # 获取当前游戏类型和配置
                    current_game_type = current_draw.game_type
                    game_config = self.multi_config.get_game_config(current_game_type)
                    if not game_config:
                        logger.error(f"游戏配置未找到: {current_game_type}")
                        continue
                        
                    logger.info(f"处理投注: ID={bet.id}, 类型={bet.bet_type}, 金额={bet.bet_amount}, 游戏类型={current_game_type}")
                    
                    # 使用游戏配置判断中奖
                    is_win = self.multi_config.check_bet_win(bet.bet_type, result, current_game_type)
                    logger.info(f"中奖判断: 投注类型={bet.bet_type}, 结果={result}, 是否中奖={is_win}")
                    
                    # 打印游戏配置信息
                    if bet.bet_type in game_config.bet_types:
                        bet_config = game_config.bet_types[bet.bet_type]
                        logger.info(f"投注配置: 类型={bet.bet_type}, 对应数字={bet_config['numbers']}, 赔率={bet_config['odds']}")
                    
                    if is_win:
                        # 使用游戏配置计算奖金
                        win_amount = self.multi_config.calculate_win_amount(bet.bet_type, bet.bet_amount, current_game_type)
                        logger.info(f"奖金计算: 投注类型={bet.bet_type}, 金额={bet.bet_amount}, 奖金={win_amount}")
                    
                    logger.info(f"结算投注: ID={bet.id}, 用户={bet.telegram_id}, 投注={bet.bet_type}, 金额={bet.bet_amount}, 是否中奖={is_win}, 奖金={win_amount}")
                    
                    # 更新投注记录
                    await lottery_bet.update(
                        session=self.uow.session,
                        db_obj=bet,
                        obj_in={
                            "is_win": is_win,
                            "win_amount": win_amount,
                            "status": 3  # 已结算
                        }
                    )
                    
                    # 派发奖金
                    if is_win and win_amount > 0:
                        # 获取用户账户
                        account = await account_crud.get_by_telegram_id_and_type(
                            self.uow.session, bet.telegram_id, self.ACCOUNT_TYPE_POINTS
                        )
                        if account:
                            # 更新账户余额
                            new_total = account.total_amount + win_amount
                            new_available = account.available_amount + win_amount
                            
                            await account_crud.update(
                                session=self.uow.session,
                                db_obj=account,
                                obj_in={
                                    "total_amount": new_total,
                                    "available_amount": new_available,
                                }
                            )
                            
                            # 添加交易记录
                            await account_transaction_crud.create(
                                self.uow.session,
                                obj_in={
                                    "account_id": account.id,
                                    "telegram_id": bet.telegram_id,
                                    "account_type": self.ACCOUNT_TYPE_POINTS,
                                    "transaction_type": self.TRANSACTION_TYPE_LOTTERY_WIN,
                                    "amount": win_amount,
                                    "balance": new_total,
                                    "remarks": f"开奖中奖 {bet.bet_type} {win_amount}积分"
                                }
                            )
                            
                            # 累计总派奖
                            total_payout += win_amount
                            logger.info(f"派奖成功: 用户={bet.telegram_id}, 投注={bet.bet_type}, 金额={bet.bet_amount}, 奖金={win_amount}")
                        else:
                            logger.error(f"派奖失败: 未找到用户账户, 用户={bet.telegram_id}")
                
                # 更新开奖记录
                await lottery_draw.update(
                    session=self.uow.session,
                    db_obj=current_draw,
                    obj_in={
                        "total_payout": total_payout,
                        "profit": current_draw.total_bets - total_payout
                    }
                )
                
                await self.uow.commit()
                
                return {
                    "success": True,
                    "draw": current_draw,
                    "result": result,
                    "total_bets": current_draw.total_bets,
                    "total_payout": total_payout,
                    "profit": current_draw.total_bets - total_payout,
                    "message": f"第 {current_draw.draw_number} 期开奖完成，结果: {result}"
                }
                
        except Exception as e:
            logger.error(f"开奖失败: {e}")
            return {
                "success": False,
                "message": "开奖失败"
            }
    
    async def claim_cashback(self, telegram_id: int) -> Dict:
        """领取返水"""
        try:
            # 获取用户未领取的返水
            unclaimed_bets = await lottery_bet.get_unclaimed_cashback(self.uow.session, telegram_id)
            
            if not unclaimed_bets:
                return {
                    "success": False,
                    "message": "没有可领取的返水"
                }
            
            total_cashback = 0
            
            async with self.uow:
                for bet in unclaimed_bets:
                    if not bet.cashback_claimed and bet.cashback_expire_time > datetime.now():
                        # 标记返水已领取
                        await lottery_bet.update(
                            session=self.uow.session,
                            db_obj=bet,
                            obj_in={"cashback_claimed": True}
                        )
                        
                        # 创建返水记录
                        cashback_data = {
                            "bet_id": bet.id,
                            "telegram_id": telegram_id,
                            "amount": bet.cashback_amount,
                            "status": 1,  # 待领取
                            "remarks": f"投注返水 {bet.bet_type}"
                        }
                        
                        await lottery_cashback.create(self.uow.session, obj_in=cashback_data)
                        
                        total_cashback += bet.cashback_amount
                
                if total_cashback > 0:
                    # 发放返水到用户账户
                    account = await account_crud.get_by_telegram_id_and_type(
                        self.uow.session,
                        telegram_id,
                        self.ACCOUNT_TYPE_POINTS
                    )
                    
                    if account:
                        account.available_amount += total_cashback
                        account.total_amount += total_cashback
                        await account_crud.update(
                            session=self.uow.session,
                            db_obj=account,
                            obj_in={"available_amount": account.available_amount, "total_amount": account.total_amount}
                        )
                        
                        # 记录返水交易
                        await account_transaction_crud.create(
                            self.uow.session,
                            obj_in={
                                "account_id": account.id,
                                "telegram_id": telegram_id,
                                "account_type": self.ACCOUNT_TYPE_POINTS,
                                "transaction_type": self.TRANSACTION_TYPE_LOTTERY_CASHBACK,
                                "amount": total_cashback,
                                "balance": account.available_amount,
                                "remarks": f"开奖返水 {total_cashback}积分"
                            }
                        )
                
                await self.uow.commit()
                
                return {
                    "success": True,
                    "total_cashback": total_cashback,
                    "message": f"成功领取返水 {total_cashback}积分"
                }
                
        except Exception as e:
            logger.error(f"领取返水失败: {e}")
            return {
                "success": False,
                "message": "领取返水失败"
            }
    
    async def get_user_bet_history(self, telegram_id: int, limit: int = 10, offset: int = 0) -> Dict:
        """
        获取用户投注历史（支持分页）
        
        Args:
            telegram_id: Telegram用户ID
            limit: 限制记录数量
            offset: 分页偏移量
            
        Returns:
            投注历史记录
        """
        try:
            async with self.uow:
                # 使用分页方法获取投注记录
                bets = await lottery_bet.get_by_telegram_id_paginated(
                    self.uow.session, 
                    telegram_id=telegram_id,
                    skip=offset,
                    limit=limit,
                    status=3  # 只查已结算
                )
                
                # 获取总数
                total_count = await lottery_bet.get_by_telegram_id_count(
                    self.uow.session,
                    telegram_id=telegram_id
                )
                
                history = []
                for bet in bets:
                    history.append({
                        "draw_number": bet.draw_number,
                        "bet_type": bet.bet_type,
                        "bet_amount": bet.bet_amount,
                        "is_win": bet.is_win,
                        "win_amount": bet.win_amount,
                        "cashback_amount": bet.cashback_amount,
                        "cashback_claimed": bet.cashback_claimed,
                        "created_at": bet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    })
                
                current_page = (offset // limit) + 1
                total_pages = (total_count + limit - 1) // limit
                
                return {
                    "success": True,
                    "history": history,
                    "total": total_count,
                    "current_page": current_page,
                    "total_pages": total_pages
                }
                
        except Exception as e:
            logger.error(f"获取投注历史失败: {e}")
            return {
                "success": False,
                "message": "获取投注历史失败",
                "history": [],
                "total": 0,
                "current_page": 1,
                "total_pages": 0
            }
    
    async def get_recent_draws(self, group_id: int = None, game_type: str = "lottery", limit: int = 10) -> Dict:
        """
        获取最近开奖记录
        
        Args:
            group_id: 群组ID，如果为None则获取所有群组
            game_type: 游戏类型，默认为"lottery"
            limit: 限制记录数量
            
        Returns:
            开奖历史记录
        """
        try:
            if group_id:
                # 获取指定群组的开奖记录
                draws = await lottery_draw.get_recent_draws(self.uow.session, group_id, game_type, limit)
            else:
                # 获取所有群组的开奖记录
                draws = await lottery_draw.get_recent_draws_all_groups(self.uow.session, game_type, limit)
            
            history = []
            for draw in draws:
                history.append({
                    "draw_number": draw.draw_number,
                    "result": draw.result,
                    "total_bets": draw.total_bets,
                    "total_payout": draw.total_payout,
                    "profit": draw.profit,
                    "draw_time": draw.draw_time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            return {
                "success": True,
                "history": history,
                "total": len(history)
            }
            
        except Exception as e:
            logger.error(f"获取开奖历史失败: {e}")
            return {
                "success": False,
                "message": "获取开奖历史失败"
            } 