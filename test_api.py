import requests
import time

# 等待服务启动
print("等待服务启动...")
time.sleep(3)

try:
    # 测试健康检查
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"\n健康检查状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    # 测试根路径
    response = requests.get("http://localhost:8000/", timeout=5)
    print(f"\n根路径状态: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    print("\n[OK] 服务运行正常！")
    print("\nAPI文档地址:")
    print("- Swagger UI: http://localhost:8000/docs")
    print("- ReDoc: http://localhost:8000/redoc")
    
except requests.exceptions.ConnectionError:
    print("\n[ERROR] 无法连接到服务，请检查:")
    print("1. 服务是否已启动")
    print("2. 端口8000是否被占用")
    print("3. 防火墙设置")
except Exception as e:
    print(f"\n[ERROR] 测试失败: {str(e)}")

