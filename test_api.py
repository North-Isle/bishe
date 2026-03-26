#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试服务器API功能
"""

import requests
import json

# 服务器地址
SERVER_URL = 'http://localhost:5000'

# 测试API登录功能
def test_api_login():
    print("=== 测试API登录功能 ===")
    url = f"{SERVER_URL}/api/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ API登录功能正常")
                return True
        print("❌ API登录功能异常")
        return False
    except Exception as e:
        print(f"❌ API登录测试失败: {e}")
        return False

# 测试人脸相关API（需要先登录）
def test_face_api():
    print("\n=== 测试人脸API功能 ===")
    
    # 先登录获取权限
    login_url = f"{SERVER_URL}/api/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        if login_response.status_code != 200:
            print("❌ 登录失败，无法测试人脸API")
            return
        
        # 获取登录的用户ID
        login_result = login_response.json()
        user_id = login_result['user']['id']
        
        # 测试人脸注册API
        print("\n--- 测试人脸注册API ---")
        register_url = f"{SERVER_URL}/api/face/register"
        # 创建一个假的人脸编码（128维）
        fake_face_encoding = [0.1] * 128
        register_data = {
            "user_id": user_id,
            "face_encoding": fake_face_encoding
        }
        
        # 需要使用会话保持登录状态
        session = requests.Session()
        # 手动复制登录时的cookie（简化测试）
        session.cookies.update(login_response.cookies)
        
        register_response = session.post(register_url, json=register_data)
        print(f"状态码: {register_response.status_code}")
        print(f"响应: {register_response.text}")
        
        if register_response.status_code == 200:
            register_result = register_response.json()
            if register_result.get('success'):
                print("✅ 人脸注册API功能正常")
            else:
                print("❌ 人脸注册API功能异常")
        else:
            print("❌ 人脸注册API返回异常状态码")
        
        # 测试人脸识别API
        print("\n--- 测试人脸识别API ---")
        recognize_url = f"{SERVER_URL}/api/face/recognize"
        recognize_data = {
            "face_encoding": fake_face_encoding
        }
        
        recognize_response = requests.post(recognize_url, json=recognize_data)
        print(f"状态码: {recognize_response.status_code}")
        print(f"响应: {recognize_response.text}")
        
        if recognize_response.status_code == 200:
            print("✅ 人脸识别API功能正常")
        else:
            print("❌ 人脸识别API功能异常")
            
    except Exception as e:
        print(f"❌ 人脸API测试失败: {e}")
        import traceback
        traceback.print_exc()

# 测试用户注册API
def test_user_register():
    print("\n=== 测试用户注册API ===")
    url = f"{SERVER_URL}/api/register"
    
    # 需要先登录管理员账号获取权限
    login_url = f"{SERVER_URL}/api/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        if login_response.status_code != 200:
            print("❌ 登录失败，无法测试用户注册API")
            return
        
        session = requests.Session()
        session.cookies.update(login_response.cookies)
        
        # 测试注册医生用户
        register_data = {
            "username": "test_doctor",
            "password": "test123",
            "real_name": "测试医生",
            "role": "doctor"
        }
        
        register_response = session.post(url, json=register_data)
        print(f"状态码: {register_response.status_code}")
        print(f"响应: {register_response.text}")
        
        if register_response.status_code == 200:
            register_result = register_response.json()
            if register_result.get('success'):
                print("✅ 用户注册API功能正常")
            else:
                print("❌ 用户注册API功能异常")
        else:
            print("❌ 用户注册API返回异常状态码")
            
    except Exception as e:
        print(f"❌ 用户注册API测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("开始测试服务器API功能...\n")
    
    # 测试API登录
    test_api_login()
    
    # 测试用户注册
    test_user_register()
    
    # 测试人脸API
    test_face_api()
    
    print("\n=== 测试完成 ===")
