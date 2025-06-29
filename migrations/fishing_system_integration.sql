-- 钓鱼系统数据库集成迁移文件
-- 为现有的 account_transactions 表添加钓鱼相关的交易类型说明

-- 添加钓鱼系统相关的交易类型注释
-- 注意：这些交易类型已经在代码中定义，这里只是添加说明

/*
交易类型说明：

现有交易类型：
1: 充值
2: 消费  
3: 转账
4: 签到奖励
5: 活动奖励
6: 冻结
7: 解冻

钓鱼系统新增交易类型：
20: 钓鱼费用 - 使用钓鱼竿消耗的积分
21: 钓鱼奖励 - 钓到普通鱼获得的积分
22: 传说鱼奖励 - 钓到传说鱼获得的积分
*/

-- 可选：创建钓鱼统计表（用于性能优化）
-- 如果不需要，可以注释掉以下代码

/*
CREATE TABLE IF NOT EXISTS fishing_statistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    telegram_id BIGINT NOT NULL,
    total_fishing_count INT NOT NULL DEFAULT 0,
    total_cost BIGINT NOT NULL DEFAULT 0,
    total_reward BIGINT NOT NULL DEFAULT 0,
    legendary_fish_count INT NOT NULL DEFAULT 0,
    last_fishing_time TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_last_fishing_time (last_fishing_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
*/

-- 可选：创建钓鱼配置表（用于动态配置）
-- 如果不需要，可以注释掉以下代码

/*
CREATE TABLE IF NOT EXISTS fishing_config (
    id INT PRIMARY KEY AUTO_INCREMENT,
    config_key VARCHAR(64) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- 插入默认配置
INSERT INTO fishing_config (config_key, config_value, description) VALUES
('legendary_fish_probability', '0.001', '传说鱼出现概率'),
('fishing_failure_probability', '0.05', '钓鱼失败概率'),
('notification_groups', '', '传说鱼通知群组ID，逗号分隔'),
('subscription_link', '', '订阅号链接');
*/

-- 创建钓鱼统计视图（可选）
-- 用于快速查询用户的钓鱼统计信息

/*
CREATE OR REPLACE VIEW fishing_user_stats AS
SELECT 
    at.telegram_id,
    COUNT(CASE WHEN at.transaction_type = 20 THEN 1 END) as fishing_count,
    SUM(CASE WHEN at.transaction_type = 20 THEN ABS(at.amount) ELSE 0 END) as total_cost,
    SUM(CASE WHEN at.transaction_type IN (21, 22) THEN at.amount ELSE 0 END) as total_reward,
    SUM(at.amount) as net_profit,
    COUNT(CASE WHEN at.transaction_type = 22 THEN 1 END) as legendary_count,
    MAX(at.created_at) as last_fishing_time
FROM account_transactions at
WHERE at.account_type = 1 
  AND at.transaction_type IN (20, 21, 22)
  AND at.is_deleted = 0
GROUP BY at.telegram_id;
*/

-- 添加索引优化（如果不存在）
-- 这些索引可能已经存在，如果不存在会自动创建

-- 为钓鱼相关查询优化索引
-- ALTER TABLE account_transactions ADD INDEX IF NOT EXISTS idx_fishing_query (telegram_id, account_type, transaction_type, created_at);

-- 为账户查询优化索引  
-- ALTER TABLE accounts ADD INDEX IF NOT EXISTS idx_fishing_account (telegram_id, account_type, status);

-- 验证现有数据
-- 检查是否有用户已经有积分账户

/*
SELECT 
    COUNT(*) as total_accounts,
    COUNT(CASE WHEN account_type = 1 THEN 1 END) as points_accounts,
    COUNT(CASE WHEN account_type = 2 THEN 1 END) as wallet_accounts
FROM accounts 
WHERE is_deleted = 0;
*/

-- 检查现有交易记录
/*
SELECT 
    transaction_type,
    COUNT(*) as count,
    SUM(amount) as total_amount
FROM account_transactions 
WHERE account_type = 1 
  AND is_deleted = 0
GROUP BY transaction_type
ORDER BY transaction_type;
*/ 