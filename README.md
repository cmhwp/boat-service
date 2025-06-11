# 绿色智能船艇农文旅服务平台

基于 FastAPI + Tortoise ORM + MySQL + Redis 构建的智能船艇服务平台用户管理系统。

## 功能特性

- 🚀 基于 FastAPI 的高性能异步 Web 框架
- 🗄️ 使用 Tortoise ORM 进行数据库操作
- 🔐 JWT Token 身份认证
- 🔒 BCrypt 密码哈希加密
- 📧 支持用户名或邮箱登录
- ✉️ 邮箱验证码注册流程
- 🔑 邮箱密码重置功能
- 👥 多角色权限管理（用户/船员/商户/管理员）
- 📱 手机号可选字段
- ✅ 实名认证状态管理
- 🔄 Redis 缓存支持

## 技术栈

- **Web框架**: FastAPI 0.104.1
- **ORM**: Tortoise ORM 0.20.0
- **数据库**: MySQL
- **缓存**: Redis
- **认证**: JWT + BCrypt
- **数据验证**: Pydantic
- **迁移工具**: Aerich

## 项目结构

```
boat-service/
├── app/
│   ├── config/          # 配置文件
│   │   └── database.py  # 数据库配置
│   │   └── user.py      # 用户模型
│   ├── schemas/         # Pydantic schemas
│   │   └── user.py      # 用户schemas
│   ├── services/        # 业务逻辑
│   │   └── user_service.py  # 用户服务
│   ├── routers/         # 路由
│   │   └── user.py      # 用户路由
│   └── utils/           # 工具类
│       ├── jwt_utils.py # JWT工具
│       └── auth.py      # 认证中间件
├── migrations/          # 数据库迁移文件
├── main.py             # 应用入口
├── requirements.txt    # 依赖包
└── pyproject.toml     # Aerich配置
```

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境配置

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
```

### 3. 数据库迁移

```bash
# 初始化迁移
aerich init-db

# 生成迁移文件
aerich migrate

# 执行迁移
aerich upgrade
```

### 4. 启动应用

```bash
# 开发模式
python main.py

# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## API 接口

应用启动后访问 `http://localhost:8000/docs` 查看 Swagger API 文档。

### 主要接口

**注册相关：**
- `POST /api/v1/users/send-verification-code` - 发送邮箱验证码
- `POST /api/v1/users/verify-email-code` - 验证邮箱验证码
- `POST /api/v1/users/register` - 完成用户注册

**登录相关：**
- `POST /api/v1/users/login` - 用户登录

**密码管理：**
- `POST /api/v1/users/forgot-password` - 忘记密码
- `GET /api/v1/users/verify-reset-token/{token}` - 验证重置token
- `POST /api/v1/users/reset-password` - 重置密码
- `POST /api/v1/users/change-password` - 修改密码

**用户管理：**
- `GET /api/v1/users/me` - 获取当前用户信息
- `PUT /api/v1/users/me` - 更新当前用户信息
- `GET /api/v1/users/` - 获取用户列表（管理员）
- `GET /api/v1/users/{user_id}` - 获取指定用户（管理员）
- `PUT /api/v1/users/{user_id}` - 更新指定用户（管理员）
- `DELETE /api/v1/users/{user_id}` - 删除用户（管理员）

## 用户角色

- `user` - 普通用户
- `crew` - 船员
- `merchant` - 商户
- `admin` - 管理员

## 实名认证状态

- `unverified` - 未认证
- `pending` - 待审核
- `verified` - 已认证

## 开发说明

### 模型字段

User 模型包含以下字段：
- `id`: 主键
- `username`: 用户名（唯一）
- `email`: 邮箱（唯一）
- `password`: 密码（BCrypt哈希）
- `phone`: 手机号（可选）
- `role`: 用户角色
- `is_active`: 是否激活
- `realname_status`: 实名认证状态
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 注册流程

1. **发送验证码**：调用 `/send-verification-code` 接口发送6位验证码到邮箱
2. **验证邮箱**：调用 `/verify-email-code` 接口验证验证码（可选步骤）
3. **完成注册**：调用 `/register` 接口完成用户注册

### 密码重置流程

1. **请求重置**：调用 `/forgot-password` 接口，系统发送重置链接到邮箱
2. **验证链接**：调用 `/verify-reset-token/{token}` 接口验证重置token有效性
3. **重置密码**：调用 `/reset-password` 接口设置新密码

### 登录方式

支持通过用户名或邮箱登录，系统会自动识别登录标识符类型。

### 邮件配置

支持主流邮件服务商：
- **QQ邮箱**：smtp.qq.com:587
- **163邮箱**：smtp.163.com:25
- **Gmail**：smtp.gmail.com:587

请确保邮箱开启SMTP服务并获取授权码。

## 许可证

MIT License 