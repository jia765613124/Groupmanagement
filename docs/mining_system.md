# 挖矿系统文档

## 概述

挖矿系统是一个基于矿工卡的积分挖矿游戏，用户可以使用USDT购买不同类型的矿工卡，矿工卡会在指定天数内每天自动挖取积分，用户可以在第二天领取这些积分奖励。

## 系统特性

### ⛏️ 矿工卡类型
- **青铜矿工卡**: 0.5U，每天5000积分，持续3天
- **白银矿工卡**: 1.0U，每天10000积分，持续3天  
- **黄金矿工卡**: 2.0U，每天20000积分，持续3天
- **钻石矿工卡**: 10.0U，每天100000积分，持续3天

**注意:** 价格在数据库中存储为整数格式，单位为0.000001U。例如：0.5U = 500000，1.0U = 1000000。

### 🎯 核心功能
- **购买矿工卡**: 使用USDT购买矿工卡
- **自动挖矿**: 矿工卡每天自动挖取积分
- **奖励领取**: 用户可以在第二天领取挖取的积分
- **数量限制**: 每种类型矿工卡最多使用10张
- **统计功能**: 查看挖矿历史和统计信息
- **批量处理**: 支持大量矿工卡的高效批量处理
- **分页管理**: 支持大量矿工卡的分页显示和管理

### 💰 经济模型
- **投入**: 使用USDT购买矿工卡
- **产出**: 每天获得固定积分奖励
- **周期**: 3天挖矿周期
- **收益**: 根据矿工卡类型获得不同收益

## 文件结构

```
bot/
├── config/
│   └── mining_config.py      # 挖矿系统配置
├── common/
│   └── mining_service.py     # 挖矿业务逻辑服务
├── crud/
│   └── mining.py             # 挖矿数据访问层
├── handlers/
│   └── mining_handler.py     # Telegram机器人挖矿处理器
├── models/
│   └── mining.py             # 挖矿数据库模型

migrations/
└── mining_tables.sql         # 数据库表结构

docs/
└── mining_system.md         # 本文档
```

## 配置说明

### 1. 环境变量配置

```bash
# 设置挖矿通知群组ID (可选)
export MINING_NOTIFICATION_GROUPS="-1001234567890,-1001987654321"
```

### 2. 数据库配置

运行数据库迁移脚本创建挖矿相关表：

```sql
-- 执行 migrations/mining_tables.sql
```

### 3. 挖矿配置

在 `bot/config/mining_config.py` 中可以调整：

- 矿工卡类型和价格
- 每日挖矿积分
- 挖矿持续天数
- 每种类型的最大数量限制

## 使用方法

### 1. 启动挖矿处理器

在机器人启动时注册挖矿处理器：

```python
from bot.handlers.mining_handler import MiningHandler

# 在机器人启动时注册
mining_handler = MiningHandler(client)
```

### 2. 用户命令

#### Telethon版本
- `/mining` - 显示挖矿菜单
- 通过内联键盘进行矿工卡购买和奖励领取

#### aiogram版本
- 通过内联键盘进行交互
- 支持按钮式操作

### 3. 每日奖励处理

需要设置定时任务来处理每日挖矿奖励：

```python
from bot.common.mining_service import MiningService
from bot.common.uow import UoW
from bot.database.db import SessionFactory

async def process_daily_mining_rewards():
    """处理每日挖矿奖励"""
    async with SessionFactory() as session:
        uow = UoW(session)
        mining_service = MiningService(uow)
        result = await mining_service.process_daily_mining_rewards()
        print(f"挖矿奖励处理结果: {result}")

# 设置定时任务，每天执行一次
# 可以使用 asyncio.create_task 或第三方调度器
```

## 核心类说明

### MiningConfig
挖矿系统配置类，包含所有矿工卡类型和挖矿规则设置。

**主要方法:**
- `get_mining_card(card_type)` - 获取矿工卡配置
- `get_all_mining_cards()` - 获取所有矿工卡配置
- `calculate_total_points(card_type)` - 计算矿工卡总积分
- `format_mining_notification()` - 格式化挖矿通知消息

### MiningService
挖矿业务逻辑服务类，处理购买、奖励发放、领取等业务逻辑。

**主要方法:**
- `can_purchase_mining_card()` - 检查是否可以购买矿工卡
- `purchase_mining_card()` - 购买矿工卡
- `get_mining_info()` - 获取挖矿信息
- `get_pending_rewards()` - 获取待领取奖励
- `claim_all_rewards()` - 领取所有奖励
- `process_daily_mining_rewards()` - 处理每日挖矿奖励

