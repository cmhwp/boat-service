"""
交互式邮件服务配置脚本
"""
import os
from pathlib import Path


def setup_email():
    """配置邮件服务"""
    print("\n" + "=" * 60)
    print("[邮件服务配置向导]")
    print("=" * 60)
    
    print("\n选择邮箱服务商:")
    print("1. QQ邮箱（推荐）")
    print("2. 163邮箱")
    print("3. Gmail")
    print("4. 其他")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    configs = {
        "1": {"host": "smtp.qq.com", "port": "587", "name": "QQ邮箱"},
        "2": {"host": "smtp.163.com", "port": "587", "name": "163邮箱"},
        "3": {"host": "smtp.gmail.com", "port": "587", "name": "Gmail"},
    }
    
    if choice in configs:
        config = configs[choice]
        smtp_host = config["host"]
        smtp_port = config["port"]
        service_name = config["name"]
    else:
        smtp_host = input("SMTP服务器地址: ").strip()
        smtp_port = input("SMTP端口 (默认587): ").strip() or "587"
        service_name = "自定义"
    
    print(f"\n配置 {service_name}...")
    email_user = input("邮箱地址: ").strip()
    email_password = input("授权码/密码: ").strip()
    
    if not email_user or not email_password:
        print("\n[错误] 邮箱地址和密码不能为空！")
        return
    
    # 生成环境变量命令
    print("\n" + "=" * 60)
    print("[配置完成] 请复制以下命令到PowerShell执行：")
    print("=" * 60)
    print("\n# Windows PowerShell:")
    print(f"$env:MAIL_HOST='{smtp_host}'")
    print(f"$env:MAIL_PORT='{smtp_port}'")
    print(f"$env:MAIL_USERNAME='{email_user}'")
    print(f"$env:MAIL_PASSWORD='{email_password}'")
    print(f"$env:EMAIL_FROM='{email_user}'")
    print("$env:MAIL_USE_TLS='True'")
    
    # 生成.env文件
    env_content = f"""# 邮件服务配置
MAIL_HOST={smtp_host}
MAIL_PORT={smtp_port}
MAIL_USERNAME={email_user}
MAIL_PASSWORD={email_password}
EMAIL_FROM={email_user}
MAIL_USE_SSL=False
MAIL_USE_TLS=True

# 数据库配置
DATABASE_URL=mysql://root:123456@localhost:3306/boat_service

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT密钥
SECRET_KEY=your-secret-key-change-in-production
"""
    
    env_file = Path(__file__).parent / '.env'
    save = input(f"\n是否保存到 .env 文件？(y/n): ").strip().lower()
    
    if save == 'y':
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print(f"[成功] 已保存到: {env_file}")
    
    print("\n" + "=" * 60)
    print("下一步:")
    print("1. 设置环境变量（上面的PowerShell命令）")
    print("2. 运行测试: python test_email.py")
    print("3. 重启后端服务: python main.py")
    print("=" * 60)


def show_qq_help():
    """显示QQ邮箱帮助"""
    print("\n" + "=" * 60)
    print("[如何获取QQ邮箱授权码]")
    print("=" * 60)
    print("\n1. 登录QQ邮箱网页版: https://mail.qq.com")
    print("2. 点击 设置 -> 账户")
    print("3. 找到 POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务")
    print("4. 开启 IMAP/SMTP服务")
    print("5. 按提示发送短信")
    print("6. 获取授权码（16位字符）")
    print("7. 将授权码作为密码使用")
    print("\n【重要】授权码不是QQ密码！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        show_qq_help()
        input("\n按Enter继续配置...")
        setup_email()
    except KeyboardInterrupt:
        print("\n\n配置已取消")

