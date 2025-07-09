"""
钓鱼系统配置文件
包含钓鱼竿类型、鱼类、概率和积分规则
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple
import random

@dataclass
class FishingRod:
    """钓鱼竿配置"""
    name: str
    cost: int
    min_fish_points: int
    description: str

@dataclass
class Fish:
    """鱼类配置"""
    name: str
    points: int
    category: str
    description: str

@dataclass
class FishCategory:
    """鱼类分类配置"""
    name: str
    probability: float
    fishes: List[Fish]
    description: str

class FishingConfig:
    """钓鱼系统配置类"""
    
    # 钓鱼竿配置
    FISHING_RODS = {
        "初级": FishingRod(
            name="初级钓鱼竿",
            cost=1000,
            min_fish_points=100,
            description="新手必备，虽然简单但也能钓到大鱼哦！"
        ),
        "中级": FishingRod(
            name="中级钓鱼竿",
            cost=3000,
            min_fish_points=300,
            description="专业级装备，钓到大鱼的概率更高！"
        ),
        "高级": FishingRod(
            name="高级钓鱼竿",
            cost=5000,
            min_fish_points=500,
            description="顶级装备，距离鲸鱼只有一步之遥！"
        )
    }
    
    # 鱼类分类配置
    FISH_CATEGORIES = {
        "一类鱼": FishCategory(
            name="一类鱼",
            probability=0.75,  # 75%
            fishes=[
                Fish("河虾", 100, "一类鱼", "虽然小，但也是收获！"),
                Fish("泥鳅", 300, "一类鱼", "滑溜溜的，手感不错！"),
                Fish("白条", 500, "一类鱼", "肉质鲜美，值得期待！")
            ],
            description="常见鱼类，容易钓到"
        ),
        "二类鱼": FishCategory(
            name="二类鱼", 
            probability=0.15,  # 15%
            fishes=[
                Fish("草鱼", 1500, "二类鱼", "体型不错，收获颇丰！"),
                Fish("鲫鱼", 4500, "二类鱼", "肉质细嫩，价值不菲！"),
                Fish("大闸蟹", 7500, "二类鱼", "蟹中之王，运气不错！")
            ],
            description="中等鱼类，有一定价值"
        ),
        "三类鱼": FishCategory(
            name="三类鱼",
            probability=0.049,  # 4.9%
            fishes=[
                Fish("大黄鱼", 3000, "三类鱼", "黄金般的色泽，珍贵稀有！"),
                Fish("毛蟹", 9000, "三类鱼", "蟹中极品，价值连城！"),
                Fish("金枪鱼", 15000, "三类鱼", "深海霸主，顶级收获！")
            ],
            description="上等鱼类，价值很高"
        ),
        "四类鱼": FishCategory(
            name="四类鱼",
            probability=0.001,  # 0.1%
            fishes=[
                Fish("金鱼", 100000, "四类鱼", "传说中的神鱼，价值十万！"),
                Fish("锦鲤", 100000, "四类鱼", "幸运的象征，价值十万！"),
                Fish("虎鲸", 100000, "四类鱼", "海洋之王，价值十万！")
            ],
            description="传说鱼类，价值连城"
        )
    }
    
    # 钓鱼失败概率
    FAILURE_PROBABILITY = 0.05  # 5%
    
    # 钓鱼失败提示
    FAILURE_MESSAGES = [
        "鱼竿太脆弱了，没能钓上来鱼并且损坏了，加油，下次一定能钓上来~！~",
        "哎呀，鱼儿跑掉了，别灰心，再试一次！",
        "鱼竿断了，但别放弃，下次一定能成功！",
        "鱼儿太狡猾了，下次用更好的鱼竿试试！"
    ]
    
    # 四类鱼通知消息模板
    LEGENDARY_FISH_NOTIFICATION = "恭喜钓鱼佬{player_name}钓上来一条价值{fish_points:,}分的{fish_name}鱼，让我们恭喜这个逼。钓鱼入口：{subscription_link}"
    
    @classmethod
    def get_fish_by_rod_and_category(cls, rod_type: str, category: str) -> Fish:
        """根据鱼竿类型和鱼类分类获取对应的鱼"""
        rod = cls.FISHING_RODS[rod_type]
        category_fishes = cls.FISH_CATEGORIES[category].fishes
        
        # 根据鱼竿类型选择对应的鱼
        if rod_type == "初级":
            return category_fishes[0]  # 最低积分鱼
        elif rod_type == "中级":
            return category_fishes[1]  # 中等积分鱼
        elif rod_type == "高级":
            return category_fishes[2]  # 最高积分鱼
        else:
            return category_fishes[0]  # 默认返回最低积分鱼
    
    @classmethod
    def get_random_fish_category(cls) -> str:
        """随机获取鱼类分类"""
        categories = list(cls.FISH_CATEGORIES.keys())
        probabilities = [cls.FISH_CATEGORIES[cat].probability for cat in categories]
        
        # 添加失败概率
        categories.append("失败")
        probabilities.append(cls.FAILURE_PROBABILITY)
        
        # 归一化概率
        total_prob = sum(probabilities)
        normalized_probs = [p / total_prob for p in probabilities]
        
        return random.choices(categories, weights=normalized_probs)[0]
    
    @classmethod
    def get_fishing_result(cls, rod_type: str) -> Dict:
        """获取钓鱼结果"""
        category = cls.get_random_fish_category()
        
        if category == "失败":
            return {
                "success": False,
                "message": random.choice(cls.FAILURE_MESSAGES),
                "fish": None,
                "points": 0,
                "is_legendary": False
            }
        
        fish = cls.get_fish_by_rod_and_category(rod_type, category)
        # 测试用：二类鱼、三类鱼和四类鱼都设为传说鱼，触发通知
        is_legendary = category in ["二类鱼", "三类鱼", "四类鱼"]
        
        return {
            "success": True,
            "message": f"恭喜钓到了{fish.name}！{fish.description}",
            "fish": fish,
            "points": fish.points,
            "is_legendary": is_legendary
        }
    
    @classmethod
    def get_rod_info(cls, rod_type: str) -> Dict:
        """获取钓鱼竿信息"""
        rod = cls.FISHING_RODS[rod_type]
        return {
            "name": rod.name,
            "cost": rod.cost,
            "min_points": rod.min_fish_points,
            "description": rod.description
        }
    
    @classmethod
    def get_all_rods_info(cls) -> Dict[str, Dict]:
        """获取所有钓鱼竿信息"""
        return {rod_type: cls.get_rod_info(rod_type) for rod_type in cls.FISHING_RODS}
    
    @classmethod
    def format_legendary_notification(cls, player_name: str, fish_name: str, fish_points: int, subscription_link: str) -> str:
        """格式化传说鱼通知消息"""
        return cls.LEGENDARY_FISH_NOTIFICATION.format(
            player_name=player_name,
            fish_name=fish_name,
            fish_points=fish_points,
            subscription_link=subscription_link
        )

# 使用示例
if __name__ == "__main__":
    # 测试钓鱼逻辑
    print("=== 钓鱼竿信息 ===")
    for rod_type, info in FishingConfig.get_all_rods_info().items():
        print(f"{rod_type}: {info['name']} - 消耗{info['cost']}积分 - {info['description']}")
    
    print("\n=== 钓鱼测试 ===")
    for rod_type in ["初级", "中级", "高级"]:
        print(f"\n使用{rod_type}钓鱼竿:")
        for i in range(5):
            result = FishingConfig.get_fishing_result(rod_type)
            if result["success"]:
                print(f"  钓到: {result['fish'].name} - {result['points']}积分")
                if result["is_legendary"]:
                    print(f"  *** 传说鱼！ ***")
            else:
                print(f"  {result['message']}") 