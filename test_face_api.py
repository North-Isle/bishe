#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试人脸API功能
"""

import requests
import json

# 服务器地址
SERVER_URL = 'http://localhost:5000'

def test_face_recognize():
    print("=== 测试人脸识别人API ===")
    url = f"{SERVER_URL}/api/face/recognize"
    
    # 创建一个假的人脸编码
    fake_face_encoding = [0.1] * 128
    data = {
        "face_encoding": fake_face_encoding
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        # 尝试解析JSON
        result = response.json()
        print("✅ 响应是有效的JSON格式")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ 响应不是有效的JSON格式: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_register_api():
    print("\n=== 测试用户注册API ===")
    url = f"{SERVER_URL}/api/register"
    
    try:
        response = requests.post(url, json={})
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        # 尝试解析JSON
        result = response.json()
        print("✅ 响应是有效的JSON格式")
        return True
    except json.JSONDecodeError as e:
        print(f"❌ 响应不是有效的JSON格式: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始测试人脸API...\n")
    
    # 测试人脸识别人API
    test_face_recognize()
    
    # 测试用户注册API
    test_register_api()
    
    print("\n=== 测试完成 ===")
