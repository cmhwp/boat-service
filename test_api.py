import requests
import json

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_user_registration_and_login():
    """测试用户注册和登录功能"""
    
    print("🧪 开始测试用户注册和登录功能...")
    
    # 1. 测试发送验证码
    print("\n1️⃣ 测试发送验证码...")
    email_data = {"email": "test@example.com"}
    response = requests.post(f"{BASE_URL}/users/send-verification-code", json=email_data)
    
    if response.status_code == 200:
        print("✅ 验证码发送请求成功")
        code_data = response.json()
        print(f"消息: {code_data['message']}")
        print(f"过期时间: {code_data['expires_in']}秒")
        
        # 模拟用户输入验证码（实际场景中用户从邮箱获取）
        verification_code = input("请输入收到的6位验证码: ")
    else:
        print(f"❌ 验证码发送失败: {response.text}")
        return
    
    # 2. 测试验证码校验
    print("\n2️⃣ 测试验证码校验...")
    verify_data = {
        "email": "test@example.com",
        "code": verification_code
    }
    response = requests.post(f"{BASE_URL}/users/verify-email-code", json=verify_data)
    
    if response.status_code == 200:
        print("✅ 验证码校验成功")
    else:
        print(f"❌ 验证码校验失败: {response.text}")
        return
    
    # 3. 测试完成注册
    print("\n3️⃣ 测试完成注册...")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123456",
        "verification_code": verification_code
    }
    response = requests.post(f"{BASE_URL}/users/register", json=register_data)
    
    if response.status_code == 200:
        print("✅ 用户注册成功")
        user_data = response.json()
        print(f"用户ID: {user_data['id']}")
        print(f"用户名: {user_data['username']}")
        print(f"邮箱: {user_data['email']}")
    else:
        print(f"❌ 用户注册失败: {response.text}")
        return
    
    # 4. 测试用户名登录
    print("\n4️⃣ 测试用户名登录...")
    login_data = {
        "identifier": "testuser",
        "password": "test123456"
    }
    
    response = requests.post(f"{BASE_URL}/users/login", json=login_data)
    
    if response.status_code == 200:
        print("✅ 用户名登录成功")
        login_result = response.json()
        access_token = login_result["access_token"]
        print(f"访问令牌: {access_token[:20]}...")
        print(f"用户角色: {login_result['user']['role']}")
    else:
        print(f"❌ 用户名登录失败: {response.text}")
        return
    
    # 5. 测试邮箱登录
    print("\n5️⃣ 测试邮箱登录...")
    login_data = {
        "identifier": "test@example.com",
        "password": "test123456"
    }
    
    response = requests.post(f"{BASE_URL}/users/login", json=login_data)
    
    if response.status_code == 200:
        print("✅ 邮箱登录成功")
    else:
        print(f"❌ 邮箱登录失败: {response.text}")
        return
    
    # 6. 测试获取当前用户信息
    print("\n6️⃣ 测试获取当前用户信息...")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    
    if response.status_code == 200:
        print("✅ 获取用户信息成功")
        user_info = response.json()
        print(f"用户名: {user_info['username']}")
        print(f"实名状态: {user_info['realname_status']}")
    else:
        print(f"❌ 获取用户信息失败: {response.text}")
    
    print("\n🎉 注册和登录测试完成！")


def test_password_reset():
    """测试密码重置功能"""
    print("\n🔐 开始测试密码重置功能...")
    
    # 1. 测试忘记密码
    print("\n1️⃣ 测试忘记密码...")
    forgot_data = {"email": "test@example.com"}
    response = requests.post(f"{BASE_URL}/users/forgot-password", json=forgot_data)
    
    if response.status_code == 200:
        print("✅ 密码重置请求成功")
        result = response.json()
        print(f"消息: {result['message']}")
        
        # 模拟用户从邮件中获取重置token
        reset_token = input("请输入邮件中的重置token（或输入'skip'跳过）: ")
        if reset_token.lower() == 'skip':
            print("跳过密码重置测试")
            return
    else:
        print(f"❌ 密码重置请求失败: {response.text}")
        return
    
    # 2. 测试验证重置token
    print("\n2️⃣ 测试验证重置token...")
    response = requests.get(f"{BASE_URL}/users/verify-reset-token/{reset_token}")
    
    if response.status_code == 200:
        print("✅ 重置token验证成功")
        token_data = response.json()
        print(f"邮箱: {token_data['email']}")
        print(f"剩余时间: {token_data['expires_in']}秒")
    else:
        print(f"❌ 重置token验证失败: {response.text}")
        return
    
    # 3. 测试重置密码
    print("\n3️⃣ 测试重置密码...")
    reset_data = {
        "token": reset_token,
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    }
    response = requests.post(f"{BASE_URL}/users/reset-password", json=reset_data)
    
    if response.status_code == 200:
        print("✅ 密码重置成功")
        result = response.json()
        print(f"消息: {result['message']}")
    else:
        print(f"❌ 密码重置失败: {response.text}")
    
    print("\n🎉 密码重置测试完成！")


def test_health_check():
    """测试健康检查接口"""
    print("🩺 测试健康检查...")
    response = requests.get("http://localhost:8000/health")
    
    if response.status_code == 200:
        health_data = response.json()
        print("✅ 健康检查通过")
        print(f"状态: {health_data['status']}")
        print(f"数据库: {health_data['database']}")
        print(f"Redis: {health_data['redis']}")
    else:
        print(f"❌ 健康检查失败: {response.text}")


if __name__ == "__main__":
    print("🚀 开始API测试...")
    print("⚠️ 注意：测试前请确保已配置邮件服务器并启动Redis")
    
    try:
        # 测试健康检查
        test_health_check()
        
        # 测试用户功能
        test_user_registration_and_login()
        
        # 测试密码重置功能
        choice = input("\n是否测试密码重置功能？(y/n): ")
        if choice.lower() == 'y':
            test_password_reset()
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用正在运行（python main.py）")
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}") 