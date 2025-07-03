# 开奖系统文档

## 概述

开奖系统是一个基于数字0-9的投注游戏，每5分钟自动开奖一次，支持多种投注类型和返水机制。

## 系统特性

### 🎲 开奖机制
- **开奖频率**: 每5分钟开奖一次
- **开奖结果**: 0-9之间的随机数字
- **随机算法**: 使用加密级别的随机数生成器（Python secrets模块）
- **公平性**: 开奖结果在后台实时生成并自动记录

### 📊 投注类型与赔率

#### 1. 大小单双 (赔率: 2.36倍)
- **小**: 数字1、2、3、4
- **大**: 数字6、7、8、9
- **单**: 数字1、3、7、9
- **双**: 数字2、4、6、8
- **投注范围**: 1 - 100,000 U

#### 2. 组合投注 (赔率: 4.60倍)
- **小单**: 数字1、3
- **小双**: 数字2、4
- **大单**: 数字7、9
- **大双**: 数字6、8
- **豹子**: 数字0、5
- **投注范围**: 1 - 50,000 U

#### 3. 数字投注 (赔率: 9.00倍)
- 任意猜中具体数字 0～9
- **投注范围**: 1 - 10,000 U

### 🎁 返水福利
- **返水比例**: 每笔投注（无论输赢）在24小时内可领取**0.8%**的返水奖励
- **领取方式**: 通过机器人命令或界面按钮领取
- **过期时间**: 24小时后自动过期

## 文件结构

```
bot/
├── config/
│   └── lottery_config.py      # 开奖系统配置
├── common/
│   └── lottery_service.py     # 开奖业务逻辑服务
├── crud/
│   └── lottery.py             # 开奖数据访问层
├── handlers/
│   └── lottery_handler.py     # Telegram机器人开奖处理器
├── models/
│   └── lottery.py             # 开奖数据库模型
└── tasks/
    └── lottery_scheduler.py   # 定时开奖任务

migrations/
└── lottery_tables.sql         # 数据库表结构

test_lottery.py                # 开奖系统测试文件
docs/
└── lottery_system.md         # 本文档
```

## 配置说明

### 1. 环境变量配置

```bash
# 设置开奖通知群组ID (必填)
export LOTTERY_NOTIFICATION_GROUPS="-1001234567890,-1001987654321"

# 设置机器人Token (如果使用aiogram)
export BOT_TOKEN="your_bot_token"
```

### 2. 数据库配置

运行数据库迁移脚本创建开奖相关表：

```sql
-- 执行 migrations/lottery_tables.sql
```

### 3. 开奖配置

在 `bot/config/lottery_config.py` 中可以调整：

- 开奖频率（默认5分钟）
- 各种投注类型的赔率
- 投注金额限制
- 返水比例

## 使用方法

### 1. 启动开奖调度器

在机器人启动时启动开奖调度器：

```python
from bot.tasks.lottery_scheduler import start_lottery_scheduler
import asyncio

# 启动开奖调度器
asyncio.create_task(start_lottery_scheduler())
```

### 2. 注册开奖处理器

```python
from bot.handlers.lottery_handler import LotteryHandler

# 在机器人启动时注册
lottery_handler = LotteryHandler(client)
```

### 3. 用户命令

#### Telethon版本
- `/lottery` - 显示开奖投注界面
- `/lottery_history` - 查看开奖历史记录
- `/bet <类型> <金额>` - 下注（例如：`/bet 小 1000`）
- `/cashback` - 领取返水

#### aiogram版本
- 通过内联键盘进行投注
- 支持按钮式交互

## 核心类说明

### LotteryConfig
开奖系统配置类，包含所有开奖规则和概率设置。

**主要方法:**
- `generate_lottery_result()` - 生成开奖结果
- `check_bet_win(bet_type, bet_amount, result)` - 检查投注是否中奖
- `calculate_win_amount(bet_type, bet_amount)` - 计算中奖金额
- `format_draw_message()` - 格式化开奖消息

### LotteryService
开奖业务逻辑服务类，处理投注、开奖、结算等业务逻辑。

