from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `merchant` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '商家ID',
    `merchant_name` VARCHAR(100) NOT NULL UNIQUE COMMENT '商家名称',
    `license_number` VARCHAR(50) NOT NULL UNIQUE COMMENT '营业执照号',
    `license_image` VARCHAR(255) NOT NULL COMMENT '营业执照图片',
    `contact_phone` VARCHAR(20) NOT NULL COMMENT '联系电话',
    `address` VARCHAR(255) COMMENT '地址',
    `description` LONGTEXT COMMENT '描述',
    `status` VARCHAR(9) NOT NULL COMMENT '状态' DEFAULT 'pending',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL UNIQUE COMMENT '关联用户',
    CONSTRAINT `fk_merchant_users_498e5ea1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='商家表';
        CREATE TABLE IF NOT EXISTS `merchant_audit` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '审核ID',
    `audit_result` VARCHAR(8) NOT NULL COMMENT '审核结果',
    `comment` LONGTEXT COMMENT '审核意见',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `admin_id` INT NOT NULL COMMENT '审核管理员',
    `merchant_id` BIGINT NOT NULL COMMENT '关联商家',
    CONSTRAINT `fk_merchant_users_10f3496c` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_merchant_merchant_954c9ba9` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='商家审核记录';
        CREATE TABLE IF NOT EXISTS `crew` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '船员ID',
    `boat_license` VARCHAR(50) NOT NULL UNIQUE COMMENT '船员证号',
    `status` VARCHAR(8) NOT NULL COMMENT '状态' DEFAULT 'active',
    `rating` DECIMAL(3,2) NOT NULL COMMENT '评分' DEFAULT 0.00,
    `join_time` DATETIME(6) NOT NULL COMMENT '加入时间' DEFAULT CURRENT_TIMESTAMP(6),
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '关联商家',
    `user_id` INT NOT NULL UNIQUE COMMENT '关联用户',
    CONSTRAINT `fk_crew_merchant_2979f907` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_users_489b8481` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船员表';
        CREATE TABLE IF NOT EXISTS `crew_application` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '申请ID',
    `status` VARCHAR(8) NOT NULL COMMENT '申请状态' DEFAULT 'pending',
    `apply_time` DATETIME(6) NOT NULL COMMENT '申请时间' DEFAULT CURRENT_TIMESTAMP(6),
    `handle_time` DATETIME(6) COMMENT '处理时间',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '申请商家',
    `user_id` INT NOT NULL COMMENT '申请用户',
    UNIQUE KEY `uid_crew_applic_user_id_8d03fc` (`user_id`, `merchant_id`),
    CONSTRAINT `fk_crew_app_merchant_4eec249e` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_app_users_0786ee93` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船员申请表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `merchant`;
        DROP TABLE IF EXISTS `crew`;
        DROP TABLE IF EXISTS `merchant_audit`;
        DROP TABLE IF EXISTS `crew_application`;"""
