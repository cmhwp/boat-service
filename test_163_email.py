"""
163邮箱测试脚本
"""
import smtplib
from email.mime.text import MIMEText

# 你的163邮箱配置
SMTP_SERVER = "smtp.163.com"
SMTP_PORT = 465
EMAIL_USER = "cmh22408@163.com"
EMAIL_PASSWORD = "QDTXLMQLCARYHZYS"

print("=" * 60)
print("163邮箱配置测试")
print("=" * 60)
print(f"\nSMTP服务器: {SMTP_SERVER}")
print(f"SMTP端口: {SMTP_PORT}")
print(f"邮箱用户: {EMAIL_USER}")
print(f"密码: ***{EMAIL_PASSWORD[-4:]}")

print("\n开始测试连接...")

try:
    # 使用SSL连接（465端口）
    print("使用SSL连接...")
    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
    print("[OK] SSL连接成功")
    
    # 登录
    print("登录邮箱...")
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    print("[OK] 登录成功")
    
    # 询问是否发送测试邮件
    test = input("\n是否发送测试邮件？(y/n): ").strip().lower()
    if test == 'y':
        to_email = input("请输入接收邮箱: ").strip()
        
        if to_email:
            msg = MIMEText("这是一封测试邮件，来自绿色智能船艇平台", 'plain', 'utf-8')
            msg['Subject'] = "测试邮件"
            msg['From'] = EMAIL_USER
            msg['To'] = to_email
            
            print(f"\n发送测试邮件到 {to_email}...")
            server.sendmail(EMAIL_USER, [to_email], msg.as_string())
            print("[OK] 邮件发送成功！")
    
    server.quit()
    
    print("\n" + "=" * 60)
    print("[成功] 163邮箱配置正确！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 设置环境变量:")
    print("   $env:MAIL_USE_SSL='True'")
    print("   $env:MAIL_USE_TLS='False'")
    print("\n2. 重启后端服务: python main.py")
    print("=" * 60)
    
except smtplib.SMTPAuthenticationError as e:
    print(f"\n[错误] 认证失败: {e}")
    print("\n可能的原因:")
    print("1. 邮箱密码错误")
    print("2. 未开启SMTP服务")
    print("3. 需要使用授权码而不是登录密码")
    
except smtplib.SMTPConnectError as e:
    print(f"\n[错误] 连接失败: {e}")
    print("\n可能的原因:")
    print("1. SMTP服务器地址错误")
    print("2. 端口被防火墙阻止")
    print("3. 网络连接问题")
    
except Exception as e:
    print(f"\n[错误] 测试失败: {e}")
    import traceback
    traceback.print_exc()


