from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `boat_booking` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '预约ID',
    `booking_number` VARCHAR(32) NOT NULL UNIQUE COMMENT '预约单号',
    `start_time` DATETIME(6) NOT NULL COMMENT '开始时间',
    `end_time` DATETIME(6) NOT NULL COMMENT '结束时间',
    `duration_hours` DECIMAL(4,1) NOT NULL COMMENT '预约时长(小时)',
    `passenger_count` INT NOT NULL COMMENT '乘客人数',
    `hourly_rate` DECIMAL(10,2) NOT NULL COMMENT '小时费率',
    `total_amount` DECIMAL(12,2) NOT NULL COMMENT '总金额',
    `status` VARCHAR(11) NOT NULL COMMENT '预约状态' DEFAULT 'pending',
    `payment_status` VARCHAR(9) NOT NULL COMMENT '支付状态' DEFAULT 'unpaid',
    `contact_name` VARCHAR(50) NOT NULL COMMENT '联系人姓名',
    `contact_phone` VARCHAR(20) NOT NULL COMMENT '联系电话',
    `user_notes` LONGTEXT COMMENT '用户备注',
    `merchant_notes` LONGTEXT COMMENT '商家备注',
    `cancel_reason` LONGTEXT COMMENT '取消原因',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `confirmed_at` DATETIME(6) COMMENT '确认时间',
    `completed_at` DATETIME(6) COMMENT '完成时间',
    `cancelled_at` DATETIME(6) COMMENT '取消时间',
    `assigned_crew_id` BIGINT COMMENT '指派船员',
    `boat_id` BIGINT NOT NULL COMMENT '预约船只',
    `merchant_id` BIGINT NOT NULL COMMENT '商家',
    `user_id` INT NOT NULL COMMENT '预约用户',
    CONSTRAINT `fk_boat_boo_crew_51727bca` FOREIGN KEY (`assigned_crew_id`) REFERENCES `crew` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_boat_boo_boat_f285dce2` FOREIGN KEY (`boat_id`) REFERENCES `boat` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_boat_boo_merchant_0cd1f4b0` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_boat_boo_users_ae766563` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船艇预约订单表';
        CREATE TABLE IF NOT EXISTS `crew_rating` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '评价ID',
    `rating` INT NOT NULL COMMENT '评分(1-5)',
    `comment` LONGTEXT COMMENT '评价内容',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `crew_id` BIGINT NOT NULL COMMENT '被评价船员',
    `user_id` INT NOT NULL COMMENT '评价用户',
    `booking_id` BIGINT NOT NULL UNIQUE COMMENT '关联预约',
    CONSTRAINT `fk_crew_rat_crew_6d91e2c1` FOREIGN KEY (`crew_id`) REFERENCES `crew` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_rat_users_a7a9bc19` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_rat_boat_boo_db3ac55f` FOREIGN KEY (`booking_id`) REFERENCES `boat_booking` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船员评价表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `crew_rating`;
        DROP TABLE IF EXISTS `boat_booking`;"""
