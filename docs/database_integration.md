# 钓鱼系统数据库集成方案

## 概述

钓鱼系统与现有账户和交易记录系统的集成方案，使用现有的 `accounts` 和 `account_transactions` 表。

## 数据库表结构

### 1. accounts 表 (积分账户)

```sql
CREATE TABLE accounts (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NULL,
    telegram_id BIGINT NOT NULL,
    account_type SMALLINT NOT NULL,  -- 1:积分账户 2:钱包账户
    total_amount BIGINT NOT NULL DEFAULT 0,
    available_amount BIGINT NOT NULL DEFAULT 0,
    frozen_amount BIGINT NOT NULL DEFAULT 0,
    status SMALLINT NOT NULL DEFAULT 1,  -- 1:正常 2:冻结
    remarks TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_account_type (account_type),
    INDEX idx_status (status)
);
```

### 2. account_transactions 表 (交易记录)

```sql
CREATE TABLE account_transactions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    account_id BIGINT NOT NULL,
    user_id BIGINT NULL,
    telegram_id BIGINT NOT NULL,
    invited_telegram_id BIGINT NULL,
    account_type SMALLINT NOT NULL,  -- 1:积分账户 2:钱包账户
    transaction_type SMALLINT NOT NULL,  -- 交易类型
    amount BIGINT NOT NULL,
    balance BIGINT NOT NULL,
    source_id VARCHAR(64) NULL,
    group_id BIGINT NULL,
    remarks TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    is_deleted TINYINT NOT NULL DEFAULT 0,
    INDEX idx_account_id (account_id),
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_transaction_type (transaction_type),
    INDEX idx_account_type (account_type)
);
```

## 交易类型定义

### 现有交易类型
- 1: 充值
- 2: 消费
- 3: 转账
- 4: 签到奖励
- 5: 活动奖励
- 6: 冻结
- 7: 解冻

### 钓鱼系统新增交易类型
- **20: 钓鱼费用** - 使用钓鱼竿消耗的积分
- **21: 钓鱼奖励** - 钓到普通鱼获得的积分
- **22: 传说鱼奖励** - 钓到传说鱼获得的积分

## 钓鱼系统集成逻辑

### 1. 账户操作

钓鱼系统使用 `account_type = 1` (积分账户) 进行所有操作：

```python
# 获取用户积分账户
account = await account_crud.get_by_telegram_id_and_type(
    session, 
    telegram_id, 
    account_type=1  # 积分账户
)
```

### 2. 积分扣除 (钓鱼费用)

```python
# 扣除钓鱼费用
account.available_amount -= rod_cost
account.total_amount -= rod_cost

# 记录交易
await transaction_crud.create(
    session=session,
    account_id=account.id,
    telegram_id=telegram_id,
    account_type=1,  # 积分账户
    transaction_type=20,  # 钓鱼费用
    amount=-rod_cost,
    balance=account.available_amount,
    remarks=f"使用{rod_name}钓鱼"
)
```

### 3. 积分奖励 (钓鱼收获)

```python
# 增加积分奖励
account.available_amount += earned_points
account.total_amount += earned_points

# 确定交易类型
transaction_type = 22 if is_legendary else 21

# 记录交易
await transaction_crud.create(
    session=session,
    account_id=account.id,
    telegram_id=telegram_id,
    account_type=1,  # 积分账户
    transaction_type=transaction_type,
    amount=earned_points,
    balance=account.available_amount,
    remarks=f"钓到{fish_name}"
)
```

## 查询示例

### 1. 获取用户积分余额

```sql
SELECT available_amount 
FROM accounts 
WHERE telegram_id = ? AND account_type = 1 AND status = 1;
```

### 2. 获取钓鱼历史记录

```sql
SELECT * FROM account_transactions 
WHERE telegram_id = ? 
  AND account_type = 1 
  AND transaction_type IN (20, 21, 22)
ORDER BY id DESC 
LIMIT 10;
```

### 3. 统计钓鱼收益

```sql
SELECT 
    SUM(CASE WHEN transaction_type = 20 THEN amount ELSE 0 END) as total_cost,
    SUM(CASE WHEN transaction_type IN (21, 22) THEN amount ELSE 0 END) as total_reward,
    SUM(amount) as net_profit
FROM account_transactions 
WHERE telegram_id = ? 
  AND account_type = 1 
  AND transaction_type IN (20, 21, 22);
```

## 数据一致性保证

### 1. 事务处理

所有钓鱼操作都在数据库事务中执行：

```python
async with self.uow:
    # 扣除费用
    account.available_amount -= cost
    await account_crud.update(session, account)
    
    # 记录扣除交易
    await transaction_crud.create(...)
    
    # 钓鱼逻辑
    if success:
        # 增加奖励
        account.available_amount += reward
        await account_crud.update(session, account)
        
        # 记录奖励交易
        await transaction_crud.create(...)
    
    await self.uow.commit()
```

### 2. 余额验证

每次操作后都会更新并记录 `balance` 字段，确保数据一致性：

```python
# 记录交易时包含交易后余额
await transaction_crud.create(
    ...,
    balance=account.available_amount,  # 交易后的余额
    ...
)
```

## 扩展建议

### 1. 添加钓鱼统计表

可以创建专门的钓鱼统计表来优化查询性能：

```sql
CREATE TABLE fishing_statistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    telegram_id BIGINT NOT NULL,
    total_fishing_count INT NOT NULL DEFAULT 0,
    total_cost BIGINT NOT NULL DEFAULT 0,
    total_reward BIGINT NOT NULL DEFAULT 0,
    legendary_fish_count INT NOT NULL DEFAULT 0,
    last_fishing_time TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_telegram_id (telegram_id)
);
```

### 2. 添加钓鱼配置表

可以创建钓鱼配置表来支持动态配置：

```sql
CREATE TABLE fishing_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(64) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

## 注意事项

1. **账户状态检查**: 钓鱼前需要检查账户状态是否为正常(1)
2. **积分余额检查**: 确保用户有足够积分进行钓鱼
3. **事务回滚**: 任何操作失败都需要回滚事务
4. **日志记录**: 重要操作需要记录详细日志
5. **性能优化**: 大量用户同时钓鱼时需要考虑数据库性能 