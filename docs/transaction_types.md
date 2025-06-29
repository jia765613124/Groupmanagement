# 交易类型对照表

## 概述

本文档列出了系统中所有交易类型的定义和用途，方便开发和管理人员参考。

## 交易类型定义

### 基础交易类型 (1-19)

| 类型ID | 类型名称 | 描述 | 金额方向 |
|--------|----------|------|----------|
| 1 | 充值 | 用户充值积分/余额 | 正数(+) |
| 2 | 消费 | 用户消费积分/余额 | 负数(-) |
| 3 | 转账 | 用户间转账 | 正数/负数 |
| 4 | 签到奖励 | 每日签到奖励 | 正数(+) |
| 5 | 活动奖励 | 参与活动获得的奖励 | 正数(+) |
| 6 | 冻结 | 账户资金冻结 | 负数(-) |
| 7 | 解冻 | 账户资金解冻 | 正数(+) |

### 钓鱼系统交易类型 (20-29)

| 类型ID | 类型名称 | 描述 | 金额方向 | 备注 |
|--------|----------|------|----------|------|
| 20 | 钓鱼费用 | 使用钓鱼竿消耗的积分 | 负数(-) | 钓鱼成本 |
| 21 | 钓鱼奖励 | 钓到普通鱼获得的积分 | 正数(+) | 普通鱼类 |
| 22 | 传说鱼奖励 | 钓到传说鱼获得的积分 | 正数(+) | 传说鱼类 |

### 预留交易类型 (30-99)

| 类型ID | 类型名称 | 描述 | 状态 |
|--------|----------|------|------|
| 30-99 | 预留 | 为未来功能预留 | 未使用 |

## 钓鱼系统交易流程

### 1. 钓鱼费用扣除
```python
# 交易类型: 20 (钓鱼费用)
# 金额: 负数 (消耗积分)
# 示例: -1000 (初级钓鱼竿)
await transaction_crud.create(
    transaction_type=20,
    amount=-1000,
    remarks="使用初级钓鱼竿钓鱼"
)
```

### 2. 钓鱼奖励发放
```python
# 交易类型: 21 (钓鱼奖励) 或 22 (传说鱼奖励)
# 金额: 正数 (获得积分)
# 示例: +1500 (钓到草鱼)
await transaction_crud.create(
    transaction_type=21,  # 或 22 (传说鱼)
    amount=1500,
    remarks="钓到草鱼"
)
```

## 查询示例

### 1. 查询用户钓鱼相关交易
```sql
SELECT * FROM account_transactions 
WHERE telegram_id = ? 
  AND account_type = 1 
  AND transaction_type IN (20, 21, 22)
ORDER BY created_at DESC;
```

### 2. 统计钓鱼收益
```sql
SELECT 
    SUM(CASE WHEN transaction_type = 20 THEN ABS(amount) ELSE 0 END) as total_cost,
    SUM(CASE WHEN transaction_type IN (21, 22) THEN amount ELSE 0 END) as total_reward,
    SUM(amount) as net_profit
FROM account_transactions 
WHERE telegram_id = ? 
  AND account_type = 1 
  AND transaction_type IN (20, 21, 22);
```

### 3. 查询传说鱼记录
```sql
SELECT * FROM account_transactions 
WHERE transaction_type = 22 
  AND account_type = 1
ORDER BY created_at DESC;
```

## 代码中的常量定义

### FishingService 中的常量
```python
class FishingService:
    # 钓鱼相关交易类型常量
    TRANSACTION_TYPE_FISHING_COST = 20      # 钓鱼费用
    TRANSACTION_TYPE_FISHING_REWARD = 21    # 钓鱼奖励
    TRANSACTION_TYPE_FISHING_LEGENDARY = 22 # 传说鱼奖励
    
    # 账户类型常量
    ACCOUNT_TYPE_POINTS = 1  # 积分账户
```

### CRUD 中的查询方法
```python
async def get_fishing_transactions(self, session, telegram_id, limit=100):
    """获取钓鱼相关的交易记录"""
    fishing_types = [20, 21, 22]  # 钓鱼费用、钓鱼奖励、传说鱼奖励
    return await self.get_by_telegram_id_and_types(
        session=session,
        telegram_id=telegram_id,
        account_type=1,  # 积分账户
        transaction_types=fishing_types,
        limit=limit
    )
```

## 注意事项

1. **交易类型唯一性**: 每个交易类型ID在整个系统中应该是唯一的
2. **金额方向**: 负数表示支出，正数表示收入
3. **账户类型**: 钓鱼系统使用 `account_type = 1` (积分账户)
4. **数据一致性**: 每次交易都会记录交易后的余额
5. **扩展性**: 新增功能时请使用预留的交易类型ID

## 扩展建议

### 未来可能的交易类型
- **30**: 钓鱼竿升级费用
- **31**: 钓鱼比赛报名费
- **32**: 钓鱼比赛奖励
- **33**: 钓鱼道具购买
- **34**: 钓鱼道具使用

### 添加新交易类型的步骤
1. 在本文档中添加新的交易类型定义
2. 在相关服务类中添加常量定义
3. 更新CRUD查询方法（如需要）
4. 更新统计查询（如需要）
5. 添加相应的业务逻辑 