### MiningHandler
挖矿处理器，负责处理Telegram机器人的挖矿相关命令和交互。

**主要功能:**
- 显示挖矿菜单
- 处理矿工卡购买
- 处理奖励领取
- 显示挖矿统计

## 数据库设计

### 1. mining_cards 表
存储用户的矿工卡记录。

**主要字段:**
- `telegram_id`: 用户ID
- `card_type`: 矿工卡类型
- `cost_usdt`: 购买价格
- `daily_points`: 每日挖矿积分
- `total_days`: 总挖矿天数
- `remaining_days`: 剩余挖矿天数
- `status`: 状态(1:挖矿中 2:已完成 3:已过期)

### 2. mining_rewards 表
存储挖矿奖励记录。

**主要字段:**
- `mining_card_id`: 关联的矿工卡ID
- `telegram_id`: 用户ID
- `reward_points`: 奖励积分
- `reward_day`: 奖励天数
- `status`: 状态(1:待领取 2:已领取)

### 3. mining_statistics 表
存储用户挖矿统计信息。

**主要字段:**
- `telegram_id`: 用户ID
- `total_cards_purchased`: 总购买数量
- `total_cost_usdt`: 总花费USDT
- `total_earned_points`: 总获得积分
- 各类型矿工卡数量统计

## 交易类型

挖矿系统使用以下交易类型：

- **40**: 购买矿工卡 - 使用USDT购买矿工卡
- **41**: 挖矿奖励 - 领取挖矿获得的积分
- **42**: 矿工卡过期 - 矿工卡过期处理

## 业务流程

### 1. 购买矿工卡流程
1. 用户选择矿工卡类型
2. 系统检查用户钱包余额
3. 系统检查同类型矿工卡数量限制
4. 扣除USDT余额
5. 创建矿工卡记录
6. 更新统计信息

### 2. 每日奖励发放流程
1. 定时任务扫描需要发放奖励的矿工卡
2. 为每个矿工卡创建奖励记录
3. 更新矿工卡状态和剩余天数
4. 标记奖励为待领取状态

### 3. 奖励领取流程
1. 用户查看待领取奖励
2. 用户选择领取所有奖励
3. 系统增加用户积分余额
4. 标记奖励为已领取状态
5. 记录积分交易

## 安全考虑

### 1. 余额验证
- 购买前验证USDT余额
- 使用事务确保数据一致性

### 2. 数量限制
- 每种类型矿工卡最多10张
- 防止用户过度购买

### 3. 时间控制
- 矿工卡有明确的开始和结束时间
- 防止过期矿工卡继续挖矿

### 4. 状态管理
- 矿工卡状态管理（挖矿中/已完成/已过期）
- 奖励状态管理（待领取/已领取）

## 扩展建议

### 1. 动态配置
可以创建挖矿配置表来支持动态配置：

```sql
CREATE TABLE mining_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(64) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2. 挖矿难度调整
可以添加挖矿难度系统，根据市场情况调整积分产出。

### 3. 特殊事件
可以添加特殊挖矿事件，如双倍积分、限时矿工卡等。

### 4. 排行榜系统
可以添加挖矿排行榜，显示挖矿收益最高的用户。

## 注意事项

1. **账户状态检查**: 购买前需要检查钱包账户状态
2. **余额验证**: 确保用户有足够USDT购买矿工卡
3. **数量限制**: 严格执行每种类型10张的限制
4. **时间控制**: 矿工卡有明确的有效期
5. **事务处理**: 所有操作都在数据库事务中执行
6. **日志记录**: 重要操作需要记录详细日志
7. **性能优化**: 大量用户同时挖矿时需要考虑数据库性能

## 故障排除

### 1. 奖励未发放
- 检查定时任务是否正常运行
- 检查矿工卡状态和剩余天数
- 检查数据库连接和事务

### 2. 购买失败
- 检查用户钱包余额
- 检查同类型矿工卡数量限制
- 检查账户状态

### 3. 领取失败
- 检查是否有待领取的奖励
- 检查积分账户状态
- 检查数据库事务

## 监控指标

建议监控以下指标：

1. **购买成功率**: 矿工卡购买成功/失败比例
2. **奖励发放率**: 每日奖励发放成功率
3. **用户活跃度**: 参与挖矿的用户数量
4. **收益情况**: 用户挖矿收益统计
5. **系统性能**: 数据库查询和事务处理时间

## 批量处理机制

### 性能优化

为了处理大量矿工卡，系统实现了高效的批量处理机制：

#### 1. 分批处理
- **批次大小**: 默认每批处理100张矿工卡
- **可配置**: 支持自定义批次大小（50-500张）
- **进度监控**: 实时显示处理进度和性能指标

#### 2. 数据库优化
- **分页查询**: 使用LIMIT和OFFSET进行分页
- **索引优化**: 在关键字段上建立索引
- **软删除**: 使用is_deleted和deleted_at字段

#### 3. 错误处理
- **重试机制**: 失败时自动重试（最多3次）
- **错误隔离**: 单张卡处理失败不影响其他卡
- **详细日志**: 记录处理过程和错误信息

### 调度器配置

```python
class MiningScheduler:
    def __init__(self):
        self.batch_size = 100      # 每批处理的矿工卡数量
        self.max_retries = 3       # 最大重试次数
        self.retry_delay = 60      # 重试延迟（秒）
