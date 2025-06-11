#!/usr/bin/env python3
"""
邮箱配置设置脚本
"""
import os


def setup_email_config():
    """设置邮箱配置"""
    print("🚢 绿色智能船艇平台 - 邮箱配置设置")
    print("=" * 50)
    
    # 获取用户输入
    print("\n请输入邮箱配置信息：")
    email_user = input("邮箱地址 (例: your_email@qq.com): ").strip()
    email_password = input("授权码 (不是邮箱密码): ").strip()
    
    # 根据邮箱类型自动设置SMTP服务器
    if "@qq.com" in email_user:
        smtp_server = "smtp.qq.com"
        smtp_port = "587"
    elif "@163.com" in email_user:
        smtp_server = "smtp.163.com"
        smtp_port = "25"
    elif "@gmail.com" in email_user:
        smtp_server = "smtp.gmail.com"
        smtp_port = "587"
    else:
        print("\n自动识别失败，请手动输入SMTP配置：")
        smtp_server = input("SMTP服务器 (例: smtp.qq.com): ").strip()
        smtp_port = input("SMTP端口 (例: 587): ").strip()
    
    # 设置环境变量
    os.environ["EMAIL_USER"] = email_user
    os.environ["EMAIL_PASSWORD"] = email_password
    os.environ["EMAIL_FROM"] = email_user
    os.environ["SMTP_SERVER"] = smtp_server
    os.environ["SMTP_PORT"] = smtp_port
    
    print(f"\n✅ 邮箱配置完成！")
    print(f"邮箱: {email_user}")
    print(f"SMTP服务器: {smtp_server}:{smtp_port}")
    print("\n⚠️ 注意：此配置仅在当前会话有效")
    print("要永久保存，请创建.env文件并添加以下内容：")
    print("-" * 40)
    print(f"EMAIL_USER={email_user}")
    print(f"EMAIL_PASSWORD={email_password}")
    print(f"EMAIL_FROM={email_user}")
    print(f"SMTP_SERVER={smtp_server}")
    print(f"SMTP_PORT={smtp_port}")
    print("-" * 40)


def test_email_connection():
    """测试邮箱连接"""
    from app.utils.email_utils import email_sender
    
    print("\n🔍 测试邮箱连接...")
    result = email_sender.test_connection()
    
    if result["success"]:
        print("✅ 邮箱配置测试成功！")
        print(f"SMTP服务器: {result.get('smtp_server')}")
        print(f"邮箱用户: {result.get('email_user')}")
    else:
        print("❌ 邮箱配置测试失败！")
        print(f"错误: {result['message']}")
        if "details" in result:
            print(f"详情: {result['details']}")


if __name__ == "__main__":
    try:
        setup_email_config()
        
        # 询问是否测试连接
        test_choice = input("\n是否测试邮箱连接？(y/n): ").strip().lower()
        if test_choice in ['y', 'yes']:
            test_email_connection()
        
        print("\n🎉 配置完成！现在可以启动应用了。")
        
    except KeyboardInterrupt:
        print("\n\n👋 配置已取消")
    except Exception as e:
        print(f"\n❌ 配置过程中出现错误: {e}") 