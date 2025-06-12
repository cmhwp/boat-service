from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `realname_auth` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '认证ID',
    `user_id` BIGINT NOT NULL UNIQUE COMMENT '用户ID',
    `real_name` VARCHAR(50) NOT NULL COMMENT '真实姓名',
    `id_card` VARCHAR(20) NOT NULL UNIQUE COMMENT '身份证号',
    `front_image` VARCHAR(255) NOT NULL COMMENT '身份证正面照片',
    `back_image` VARCHAR(255) NOT NULL COMMENT '身份证背面照片',
    `status` VARCHAR(8) NOT NULL COMMENT '认证状态' DEFAULT 'pending',
    `reject_reason` LONGTEXT COMMENT '拒绝原因',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='实名认证表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `realname_auth`;"""
