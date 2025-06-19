from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `cart` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '购物车ID',
    `quantity` INT NOT NULL COMMENT '商品数量',
    `created_at` DATETIME(6) NOT NULL COMMENT '添加时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `product_id` BIGINT NOT NULL COMMENT '商品',
    `user_id` INT NOT NULL COMMENT '用户',
    UNIQUE KEY `uid_cart_user_id_d2f7dd` (`user_id`, `product_id`),
    CONSTRAINT `fk_cart_product_92186a63` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cart_users_ee2917eb` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='购物车表';
        CREATE TABLE IF NOT EXISTS `order` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
    `order_number` VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号',
    `total_amount` DECIMAL(12,2) NOT NULL COMMENT '订单总金额',
    `discount_amount` DECIMAL(10,2) NOT NULL COMMENT '优惠金额' DEFAULT 0,
    `shipping_fee` DECIMAL(8,2) NOT NULL COMMENT '运费' DEFAULT 0,
    `final_amount` DECIMAL(12,2) NOT NULL COMMENT '实付金额',
    `status` VARCHAR(9) NOT NULL COMMENT '订单状态' DEFAULT 'pending',
    `payment_method` VARCHAR(8) COMMENT '支付方式',
    `receiver_name` VARCHAR(50) NOT NULL COMMENT '收货人姓名',
    `receiver_phone` VARCHAR(20) NOT NULL COMMENT '收货人电话',
    `receiver_address` VARCHAR(255) NOT NULL COMMENT '收货地址',
    `user_notes` LONGTEXT COMMENT '用户备注',
    `merchant_notes` LONGTEXT COMMENT '商家备注',
    `cancel_reason` LONGTEXT COMMENT '取消原因',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `paid_at` DATETIME(6) COMMENT '支付时间',
    `shipped_at` DATETIME(6) COMMENT '发货时间',
    `delivered_at` DATETIME(6) COMMENT '送达时间',
    `completed_at` DATETIME(6) COMMENT '完成时间',
    `cancelled_at` DATETIME(6) COMMENT '取消时间',
    `merchant_id` BIGINT NOT NULL COMMENT '商家',
    `user_id` INT NOT NULL COMMENT '用户',
    CONSTRAINT `fk_order_merchant_cbdbd06e` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_order_users_3768b2b0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='订单表';
        CREATE TABLE IF NOT EXISTS `order_item` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '订单项ID',
    `quantity` INT NOT NULL COMMENT '商品数量',
    `unit_price` DECIMAL(10,2) NOT NULL COMMENT '单价',
    `total_price` DECIMAL(12,2) NOT NULL COMMENT '小计',
    `product_name` VARCHAR(100) NOT NULL COMMENT '商品名称',
    `product_unit` VARCHAR(20) NOT NULL COMMENT '计量单位',
    `product_image` VARCHAR(255) COMMENT '商品图片',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `order_id` BIGINT NOT NULL COMMENT '订单',
    `product_id` BIGINT NOT NULL COMMENT '商品',
    CONSTRAINT `fk_order_it_order_23934b93` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_order_it_product_10ab7db4` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='订单项表';
        CREATE TABLE IF NOT EXISTS `payment_record` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '支付记录ID',
    `payment_number` VARCHAR(32) NOT NULL UNIQUE COMMENT '支付单号',
    `amount` DECIMAL(12,2) NOT NULL COMMENT '支付金额',
    `payment_method` VARCHAR(8) NOT NULL COMMENT '支付方式',
    `is_success` BOOL NOT NULL COMMENT '是否支付成功' DEFAULT 0,
    `third_party_number` VARCHAR(64) COMMENT '第三方支付单号',
    `created_at` DATETIME(6) NOT NULL COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `paid_at` DATETIME(6) COMMENT '支付时间',
    `order_id` BIGINT NOT NULL COMMENT '订单',
    `user_id` INT NOT NULL COMMENT '用户',
    CONSTRAINT `fk_payment__order_66b04302` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_payment__users_e84cb460` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='支付记录表';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `payment_record`;
        DROP TABLE IF EXISTS `cart`;
        DROP TABLE IF EXISTS `order`;
        DROP TABLE IF EXISTS `order_item`;"""
