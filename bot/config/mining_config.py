"""
挖矿系统配置文件
包含矿工卡类型、挖矿规则和积分奖励配置
"""

from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime, timedelta

@dataclass
class MiningCard:
    """矿工卡配置"""
    name: str
    card_type: str
    cost_usdt: float
    daily_points: int
    duration_days: int
    max_cards: int
    description: str

@dataclass
class MiningReward:
    """挖矿奖励配置"""
    card_type: str
    daily_points: int
    total_days: int
    total_points: int

class MiningConfig:
    """挖矿系统配置类"""
    
    # 矿工卡配置
    MINING_CARDS = {
        "青铜": MiningCard(
            name="青铜矿工卡",
            card_type="青铜",
            cost_usdt=500000,  # 0.5U * 1000000
            daily_points=5000,
            duration_days=3,
            max_cards=10,
            description="基础矿工卡，每天可挖取5000积分，持续3天"
        ),
        "白银": MiningCard(
            name="白银矿工卡", 
            card_type="白银",
            cost_usdt=1000000,  # 1.0U * 1000000
            daily_points=10000,
            duration_days=3,
            max_cards=10,
            description="进阶矿工卡，每天可挖取10000积分，持续3天"
        ),
        "黄金": MiningCard(
            name="黄金矿工卡",
            card_type="黄金", 
            cost_usdt=2000000,  # 2.0U * 1000000
            daily_points=20000,
            duration_days=3,
            max_cards=10,
            description="高级矿工卡，每天可挖取20000积分，持续3天"
        ),
        "钻石": MiningCard(
            name="钻石矿工卡",
            card_type="钻石",
            cost_usdt=10000000,  # 10.0U * 1000000
            daily_points=100000,
            duration_days=3,
            max_cards=10,
            description="顶级矿工卡，每天可挖取100000积分，持续3天"
        )
    }
    
    # 挖矿相关交易类型常量
    TRANSACTION_TYPE_MINING_PURCHASE = 40  # 购买矿工卡
    TRANSACTION_TYPE_MINING_REWARD = 41    # 挖矿奖励
    TRANSACTION_TYPE_MINING_EXPIRE = 42    # 矿工卡过期
    
    # 账户类型常量
    ACCOUNT_TYPE_POINTS = 1  # 积分账户
    ACCOUNT_TYPE_WALLET = 2  # 钱包账户
    
    @classmethod
    def get_mining_card(cls, card_type: str) -> MiningCard:
        """获取矿工卡配置"""
        return cls.MINING_CARDS.get(card_type)
    
    @classmethod
    def get_all_mining_cards(cls) -> Dict[str, MiningCard]:
        """获取所有矿工卡配置"""
        return cls.MINING_CARDS
    
    @classmethod
    def calculate_total_points(cls, card_type: str) -> int:
        """计算矿工卡总积分"""
        card = cls.get_mining_card(card_type)
        if not card:
            return 0
        return card.daily_points * card.duration_days
    
    @classmethod
    def get_mining_reward_info(cls, card_type: str) -> MiningReward:
        """获取挖矿奖励信息"""
        card = cls.get_mining_card(card_type)
        if not card:
            return None
        
        return MiningReward(
            card_type=card.card_type,
            daily_points=card.daily_points,
            total_days=card.duration_days,
            total_points=card.daily_points * card.duration_days
        )
    
    @classmethod
    def format_mining_notification(cls, player_name: str, card_type: str, points: int) -> str:
        """格式化挖矿通知消息"""
        return f"恭喜{player_name}获得了矿工们帮您挖取的积分: {points:,}"
    
    @classmethod
    def get_card_display_info(cls, card_type: str) -> Dict:
        """获取矿工卡显示信息"""
        card = cls.get_mining_card(card_type)
        if not card:
            return None
        
        return {
            "name": card.name,
            "cost_usdt": card.cost_usdt / 1000000,  # 转换为USDT显示
            "cost_usdt_raw": card.cost_usdt,  # 原始整数值
            "daily_points": card.daily_points,
            "duration_days": card.duration_days,
            "max_cards": card.max_cards,
            "total_points": card.daily_points * card.duration_days,
            "description": card.description
        }
    
    @classmethod
    def get_all_cards_display_info(cls) -> Dict[str, Dict]:
        """获取所有矿工卡显示信息"""
        return {
            card_type: cls.get_card_display_info(card_type)
            for card_type in cls.MINING_CARDS.keys()
        }

# 使用示例
if __name__ == "__main__":
    print("=== 矿工卡信息 ===")
    for card_type, info in MiningConfig.get_all_cards_display_info().items():
        print(f"{card_type}: {info['name']}")
        print(f"   价格: {info['cost_usdt']}U")
        print(f"   每日积分: {info['daily_points']:,}")
        print(f"   持续天数: {info['duration_days']}天")
        print(f"   总积分: {info['total_points']:,}")
        print(f"   最大数量: {info['max_cards']}张")
        print(f"   描述: {info['description']}")
        print() 