```

### 性能指标

典型性能表现（基于测试数据）：
- **处理速度**: 每张卡约0.01-0.05秒
- **内存使用**: 每批100张卡约10-20MB
- **数据库负载**: 批次间1秒休息，避免过载

## 业务逻辑

### 购买矿工卡流程

1. **验证用户余额**: 检查用户USDT余额是否足够
2. **检查持有限制**: 验证用户是否达到该类型卡的最大持有量
3. **扣除费用**: 从用户账户扣除相应USDT
4. **创建矿工卡**: 在数据库中创建矿工卡记录
5. **记录交易**: 创建账户交易记录

### 每日奖励处理流程

1. **定时触发**: 调度器每小时检查一次
2. **批量查询**: 获取需要处理的矿工卡（分页）
3. **计算奖励**: 为每张卡计算当日积分奖励
4. **创建奖励记录**: 生成挖矿奖励记录
5. **更新卡状态**: 更新矿工卡状态和剩余天数
6. **统计汇总**: 记录处理统计信息

### 奖励领取流程

1. **查询待领取**: 获取用户未领取的奖励
2. **计算总额**: 统计总积分数量
3. **更新账户**: 将积分添加到用户账户
4. **标记已领取**: 更新奖励记录状态
5. **发送通知**: 向用户发送领取成功消息

## 安全考虑

### 数据安全
- **软删除**: 重要数据使用软删除，保留历史记录
- **事务处理**: 关键操作使用数据库事务确保一致性
- **输入验证**: 所有用户输入都进行验证和清理

### 业务安全
- **余额检查**: 购买前严格检查用户余额
- **持有限制**: 严格执行每种类型卡的最大持有量限制
- **时间验证**: 确保奖励发放的时间逻辑正确

## 监控和日志

### 日志记录
- **操作日志**: 记录所有关键操作
- **错误日志**: 详细记录错误信息和堆栈跟踪
- **性能日志**: 记录处理时间和性能指标

### 监控指标
- **处理卡数**: 每日处理的矿工卡数量
- **发放积分**: 每日发放的积分总量
- **处理时间**: 批量处理的耗时统计
- **错误率**: 处理失败的比例

## 故障排除

### 常见问题

#### 1. 批量处理失败
**症状**: 调度器报告批量处理失败
**解决方案**: 
- 检查数据库连接
- 查看详细错误日志
- 调整批次大小
- 检查数据库索引

#### 2. 性能问题
**症状**: 处理速度慢，内存使用高
**解决方案**:
- 减小批次大小
- 增加批次间休息时间
- 优化数据库查询
- 检查数据库性能

#### 3. 数据不一致
**症状**: 矿工卡状态与奖励记录不匹配
**解决方案**:
- 检查事务处理逻辑
- 验证数据完整性
- 运行数据修复脚本

### 维护命令

```bash
# 手动处理挖矿奖励
python -c "
import asyncio
from bot.tasks.mining_scheduler import process_mining_rewards_manual
asyncio.run(process_mining_rewards_manual())
"

# 性能测试
python examples/mining_batch_test.py
```

## 扩展性

### 水平扩展
- **多实例部署**: 支持多个调度器实例
- **负载均衡**: 通过数据库锁机制避免重复处理
- **分片处理**: 可按用户ID或时间范围分片处理

### 功能扩展
- **新卡类型**: 易于添加新的矿工卡类型
- **奖励机制**: 支持复杂的奖励计算逻辑
- **活动系统**: 可集成限时活动和特殊奖励

## 总结

挖矿系统通过批量处理机制，能够高效处理大量矿工卡的日常奖励发放。系统具有良好的扩展性和稳定性，支持高并发场景下的稳定运行。 