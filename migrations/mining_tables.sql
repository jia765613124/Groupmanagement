-- 挖矿系统数据库表结构迁移文件

-- 创建矿工卡记录表
CREATE TABLE IF NOT EXISTS mining_cards (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    telegram_id BIGINT NOT NULL COMMENT 'Telegram用户ID',
    card_type VARCHAR(20) NOT NULL COMMENT '矿工卡类型(青铜/白银/黄金/钻石)',
    cost_usdt BIGINT NOT NULL COMMENT '购买价格(USDT，单位：0.0001U)',
    daily_points BIGINT NOT NULL COMMENT '每日挖矿积分',
    total_days INT NOT NULL COMMENT '总挖矿天数',
    remaining_days INT NOT NULL COMMENT '剩余挖矿天数',
    total_points BIGINT NOT NULL COMMENT '总可获得积分',
    earned_points BIGINT NOT NULL DEFAULT 0 COMMENT '已获得积分',
    status SMALLINT NOT NULL DEFAULT 1 COMMENT '状态(1:挖矿中 2:已完成 3:已过期)',
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    end_time TIMESTAMP NOT NULL COMMENT '结束时间',
    last_reward_time TIMESTAMP NULL COMMENT '最后奖励时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除',
    deleted_at TIMESTAMP NULL COMMENT '删除时间',
    remarks TEXT NULL COMMENT '备注',
    
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_card_type (card_type),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time),
    INDEX idx_end_time (end_time),
    INDEX idx_last_reward_time (last_reward_time),
    INDEX idx_telegram_card_type (telegram_id, card_type),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='矿工卡记录表';

-- 创建挖矿奖励记录表
CREATE TABLE IF NOT EXISTS mining_rewards (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    mining_card_id BIGINT NOT NULL COMMENT '矿工卡ID',
    telegram_id BIGINT NOT NULL COMMENT 'Telegram用户ID',
    card_type VARCHAR(20) NOT NULL COMMENT '矿工卡类型',
    reward_points BIGINT NOT NULL COMMENT '奖励积分',
    reward_day INT NOT NULL COMMENT '奖励天数(第几天)',
    reward_date TIMESTAMP NOT NULL COMMENT '奖励日期',
    status SMALLINT NOT NULL DEFAULT 1 COMMENT '状态(1:待领取 2:已领取)',
    claimed_time TIMESTAMP NULL COMMENT '领取时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除',
    deleted_at TIMESTAMP NULL COMMENT '删除时间',
    remarks TEXT NULL COMMENT '备注',
    
    INDEX idx_mining_card_id (mining_card_id),
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_card_type (card_type),
    INDEX idx_status (status),
    INDEX idx_reward_date (reward_date),
    INDEX idx_claimed_time (claimed_time),
    INDEX idx_telegram_status (telegram_id, status),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='挖矿奖励记录表';

-- 创建挖矿统计表
CREATE TABLE IF NOT EXISTS mining_statistics (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    telegram_id BIGINT NOT NULL UNIQUE COMMENT 'Telegram用户ID',
    total_cards_purchased INT NOT NULL DEFAULT 0 COMMENT '总购买矿工卡数量',
    total_cost_usdt BIGINT NOT NULL DEFAULT 0 COMMENT '总花费USDT(单位：0.0001U)',
    total_earned_points BIGINT NOT NULL DEFAULT 0 COMMENT '总获得积分',
    bronze_cards INT NOT NULL DEFAULT 0 COMMENT '青铜矿工卡数量',
    silver_cards INT NOT NULL DEFAULT 0 COMMENT '白银矿工卡数量',
    gold_cards INT NOT NULL DEFAULT 0 COMMENT '黄金矿工卡数量',
    diamond_cards INT NOT NULL DEFAULT 0 COMMENT '钻石矿工卡数量',
    last_mining_time TIMESTAMP NULL COMMENT '最后挖矿时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    is_deleted TINYINT(1) DEFAULT 0 COMMENT '是否删除',
    deleted_at TIMESTAMP NULL COMMENT '删除时间',
    remarks TEXT NULL COMMENT '备注',
    
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_last_mining_time (last_mining_time),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='挖矿统计表';

-- 为现有的 account_transactions 表添加挖矿相关的交易类型说明
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

钓鱼系统交易类型：
20: 钓鱼费用 - 使用钓鱼竿消耗的积分
21: 钓鱼奖励 - 钓到普通鱼获得的积分
22: 传说鱼奖励 - 钓到传说鱼获得的积分

挖矿系统新增交易类型：
40: 购买矿工卡 - 使用USDT购买矿工卡
41: 挖矿奖励 - 领取挖矿获得的积分
42: 矿工卡过期 - 矿工卡过期处理
*/

-- 插入示例数据（可选）
-- 注意：在实际部署时，这些示例数据应该被删除或注释掉

/*
-- 插入示例矿工卡记录
INSERT INTO mining_cards (telegram_id, card_type, cost_usdt, daily_points, total_days, remaining_days, total_points, earned_points, status, start_time, end_time, remarks) VALUES
(123456789, '青铜', 5000, 5000, 3, 2, 15000, 5000, 1, NOW(), DATE_ADD(NOW(), INTERVAL 3 DAY), '示例青铜矿工卡'),
(123456789, '白银', 10000, 10000, 3, 1, 30000, 20000, 1, NOW(), DATE_ADD(NOW(), INTERVAL 3 DAY), '示例白银矿工卡');

-- 插入示例挖矿奖励记录
INSERT INTO mining_rewards (mining_card_id, telegram_id, card_type, reward_points, reward_day, reward_date, status, remarks) VALUES
(1, 123456789, '青铜', 5000, 1, DATE_SUB(NOW(), INTERVAL 1 DAY), 1, '青铜矿工卡第1天奖励'),
(2, 123456789, '白银', 10000, 1, DATE_SUB(NOW(), INTERVAL 1 DAY), 1, '白银矿工卡第1天奖励'),
(2, 123456789, '白银', 10000, 2, NOW(), 1, '白银矿工卡第2天奖励');

-- 插入示例挖矿统计记录
INSERT INTO mining_statistics (telegram_id, total_cards_purchased, total_cost_usdt, total_earned_points, bronze_cards, silver_cards, gold_cards, diamond_cards, last_mining_time, remarks) VALUES
(123456789, 2, 15000, 25000, 1, 1, 0, 0, NOW(), '示例用户挖矿统计');
*/ 