# 开奖系统与基类集成说明

## 概述

开奖系统已成功集成到你的项目基类架构中，所有模型都继承自 `bot.models.base.Base` 类，确保了一致性和可维护性。

## 基类集成详情

### 1. 继承关系

所有开奖系统模型都继承自你的 `Base` 类：

```python
from bot.models.base import Base

class LotteryDraw(Base):
    # 开奖记录模型
    
class LotteryBet(Base):
    # 投注记录模型
    
class LotteryCashback(Base):
    # 返水记录模型
```

### 2. 通用字段

所有模型自动包含以下通用字段（来自 `Base` 类）：

- `created_at`: 创建时间（TIMESTAMP，自动设置）
- `updated_at`: 更新时间（TIMESTAMP，自动更新）
- `deleted_at`: 删除时间（TIMESTAMP，可为空）
- `is_deleted`: 是否删除（BOOLEAN，默认False）

### 3. 字段类型映射

使用你的 `bot.models.fields` 中定义的字段类型：

```python
from bot.models.fields import (
    bigint_pk,      # 主键字段
    timestamp,      # 时间戳字段
    is_deleted,     # 软删除字段
    bigint_field,   # 大整数字段
    varchar_field,  # 字符串字段
    text_field      # 文本字段
)
```

## 模型字段对比

### 更新前 vs 更新后

#### LotteryDraw 模型

**更新前：**
```python
id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
created_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now)
updated_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False, default=datetime.now, onupdate=datetime.now)
```

**更新后：**
```python
id: Mapped[bigint_pk]
created_at: Mapped[timestamp]  # 来自Base类
updated_at: Mapped[timestamp]  # 来自Base类
deleted_at: Mapped[datetime | None]  # 来自Base类
is_deleted: Mapped[is_deleted]  # 来自Base类
```

#### LotteryBet 模型

**更新前：**
```python
telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
bet_type: Mapped[str] = mapped_column(String(20), nullable=False)
bet_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
```

**更新后：**
```python
telegram_id: Mapped[bigint_field]
bet_type: Mapped[varchar_field(20)]
bet_amount: Mapped[bigint_field]
```

## 数据库表结构

### 更新后的表结构

所有表都包含通用字段：

```sql
-- 开奖记录表
CREATE TABLE lottery_draws (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    -- ... 业务字段 ...
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    -- ... 索引 ...
    INDEX idx_created_at (created_at),
    INDEX idx_is_deleted (is_deleted)
);
```

## 优势

### 1. 一致性
- 所有模型使用相同的字段定义
- 统一的命名规范
- 一致的数据库结构

### 2. 可维护性
- 字段类型集中管理
- 修改字段类型只需更新 `fields.py`
- 减少重复代码

### 3. 功能增强
- 自动软删除支持
- 统一的时间戳管理
- 更好的索引优化

### 4. 扩展性
- 易于添加新的通用字段
- 支持字段级别的配置
- 便于后续功能扩展

## 使用示例

### 创建模型实例

```python
# 创建开奖记录
draw = LotteryDraw(
    draw_number="202401011000",
    result=7,
    total_bets=50000,
    total_payout=30000,
    profit=20000,
    status=2,
    draw_time=datetime.now(),
    remarks="正常开奖"
)
# created_at, updated_at, is_deleted 自动设置
```

### 查询模型

```python
# 查询未删除的开奖记录
draws = await session.execute(
    select(LotteryDraw).where(LotteryDraw.is_deleted == False)
)

# 按创建时间排序
draws = await session.execute(
    select(LotteryDraw).order_by(LotteryDraw.created_at.desc())
)
```

### 软删除

```python
# 软删除记录
draw.is_deleted = True
draw.deleted_at = datetime.now()
await session.commit()
```

## 迁移说明

### 数据库迁移

如果已有数据库表，需要执行以下SQL添加通用字段：

```sql
-- 为现有表添加通用字段
ALTER TABLE lottery_draws 
ADD COLUMN deleted_at TIMESTAMP NULL COMMENT '删除时间',
ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否删除',
ADD INDEX idx_created_at (created_at),
ADD INDEX idx_is_deleted (is_deleted);

ALTER TABLE lottery_bets 
ADD COLUMN deleted_at TIMESTAMP NULL COMMENT '删除时间',
ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否删除',
ADD INDEX idx_is_deleted (is_deleted);

ALTER TABLE lottery_cashbacks 
ADD COLUMN deleted_at TIMESTAMP NULL COMMENT '删除时间',
ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否删除',
ADD INDEX idx_is_deleted (is_deleted);
```

## 测试验证

运行测试脚本验证集成：

```bash
# 运行开奖系统测试
python test_lottery.py

# 运行演示脚本
python lottery_demo_with_base.py
```

## 总结

开奖系统已完全集成到你的基类架构中，提供了：

1. **统一的字段管理** - 使用 `fields.py` 中定义的字段类型
2. **自动时间戳** - 创建和更新时间自动管理
3. **软删除支持** - 支持数据软删除而不物理删除
4. **一致的索引** - 统一的索引策略
5. **更好的维护性** - 代码更简洁，更易维护

这种集成确保了开奖系统与项目其他部分的一致性，并为未来的功能扩展提供了良好的基础。 