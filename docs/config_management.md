# 开奖系统配置管理

## 配置文件说明

### 1. `multi_game_config.py` - 多群组配置（推荐使用）

**用途：** 支持多个群组运行不同的开奖游戏

**特点：**
- 支持多种游戏类型（lottery、fast_lottery、high_odds）
- 每个群组可以有不同的配置
- 支持群组级别的权限控制
- 灵活的投注限制和赔率设置

**使用场景：**
- 新项目开发
- 需要多群组支持
- 需要不同游戏类型

### 2. `lottery_config.py` - 单群组配置（向后兼容）

**用途：** 单群组开奖系统配置

**特点：**
- 保持与旧版本的兼容性
- 自动从多群组配置中获取lottery游戏配置
- 如果多群组配置中没有lottery，使用默认配置

**使用场景：**
- 旧代码维护
- 简单的单群组应用
- 向后兼容性要求

## 配置冲突解决

### 问题
两个配置文件可能存在以下冲突：
1. 重复的投注类型定义
2. 不同的赔率设置
3. 功能重叠

### 解决方案

#### 1. 统一配置源
- `lottery_config.py` 现在从 `multi_game_config.py` 获取配置
- 确保配置数据的一致性

#### 2. 使用建议

**新项目：**
```python
from bot.config.multi_game_config import MultiGameConfig

config = MultiGameConfig()
game_config = config.get_game_config("lottery")
group_config = config.get_group_config(group_id)
```

**旧项目（向后兼容）：**
```python
from bot.config.lottery_config import LotteryConfig

config = LotteryConfig()
bet_types = config.get_bet_types()
result = config.generate_lottery_result()
```

#### 3. 配置优先级

1. **多群组配置** > **单群组配置**
2. **群组特定配置** > **游戏类型默认配置**
3. **运行时配置** > **静态配置**

## 配置最佳实践

### 1. 游戏类型配置

```python
# 在 multi_game_config.py 中添加新游戏类型
game_configs = {
    "new_game": GameConfig(
        game_type="new_game",
        name="新游戏",
        description="新游戏描述",
        draw_interval=5,
        bet_types={
            "小": {"numbers": [1, 2, 3, 4], "odds": 2.0, "min_bet": 1, "max_bet": 50000},
            # ... 更多投注类型
        },
        number_odds=8.0,
        number_min_bet=1,
        number_max_bet=5000,
        cashback_rate=0.005,
    ),
}
```

### 2. 群组配置

```python
# 添加新群组配置
group_config = GroupConfig(
    group_id=-1001234567893,
    group_name="新群组",
    game_type="new_game",
    enabled=True,
    admin_only=False,
    min_bet=1,
    max_bet=50000,
    auto_draw=True,
    notification_groups=[-1001234567893]
)

multi_config.add_group_config(group_config)
```

### 3. 动态配置更新

```python
# 运行时更新配置
multi_config.update_group_config(
    group_id=-1001234567890,
    enabled=False,  # 禁用群组
    max_bet=200000  # 更新最大投注金额
)
```

## 迁移指南

### 从单群组到多群组

1. **更新导入**
```python
# 旧代码
from bot.config.lottery_config import LotteryConfig

# 新代码
from bot.config.multi_game_config import MultiGameConfig
```

2. **更新配置获取**
```python
# 旧代码
config = LotteryConfig()
bet_types = config.BET_TYPES

# 新代码
config = MultiGameConfig()
game_config = config.get_game_config("lottery")
bet_types = game_config.bet_types
```

3. **更新方法调用**
```python
# 旧代码
result = config.generate_lottery_result()

# 新代码
result = config.generate_secure_result()
```

### 保持向后兼容

如果需要在旧代码中使用新配置：

```python
from bot.config.lottery_config import LotteryConfig

# 这些方法现在会自动使用多群组配置
config = LotteryConfig()
bet_types = config.get_bet_types()  # 从多群组配置获取
result = config.generate_lottery_result()  # 使用多群组的安全生成方法
```

## 配置验证

### 1. 配置完整性检查

```python
def validate_config():
    """验证配置完整性"""
    config = MultiGameConfig()
    
    # 检查所有游戏类型
    for game_type, game_config in config.game_configs.items():
        assert game_config.enabled, f"游戏类型 {game_type} 未启用"
        assert game_config.bet_types, f"游戏类型 {game_type} 缺少投注类型配置"
    
    # 检查所有群组配置
    for group_id, group_config in config.group_configs.items():
        assert group_config.enabled, f"群组 {group_id} 未启用"
        assert group_config.game_type in config.game_configs, f"群组 {group_id} 的游戏类型不存在"
```

### 2. 配置冲突检测

```python
def detect_config_conflicts():
    """检测配置冲突"""
    config = MultiGameConfig()
    
    # 检查群组ID冲突
    group_ids = set()
    for group_config in config.group_configs.values():
        if group_config.group_id in group_ids:
            print(f"警告：群组ID {group_config.group_id} 重复")
        group_ids.add(group_config.group_id)
```

## 总结

- **推荐使用 `multi_game_config.py`** 进行新开发
- **`lottery_config.py`** 保持向后兼容，自动使用多群组配置
- 两个配置文件现在统一配置源，避免冲突
- 支持动态配置更新和运行时配置管理 