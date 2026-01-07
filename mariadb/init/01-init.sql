-- MariaDB 初始化脚本
-- 设置字符集和排序规则
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建数据库(如果不存在)
CREATE DATABASE IF NOT EXISTS `tiktok_products` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE `tiktok_products`;

-- 设置时区
SET time_zone = '+08:00';

-- 创建同步日志表
CREATE TABLE IF NOT EXISTS `db_sync_log` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `sync_type` enum('FULL','INCREMENTAL') NOT NULL COMMENT '同步类型: FULL-全量, INCREMENTAL-增量',
  `direction` enum('REMOTE_TO_LOCAL','LOCAL_TO_REMOTE') NOT NULL COMMENT '同步方向',
  `status` enum('SUCCESS','FAILED','IN_PROGRESS') NOT NULL DEFAULT 'IN_PROGRESS' COMMENT '同步状态',
  `start_time` datetime NOT NULL COMMENT '开始时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `duration` int(11) DEFAULT NULL COMMENT '耗时(秒)',
  `tables_synced` int(11) DEFAULT '0' COMMENT '同步的表数量',
  `rows_affected` int(11) DEFAULT '0' COMMENT '影响的行数',
  `error_message` text COMMENT '错误信息',
  `last_sync_position` varchar(255) DEFAULT NULL COMMENT '最后同步位置(用于增量同步)',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_sync_type` (`sync_type`),
  KEY `idx_status` (`status`),
  KEY `idx_start_time` (`start_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据库同步日志表';

-- 创建同步配置表
CREATE TABLE IF NOT EXISTS `db_sync_config` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `table_name` varchar(100) NOT NULL COMMENT '表名',
  `sync_enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用同步',
  `sync_type` enum('FULL','INCREMENTAL') NOT NULL DEFAULT 'INCREMENTAL' COMMENT '同步类型',
  `sync_direction` enum('BOTH','REMOTE_TO_LOCAL','LOCAL_TO_REMOTE') NOT NULL DEFAULT 'BOTH' COMMENT '同步方向',
  `last_sync_time` datetime DEFAULT NULL COMMENT '最后同步时间',
  `last_sync_position` varchar(255) DEFAULT NULL COMMENT '最后同步位置',
  `priority` int(11) NOT NULL DEFAULT '0' COMMENT '同步优先级(数字越大优先级越高)',
  `conflict_resolution` enum('REMOTE_WINS','LOCAL_WINS','SKIP','MANUAL') NOT NULL DEFAULT 'REMOTE_WINS' COMMENT '冲突解决策略',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_table_name` (`table_name`),
  KEY `idx_priority` (`priority`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据库同步配置表';

-- 插入默认同步配置(需要根据实际表结构调整)
INSERT INTO `db_sync_config` (`table_name`, `sync_enabled`, `sync_type`, `sync_direction`, `priority`) VALUES
('stores', 1, 'FULL', 'REMOTE_TO_LOCAL', 95),
('products', 1, 'FULL', 'REMOTE_TO_LOCAL', 90),
('ai_content_items', 1, 'FULL', 'REMOTE_TO_LOCAL', 85),
('product_tags', 1, 'FULL', 'REMOTE_TO_LOCAL', 80),
('product_reviews', 1, 'FULL', 'REMOTE_TO_LOCAL', 75),
('product_variations', 1, 'FULL', 'REMOTE_TO_LOCAL', 70),
('product_videos', 1, 'FULL', 'REMOTE_TO_LOCAL', 65),
('product_images', 1, 'FULL', 'REMOTE_TO_LOCAL', 60)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

SET FOREIGN_KEY_CHECKS = 1;