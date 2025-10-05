# 绿色智能船艇农文旅服务平台

> 基于 FastAPI + Tortoise ORM + MySQL + Redis + 腾讯云COS 构建的智能船艇农文旅服务平台

## 项目简介

绿色智能船艇农文旅服务平台是一个集船艇预约、农产品销售、商家管理、船员服务于一体的综合性服务平台。平台为用户提供便捷的船艇预约服务，同时支持农文旅产品的在线购买，打造水上旅游与农业体验的完整生态链。

## 功能特性

### 🚀 核心功能
- **用户系统**: 用户注册/登录、邮箱验证、密码重置、多角色权限管理
- **实名认证**: 身份证上传、实名认证申请、管理员审核
- **商家系统**: 商家申请、营业执照上传、管理员审核、商家信息管理
- **船员系统**: 船员申请、商家审核、船员管理、评价系统
- **船艇管理**: 船艇信息管理、状态监控、预约调度
- **预约服务**: 船艇预约、时间管理、费用计算、状态跟踪
- **农产品商城**: 产品管理、购物车、订单系统、库存管理
- **支付系统**: 多种支付方式、支付记录、退款处理
- **数据统计**: 运营数据分析、图表展示、业务洞察

### ✨ 高级功能 (v2.0)
- **分账系统**: 平台、商家、船员三方自动分账，透明化收益管理
- **WebSocket通知**: 实时推送预约、订单、评价等业务通知
- **邮件增强**: 预约确认邮件、发货提醒邮件，精美HTML模板
- **船艇服务评价**: 独立的服务评价体系，多维度评分，支持图片和点赞
- **农产品评价**: 质量、新鲜度、包装评分，支持匿名评价和商家回复

### 🛠️ 技术特性
- 基于 FastAPI 的高性能异步 Web 框架
- 使用 Tortoise ORM 进行异步数据库操作
- JWT Token 身份认证与权限控制
- BCrypt 密码哈希加密
- Redis 缓存支持
- 腾讯云COS文件存储
- 自动化任务调度
- 完善的异常处理机制
- 丰富的API文档

## 技术栈

- **Web框架**: FastAPI 0.104.1
- **ORM**: Tortoise ORM 0.20.0
- **数据库**: MySQL
- **缓存**: Redis 5.0.1
- **认证**: JWT + BCrypt
- **数据验证**: Pydantic 2.5.0
- **文件存储**: 腾讯云COS
- **图片处理**: Pillow 10.1.0
- **迁移工具**: Aerich 0.7.2
- **HTTP服务**: Uvicorn 0.24.0

## 项目结构

```
boat-service/
├── app/                         # 应用核心目录
│   ├── config/                  # 配置文件
│   │   ├── database.py         # 数据库配置
│   │   ├── redis_client.py     # Redis配置
│   │   └── cos_config.py       # 腾讯云COS配置
│   ├── models/                  # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── merchant.py         # 商家模型
│   │   ├── crew.py             # 船员模型
│   │   ├── boat.py             # 船艇模型
│   │   ├── product.py          # 农产品模型
│   │   ├── booking.py          # 预约模型
│   │   ├── order.py            # 订单模型
│   │   └── realname_auth.py    # 实名认证模型
│   ├── schemas/                 # Pydantic数据模式
│   │   ├── user.py             # 用户数据模式
│   │   ├── merchant.py         # 商家数据模式
│   │   ├── crew.py             # 船员数据模式
│   │   ├── boat.py             # 船艇数据模式
│   │   ├── product.py          # 产品数据模式
│   │   ├── booking.py          # 预约数据模式
│   │   ├── order.py            # 订单数据模式
│   │   ├── dashboard.py        # 仪表盘数据模式
│   │   └── response.py         # 统一响应模式
│   ├── services/                # 业务逻辑层
│   │   ├── user_service.py     # 用户服务
│   │   ├── merchant_service.py # 商家服务
│   │   ├── crew_service.py     # 船员服务
│   │   ├── boat_service.py     # 船艇服务
│   │   ├── product_service.py  # 产品服务
│   │   ├── booking_service.py  # 预约服务
│   │   ├── order_service.py    # 订单服务
│   │   ├── cart_service.py     # 购物车服务
│   │   ├── task_service.py     # 任务服务
│   │   └── dashboard_service.py # 统计服务
│   ├── routers/                 # API路由
│   │   ├── user.py             # 用户路由
│   │   ├── merchant.py         # 商家路由
│   │   ├── crew.py             # 船员路由
│   │   ├── boat.py             # 船艇路由
│   │   ├── product.py          # 产品路由
│   │   ├── booking.py          # 预约路由
│   │   ├── order.py            # 订单路由
│   │   ├── cart.py             # 购物车路由
│   │   └── dashboard.py        # 统计路由
│   └── utils/                   # 工具类
│       ├── auth.py             # 认证中间件
│       ├── jwt_utils.py        # JWT工具
│       ├── cos_utils.py        # 腾讯云COS工具
│       ├── email_utils.py      # 邮件工具
│       ├── redis_utils.py      # Redis工具
│       └── exception_handlers.py # 异常处理
├── migrations/                  # 数据库迁移文件
├── scripts/                     # 脚本文件
│   └── init_admin.py           # 管理员初始化脚本
├── main.py                     # 应用入口
├── init_db.py                  # 数据库初始化
├── requirements.txt            # 依赖包
└── pyproject.toml             # Aerich配置
```

