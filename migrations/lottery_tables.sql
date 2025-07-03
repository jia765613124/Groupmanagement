-- 开奖系统数据库表结构

-- 开奖记录表
CREATE TABLE IF NOT EXISTS lottery_draws (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    group_id BIGINT NOT NULL COMMENT '群组ID',
    game_type VARCHAR(20) NOT NULL COMMENT '游戏类型',
    draw_number VARCHAR(32) NOT NULL COMMENT '期号',
    result INT NOT NULL COMMENT '开奖结果(0-9)',
    total_bets BIGINT NOT NULL DEFAULT 0 COMMENT '总投注金额',
    total_payout BIGINT NOT NULL DEFAULT 0 COMMENT '总派奖金额',
    profit BIGINT NOT NULL DEFAULT 0 COMMENT '盈亏金额',
    status SMALLINT NOT NULL DEFAULT 1 COMMENT '状态(1:进行中 2:已开奖)',
    draw_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '开奖时间',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否删除',
    remarks TEXT NULL COMMENT '备注',
    INDEX idx_group_game (group_id, game_type),
    INDEX idx_draw_number (group_id, game_type, draw_number),
    INDEX idx_draw_time (draw_time),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_is_deleted (is_deleted),
    UNIQUE KEY uk_group_game_draw (group_id, game_type, draw_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='开奖记录表';

-- 投注记录表
CREATE TABLE IF NOT EXISTS lottery_bets (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    group_id BIGINT NOT NULL COMMENT '群组ID',
    game_type VARCHAR(20) NOT NULL COMMENT '游戏类型',
    draw_number VARCHAR(32) NOT NULL COMMENT '期号',
    telegram_id BIGINT NOT NULL COMMENT 'Telegram用户ID',
    bet_type VARCHAR(20) NOT NULL COMMENT '投注类型',
    bet_amount BIGINT NOT NULL COMMENT '投注金额',
    odds DECIMAL(10,2) NOT NULL COMMENT '赔率',
    is_win BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否中奖',
    win_amount BIGINT NOT NULL DEFAULT 0 COMMENT '中奖金额',
    cashback_amount BIGINT NOT NULL DEFAULT 0 COMMENT '返水金额',
    cashback_claimed BOOLEAN NOT NULL DEFAULT FALSE COMMENT '返水是否已领取',
    cashback_expire_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '返水过期时间',
    status SMALLINT NOT NULL DEFAULT 1 COMMENT '状态(1:投注中 2:已开奖 3:已结算)',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否删除',
    remarks TEXT NULL COMMENT '备注',
    INDEX idx_group_game (group_id, game_type),
    INDEX idx_draw_number (group_id, game_type, draw_number),
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_bet_type (bet_type),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_cashback_expire (cashback_expire_time),
    INDEX idx_is_deleted (is_deleted),
    UNIQUE KEY uk_group_game_draw_user_bet (group_id, game_type, draw_number, telegram_id, bet_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='投注记录表';

-- 返水记录表
CREATE TABLE IF NOT EXISTS lottery_cashbacks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '主键ID',
    group_id BIGINT NOT NULL COMMENT '群组ID',
    game_type VARCHAR(20) NOT NULL COMMENT '游戏类型',
    bet_id BIGINT NOT NULL COMMENT '投注记录ID',
    telegram_id BIGINT NOT NULL COMMENT 'Telegram用户ID',
    amount BIGINT NOT NULL COMMENT '返水金额',
    status SMALLINT NOT NULL DEFAULT 1 COMMENT '状态(1:待领取 2:已领取)',
    claimed_at TIMESTAMP NULL COMMENT '领取时间',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    deleted_at TIMESTAMP NULL COMMENT '删除时间',
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否删除',
    remarks TEXT NULL COMMENT '备注',
    INDEX idx_group_game (group_id, game_type),
    INDEX idx_bet_id (bet_id),
    INDEX idx_telegram_id (telegram_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    INDEX idx_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='返水记录表';

-- 添加外键约束（可选）
-- ALTER TABLE lottery_bets ADD CONSTRAINT fk_lottery_bets_draw_number 
--     FOREIGN KEY (draw_number) REFERENCES lottery_draws(draw_number) ON DELETE CASCADE;

-- ALTER TABLE lottery_cashbacks ADD CONSTRAINT fk_lottery_cashbacks_bet_id 
--     FOREIGN KEY (bet_id) REFERENCES lottery_bets(id) ON DELETE CASCADE; 