"""
多群组游戏配置系统
支持不同群组运行不同的游戏
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import secrets
import random
import logging

logger = logging.getLogger(__name__)

@dataclass
class GameConfig:
    """游戏配置"""
    game_type: str
    name: str
    description: str
    draw_interval: int  # 开奖间隔（分钟）
    bet_types: Dict[str, Dict]  # 投注类型配置
    number_odds: float  # 数字投注赔率
    number_min_bet: int  # 数字投注最小金额
    number_max_bet: int  # 数字投注最大金额
    cashback_rate: float  # 返水比例
    enabled: bool = True  # 是否启用

@dataclass
class GroupConfig:
    """群组配置"""
    group_id: int
    group_name: str
    game_type: str
    enabled: bool = True
    admin_only: bool = False  # 是否仅管理员可操作
    min_bet: int = 1  # 最小投注金额
    max_bet: int = 100000  # 最大投注金额
    auto_draw: bool = True  # 是否自动开奖
    notification_groups: List[int] = None  # 通知群组列表

class MultiGameConfig:
    """多群组游戏配置管理器"""
    
    def __init__(self):
        # 预定义游戏类型配置
        self.game_configs = {
            "lottery": GameConfig(
                game_type="lottery",
                name="数字开奖",
                description="经典数字开奖游戏，猜中数字获得高额奖励",
                draw_interval=5,
                bet_types={
                    "小": {"numbers": [1, 2, 3, 4], "odds": 2.36, "min_bet": 1, "max_bet": 100000},
                    "大": {"numbers": [6, 7, 8, 9], "odds": 2.36, "min_bet": 1, "max_bet": 100000},
                    "单": {"numbers": [1, 3, 7, 9], "odds": 2.36, "min_bet": 1, "max_bet": 100000},
                    "双": {"numbers": [2, 4, 6, 8], "odds": 2.36, "min_bet": 1, "max_bet": 100000},
                    "小单": {"numbers": [1, 3], "odds": 4.6, "min_bet": 1, "max_bet": 50000},
                    "小双": {"numbers": [2, 4], "odds": 4.6, "min_bet": 1, "max_bet": 50000},
                    "大单": {"numbers": [7, 9], "odds": 4.6, "min_bet": 1, "max_bet": 50000},
                    "大双": {"numbers": [6, 8], "odds": 4.6, "min_bet": 1, "max_bet": 50000},
                    "豹子": {"numbers": [0, 5], "odds": 4.6, "min_bet": 1, "max_bet": 50000},
                },
                number_odds=9.0,
                number_min_bet=1,
                number_max_bet=10000,
                cashback_rate=0.008,
            ),
            "fast_lottery": GameConfig(
                game_type="fast_lottery",
                name="快速开奖",
                description="快速开奖游戏，每3分钟开奖一次",
                draw_interval=3,
                bet_types={
                    "小": {"numbers": [1, 2, 3, 4], "odds": 2.0, "min_bet": 1, "max_bet": 50000},
                    "大": {"numbers": [6, 7, 8, 9], "odds": 2.0, "min_bet": 1, "max_bet": 50000},
                    "单": {"numbers": [1, 3, 7, 9], "odds": 2.0, "min_bet": 1, "max_bet": 50000},
                    "双": {"numbers": [2, 4, 6, 8], "odds": 2.0, "min_bet": 1, "max_bet": 50000},
                },
                number_odds=8.0,
                number_min_bet=1,
                number_max_bet=5000,
                cashback_rate=0.005,
            ),
            "high_odds": GameConfig(
                game_type="high_odds",
                name="高赔率开奖",
                description="高赔率开奖游戏，风险更高收益更大",
                draw_interval=10,
                bet_types={
                    "小": {"numbers": [1, 2, 3, 4], "odds": 3.0, "min_bet": 10, "max_bet": 200000},
                    "大": {"numbers": [6, 7, 8, 9], "odds": 3.0, "min_bet": 10, "max_bet": 200000},
                    "单": {"numbers": [1, 3, 7, 9], "odds": 3.0, "min_bet": 10, "max_bet": 200000},
                    "双": {"numbers": [2, 4, 6, 8], "odds": 3.0, "min_bet": 10, "max_bet": 200000},
                    "小单": {"numbers": [1, 3], "odds": 6.0, "min_bet": 10, "max_bet": 100000},
                    "小双": {"numbers": [2, 4], "odds": 6.0, "min_bet": 10, "max_bet": 100000},
                    "大单": {"numbers": [7, 9], "odds": 6.0, "min_bet": 10, "max_bet": 100000},
                    "大双": {"numbers": [6, 8], "odds": 6.0, "min_bet": 10, "max_bet": 100000},
                    "豹子": {"numbers": [0, 5], "odds": 6.0, "min_bet": 10, "max_bet": 100000},
                },
                number_odds=12.0,
                number_min_bet=10,
                number_max_bet=20000,
                cashback_rate=0.01,
            ),
        }
        
        # 群组配置（可以从数据库或配置文件加载）
        self.group_configs: Dict[int, GroupConfig] = {}
        
        # 默认群组配置
        self._init_default_groups()
    
    def _init_default_groups(self):
        """初始化默认群组配置"""
        # 示例群组配置
        default_groups = [
            GroupConfig(
                group_id=-1002417673222,
                group_name="开奖群组2",
                game_type="lottery",
                enabled=True,
                admin_only=False,
                min_bet=1,
                max_bet=100000,
                auto_draw=True,
                notification_groups=[-1002417673222]
            ),
        ]
        
        for group in default_groups:
            self.group_configs[group.group_id] = group
    
    def get_game_config(self, game_type: str) -> Optional[GameConfig]:
        """获取游戏配置"""
        return self.game_configs.get(game_type)
    
    def get_group_config(self, group_id: int) -> Optional[GroupConfig]:
        """获取群组配置"""
        return self.group_configs.get(group_id)
    
    def add_group_config(self, group_config: GroupConfig):
        """添加群组配置"""
        self.group_configs[group_config.group_id] = group_config
    
    def remove_group_config(self, group_id: int):
        """移除群组配置"""
        if group_id in self.group_configs:
            del self.group_configs[group_id]
    
    def update_group_config(self, group_id: int, **kwargs):
        """更新群组配置"""
        if group_id in self.group_configs:
            group = self.group_configs[group_id]
            for key, value in kwargs.items():
                if hasattr(group, key):
                    setattr(group, key, value)
    
    def get_enabled_groups(self) -> List[GroupConfig]:
        """获取所有启用的群组"""
        return [group for group in self.group_configs.values() if group.enabled]
    
    def get_groups_by_game_type(self, game_type: str) -> List[GroupConfig]:
        """根据游戏类型获取群组"""
        return [group for group in self.group_configs.values() 
                if group.game_type == game_type and group.enabled]
    
    def generate_draw_number(self, group_id: int, game_type: str) -> str:
        """生成期号"""
        import random
        now = datetime.now()
        # 格式：年月日时分秒微秒 + 3位随机数
        timestamp = now.strftime("%Y%m%d%H%M%S%f")  # 20位
        random_num = f"{random.randint(100, 999)}"  # 3位
        return f"{timestamp}{random_num}"
    
    def generate_secure_result(self) -> int:
        """生成安全的开奖结果"""
        return secrets.randbelow(10)
    
    def check_bet_win(self, bet_type: str, result: int, game_type: str) -> bool:
        """检查投注是否中奖"""
        game_config = self.get_game_config(game_type)
        if not game_config:
            logger.error(f"游戏配置未找到: {game_type}")
            return False
        
        # 数字投注
        if bet_type.isdigit() and len(bet_type) == 1:
            is_win = int(bet_type) == result
            logger.info(f"数字投注判断: 投注={bet_type}, 结果={result}, 是否中奖={is_win}")
            return is_win
        
        # 其他投注类型
        bet_config = game_config.bet_types.get(bet_type)
        if not bet_config:
            logger.error(f"投注类型配置未找到: {bet_type}")
            return False
        
        is_win = result in bet_config["numbers"]
        logger.info(f"组合投注判断: 投注类型={bet_type}, 结果={result}, 对应数字={bet_config['numbers']}, 是否中奖={is_win}")
        return is_win
    
    def calculate_win_amount(self, bet_type: str, bet_amount: int, game_type: str) -> int:
        """计算中奖金额"""
        game_config = self.get_game_config(game_type)
        if not game_config:
            logger.error(f"游戏配置未找到: {game_type}")
            return 0
        
        # 数字投注
        if bet_type.isdigit() and len(bet_type) == 1:
            win_amount = int(bet_amount * game_config.number_odds)
            logger.info(f"数字投注奖金计算: 投注={bet_type}, 金额={bet_amount}, 赔率={game_config.number_odds}, 奖金={win_amount}")
            return win_amount
        
        # 其他投注类型
        bet_config = game_config.bet_types.get(bet_type)
        if not bet_config:
            logger.error(f"投注类型配置未找到: {bet_type}")
            return 0
        
        win_amount = int(bet_amount * bet_config["odds"])
        logger.info(f"组合投注奖金计算: 类型={bet_type}, 金额={bet_amount}, 赔率={bet_config['odds']}, 奖金={win_amount}")
        return win_amount
    
    def calculate_cashback(self, bet_amount: int, game_type: str) -> int:
        """计算返水金额"""
        game_config = self.get_game_config(game_type)
        if not game_config:
            return 0
        
        return int(bet_amount * game_config.cashback_rate)
    
    def get_next_draw_time(self, group_id: int) -> datetime:
        """获取下次开奖时间"""
        group_config = self.get_group_config(group_id)
        if not group_config:
            raise ValueError(f"群组 {group_id} 未配置")
        
        game_config = self.get_game_config(group_config.game_type)
        if not game_config:
            raise ValueError(f"游戏类型 {group_config.game_type} 未配置")
        
        now = datetime.now()
        interval_minutes = game_config.draw_interval
        
        # 计算下次开奖时间（整点对齐）
        next_draw = now.replace(second=0, microsecond=0)
        while next_draw <= now:
            next_draw += timedelta(minutes=interval_minutes)
        
        return next_draw
    
    def validate_bet(self, group_id: int, bet_type: str, bet_amount: int) -> tuple[bool, str]:
        """验证投注"""
        group_config = self.get_group_config(group_id)
        if not group_config:
            return False, "群组未配置"
        
        if not group_config.enabled:
            return False, "群组游戏已禁用"
        
        game_config = self.get_game_config(group_config.game_type)
        if not game_config:
            return False, "游戏类型未配置"
        
        # 检查投注金额
        if bet_amount < group_config.min_bet:
            return False, f"投注积分不能少于 {group_config.min_bet}积分"
        
        if bet_amount > group_config.max_bet:
            return False, f"投注积分不能超过 {group_config.max_bet}积分"
        
        # 检查投注类型
        if bet_type.isdigit() and len(bet_type) == 1:
            # 数字投注
            if bet_amount < game_config.number_min_bet:
                return False, f"数字投注最小积分为 {game_config.number_min_bet}积分"
            if bet_amount > game_config.number_max_bet:
                return False, f"数字投注最大积分为 {game_config.number_max_bet}积分"
        else:
            # 其他投注类型
            bet_config = game_config.bet_types.get(bet_type)
            if not bet_config:
                return False, f"无效的投注类型: {bet_type}"
            
            if bet_amount < bet_config["min_bet"]:
                return False, f"{bet_type}投注最小积分为 {bet_config['min_bet']}积分"
            if bet_amount > bet_config["max_bet"]:
                return False, f"{bet_type}投注最大积分为 {bet_config['max_bet']}积分"
        
        return True, "投注验证通过"
    
    def get_bet_odds(self, bet_type: str, game_type: str) -> float:
        """获取投注赔率"""
        game_config = self.get_game_config(game_type)
        if not game_config:
            return 0.0
        
        # 数字投注
        if bet_type.isdigit() and len(bet_type) == 1:
            return game_config.number_odds
        
        # 其他投注类型
        bet_config = game_config.bet_types.get(bet_type)
        if not bet_config:
            return 0.0
        
        return bet_config["odds"]
    
    def format_game_info(self, group_id: int) -> str:
        """格式化游戏信息"""
        group_config = self.get_group_config(group_id)
        if not group_config:
            return "❌ 群组未配置"
        
        game_config = self.get_game_config(group_config.game_type)
        if not game_config:
            return "❌ 游戏类型未配置"
        
        next_draw = self.get_next_draw_time(group_id)
        
        info = f"🎲 **{game_config.name}**\n\n"
        info += f"📝 **游戏说明:** {game_config.description}\n\n"
        info += f"⏰ **开奖间隔:** 每 {game_config.draw_interval} 分钟\n"
        info += f"🕐 **下次开奖:** {next_draw.strftime('%H:%M')}\n\n"
        info += f"💰 **投注范围:** {group_config.min_bet} - {group_config.max_bet:,} 积分\n"
        info += f"🎁 **返水比例:** {game_config.cashback_rate * 100}%\n\n"
        
        info += "📊 **投注类型与赔率:**\n\n"
        
        # 大小单双
        basic_types = ["小", "大", "单", "双"]
        basic_info = []
        for bet_type in basic_types:
            if bet_type in game_config.bet_types:
                odds = game_config.bet_types[bet_type]["odds"]
                numbers = game_config.bet_types[bet_type]["numbers"]
                basic_info.append(f"   {bet_type}: 数字{numbers} - 赔率{odds}倍")
        
        if basic_info:
            info += "🔸 **基础投注:**\n"
            info += "\n".join(basic_info) + "\n\n"
        
        # 组合投注
        combo_types = ["小单", "小双", "大单", "大双", "豹子"]
        combo_info = []
        for bet_type in combo_types:
            if bet_type in game_config.bet_types:
                odds = game_config.bet_types[bet_type]["odds"]
                numbers = game_config.bet_types[bet_type]["numbers"]
                max_bet = game_config.bet_types[bet_type]["max_bet"]
                combo_info.append(f"   {bet_type}: 数字{numbers} - 赔率{odds}倍 (最大{max_bet:,}积分)")
        
        if combo_info:
            info += "🔸 **组合投注:**\n"
            info += "\n".join(combo_info) + "\n\n"
        
        # 数字投注
        info += f"🔸 **数字投注:**\n"
        info += f"   任意猜中具体数字 0～9 - 赔率{game_config.number_odds}倍\n"
        info += f"   投注范围: {game_config.number_min_bet} - {game_config.number_max_bet:,} 积分\n\n"
        
        if group_config.admin_only:
            info += "⚠️ **仅管理员可操作**\n"
        
        return info 