## 安装和运行

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 6.0+

### 2. 克隆项目

```bash
git clone <repository-url>
cd boat-service
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 环境配置

创建 `.env` 文件并配置以下环境变量：

```env
# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=boat_service
DB_ECHO=False

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# JWT配置
JWT_SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60

# 邮件配置
SMTP_SERVER=smtp.qq.com
SMTP_PORT=587
EMAIL_USER=your_email@qq.com
EMAIL_PASSWORD=your_email_password
EMAIL_FROM=your_email@qq.com

# 前端配置
FRONTEND_URL=http://localhost:3000

# 腾讯云COS配置
COS_SECRET_ID=your_secret_id
COS_SECRET_KEY=your_secret_key
COS_REGION=ap-guangzhou
COS_BUCKET=your_bucket_name
COS_DOMAIN=https://your-domain.com
COS_MAX_FILE_SIZE=10485760
COS_ALLOWED_IMAGE_TYPES=["jpg", "jpeg", "png", "gif", "webp"]
COS_AVATAR_PREFIX=avatars/
COS_IDENTITY_PREFIX=identity/
COS_MERCHANT_LICENSE_PREFIX=merchant-licenses/
COS_BOAT_PREFIX=boats/
COS_SERVICE_PREFIX=services/
COS_PRODUCT_PREFIX=products/
COS_REVIEW_PREFIX=reviews/
```

### 5. 数据库初始化

```bash
# 初始化数据库表结构
python init_db.py

