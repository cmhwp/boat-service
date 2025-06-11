import smtplib
import os
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional


class EmailSender:
    """邮件发送工具类"""
    
    def __init__(self):
        # 支持多种环境变量格式
        self.smtp_server = os.getenv("MAIL_HOST") or os.getenv("SMTP_SERVER", "smtp.qq.com")
        self.smtp_port = int(os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("MAIL_USERNAME") or os.getenv("EMAIL_USER", "")
        self.email_password = os.getenv("MAIL_PASSWORD") or os.getenv("EMAIL_PASSWORD", "")
        self.email_from = os.getenv("EMAIL_FROM", self.email_user)
        
        # SSL/TLS配置
        self.use_ssl = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
        self.use_tls = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
        self.validate_certs = os.getenv("MAIL_VALIDATE_CERTS", "True").lower() == "true"
        
    def is_configured(self) -> bool:
        """检查邮件配置是否完整"""
        return bool(self.email_user and self.email_password and self.smtp_server)
        
    def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送邮件"""
        try:
            # 检查配置
            if not self.is_configured():
                print("邮件配置不完整，请检查环境变量：MAIL_USERNAME/EMAIL_USER, MAIL_PASSWORD/EMAIL_PASSWORD")
                return False
            
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_from
            msg['To'] = to_email
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 根据配置选择连接方式
            server = None
            try:
                if self.use_ssl and self.smtp_port in [465, 994]:
                    # 使用SSL连接 (端口465)
                    print(f"使用SSL连接到 {self.smtp_server}:{self.smtp_port}")
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
                else:
                    # 使用普通SMTP连接
                    print(f"使用SMTP连接到 {self.smtp_server}:{self.smtp_port}")
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                    
                    # 如果启用TLS，则启动TLS
                    if self.use_tls:
                        print("启用TLS加密")
                        server.starttls()
                
                # 登录并发送邮件
                print(f"尝试使用用户名 {self.email_user} 登录")
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
                print(f"邮件发送成功：{to_email}")
                return True
                
            finally:
                if server:
                    server.quit()
                    
        except smtplib.SMTPAuthenticationError as e:
            print(f"SMTP认证失败: {e}")
            print("请检查邮箱用户名和授权码是否正确")
            print(f"当前配置：用户名={self.email_user}, 服务器={self.smtp_server}:{self.smtp_port}")
            return False
        except smtplib.SMTPConnectError as e:
            print(f"SMTP连接失败: {e}")
            print("请检查SMTP服务器地址和端口，或检查网络连接")
            return False
        except smtplib.SMTPServerDisconnected as e:
            print(f"SMTP服务器断开连接: {e}")
            return False
        except Exception as e:
            print(f"邮件发送失败: {e}")
            print(f"错误类型: {type(e).__name__}")
            return False
    
    def test_connection(self) -> dict:
        """测试邮件服务器连接"""
        try:
            if not self.is_configured():
                return {
                    "success": False,
                    "message": "邮件配置不完整",
                    "details": "请设置环境变量：MAIL_USERNAME/EMAIL_USER, MAIL_PASSWORD/EMAIL_PASSWORD"
                }
            
            server = None
            try:
                if self.use_ssl and self.smtp_port in [465, 994]:
                    # 使用SSL连接
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=30)
                else:
                    # 使用普通SMTP连接
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30)
                    if self.use_tls:
                        server.starttls()
                
                server.login(self.email_user, self.email_password)
                
                return {
                    "success": True,
                    "message": "邮件服务器连接成功",
                    "smtp_server": self.smtp_server,
                    "smtp_port": self.smtp_port,
                    "email_user": self.email_user,
                    "use_ssl": self.use_ssl,
                    "use_tls": self.use_tls
                }
            finally:
                if server:
                    server.quit()
                    
        except smtplib.SMTPAuthenticationError as e:
            return {
                "success": False,
                "message": "SMTP认证失败",
                "details": f"用户名或授权码错误: {e}"
            }
        except smtplib.SMTPConnectError as e:
            return {
                "success": False,
                "message": "SMTP连接失败",
                "details": f"无法连接到服务器: {e}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": "连接测试失败",
                "details": f"{type(e).__name__}: {str(e)}"
            }
    
    def send_verification_code(self, to_email: str, code: str) -> bool:
        """发送验证码邮件"""
        subject = "绿色智能船艇平台 - 邮箱验证码"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>邮箱验证码</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 28px;">🚢 绿色智能船艇平台</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">您的专属农文旅服务平台</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 10px; margin: 20px 0;">
                    <h2 style="color: #2c3e50; margin-top: 0;">邮箱验证码</h2>
                    <p>您好！感谢您注册绿色智能船艇平台。</p>
                    <p>您的验证码是：</p>
                    <div style="background: #fff; border: 2px dashed #667eea; padding: 20px; text-align: center; margin: 20px 0; border-radius: 8px;">
                        <span style="font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 5px;">{code}</span>
                    </div>
                    <p><strong>注意事项：</strong></p>
                    <ul style="color: #666;">
                        <li>验证码有效期为 <strong>5分钟</strong></li>
                        <li>请不要将验证码泄露给他人</li>
                        <li>如果您没有注册此账户，请忽略此邮件</li>
                    </ul>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2024 绿色智能船艇平台 版权所有</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html_content)
    
    def send_password_reset_email(self, to_email: str, reset_token: str, username: str) -> bool:
        """发送密码重置邮件"""
        reset_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"
        subject = "绿色智能船艇平台 - 密码重置"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>密码重置</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 10px; text-align: center; color: white;">
                    <h1 style="margin: 0; font-size: 28px;">🚢 绿色智能船艇平台</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">您的专属农文旅服务平台</p>
                </div>
                
                <div style="background: #f8f9fa; padding: 30px; border-radius: 10px; margin: 20px 0;">
                    <h2 style="color: #2c3e50; margin-top: 0;">🔐 密码重置</h2>
                    <p>尊敬的 <strong>{username}</strong>，您好！</p>
                    <p>我们收到了您的密码重置请求。请点击下面的按钮来重置您的密码：</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                            重置密码
                        </a>
                    </div>
                    
                    <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
                    <div style="background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; word-break: break-all; font-family: monospace; font-size: 14px;">
                        {reset_url}
                    </div>
                    
                    <p><strong>安全提醒：</strong></p>
                    <ul style="color: #666;">
                        <li>此链接有效期为 <strong>30分钟</strong></li>
                        <li>如果您没有请求密码重置，请忽略此邮件</li>
                        <li>为了您的账户安全，请设置强密码</li>
                    </ul>
                </div>
                
                <div style="text-align: center; color: #666; font-size: 14px;">
                    <p>此邮件由系统自动发送，请勿回复</p>
                    <p>© 2024 绿色智能船艇平台 版权所有</p>
                </div>
            </div>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, html_content)


def generate_verification_code(length: int = 6) -> str:
    """生成验证码"""
    return ''.join(random.choices(string.digits, k=length))


def generate_reset_token(length: int = 32) -> str:
    """生成重置token"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


# 全局邮件发送器实例
email_sender = EmailSender() 