**主要方法:**
- `create_new_draw()` - 创建新的开奖期
- `place_bet(telegram_id, bet_type, bet_amount)` - 下注
- `draw_lottery()` - 开奖
- `claim_cashback(telegram_id)` - 领取返水

### LotteryScheduler
开奖调度器，负责定时开奖和发送结果。

**主要功能:**
- 每5分钟自动开奖
- 发送开奖结果到群组
- 清理过期返水记录

## 数据库表结构

### lottery_draws (开奖记录表)
- `draw_number`: 期号
- `result`: 开奖结果(0-9)
- `total_bets`: 总投注金额
- `total_payout`: 总派奖金额
- `profit`: 盈亏金额
- `status`: 状态(1:进行中 2:已开奖)

### lottery_bets (投注记录表)
- `draw_number`: 期号
- `telegram_id`: Telegram用户ID
- `bet_type`: 投注类型
- `bet_amount`: 投注金额
- `odds`: 赔率
- `is_win`: 是否中奖
- `win_amount`: 中奖金额
- `cashback_amount`: 返水金额
- `cashback_claimed`: 返水是否已领取

### lottery_cashbacks (返水记录表)
- `bet_id`: 投注记录ID
- `telegram_id`: Telegram用户ID
- `amount`: 返水金额
- `status`: 状态(1:待领取 2:已领取)

## 概率分析

### 中奖概率
- **大小单双**: 40% (4/10)
- **组合投注**: 20% (2/10)
- **豹子**: 20% (2/10)
- **数字投注**: 10% (1/10)

### 期望值分析
- **大小单双**: 期望值约为-6.4% (40% × 2.36 - 100%)
- **组合投注**: 期望值约为-8% (20% × 4.60 - 100%)
- **数字投注**: 期望值约为-10% (10% × 9.00 - 100%)

### 返水机制
返水机制可以部分抵消负期望值，提高用户体验。

## 测试

运行测试文件验证系统逻辑：

```bash
python test_lottery.py
```

测试内容包括：
- 开奖配置验证
- 随机数生成测试
- 投注中奖检查测试
- 中奖金额计算测试
- 概率分布测试

## 扩展功能

### 1. 动态赔率调整
可以根据投注情况动态调整赔率：

```python
def adjust_odds_by_bet_volume(total_bets, target_profit):
    """根据投注量调整赔率"""
    # 实现动态赔率逻辑
    pass
```

### 2. 开奖结果预测
可以添加开奖结果预测功能：

```python
def predict_next_result():
    """预测下次开奖结果"""
    # 实现预测逻辑
    pass
```

### 3. 投注统计报表
可以添加详细的投注统计功能：

```python
def generate_betting_report(start_date, end_date):
    """生成投注统计报表"""
    # 实现报表生成逻辑
    pass
```

## 注意事项

1. **开奖时间**: 确保服务器时间准确，开奖基于服务器时间
2. **数据库性能**: 大量用户同时投注时需要考虑数据库性能优化
3. **消息发送**: 确保机器人有群组发送消息的权限
4. **返水过期**: 定期清理过期的返水记录
5. **异常处理**: 开奖过程中需要完善的异常处理机制

## 故障排除

### 常见问题

1. **开奖结果未发送到群组**
   - 检查群组ID配置
   - 验证机器人权限
   - 检查网络连接

2. **投注失败**
   - 检查用户积分余额
   - 验证投注类型和金额
   - 检查数据库连接

3. **返水无法领取**
   - 检查返水是否已过期
   - 验证返水是否已领取
   - 检查用户账户状态

### 日志监控

系统会记录以下关键日志：
- 开奖调度器启动/停止
- 开奖结果生成
- 投注操作记录
- 返水领取记录
- 异常错误信息

### 性能优化建议

1. **数据库索引**: 确保关键字段有适当的索引
2. **连接池**: 使用数据库连接池提高性能
3. **缓存**: 对频繁查询的数据使用缓存
4. **异步处理**: 使用异步操作提高并发性能 