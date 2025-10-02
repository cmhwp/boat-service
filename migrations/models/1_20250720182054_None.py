from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `users` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `email` VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱',
    `password` VARCHAR(255) NOT NULL  COMMENT '密码',
    `phone` VARCHAR(20)   COMMENT '手机号',
    `avatar` VARCHAR(500)   COMMENT '头像URL',
    `role` VARCHAR(8) NOT NULL  COMMENT '用户角色' DEFAULT 'user',
    `is_active` BOOL NOT NULL  COMMENT '是否激活' DEFAULT 1,
    `realname_status` VARCHAR(10) NOT NULL  COMMENT '实名认证状态' DEFAULT 'unverified',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='用户表';
CREATE TABLE IF NOT EXISTS `realname_auth` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '认证ID',
    `user_id` BIGINT NOT NULL UNIQUE COMMENT '用户ID',
    `real_name` VARCHAR(50) NOT NULL  COMMENT '真实姓名',
    `id_card` VARCHAR(20) NOT NULL UNIQUE COMMENT '身份证号',
    `front_image` VARCHAR(255) NOT NULL  COMMENT '身份证正面照片',
    `back_image` VARCHAR(255) NOT NULL  COMMENT '身份证背面照片',
    `status` VARCHAR(8) NOT NULL  COMMENT '认证状态' DEFAULT 'pending',
    `reject_reason` LONGTEXT   COMMENT '拒绝原因',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)
) CHARACTER SET utf8mb4 COMMENT='实名认证表';
CREATE TABLE IF NOT EXISTS `merchant` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '商家ID',
    `merchant_name` VARCHAR(100) NOT NULL UNIQUE COMMENT '商家名称',
    `license_number` VARCHAR(50) NOT NULL UNIQUE COMMENT '营业执照号',
    `license_image` VARCHAR(255) NOT NULL  COMMENT '营业执照图片',
    `contact_phone` VARCHAR(20) NOT NULL  COMMENT '联系电话',
    `address` VARCHAR(255)   COMMENT '地址',
    `description` LONGTEXT   COMMENT '描述',
    `status` VARCHAR(9) NOT NULL  COMMENT '状态' DEFAULT 'pending',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `user_id` INT NOT NULL UNIQUE COMMENT '关联用户',
    CONSTRAINT `fk_merchant_users_498e5ea1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='商家表';
CREATE TABLE IF NOT EXISTS `merchant_audit` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '审核ID',
    `audit_result` VARCHAR(8) NOT NULL  COMMENT '审核结果',
    `comment` LONGTEXT   COMMENT '审核意见',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `admin_id` INT NOT NULL COMMENT '审核管理员',
    `merchant_id` BIGINT NOT NULL COMMENT '关联商家',
    CONSTRAINT `fk_merchant_users_10f3496c` FOREIGN KEY (`admin_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_merchant_merchant_954c9ba9` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='商家审核记录';
CREATE TABLE IF NOT EXISTS `crew` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '船员ID',
    `boat_license` VARCHAR(50) NOT NULL UNIQUE COMMENT '船员证号',
    `status` VARCHAR(8) NOT NULL  COMMENT '状态' DEFAULT 'active',
    `rating` DECIMAL(3,2) NOT NULL  COMMENT '评分' DEFAULT 0.00,
    `join_time` DATETIME(6) NOT NULL  COMMENT '加入时间' DEFAULT CURRENT_TIMESTAMP(6),
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '关联商家',
    `user_id` INT NOT NULL UNIQUE COMMENT '关联用户',
    CONSTRAINT `fk_crew_merchant_2979f907` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_users_489b8481` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船员表';
