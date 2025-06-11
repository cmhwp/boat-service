#!/usr/bin/env python3
"""
163邮箱配置设置脚本
"""
import os


def setup_163_email():
    """设置163邮箱配置"""
    print("🚢 绿色智能船艇平台 - 163邮箱配置")
    print("=" * 50)
    
    # 根据您提供的配置设置环境变量
    email_config = {
        "MAIL_PROTOCOL": "smtp",
        "MAIL_DEFAULT_ENCODING": "UTF-8",
        "MAIL_HOST": "smtp.163.com",
        "MAIL_PORT": "465",
        "MAIL_USERNAME": "cmh22408@163.com",
        "MAIL_PASSWORD": "QDTXLMQLCARYHZYS",
        "MAIL_USE_SSL": "True",
        "MAIL_USE_TLS": "True",
        "MAIL_VALIDATE_CERTS": "True",
        "MAIL_TEST_CONNECTION": "True"
    }
    
    # 设置环境变量
    for key, value in email_config.items():
        os.environ[key] = value
        print(f"设置 {key} = {value}")
    
    print(f"\n✅ 163邮箱配置完成！")
    print(f"邮箱: {email_config['MAIL_USERNAME']}")
    print(f"SMTP服务器: {email_config['MAIL_HOST']}:{email_config['MAIL_PORT']}")
    print(f"SSL: {email_config['MAIL_USE_SSL']}")
    
    return email_config


def test_163_email():
    """测试163邮箱连接"""
    try:
        from app.utils.email_utils import email_sender
        
        print("\n🔍 测试163邮箱连接...")
        result = email_sender.test_connection()
        
        if result["success"]:
            print("✅ 163邮箱配置测试成功！")
            print(f"SMTP服务器: {result.get('smtp_server')}:{result.get('smtp_port')}")
            print(f"邮箱用户: {result.get('email_user')}")
            print(f"SSL: {result.get('use_ssl')}")
            print(f"TLS: {result.get('use_tls')}")
        else:
            print("❌ 163邮箱配置测试失败！")
            print(f"错误: {result['message']}")
            if "details" in result:
                print(f"详情: {result['details']}")
                
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")


def create_env_file():
    """创建.env文件"""
    env_content = """# 163邮箱配置
MAIL_PROTOCOL=smtp
MAIL_DEFAULT_ENCODING=UTF-8
MAIL_HOST=smtp.163.com
MAIL_PORT=465
MAIL_USERNAME=cmh22408@163.com
MAIL_PASSWORD=QDTXLMQLCARYHZYS
MAIL_USE_SSL=True
MAIL_USE_TLS=True
MAIL_VALIDATE_CERTS=True
MAIL_TEST_CONNECTION=True

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
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

# 前端配置
FRONTEND_URL=http://localhost:3000
"""
    
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)
        print("\n📄 .env文件创建成功！")
        print("文件路径: .env")
    except Exception as e:
        print(f"\n❌ 创建.env文件失败: {e}")


if __name__ == "__main__":
    try:
        # 设置环境变量
        setup_163_email()
        
        # 询问是否创建.env文件
        create_env = input("\n是否创建.env文件以永久保存配置？(y/n): ").strip().lower()
        if create_env in ['y', 'yes']:
            create_env_file()
        
        # 询问是否测试连接
        test_choice = input("\n是否测试163邮箱连接？(y/n): ").strip().lower()
        if test_choice in ['y', 'yes']:
            test_163_email()
        
        print("\n🎉 163邮箱配置完成！现在可以启动应用了。")
        print("启动命令: python main.py")
        
    except KeyboardInterrupt:
        print("\n\n👋 配置已取消")
    except Exception as e:
        print(f"\n❌ 配置过程中出现错误: {e}") 