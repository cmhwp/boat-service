from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `boat` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '船只ID',
    `name` VARCHAR(100) NOT NULL COMMENT '船只名称',
    `license_number` VARCHAR(50) NOT NULL UNIQUE COMMENT '船只证书号',
    `boat_type` VARCHAR(11) NOT NULL COMMENT '船只类型' DEFAULT 'sightseeing',
    `capacity` INT NOT NULL COMMENT '载客量',
    `hourly_rate` DECIMAL(10,2) NOT NULL COMMENT '小时费率',
    `description` LONGTEXT COMMENT '船只描述',
    `images` JSON NOT NULL COMMENT '船只图片列表',
    `status` VARCHAR(11) NOT NULL COMMENT '状态' DEFAULT 'available',
    `current_location` VARCHAR(255) COMMENT '当前位置',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '所属商家',
    CONSTRAINT `fk_boat_merchant_57327ee0` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船只表';
        CREATE TABLE IF NOT EXISTS `product` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '商品ID',
    `name` VARCHAR(100) NOT NULL COMMENT '商品名称',
    `category` VARCHAR(9) NOT NULL COMMENT '商品分类' DEFAULT 'other',
    `description` LONGTEXT COMMENT '商品描述',
    `price` DECIMAL(10,2) NOT NULL COMMENT '商品价格',
    `stock` INT NOT NULL COMMENT '库存数量' DEFAULT 0,
    `unit` VARCHAR(20) NOT NULL COMMENT '计量单位' DEFAULT '份',
    `images` JSON NOT NULL COMMENT '商品图片列表',
    `rating` DECIMAL(3,2) NOT NULL COMMENT '评分' DEFAULT 0,
    `sales_count` INT NOT NULL COMMENT '销售数量' DEFAULT 0,
    `status` VARCHAR(9) NOT NULL COMMENT '状态' DEFAULT 'available',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '所属商家',
    CONSTRAINT `fk_product_merchant_174d97f6` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='农产品表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `product`;
        DROP TABLE IF EXISTS `boat`;"""