CREATE TABLE IF NOT EXISTS `crew_application` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '申请ID',
    `status` VARCHAR(8) NOT NULL  COMMENT '申请状态' DEFAULT 'pending',
    `apply_time` DATETIME(6) NOT NULL  COMMENT '申请时间' DEFAULT CURRENT_TIMESTAMP(6),
    `handle_time` DATETIME(6)   COMMENT '处理时间',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '申请商家',
    `user_id` INT NOT NULL COMMENT '申请用户',
    UNIQUE KEY `uid_crew_applic_user_id_8d03fc` (`user_id`, `merchant_id`),
    CONSTRAINT `fk_crew_app_merchant_4eec249e` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_app_users_0786ee93` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船员申请表';
CREATE TABLE IF NOT EXISTS `boat` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '船只ID',
    `name` VARCHAR(100) NOT NULL  COMMENT '船只名称',
    `license_number` VARCHAR(50) NOT NULL UNIQUE COMMENT '船只证书号',
    `boat_type` VARCHAR(11) NOT NULL  COMMENT '船只类型' DEFAULT 'sightseeing',
    `capacity` INT NOT NULL  COMMENT '载客量',
    `hourly_rate` DECIMAL(10,2) NOT NULL  COMMENT '小时费率',
    `description` LONGTEXT   COMMENT '船只描述',
    `images` JSON NOT NULL  COMMENT '船只图片列表',
    `status` VARCHAR(11) NOT NULL  COMMENT '状态' DEFAULT 'available',
    `current_location` VARCHAR(255)   COMMENT '当前位置',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '所属商家',
    CONSTRAINT `fk_boat_merchant_57327ee0` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船只表';
CREATE TABLE IF NOT EXISTS `product` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '商品ID',
    `name` VARCHAR(100) NOT NULL  COMMENT '商品名称',
    `category` VARCHAR(9) NOT NULL  COMMENT '商品分类' DEFAULT 'other',
    `description` LONGTEXT   COMMENT '商品描述',
    `price` DECIMAL(10,2) NOT NULL  COMMENT '商品价格',
    `stock` INT NOT NULL  COMMENT '库存数量' DEFAULT 0,
    `unit` VARCHAR(20) NOT NULL  COMMENT '计量单位' DEFAULT '份',
    `images` JSON NOT NULL  COMMENT '商品图片列表',
    `rating` DECIMAL(3,2) NOT NULL  COMMENT '评分' DEFAULT 0,
    `sales_count` INT NOT NULL  COMMENT '销售数量' DEFAULT 0,
    `status` VARCHAR(9) NOT NULL  COMMENT '状态' DEFAULT 'available',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `merchant_id` BIGINT NOT NULL COMMENT '所属商家',
    CONSTRAINT `fk_product_merchant_174d97f6` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='农产品表';
CREATE TABLE IF NOT EXISTS `boat_booking` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '预约ID',
    `booking_number` VARCHAR(32) NOT NULL UNIQUE COMMENT '预约单号',
    `start_time` DATETIME(6) NOT NULL  COMMENT '开始时间',
    `end_time` DATETIME(6) NOT NULL  COMMENT '结束时间',
    `duration_hours` DECIMAL(4,1) NOT NULL  COMMENT '预约时长(小时)',
    `passenger_count` INT NOT NULL  COMMENT '乘客人数',
    `hourly_rate` DECIMAL(10,2) NOT NULL  COMMENT '小时费率',
    `total_amount` DECIMAL(12,2) NOT NULL  COMMENT '总金额',
    `status` VARCHAR(11) NOT NULL  COMMENT '预约状态' DEFAULT 'pending',
    `payment_status` VARCHAR(9) NOT NULL  COMMENT '支付状态' DEFAULT 'unpaid',
    `contact_name` VARCHAR(50) NOT NULL  COMMENT '联系人姓名',
    `contact_phone` VARCHAR(20) NOT NULL  COMMENT '联系电话',
    `user_notes` LONGTEXT   COMMENT '用户备注',
    `merchant_notes` LONGTEXT   COMMENT '商家备注',
    `cancel_reason` LONGTEXT   COMMENT '取消原因',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `confirmed_at` DATETIME(6)   COMMENT '确认时间',
    `completed_at` DATETIME(6)   COMMENT '完成时间',
    `cancelled_at` DATETIME(6)   COMMENT '取消时间',
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
    `rating` INT NOT NULL  COMMENT '评分(1-5)',
    `comment` LONGTEXT   COMMENT '评价内容',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `crew_id` BIGINT NOT NULL COMMENT '被评价船员',
    `user_id` INT NOT NULL COMMENT '评价用户',
    `booking_id` BIGINT NOT NULL UNIQUE COMMENT '关联预约',
    CONSTRAINT `fk_crew_rat_crew_6d91e2c1` FOREIGN KEY (`crew_id`) REFERENCES `crew` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_rat_users_a7a9bc19` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_crew_rat_boat_boo_db3ac55f` FOREIGN KEY (`booking_id`) REFERENCES `boat_booking` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='船员评价表';
CREATE TABLE IF NOT EXISTS `cart` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '购物车ID',
    `quantity` INT NOT NULL  COMMENT '商品数量',
    `created_at` DATETIME(6) NOT NULL  COMMENT '添加时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `product_id` BIGINT NOT NULL COMMENT '商品',
    `user_id` INT NOT NULL COMMENT '用户',
    UNIQUE KEY `uid_cart_user_id_d2f7dd` (`user_id`, `product_id`),
    CONSTRAINT `fk_cart_product_92186a63` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_cart_users_ee2917eb` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='购物车表';
