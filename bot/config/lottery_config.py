"""
开奖系统配置文件（单群组版本，保持向后兼容）
包含开奖规则、赔率、投注限制等配置
注意：新项目建议使用 multi_game_config.py 支持多群组功能
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple
import secrets
from datetime import datetime, timedelta
from bot.config.multi_game_config import MultiGameConfig

@dataclass
class BetType:
    """投注类型配置"""
    name: str
    numbers: List[int]
    odds: float
    min_bet: int
    max_bet: int
    description: str

class LotteryConfig:
    """开奖系统配置类（单群组版本）"""
    
    # 开奖频率（分钟）
    DRAW_INTERVAL_MINUTES = 5
    
    # 默认群组ID（用于单群组模式）
    DEFAULT_GROUP_ID = -1001234567890
    
    # 开奖结果范围
    RESULT_RANGE = (0, 9)  # 0-9
    
    # 返水比例
    CASHBACK_RATE = 0.008  # 0.8%
    
    # 数字投注配置
    NUMBER_BET_ODDS = 9.0
    NUMBER_BET_MIN = 1
    NUMBER_BET_MAX = 10000
    
    # 获取多群组配置实例
    _multi_config = MultiGameConfig()
    
    @classmethod
    def get_bet_types(cls) -> Dict[str, BetType]:
        """获取投注类型配置（从多群组配置中获取）"""
        game_config = cls._multi_config.get_game_config("lottery")
        if not game_config:
            # 如果多群组配置中没有lottery，返回默认配置
            return cls._get_default_bet_types()
        
        # 从多群组配置转换为BetType格式
        bet_types = {}
        for bet_type, config in game_config.bet_types.items():
            bet_types[bet_type] = BetType(
                name=bet_type,
                numbers=config["numbers"],
                odds=config["odds"],
                min_bet=config["min_bet"],
                max_bet=config["max_bet"],
                description=f"数字{config['numbers']}"
            )
        
        return bet_types
    
    @classmethod
    def _get_default_bet_types(cls) -> Dict[str, BetType]:
        """获取默认投注类型配置（向后兼容）"""
        return {
            # 大小单双
            "小": BetType(
                name="小",
                numbers=[1, 2, 3, 4],
                odds=2.36,
                min_bet=1,
                max_bet=100000,
                description="数字1、2、3、4"
            ),
            "大": BetType(
                name="大",
                numbers=[6, 7, 8, 9],
                odds=2.36,
                min_bet=1,
                max_bet=100000,
                description="数字6、7、8、9"
            ),
            "单": BetType(
                name="单",
                numbers=[1, 3, 7, 9],
                odds=2.36,
                min_bet=1,
                max_bet=100000,
                description="数字1、3、7、9"
            ),
            "双": BetType(
                name="双",
                numbers=[2, 4, 6, 8],
                odds=2.36,
                min_bet=1,
                max_bet=100000,
                description="数字2、4、6、8"
            ),
            
            # 组合投注
            "小单": BetType(
                name="小单",
                numbers=[1, 3],
                odds=4.60,
                min_bet=1,
                max_bet=50000,
                description="数字1、3"
            ),
            "小双": BetType(
                name="小双",
                numbers=[2, 4],
                odds=4.60,
                min_bet=1,
                max_bet=50000,
                description="数字2、4"
            ),
            "大单": BetType(
                name="大单",
                numbers=[7, 9],
                odds=4.60,
                min_bet=1,
                max_bet=50000,
                description="数字7、9"
            ),
            "大双": BetType(
                name="大双",
                numbers=[6, 8],
                odds=4.60,
                min_bet=1,
                max_bet=50000,
                description="数字6、8"
            ),
            "豹子": BetType(
                name="豹子",
                numbers=[0, 5],
                odds=4.60,
                min_bet=1,
                max_bet=50000,
                description="数字0、5"
            ),
        }
    
    @classmethod
    def generate_lottery_result(cls) -> int:
        """生成开奖结果（0-9）"""
        return cls._multi_config.generate_secure_result()
    
    @classmethod
    def get_bet_type_info(cls, bet_type: str) -> BetType:
        """获取投注类型信息"""
        bet_types = cls.get_bet_types()
        return bet_types.get(bet_type)
    
    @classmethod
    def get_all_bet_types(cls) -> Dict[str, BetType]:
        """获取所有投注类型"""
        return cls.get_bet_types()
    
    @classmethod
    def check_bet_win(cls, bet_type: str, bet_number: int, result: int) -> bool:
        """检查投注是否中奖"""
        return cls._multi_config.check_bet_win(bet_type, result, "lottery")
    
    @classmethod
    def calculate_win_amount(cls, bet_type: str, bet_amount: int) -> int:
        """计算中奖金额"""
        return cls._multi_config.calculate_win_amount(bet_type, bet_amount, "lottery")
    
    @classmethod
    def calculate_cashback(cls, bet_amount: int) -> int:
        """计算返水金额"""
        return cls._multi_config.calculate_cashback(bet_amount, "lottery")
    
    @classmethod
    def get_next_draw_time(cls) -> datetime:
        """获取下次开奖时间"""
        return cls._multi_config.get_next_draw_time(cls.DEFAULT_GROUP_ID)
    
    @classmethod
    def format_draw_message(cls, draw_number: str, result: int, total_bets: int, total_payout: int) -> str:
        """格式化开奖消息"""
        message = f"🎲 **第 {draw_number} 期开奖结果** 🎲\n\n"
        message += f"🏆 **开奖号码: {result}**\n\n"
        
        # 添加大小单双信息
        if result in [1, 2, 3, 4]:
            message += "📊 **大小单双:** 小"
        elif result in [6, 7, 8, 9]:
            message += "📊 **大小单双:** 大"
        else:
            message += "📊 **大小单双:** 豹子"
        
        if result in [1, 3, 7, 9]:
            message += " 单"
        elif result in [2, 4, 6, 8]:
            message += " 双"
        else:
            message += " 豹子"
        
        message += f"\n\n📈 **本期统计:**\n"
        message += f"   总投注: {total_bets:,} U\n"
        message += f"   总派奖: {total_payout:,} U\n"
        
        # 计算盈亏
        profit = total_bets - total_payout
        if profit > 0:
            message += f"   💰 盈利: +{profit:,} U"
        else:
            message += f"   💸 亏损: {profit:,} U"
        
        message += f"\n\n⏰ **下期开奖:** {cls.get_next_draw_time().strftime('%H:%M')}"
        
        return message
    
    @classmethod
    def format_bet_interface(cls) -> str:
        """格式化投注界面"""
        return cls._multi_config.format_game_info(cls.DEFAULT_GROUP_ID) 