# 或使用Aerich进行迁移管理
aerich init-db
aerich migrate
aerich upgrade
```

### 6. 创建管理员账户

```bash
python scripts/init_admin.py
```

### 7. 启动应用

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 8. 访问应用

- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## 🆕 v2.0 新增功能

### 分账系统
自动化的三方分账机制，透明化收益分配：
- 预约服务：平台5% + 商家35% + 船员60%
- 订单商品：平台10% + 商家90%
- 支持分账记录查询和统计

### WebSocket实时通知
- 实时推送业务通知
- 支持心跳保活机制
- WebSocket端点：`/api/v1/notifications/ws`

### 邮件通知增强
- 预约确认邮件：包含预约详情、船艇信息
- 发货提醒邮件：包含物流信息、商品清单
- 精美HTML模板，响应式设计

### 船艇服务评价
- 三维度评分：服务质量、船艇状况、性价比
- 支持图片上传和标签
- 商家回复和点赞功能

### 农产品评价
- 三维度评分：质量、新鲜度、包装
- 支持匿名评价
- 商家回复和点赞功能

**详细文档**: 请参阅 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 和 [CHANGELOG.md](CHANGELOG.md)

---

## API 接口文档

### 用户系统 API

**注册相关**
- `POST /api/v1/users/send-verification-code` - 发送邮箱验证码
- `POST /api/v1/users/verify-email-code` - 验证邮箱验证码
- `POST /api/v1/users/register` - 完成用户注册

**登录相关**
- `POST /api/v1/users/login` - 用户登录

**密码管理**
- `POST /api/v1/users/forgot-password` - 忘记密码
- `GET /api/v1/users/verify-reset-token/{token}` - 验证重置token
- `POST /api/v1/users/reset-password` - 重置密码
- `POST /api/v1/users/change-password` - 修改密码

**用户管理**
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `POST /api/v1/users/upload-avatar` - 上传头像

### 实名认证 API

- `POST /api/v1/realname-auth/upload-identity` - 上传身份证
- `POST /api/v1/realname-auth/submit` - 提交实名认证申请
- `GET /api/v1/realname-auth/status` - 查看认证状态
- `POST /api/v1/realname-auth/audit` - 审核实名认证（管理员）

### 商家系统 API

- `POST /api/v1/merchants/upload-license` - 上传营业执照
- `POST /api/v1/merchants/apply` - 申请成为商家
- `POST /api/v1/merchants/audit` - 审核商家申请（管理员）
- `GET /api/v1/merchants/me` - 获取我的商家信息
- `PUT /api/v1/merchants/me` - 更新商家信息

### 船员系统 API

- `GET /api/v1/crew/merchants` - 获取可申请的商家列表
- `POST /api/v1/crew/apply` - 申请成为船员
- `POST /api/v1/crew/handle-application` - 处理船员申请（商家）
- `GET /api/v1/crew/applications` - 获取船员申请列表（商家）
- `GET /api/v1/crew/me` - 获取我的船员信息

### 船艇管理 API

- `POST /api/v1/boats/` - 添加船艇（商家）
- `GET /api/v1/boats/` - 获取船艇列表
- `GET /api/v1/boats/{boat_id}` - 获取船艇详情
- `PUT /api/v1/boats/{boat_id}` - 更新船艇信息（商家）
- `POST /api/v1/boats/{boat_id}/upload-images` - 上传船艇图片

### 预约服务 API

- `POST /api/v1/bookings/` - 创建预约
- `GET /api/v1/bookings/my` - 获取我的预约列表
- `GET /api/v1/bookings/merchant` - 获取商家预约列表
- `POST /api/v1/bookings/{booking_id}/confirm` - 确认预约（商家）
- `POST /api/v1/bookings/{booking_id}/cancel` - 取消预约
- `POST /api/v1/bookings/{booking_id}/complete` - 完成服务（船员）

### 农产品商城 API

- `POST /api/v1/products/` - 添加产品（商家）
- `GET /api/v1/products/` - 获取产品列表
- `GET /api/v1/products/{product_id}` - 获取产品详情
- `PUT /api/v1/products/{product_id}` - 更新产品信息（商家）
- `POST /api/v1/products/{product_id}/upload-images` - 上传产品图片

### 购物车 API

- `POST /api/v1/cart/add` - 添加到购物车
- `GET /api/v1/cart/` - 获取购物车列表
- `PUT /api/v1/cart/{cart_id}` - 更新购物车商品数量
- `DELETE /api/v1/cart/{cart_id}` - 删除购物车商品
- `DELETE /api/v1/cart/clear` - 清空购物车

### 订单系统 API

- `POST /api/v1/orders/` - 创建订单
- `GET /api/v1/orders/my` - 获取我的订单列表
- `GET /api/v1/orders/merchant` - 获取商家订单列表
- `GET /api/v1/orders/{order_id}` - 获取订单详情
- `POST /api/v1/orders/{order_id}/pay` - 支付订单
- `POST /api/v1/orders/{order_id}/ship` - 发货（商家）
- `POST /api/v1/orders/{order_id}/cancel` - 取消订单

### 数据统计 API

- `GET /api/v1/dashboard/overview` - 获取仪表盘概览
- `GET /api/v1/dashboard/charts` - 获取图表数据

### 分账管理 API (v2.0)

- `POST /api/v1/split-payments/rules` - 创建分账规则（管理员）
- `GET /api/v1/split-payments/` - 获取分账记录列表
- `GET /api/v1/split-payments/stats` - 获取分账统计

### 通知管理 API (v2.0)

- `WS /api/v1/notifications/ws` - WebSocket连接端点
- `GET /api/v1/notifications/` - 获取通知列表
- `POST /api/v1/notifications/mark-read` - 标记通知为已读
- `POST /api/v1/notifications/mark-all-read` - 标记全部已读
- `GET /api/v1/notifications/stats` - 获取通知统计
- `DELETE /api/v1/notifications/{id}` - 删除通知

### 评价管理 API (v2.0)

**船艇服务评价**
- `POST /api/v1/reviews/boat-service` - 创建船艇服务评价
- `GET /api/v1/reviews/boat-service` - 获取评价列表
- `POST /api/v1/reviews/boat-service/{id}/reply` - 商家回复评价
- `POST /api/v1/reviews/boat_service/{id}/helpful` - 标记有帮助

**农产品评价**
- `POST /api/v1/reviews/product` - 创建农产品评价
- `GET /api/v1/reviews/product` - 获取评价列表
- `POST /api/v1/reviews/product/{id}/reply` - 商家回复评价
- `POST /api/v1/reviews/product/{id}/helpful` - 标记有帮助

## 用户角色和权限

### 角色类型
- `user` - 普通用户：可以预约船艇、购买农产品
- `crew` - 船员：可以执行船艇服务、查看指派的预约
- `merchant` - 商家：可以管理船艇、处理预约、管理农产品、处理订单
- `admin` - 管理员：可以审核商家申请、查看所有数据

### 认证状态
- `unverified` - 未认证
- `pending` - 待审核
- `verified` - 已认证

## 业务流程

### 用户注册流程
1. 发送邮箱验证码
2. 验证邮箱（可选）
3. 完成用户注册

### 商家申请流程
1. 用户注册并登录
2. 上传营业执照
3. 提交商家申请
4. 管理员审核
5. 审核通过后角色变更为merchant

### 船员申请流程
1. 查看可申请的商家列表
2. 提交船员申请
3. 商家审核申请
4. 审核通过后角色变更为crew

### 船艇预约流程
1. 用户浏览船艇列表
2. 选择时间和船艇创建预约
3. 商家确认预约并指派船员
4. 船员执行服务
5. 完成服务并评价

### 农产品购买流程
1. 用户浏览产品列表
2. 添加商品到购物车
3. 创建订单
4. 支付订单
5. 商家发货
6. 确认收货完成交易

## 文件上传

### 支持的文件类型
- 图片格式：JPG, JPEG, PNG, GIF, WebP
- 文件大小限制：10MB

### 上传目录结构
- `avatars/` - 用户头像
- `identity/` - 身份证图片
- `merchant-licenses/` - 营业执照
- `boats/` - 船艇图片
- `products/` - 产品图片
- `reviews/` - 评价图片

### 图片处理
- 自动压缩：头像限制512KB，营业执照限制2MB
- 格式转换：自动转换为JPEG格式
- 唯一命名：时间戳 + UUID确保文件名唯一

## 定时任务

### 预约自动取消
- 检查间隔：5分钟
- 取消规则：商家超过20分钟未确认的预约自动取消
- 日志记录：完整的任务执行日志

## 开发指南

### 代码规范
- 文件命名：使用下划线命名法（snake_case）
- 类命名：使用驼峰命名法（PascalCase）  
- 函数/变量命名：使用下划线命名法（snake_case）
- 注释：使用中文注释，API文档使用中文描述

### 错误处理
- 统一使用ResponseHelper返回错误信息
- 完善的异常处理机制
- 详细的错误日志记录

### 数据库设计
- 所有表使用BIGINT作为主键
- 统一使用created_at、updated_at时间字段
- 外键关系通过Tortoise ORM定义
- 枚举值使用字符串类型存储

## 部署说明

### Docker部署（推荐）

```bash
# 构建镜像
docker build -t boat-service .

# 运行容器
docker run -d -p 8000:8000 --env-file .env boat-service
```

### 生产环境配置

1. 设置环境变量为生产环境值
2. 配置HTTPS证书
3. 设置反向代理（Nginx）
4. 配置数据库连接池
5. 启用Redis集群
6. 配置日志轮转
7. 设置监控和告警

## 常见问题

### Q: 如何重置管理员密码？
A: 运行 `python scripts/init_admin.py` 创建新的管理员账户

### Q: COS上传失败怎么办？
A: 检查COS配置是否正确，确认bucket权限设置

### Q: Redis连接失败？
A: 检查Redis服务状态和连接配置

### Q: 数据库迁移失败？
A: 使用 `aerich migrate` 和 `aerich upgrade` 进行迁移

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

如有问题，请联系开发团队或提交Issue。

---

🚢 **绿色智能船艇农文旅服务平台** - 让水上旅游与农业体验更美好！ 