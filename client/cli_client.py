#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于命令行的树莓派客户端
完全避免使用PyQt5图形界面，解决Qt平台插件冲突问题
"""

import sys
import os
import cv2
import numpy as np
import time
from utils.video_utils import init_camera, capture_frame, release_camera
from utils.face_utils import (
    detect_faces, get_face_encoding, register_face_with_server,
    recognize_face_with_server, register_user_with_server, login_with_server,
    is_face_recognition_available
)
from config import SERVER_HOST, SERVER_PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

# 清除OpenCV的Qt插件路径
ios.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

# 确保不使用任何Qt功能
os.environ["OPENCV_IGNORE_QT"] = "1"

class CLIClient:
    def __init__(self):
        self.cap = None
        self.current_user = None
        self.face_encoding = None
    
    def print_banner(self):
        """打印欢迎信息"""
        print("=" * 50)
        print("🏥 远程医疗系统 - 命令行客户端")
        print("=" * 50)
        print("服务器地址: {0}:{1}".format(SERVER_HOST, SERVER_PORT))
        print("人脸识别功能: {0}".format("可用" if is_face_recognition_available() else "不可用"))
        print("=" * 50)
    
    def init_camera(self):
        """初始化摄像头"""
        print("\n正在初始化摄像头...")
        self.cap = init_camera(VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS)
        if not self.cap:
            print("❌ 摄像头初始化失败")
            return False
        print("✅ 摄像头初始化成功")
        return True
    
    def release_camera(self):
        """释放摄像头资源"""
        if self.cap:
            release_camera(self.cap)
            self.cap = None
    
    def register_new_user(self):
        """注册新用户"""
        print("\n=== 用户注册 ===")
        
        username = input("请输入用户名: ").strip()
        if not username:
            print("❌ 用户名不能为空")
            return
            
        password = input("请输入密码: ").strip()
        if not password:
            print("❌ 密码不能为空")
            return
            
        real_name = input("请输入真实姓名: ").strip()
        id_card = input("请输入身份证号: ").strip()
        
        print("正在注册用户...")
        success, result = register_user_with_server(SERVER_HOST, SERVER_PORT, 
                                                   username, password, real_name, id_card)
        
        if success:
            user_id = result
            print("✅ 用户注册成功！用户ID: {0}".format(user_id))
            
            # 询问是否注册人脸
            register_face = input("是否注册人脸（y/n）: ").lower()
            if register_face == 'y' and is_face_recognition_available():
                self.register_face(user_id)
        else:
            print("❌ 注册失败: {0}".format(result))
    
    def register_face(self, user_id):
        """注册人脸"""
        print("\n=== 人脸注册 ===")
        print("请面对摄像头，确保光线充足...")
        
        if not self.cap and not self.init_camera():
            return
        
        face_detected = False
        
        for i in range(10):  # 尝试10次
            print("正在检测人脸... ({0}/10)".format(i+1))
            ret, frame = capture_frame(self.cap)
            
            if ret and frame is not None:
                face_locations = detect_faces(frame)
                
                if len(face_locations) == 1:
                    print("✅ 检测到人脸！正在提取特征...")
                    
                    face_encoding = get_face_encoding(frame, face_locations[0])
                    if face_encoding:
                        print("✅ 人脸特征提取成功！正在注册到服务器...")
                        
                        # 发送到服务器
                        success, message = register_face_with_server(SERVER_HOST, SERVER_PORT, 
                                                                   user_id, face_encoding)
                        
                        if success:
                            print("✅ 人脸注册成功！")
                            self.face_encoding = face_encoding
                            face_detected = True
                            break
                        else:
                            print("❌ 人脸注册失败: {0}".format(message))
                            break
                    else:
                        print("❌ 人脸特征提取失败")
                elif len(face_locations) > 1:
                    print("❌ 检测到多张人脸，请确保画面中只有一个人")
                else:
                    print("❌ 未检测到人脸")
            
            time.sleep(1)  # 等待1秒后再次尝试
        
        if not face_detected:
            print("❌ 多次尝试后仍未成功注册人脸")
    
    def login_with_password(self):
        """密码登录"""
        print("\n=== 密码登录 ===")
        
        username = input("请输入用户名: ").strip()
        password = input("请输入密码: ").strip()
        
        if not username or not password:
            print("❌ 用户名和密码不能为空")
            return
            
        print("正在登录...")
        success, result = login_with_server(SERVER_HOST, SERVER_PORT, username, password)
        
        if success:
            self.current_user = result
            print("✅ 登录成功！")
            print("欢迎, {0} ({1})".format(self.current_user.get('real_name', self.current_user.get('username')), 
                                          self.current_user.get('role')))
        else:
            print("❌ 登录失败: {0}".format(result))
    
    def login_with_face(self):
        """人脸登录"""
        print("\n=== 人脸登录 ===")
        
        if not is_face_recognition_available():
            print("❌ 人脸识别功能不可用")
            print("请安装face_recognition库: pip install face_recognition")
            return
            
        if not self.cap and not self.init_camera():
            return
        
        print("请面对摄像头，确保光线充足...")
        
        face_detected = False
        
        for i in range(10):  # 尝试10次
            print("正在检测人脸... ({0}/10)".format(i+1))
            ret, frame = capture_frame(self.cap)
            
            if ret and frame is not None:
                face_locations = detect_faces(frame)
                
                if len(face_locations) == 1:
                    print("✅ 检测到人脸！正在识别...")
                    
                    face_encoding = get_face_encoding(frame, face_locations[0])
                    if face_encoding:
                        print("✅ 正在验证身份...")
                        
                        # 发送到服务器进行识别
                        success, result = recognize_face_with_server(SERVER_HOST, SERVER_PORT, 
                                                                    face_encoding)
                        
                        if success:
                            self.current_user = result
                            print("✅ 人脸识别成功！")
                            print("欢迎, {0} ({1})".format(self.current_user.get('real_name', self.current_user.get('username')), 
                                                          self.current_user.get('role')))
                            face_detected = True
                            break
                        else:
                            print("❌ 人脸识别失败: {0}".format(result))
                            break
                    else:
                        print("❌ 人脸特征提取失败")
                elif len(face_locations) > 1:
                    print("❌ 检测到多张人脸，请确保画面中只有一个人")
                else:
                    print("❌ 未检测到人脸")
            
            time.sleep(1)  # 等待1秒后再次尝试
        
        if not face_detected:
            print("❌ 多次尝试后仍未成功登录")
    
    def show_main_menu(self):
        """显示主菜单"""
        while True:
            print("\n=== 主菜单 ===")
            print("1. 注册新用户")
            print("2. 密码登录")
            print("3. 人脸登录")
            print("4. 退出")
            
            choice = input("请选择操作 (1-4): ").strip()
            
            if choice == '1':
                self.register_new_user()
            elif choice == '2':
                self.login_with_password()
                if self.current_user:
                    self.show_user_menu()
            elif choice == '3':
                self.login_with_face()
                if self.current_user:
                    self.show_user_menu()
            elif choice == '4':
                print("\n感谢使用，再见！")
                self.release_camera()
                break
            else:
                print("❌ 无效的选择，请重新输入")
    
    def show_user_menu(self):
        """显示用户菜单"""
        while True:
            print("\n=== 用户菜单 ===")
            print("1. 重新注册人脸")
            print("2. 退出登录")
            
            choice = input("请选择操作 (1-2): ").strip()
            
            if choice == '1':
                if self.current_user:
                    self.register_face(self.current_user.get('id'))
            elif choice == '2':
                print("\n已退出登录")
                self.current_user = None
                break
            else:
                print("❌ 无效的选择，请重新输入")

def main():
    """主函数"""
    client = CLIClient()
    client.print_banner()
    client.show_main_menu()

if __name__ == "__main__":
    main()