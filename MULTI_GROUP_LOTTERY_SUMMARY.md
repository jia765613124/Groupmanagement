# 多群组开奖系统总结

## 🎯 系统概述

多群组开奖系统支持在不同群组中运行不同的游戏，每个群组可以配置不同的游戏类型、赔率、开奖间隔等参数，实现灵活的游戏管理。

## 🏗️ 系统架构

### 1. 数据库模型更新

#### 新增字段
- `group_id`: 群组ID，支持多群组隔离
- `game_type`: 游戏类型，支持不同游戏模式

#### 模型结构
```python
# 开奖记录模型
class LotteryDraw(Base):
    group_id: Mapped[bigint_field]
    game_type: Mapped[str]
    draw_number: Mapped[str]
    # ... 其他字段

# 投注记录模型  
class LotteryBet(Base):
    group_id: Mapped[bigint_field]
    game_type: Mapped[str]
    draw_number: Mapped[str]
    # ... 其他字段

# 返水记录模型
class LotteryCashback(Base):
    group_id: Mapped[bigint_field]
    game_type: Mapped[str]
    # ... 其他字段
```

### 2. 多游戏配置系统

#### 游戏类型
1. **lottery** - 经典数字开奖
   - 开奖间隔: 5分钟
   - 返水比例: 0.8%
   - 数字投注赔率: 9.0倍

2. **fast_lottery** - 快速开奖
   - 开奖间隔: 3分钟
   - 返水比例: 0.5%
   - 数字投注赔率: 8.0倍

3. **high_odds** - 高赔率开奖
   - 开奖间隔: 10分钟
   - 返水比例: 1.0%
   - 数字投注赔率: 12.0倍

#### 群组配置
```python
@dataclass
class GroupConfig:
    group_id: int
    group_name: str
    game_type: str
    enabled: bool = True
    admin_only: bool = False
    min_bet: int = 1
    max_bet: int = 100000
    auto_draw: bool = True
    notification_groups: List[int] = None
```

## 🎮 功能特性

### 1. 多群组支持
- ✅ 每个群组独立运行
- ✅ 群组间数据隔离
- ✅ 独立的开奖时间表
- ✅ 独立的投注限制

### 2. 多游戏类型
- ✅ 经典开奖游戏
- ✅ 快速开奖游戏
- ✅ 高赔率游戏
- ✅ 可扩展新游戏类型

### 3. 灵活配置
- ✅ 群组级别投注限制
- ✅ 游戏级别赔率配置
- ✅ 管理员权限控制
- ✅ 自动开奖开关

### 4. 数据隔离
- ✅ 期号按群组+游戏类型生成
- ✅ 投注记录按群组隔离
- ✅ 返水记录按群组隔离
- ✅ 统计信息按群组计算

## 📊 数据库表结构

### 更新后的表结构
```sql
-- 开奖记录表
CREATE TABLE lottery_draws (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    group_id BIGINT NOT NULL COMMENT '群组ID',
    game_type VARCHAR(20) NOT NULL COMMENT '游戏类型',
    draw_number VARCHAR(32) NOT NULL COMMENT '期号',
    -- ... 其他字段
    UNIQUE KEY uk_group_game_draw (group_id, game_type, draw_number)
);

-- 投注记录表
CREATE TABLE lottery_bets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    group_id BIGINT NOT NULL COMMENT '群组ID',
    game_type VARCHAR(20) NOT NULL COMMENT '游戏类型',
    draw_number VARCHAR(32) NOT NULL COMMENT '期号',
    -- ... 其他字段
    UNIQUE KEY uk_group_game_draw_user_bet (group_id, game_type, draw_number, telegram_id, bet_type)
);

-- 返水记录表
CREATE TABLE lottery_cashbacks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    group_id BIGINT NOT NULL COMMENT '群组ID',
    game_type VARCHAR(20) NOT NULL COMMENT '游戏类型',
    -- ... 其他字段
);
```

## 🔧 配置管理

### 1. 游戏配置
```python
game_configs = {
    "lottery": GameConfig(
        game_type="lottery",
        name="数字开奖",
        draw_interval=5,
        bet_types={...},
        number_odds=9.0,
        cashback_rate=0.008,
    ),
    # ... 其他游戏类型
}
```

### 2. 群组配置
```python
group_configs = {
    -1001234567890: GroupConfig(
        group_id=-1001234567890,
        group_name="开奖群组1",
        game_type="lottery",
        enabled=True,
        admin_only=False,
        min_bet=1,
        max_bet=100000,
    ),
    # ... 其他群组
}
```

## 🎯 使用场景

### 1. 不同群组不同游戏
- 群组A: 经典开奖（5分钟间隔）
- 群组B: 快速开奖（3分钟间隔）
- 群组C: 高赔率开奖（10分钟间隔）

### 2. 权限控制
- 普通群组: 所有用户可投注
- VIP群组: 仅管理员可投注
- 测试群组: 可临时禁用

### 3. 投注限制
- 新手群组: 小额投注限制
- 高级群组: 大额投注支持
- 风险控制: 最大投注限制

## 📈 优势

### 1. 灵活性
- 支持多种游戏类型
- 群组级别配置
- 动态调整参数

### 2. 可扩展性
- 易于添加新游戏类型
- 支持更多群组
- 配置热更新

### 3. 数据安全
- 群组间数据隔离
- 独立的期号生成
- 防止跨群组操作

### 4. 管理便利
- 统一的配置管理
- 群组级别统计
- 灵活的权限控制

## 🚀 部署说明

### 1. 数据库迁移
```sql
-- 执行更新后的迁移脚本
source migrations/lottery_tables.sql;
```

### 2. 配置群组
```python
# 添加新群组配置
config = MultiGameConfig()
new_group = GroupConfig(
    group_id=-1001234567890,
    group_name="我的开奖群组",
    game_type="lottery",
    enabled=True,
    admin_only=False,
    min_bet=1,
    max_bet=100000,
)
config.add_group_config(new_group)
```

### 3. 启动服务
```python
# 使用多群组配置启动服务
from bot.config.multi_game_config import MultiGameConfig
config = MultiGameConfig()
# 启动开奖服务...
```

## 📝 示例用法

### 1. 查看群组游戏信息
```python
game_info = config.format_game_info(group_id)
print(game_info)
```

### 2. 验证投注
```python
is_valid, message = config.validate_bet(group_id, "小", 1000)
if is_valid:
    # 执行投注
    pass
```

### 3. 计算中奖金额
```python
win_amount = config.calculate_win_amount("小", 1000, "lottery")
cashback = config.calculate_cashback(1000, "lottery")
```

### 4. 生成期号
```python
draw_number = config.generate_draw_number(group_id, "lottery")
# 输出: 2025070207237890LOT
```

## 🎉 总结

多群组开奖系统成功实现了：

1. **多群组支持** - 不同群组运行不同游戏
2. **数据隔离** - 群组间数据完全隔离
3. **灵活配置** - 支持多种游戏类型和参数
4. **权限控制** - 群组级别的权限管理
5. **扩展性强** - 易于添加新功能和游戏类型

这个系统为你的多群组游戏运营提供了强大的技术支撑！🎲 