/*
 Navicat Premium Dump SQL

 Source Server         : 我的电脑
 Source Server Type    : MySQL
 Source Server Version : 80403 (8.4.3)
 Source Host           : localhost:3306
 Source Schema         : tg_search_bot

 Target Server Type    : MySQL
 Target Server Version : 80403 (8.4.3)
 File Encoding         : 65001

 Date: 13/04/2025 21:08:48
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for alembic_version
-- ----------------------------
DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------
-- Table structure for t_search_base_config
-- ----------------------------
DROP TABLE IF EXISTS `t_search_base_config`;
CREATE TABLE `t_search_base_config` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `config_key` varchar(100) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `config_type` enum('system','business','security','notification') NOT NULL COMMENT '配置类型',
  `description` text COMMENT '描述',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`),
  KEY `idx_config_type` (`config_type`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='基础配置表';

-- ----------------------------
-- Table structure for t_search_channels
-- ----------------------------
DROP TABLE IF EXISTS `t_search_channels`;
CREATE TABLE `t_search_channels` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `channel_id` bigint NOT NULL COMMENT 'Telegram频道ID',
  `channel_name` varchar(255) NOT NULL COMMENT '频道名称',
  `channel_username` varchar(255) DEFAULT NULL COMMENT '频道用户名',
  `description` text COMMENT '频道描述',
  `member_count` int DEFAULT '0' COMMENT '成员数量',
  `is_public` tinyint(1) DEFAULT '1' COMMENT '是否公开',
  `is_monitored` tinyint(1) DEFAULT '0' COMMENT '是否监控',
  `monitor_priority` int DEFAULT '100' COMMENT '监控优先级',
  `monitor_interval` int DEFAULT '300' COMMENT '监控间隔(秒)',
  `last_monitor_time` timestamp NULL DEFAULT NULL COMMENT '最后监控时间',
  `areas` json DEFAULT NULL COMMENT '覆盖地区',
  `area_level` tinyint DEFAULT NULL COMMENT '地区级别',
  `is_all_area` tinyint(1) DEFAULT '0' COMMENT '是否全地区',
  `status` enum('active','inactive','banned') DEFAULT 'active' COMMENT '状态',
  `last_activity_at` timestamp NULL DEFAULT NULL COMMENT '最后活动时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_channel_id` (`channel_id`),
  KEY `idx_channel_username` (`channel_username`),
  KEY `idx_is_monitored` (`is_monitored`),
  KEY `idx_status` (`status`),
  KEY `idx_area_level` (`area_level`),
  KEY `idx_last_activity` (`last_activity_at`),
  FULLTEXT KEY `idx_search` (`channel_name`,`description`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='频道表';

-- ----------------------------
-- Table structure for t_search_groups
-- ----------------------------
DROP TABLE IF EXISTS `t_search_groups`;
CREATE TABLE `t_search_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `group_id` bigint NOT NULL COMMENT 'Telegram群组ID',
  `group_name` varchar(255) NOT NULL COMMENT '群组名称',
  `group_username` varchar(255) DEFAULT NULL COMMENT '群组用户名',
  `description` text COMMENT '群组描述',
  `member_count` int DEFAULT '0' COMMENT '成员数量',
  `is_public` tinyint(1) DEFAULT '1' COMMENT '是否公开',
  `is_monitored` tinyint(1) DEFAULT '0' COMMENT '是否监控',
  `monitor_priority` int DEFAULT '100' COMMENT '监控优先级',
  `monitor_interval` int DEFAULT '300' COMMENT '监控间隔(秒)',
  `last_monitor_time` timestamp NULL DEFAULT NULL COMMENT '最后监控时间',
  `areas` json DEFAULT NULL COMMENT '覆盖地区',
  `area_level` tinyint DEFAULT NULL COMMENT '地区级别',
  `is_all_area` tinyint(1) DEFAULT '0' COMMENT '是否全地区',
  `status` enum('active','inactive','banned') DEFAULT 'active' COMMENT '状态',
  `last_activity_at` timestamp NULL DEFAULT NULL COMMENT '最后活动时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_group_id` (`group_id`),
  KEY `idx_group_username` (`group_username`),
  KEY `idx_is_monitored` (`is_monitored`),
  KEY `idx_status` (`status`),
  KEY `idx_area_level` (`area_level`),
  KEY `idx_last_activity` (`last_activity_at`),
  FULLTEXT KEY `idx_search` (`group_name`,`description`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='群组表';

-- ----------------------------
-- Table structure for t_search_messages
-- ----------------------------
DROP TABLE IF EXISTS `t_search_messages`;
CREATE TABLE `t_search_messages` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `message_id` varchar(100) NOT NULL COMMENT '消息ID',
  `message_type` enum('teacher','normal') NOT NULL COMMENT '消息类型',
  `title` text COMMENT '消息标题',
  `content` text COMMENT '消息内容',
  `matched_rule_id` bigint DEFAULT NULL COMMENT '匹配规则ID',
  `status` enum('active','inactive','deleted') DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  `channel_id` bigint DEFAULT NULL COMMENT '频道ID',
  `group_id` bigint DEFAULT NULL COMMENT '群组ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_message` (`message_id`),
  KEY `idx_message_type` (`message_type`),
  KEY `idx_rule` (`matched_rule_id`),
  KEY `idx_status` (`status`),
  KEY `channel_id` (`channel_id`),
  KEY `group_id` (`group_id`),
  FULLTEXT KEY `idx_content` (`title`,`content`),
  CONSTRAINT `t_search_messages_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `t_search_channels` (`id`) ON DELETE SET NULL,
  CONSTRAINT `t_search_messages_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `t_search_groups` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='消息记录表';

-- ----------------------------
-- Table structure for t_search_monitor_rules
-- ----------------------------
DROP TABLE IF EXISTS `t_search_monitor_rules`;
CREATE TABLE `t_search_monitor_rules` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `rule_name` varchar(100) NOT NULL COMMENT '规则名称',
  `rule_type` enum('regex','keyword') NOT NULL COMMENT '规则类型',
  `match_pattern` text NOT NULL COMMENT '匹配模式',
  `field_type` enum('name','areas','prices','categories','telegram','phone','introduction') NOT NULL COMMENT '字段类型',
  `extract_pattern` text COMMENT '提取模式',
  `is_required` tinyint(1) DEFAULT '0' COMMENT '是否必需',
  `priority` int DEFAULT '100' COMMENT '优先级',
  `status` enum('active','inactive') DEFAULT 'active' COMMENT '状态',
  `monitor_type` enum('teacher','normal') NOT NULL COMMENT '监控类型',
  `source_type` enum('channel','group','teacher') NOT NULL COMMENT '来源类型',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  `channel_id` bigint DEFAULT NULL COMMENT '频道ID',
  `group_id` bigint DEFAULT NULL COMMENT '群组ID',
  PRIMARY KEY (`id`),
  KEY `idx_rule_type` (`rule_type`),
  KEY `idx_field_type` (`field_type`),
  KEY `idx_priority` (`priority`),
  KEY `idx_monitor_type` (`monitor_type`),
  KEY `idx_status` (`status`),
  KEY `channel_id` (`channel_id`),
  KEY `group_id` (`group_id`),
  CONSTRAINT `t_search_monitor_rules_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `t_search_channels` (`id`) ON DELETE SET NULL,
  CONSTRAINT `t_search_monitor_rules_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `t_search_groups` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='监控规则表';

-- ----------------------------
-- Table structure for t_search_resources
-- ----------------------------
DROP TABLE IF EXISTS `t_search_resources`;
CREATE TABLE `t_search_resources` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `message_id` varchar(100) NOT NULL COMMENT '消息ID',
  `title` varchar(255) NOT NULL COMMENT '资源标题',
  `description` text COMMENT '资源描述',
  `url` text COMMENT '资源链接',
  `resource_type` enum('document','video','link','image','audio','archive','presentation','spreadsheet','other') NOT NULL COMMENT '资源类型',
  `file_size` bigint DEFAULT NULL COMMENT '文件大小',
  `file_md5` varchar(32) DEFAULT NULL COMMENT '文件MD5',
  `telegram_file_id` text COMMENT 'Telegram文件ID',
  `download_count` int DEFAULT '0' COMMENT '下载次数',
  `view_count` int DEFAULT '0' COMMENT '查看次数',
  `status` enum('active','inactive','banned') DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  `channel_id` bigint DEFAULT NULL COMMENT '频道ID',
  `group_id` bigint DEFAULT NULL COMMENT '群组ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_resource` (`message_id`),
  KEY `idx_resource_type` (`resource_type`),
  KEY `idx_file_md5` (`file_md5`),
  KEY `idx_status` (`status`),
  KEY `channel_id` (`channel_id`),
  KEY `group_id` (`group_id`),
  FULLTEXT KEY `idx_search` (`title`,`description`),
  CONSTRAINT `t_search_resources_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `t_search_channels` (`id`) ON DELETE SET NULL,
  CONSTRAINT `t_search_resources_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `t_search_groups` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='资源表';

-- ----------------------------
-- Table structure for t_search_teachers
-- ----------------------------
DROP TABLE IF EXISTS `t_search_teachers`;
CREATE TABLE `t_search_teachers` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `name` varchar(100) NOT NULL COMMENT '教师姓名',
  `areas` json DEFAULT NULL COMMENT '地区',
  `prices` json DEFAULT NULL COMMENT '价格',
  `categories` json DEFAULT NULL COMMENT '科目分类',
  `telegram_channel` varchar(255) DEFAULT NULL COMMENT 'Telegram频道',
  `telegram_bot` varchar(255) DEFAULT NULL COMMENT 'Telegram机器人',
  `telegram_contact` varchar(255) DEFAULT NULL COMMENT 'Telegram联系方式',
  `phone` varchar(20) DEFAULT NULL COMMENT '电话',
  `qq` varchar(20) DEFAULT NULL COMMENT 'QQ',
  `wechat` varchar(50) DEFAULT NULL COMMENT '微信',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `source_name` varchar(255) DEFAULT NULL COMMENT '来源名称',
  `message_id` varchar(100) NOT NULL COMMENT '消息ID',
  `message_text` text COMMENT '原始消息内容',
  `found_at` timestamp NULL DEFAULT NULL COMMENT '发现时间',
  `found_count` int DEFAULT '1' COMMENT '发现次数',
  `is_main_source` tinyint(1) DEFAULT '0' COMMENT '是否主要来源',
  `matched_rule_id` bigint DEFAULT NULL COMMENT '匹配规则ID',
  `popularity` int DEFAULT '0' COMMENT '热度',
  `introduction` text COMMENT '简介',
  `report` json DEFAULT NULL COMMENT '报告',
  `notes` text COMMENT '备注',
  `status` enum('active','inactive','verified','unverified') DEFAULT 'unverified' COMMENT '状态',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  `channel_id` bigint DEFAULT NULL COMMENT '频道ID',
  `group_id` bigint DEFAULT NULL COMMENT '群组ID',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`),
  KEY `idx_popularity` (`popularity`),
  KEY `idx_telegram_channel` (`telegram_channel`),
  KEY `idx_telegram_bot` (`telegram_bot`),
  KEY `idx_telegram_contact` (`telegram_contact`),
  KEY `idx_phone` (`phone`),
  KEY `idx_qq` (`qq`),
  KEY `idx_wechat` (`wechat`),
  KEY `idx_email` (`email`),
  KEY `idx_source_name` (`source_name`),
  KEY `idx_message_id` (`message_id`),
  KEY `idx_found_count` (`found_count`),
  KEY `idx_is_main` (`is_main_source`),
  KEY `idx_status` (`status`),
  KEY `channel_id` (`channel_id`),
  KEY `group_id` (`group_id`),
  FULLTEXT KEY `idx_search` (`name`,`introduction`),
  CONSTRAINT `t_search_teachers_ibfk_1` FOREIGN KEY (`channel_id`) REFERENCES `t_search_channels` (`id`) ON DELETE SET NULL,
  CONSTRAINT `t_search_teachers_ibfk_2` FOREIGN KEY (`group_id`) REFERENCES `t_search_groups` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='教师信息表';

-- ----------------------------
-- Table structure for t_search_users
-- ----------------------------
DROP TABLE IF EXISTS `t_search_users`;
CREATE TABLE `t_search_users` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `telegram_id` bigint NOT NULL COMMENT 'Telegram用户ID',
  `username` varchar(64) DEFAULT NULL COMMENT 'Telegram用户名',
  `first_name` varchar(64) DEFAULT NULL COMMENT 'Telegram名字',
  `last_name` varchar(64) DEFAULT NULL COMMENT 'Telegram姓氏',
  `language_code` varchar(10) DEFAULT NULL COMMENT '语言代码',
  `is_premium` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为Telegram高级用户',
  `join_source` enum('private','group') NOT NULL COMMENT '加入来源',
  `source_group_id` bigint DEFAULT NULL COMMENT '来源群组ID',
  `status` enum('active','inactive','banned') DEFAULT 'active' COMMENT '状态',
  `last_active_time` timestamp NULL DEFAULT NULL COMMENT '最后活跃时间',
  `remarks` text COMMENT '备注',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_telegram_id` (`telegram_id`),
  KEY `idx_username` (`username`),
  KEY `idx_status` (`status`),
  KEY `idx_join_source` (`join_source`),
  KEY `idx_source_group` (`source_group_id`),
  KEY `idx_last_active` (`last_active_time`),
  FULLTEXT KEY `idx_search` (`username`,`first_name`,`last_name`,`remarks`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='用户表';

-- ----------------------------
-- Table structure for t_search_user_resource_downloads
-- ----------------------------
DROP TABLE IF EXISTS `t_search_user_resource_downloads`;
CREATE TABLE `t_search_user_resource_downloads` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `user_id` bigint NOT NULL COMMENT '用户ID',
  `resource_id` bigint NOT NULL COMMENT '资源ID',
  `download_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下载时间',
  `ip_address` varchar(45) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` text COMMENT '用户代理',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_resource` (`user_id`,`resource_id`),
  KEY `idx_download_time` (`download_time`),
  KEY `resource_id` (`resource_id`),
  CONSTRAINT `t_search_user_resource_downloads_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `t_search_users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `t_search_user_resource_downloads_ibfk_2` FOREIGN KEY (`resource_id`) REFERENCES `t_search_resources` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='用户资源下载表';

-- ----------------------------
-- Table structure for t_search_user_teacher_follows
-- ----------------------------
DROP TABLE IF EXISTS `t_search_user_teacher_follows`;
CREATE TABLE `t_search_user_teacher_follows` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `teacher_id` bigint NOT NULL COMMENT '教师ID',
  `follow_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '关注时间',
  `status` enum('active','inactive') DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_teacher` (`user_id`,`teacher_id`),
  KEY `idx_follow_time` (`follow_time`),
  KEY `idx_status` (`status`),
  KEY `teacher_id` (`teacher_id`),
  CONSTRAINT `t_search_user_teacher_follows_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `t_search_teachers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='用户教师关注表';

-- ----------------------------
-- Table structure for t_search_resource_forwards
-- ----------------------------
DROP TABLE IF EXISTS `t_search_resource_forwards`;
CREATE TABLE `t_search_resource_forwards` (
  `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `resource_id` bigint NOT NULL COMMENT '资源ID',
  `teacher_id` bigint DEFAULT NULL COMMENT '教师ID',
  `target_type` enum('channel','group') NOT NULL COMMENT '转发目标类型',
  `target_id` bigint NOT NULL COMMENT '转发目标ID',
  `areas` json DEFAULT NULL COMMENT '目标地区',
  `forward_count` int DEFAULT '0' COMMENT '转发次数',
  `last_forward_time` timestamp NULL DEFAULT NULL COMMENT '最后转发时间',
  `status` enum('active','inactive') DEFAULT 'active' COMMENT '状态',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_deleted` tinyint(1) DEFAULT '0' COMMENT '是否删除',
  `deleted_at` timestamp NULL DEFAULT NULL COMMENT '删除时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_resource_target` (`resource_id`,`target_type`,`target_id`),
  KEY `idx_target` (`target_type`,`target_id`),
  KEY `idx_forward_count` (`forward_count`),
  KEY `idx_last_forward` (`last_forward_time`),
  KEY `idx_status` (`status`),
  KEY `teacher_id` (`teacher_id`),
  CONSTRAINT `t_search_resource_forwards_ibfk_1` FOREIGN KEY (`resource_id`) REFERENCES `t_search_resources` (`id`) ON DELETE CASCADE,
  CONSTRAINT `t_search_resource_forwards_ibfk_2` FOREIGN KEY (`teacher_id`) REFERENCES `t_search_teachers` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci ROW_FORMAT=COMPRESSED COMMENT='资源转发表';

SET FOREIGN_KEY_CHECKS = 1;
