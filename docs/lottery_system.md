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

#### 1. 大小单双 (赔率: 1.8倍)
- **小**: 数字1、2、3、4
- **大**: 数字6、7、8、9
- **单**: 数字1、3、7、9
- **双**: 数字2、4、6、8
- **投注范围**: 1 - 100,000 U

#### 2. 组合投注 (赔率: 3倍)
- **小单**: 数字1、3
- **小双**: 数字2、4
- **大单**: 数字7、9
- **大双**: 数字6、8
- **豹子**: 数字0、5
- **投注范围**: 1 - 50,000 U

#### 3. 数字投注 (赔率: 6倍)
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
- `calculate_win_amount(bet_type, bet_amount)`

### 期望值分析
- **大小单双**: 期望值约为-28% (40% × 1.8 - 100%)
- **组合投注**: 期望值约为-40% (20% × 3.0 - 100%)
- **数字投注**: 期望值约为-40% (10% × 6.0 - 100%)