"""
邮件服务测试脚本
用于测试邮件配置是否正确
"""
import os
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.email_utils import EmailSender


def test_email_config():
    """测试邮件配置"""
    print("=" * 60)
    print("邮件服务配置测试")
    print("=" * 60)
    
    sender = EmailSender()
    
    # 检查配置
    print("\n1. 检查邮件配置...")
    print(f"   SMTP服务器: {sender.smtp_server}")
    print(f"   SMTP端口: {sender.smtp_port}")
    print(f"   邮箱用户名: {sender.email_user}")
    print(f"   邮箱密码: {'已配置' if sender.email_password else '未配置'}")
    print(f"   发件人: {sender.email_from}")
    print(f"   使用SSL: {sender.use_ssl}")
    print(f"   使用TLS: {sender.use_tls}")
    
    if not sender.is_configured():
        print("\n❌ 邮件配置不完整！")
        print("\n请按照以下步骤配置：")
        print("\n【方法1】创建 .env 文件（推荐）")
        print("   1. 复制 .env.example 为 .env")
        print("   2. 修改邮件相关配置")
        print("\n【方法2】设置环境变量")
        print("   Windows PowerShell:")
        print("   $env:MAIL_HOST='smtp.qq.com'")
        print("   $env:MAIL_PORT='587'")
        print("   $env:MAIL_USERNAME='your_email@qq.com'")
        print("   $env:MAIL_PASSWORD='your_auth_code'")
        print("\n【如何获取QQ邮箱授权码】")
        print("   1. 登录QQ邮箱网页版")
        print("   2. 点击 设置 -> 账户")
        print("   3. 找到 POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务")
        print("   4. 开启 IMAP/SMTP服务")
        print("   5. 生成授权码（16位字符）")
        print("   6. 将授权码填入 MAIL_PASSWORD")
        return False
    
    print("\n✅ 邮件配置完整")
    
    # 测试发送
    print("\n2. 测试发送邮件...")
    test_email = input("   请输入测试邮箱地址（留空跳过测试）: ").strip()
    
    if test_email:
        print(f"   正在发送测试邮件到 {test_email}...")
        result = sender.send_verification_code(test_email)
        
        if result['success']:
            print(f"\n✅ 测试邮件发送成功！")
            print(f"   验证码: {result['code']}")
            print(f"   过期时间: {result['expires_in']}秒")
        else:
            print(f"\n❌ 测试邮件发送失败！")
            print(f"   错误信息: {result['message']}")
            if 'details' in result:
                print(f"   详细信息: {result['details']}")
    else:
        print("   跳过发送测试")
    
    print("\n" + "=" * 60)
    return True


def main():
    """主函数"""
    try:
        # 尝试加载 .env 文件
        try:
            from dotenv import load_dotenv
            env_file = Path(__file__).parent / '.env'
            if env_file.exists():
                load_dotenv(env_file)
                print(f"✅ 已加载 .env 文件: {env_file}")
            else:
                print(f"⚠️  未找到 .env 文件: {env_file}")
                print("   请创建 .env 文件或设置环境变量")
        except ImportError:
            print("⚠️  未安装 python-dotenv，使用系统环境变量")
            print("   建议安装: pip install python-dotenv")
        
        print()
        
        # 运行测试
        test_email_config()
        
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


