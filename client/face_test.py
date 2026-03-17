#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的人脸识别测试脚本，用于测试树莓派5上的人脸识别功能
不使用PyQt5图形界面，避免Qt平台插件冲突
"""

import sys
import os
import cv2
import numpy as np
from utils.video_utils import init_camera, capture_frame, release_camera
from utils.face_utils import detect_faces, get_face_encoding
from config import VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

# 尝试导入face_recognition库
FACE_RECOGNITION_AVAILABLE = False
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    print("✓ 成功加载face_recognition库")
except Exception as e:
    print(f"✗ 无法加载face_recognition库: {e}")

def test_camera():
    """测试摄像头功能"""
    print("\n正在测试摄像头...")
    cap = init_camera(VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS)
    if not cap:
        print("✗ 摄像头初始化失败")
        return False
    
    print("✓ 摄像头初始化成功")
    
    # 测试捕获几帧
    for i in range(3):
        ret, frame = capture_frame(cap)
        if ret and frame is not None:
            print(f"✓ 成功捕获第 {i+1} 帧，尺寸: {frame.shape}")
        else:
            print(f"✗ 捕获第 {i+1} 帧失败")
    
    release_camera(cap)
    print("✓ 摄像头资源已释放")
    return True

def test_face_detection():
    """测试人脸检测功能"""
    print("\n正在测试人脸检测...")
    
    cap = init_camera(VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS)
    if not cap:
        print("✗ 无法初始化摄像头")
        return False
    
    print("请面对摄像头...")
    
    # 尝试检测人脸
    for i in range(5):
        ret, frame = capture_frame(cap)
        if ret and frame is not None:
            print(f"捕获帧 {i+1}...")
            face_locations = detect_faces(frame)
            
            if len(face_locations) > 0:
                print(f"✓ 检测到 {len(face_locations)} 张人脸")
                
                # 测试人脸特征提取
                if FACE_RECOGNITION_AVAILABLE:
                    face_encoding = get_face_encoding(frame, face_locations[0])
                    if face_encoding:
                        print("✓ 成功提取人脸特征")
                        print(f"人脸特征向量长度: {len(face_encoding)}")
                    else:
                        print("✗ 人脸特征提取失败")
                
                release_camera(cap)
                return True
            else:
                print("未检测到人脸，继续尝试...")
        
        import time
        time.sleep(0.5)
    
    release_camera(cap)
    print("✗ 多次尝试后仍未检测到人脸")
    return False

def main():
    """主函数"""
    print("=== 树莓派5人脸识别测试脚本 ===")
    
    # 测试摄像头
    if not test_camera():
        print("\n❌ 摄像头测试失败")
        sys.exit(1)
    
    # 测试人脸检测
    if not test_face_detection():
        print("\n❌ 人脸检测测试失败")
        sys.exit(1)
    
    print("\n🎉 所有测试通过！人脸识别功能正常工作")
    print("\n接下来可以尝试:")
    print("1. 安装PyQt5依赖: sudo apt install -y python3-pyqt5 libqt5gui5 libqt5widgets5")
    print("2. 安装xcb依赖: sudo apt install -y libxcb-xinerama0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xkb1")
    print("3. 重新运行GUI客户端")

if __name__ == "__main__":
    main()