CREATE TABLE IF NOT EXISTS `order` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '订单ID',
    `order_number` VARCHAR(32) NOT NULL UNIQUE COMMENT '订单号',
    `total_amount` DECIMAL(12,2) NOT NULL  COMMENT '订单总金额',
    `discount_amount` DECIMAL(10,2) NOT NULL  COMMENT '优惠金额' DEFAULT 0,
    `shipping_fee` DECIMAL(8,2) NOT NULL  COMMENT '运费' DEFAULT 0,
    `final_amount` DECIMAL(12,2) NOT NULL  COMMENT '实付金额',
    `status` VARCHAR(9) NOT NULL  COMMENT '订单状态' DEFAULT 'pending',
    `payment_method` VARCHAR(8)   COMMENT '支付方式',
    `receiver_name` VARCHAR(50) NOT NULL  COMMENT '收货人姓名',
    `receiver_phone` VARCHAR(20) NOT NULL  COMMENT '收货人电话',
    `receiver_address` VARCHAR(255) NOT NULL  COMMENT '收货地址',
    `user_notes` LONGTEXT   COMMENT '用户备注',
    `merchant_notes` LONGTEXT   COMMENT '商家备注',
    `cancel_reason` LONGTEXT   COMMENT '取消原因',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL  COMMENT '更新时间' DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `paid_at` DATETIME(6)   COMMENT '支付时间',
    `shipped_at` DATETIME(6)   COMMENT '发货时间',
    `delivered_at` DATETIME(6)   COMMENT '送达时间',
    `completed_at` DATETIME(6)   COMMENT '完成时间',
    `cancelled_at` DATETIME(6)   COMMENT '取消时间',
    `merchant_id` BIGINT NOT NULL COMMENT '商家',
    `user_id` INT NOT NULL COMMENT '用户',
    CONSTRAINT `fk_order_merchant_cbdbd06e` FOREIGN KEY (`merchant_id`) REFERENCES `merchant` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_order_users_3768b2b0` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='订单表';
CREATE TABLE IF NOT EXISTS `order_item` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '订单项ID',
    `quantity` INT NOT NULL  COMMENT '商品数量',
    `unit_price` DECIMAL(10,2) NOT NULL  COMMENT '单价',
    `total_price` DECIMAL(12,2) NOT NULL  COMMENT '小计',
    `product_name` VARCHAR(100) NOT NULL  COMMENT '商品名称',
    `product_unit` VARCHAR(20) NOT NULL  COMMENT '计量单位',
    `product_image` VARCHAR(255)   COMMENT '商品图片',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `order_id` BIGINT NOT NULL COMMENT '订单',
    `product_id` BIGINT NOT NULL COMMENT '商品',
    CONSTRAINT `fk_order_it_order_23934b93` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_order_it_product_10ab7db4` FOREIGN KEY (`product_id`) REFERENCES `product` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='订单项表';
CREATE TABLE IF NOT EXISTS `payment_record` (
    `id` BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT COMMENT '支付记录ID',
    `payment_number` VARCHAR(32) NOT NULL UNIQUE COMMENT '支付单号',
    `amount` DECIMAL(12,2) NOT NULL  COMMENT '支付金额',
    `payment_method` VARCHAR(8) NOT NULL  COMMENT '支付方式',
    `is_success` BOOL NOT NULL  COMMENT '是否支付成功' DEFAULT 0,
    `third_party_number` VARCHAR(64)   COMMENT '第三方支付单号',
    `created_at` DATETIME(6) NOT NULL  COMMENT '创建时间' DEFAULT CURRENT_TIMESTAMP(6),
    `paid_at` DATETIME(6)   COMMENT '支付时间',
    `order_id` BIGINT NOT NULL COMMENT '订单',
    `user_id` INT NOT NULL COMMENT '用户',
    CONSTRAINT `fk_payment__order_66b04302` FOREIGN KEY (`order_id`) REFERENCES `order` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_payment__users_e84cb460` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4 COMMENT='支付记录表';
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
