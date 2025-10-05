"""
检查邮件配置脚本
"""
import os
import sys

# 加载环境变量
try:
    from dotenv import load_dotenv
    from pathlib import Path
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"[OK] 已加载 .env 文件")
    else:
        print(f"[警告] 未找到 .env 文件")
except ImportError:
    print("[警告] 未安装 python-dotenv")

print("\n" + "=" * 60)
print("邮件服务配置检查")
print("=" * 60)

# 检查环境变量
configs = {
    "SMTP服务器": ["MAIL_HOST", "SMTP_SERVER"],
    "SMTP端口": ["MAIL_PORT", "SMTP_PORT"],
    "邮箱用户名": ["MAIL_USERNAME", "EMAIL_USER"],
    "邮箱密码": ["MAIL_PASSWORD", "EMAIL_PASSWORD"],
    "发件人": ["EMAIL_FROM"],
}

print("\n【环境变量检查】")
for name, keys in configs.items():
    value = None
    found_key = None
    for key in keys:
        value = os.getenv(key)
        if value:
            found_key = key
            break
    
    if value:
        if "密码" in name or "PASSWORD" in name:
            display = "***" + value[-4:] if len(value) > 4 else "****"
        else:
            display = value
        print(f"✓ {name}: {display} (来自 {found_key})")
    else:
        print(f"✗ {name}: 未配置 (需要设置: {' 或 '.join(keys)})")

# 获取实际配置
smtp_server = os.getenv("MAIL_HOST") or os.getenv("SMTP_SERVER")
smtp_port = os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT")
email_user = os.getenv("MAIL_USERNAME") or os.getenv("EMAIL_USER")
email_password = os.getenv("MAIL_PASSWORD") or os.getenv("EMAIL_PASSWORD")

# SSL/TLS配置
use_ssl = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
use_tls = os.getenv("MAIL_USE_TLS", "True").lower() == "true"

print(f"\n使用SSL: {use_ssl}")
print(f"使用TLS: {use_tls}")

# 检查配置问题
print("\n" + "=" * 60)
print("【诊断结果】")
print("=" * 60)

if not all([smtp_server, smtp_port, email_user, email_password]):
    print("\n✗ 配置不完整！")
    sys.exit(1)

# 检查端口配置
port = int(smtp_port)
print(f"\n检测到端口: {port}")

if port == 465:
    if not use_ssl:
        print("⚠️  警告: 465端口应该使用SSL连接")
        print("   请设置: MAIL_USE_SSL=True")
        print("   请设置: MAIL_USE_TLS=False")
        print("\n修复命令:")
        print("   $env:MAIL_USE_SSL='True'")
        print("   $env:MAIL_USE_TLS='False'")
    else:
        print("✓ SSL配置正确")
elif port == 587:
    if not use_tls:
        print("⚠️  警告: 587端口应该使用TLS连接")
        print("   请设置: MAIL_USE_TLS=True")
    else:
        print("✓ TLS配置正确")

# 检查163邮箱特殊配置
if "163.com" in smtp_server:
    print("\n【163邮箱特别提示】")
    print("✓ 检测到163邮箱")
    if port == 465:
        print("✓ 465端口 - 需要SSL")
        if use_ssl and not use_tls:
            print("✓ SSL配置正确")
        else:
            print("✗ 配置错误！请使用SSL")
    elif port == 25:
        print("⚠️  25端口 - 不推荐，建议使用465")

print("\n" + "=" * 60)
print("【测试邮件发送】")
print("=" * 60)

try:
    from app.utils.email_utils import EmailSender
    
    sender = EmailSender()
    
    if not sender.is_configured():
        print("\n✗ 邮件服务未配置完整")
        sys.exit(1)
    
    print("\n✓ 邮件服务配置完整")
    
    # 询问是否测试
    test = input("\n是否发送测试邮件？(y/n): ").strip().lower()
    if test == 'y':
        test_email = input("请输入测试邮箱地址: ").strip()
        if test_email:
            print(f"\n正在发送测试邮件到 {test_email}...")
            result = sender.send_verification_code(test_email)
            
            if result['success']:
                print("\n✓✓✓ 测试成功！")
                print(f"验证码: {result['code']}")
                print(f"过期时间: {result['expires_in']}秒")
            else:
                print("\n✗✗✗ 测试失败！")
                print(f"错误: {result['message']}")
                if 'details' in result:
                    print(f"详情: {result['details']}")
    
except Exception as e:
    print(f"\n✗ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)


