# 树莓派客户端桌面应用程序（PyQt5）
import sys
import os

# 移除OpenCV的Qt插件路径，避免与PyQt5冲突
os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH", None)

import cv2
import socketio
import threading
import numpy as np
import base64
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QLineEdit, QSplitter, QFrame, QStatusBar,
                             QDialog, QTabWidget, QFormLayout, QMessageBox,
                             QStackedWidget, QGroupBox, QScrollArea)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QFont
from config import SERVER_HOST, SERVER_PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.video_utils import capture_frame, frame_to_base64, base64_to_frame, init_camera, release_camera
from utils.audio_utils import init_audio_stream, read_audio, audio_to_base64, close_audio_stream, base64_to_audio
from utils.face_utils import (detect_faces, get_face_encoding, draw_face_box,
                              register_face_with_server, recognize_face_with_server,
                              register_user_with_server, login_with_server,
                              is_face_recognition_available)
import pyaudio


class Communicate(QObject):
    new_local_frame = pyqtSignal(np.ndarray)
    new_remote_frame = pyqtSignal(np.ndarray)
    new_message = pyqtSignal(dict)
    connection_status = pyqtSignal(str)
    face_detected = pyqtSignal(object)


class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("远程医疗系统 - 登录")
        self.resize(1100, 550)
        self.current_user = None
        self.face_encoding = None
        self.face_timer = None
        self.cap = None
        self.init_ui()
        self.init_camera()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("🏥 远程医疗系统")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # 创建滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 创建内容widget
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        
        # 内容layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tab_widget = QTabWidget()
        content_layout.addWidget(self.tab_widget)
        
        main_layout.addWidget(scroll)
        
        login_tab = QWidget()
        login_layout = QVBoxLayout(login_tab)
        login_layout.setSpacing(15)
        
        login_group = QGroupBox("账号密码登录")
        login_form = QFormLayout(login_group)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        login_form.addRow("用户名:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        login_form.addRow("密码:", self.password_input)
        
        login_layout.addWidget(login_group)
        
        login_btn = QPushButton("登录")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        login_btn.clicked.connect(self.handle_login)
        login_layout.addWidget(login_btn)
        
        face_login_group = QGroupBox("人脸登录")
        face_login_layout = QVBoxLayout(face_login_group)
        
        self.face_login_video = QLabel()
        self.face_login_video.setFixedSize(300, 225)
        self.face_login_video.setStyleSheet("background-color: #2a2a2a; border-radius: 8px;")
        self.face_login_video.setAlignment(Qt.AlignCenter)
        self.face_login_video.setText("摄像头加载中...")
        face_login_layout.addWidget(self.face_login_video, alignment=Qt.AlignCenter)
        
        self.face_login_btn = QPushButton("👤 人脸登录")
        self.face_login_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #219a52; }
        """)
        self.face_login_btn.clicked.connect(self.handle_face_login)
        face_login_layout.addWidget(self.face_login_btn)
        
        login_layout.addWidget(face_login_group)
        login_layout.addStretch()
        
        self.tab_widget.addTab(login_tab, "登录")
        
        register_tab = QWidget()
        register_layout = QVBoxLayout(register_tab)
        register_layout.setSpacing(15)
        
        register_group = QGroupBox("注册新用户")
        register_form = QFormLayout(register_group)
        
        self.reg_username = QLineEdit()
        self.reg_username.setPlaceholderText("请输入用户名")
        register_form.addRow("用户名:", self.reg_username)
        
        self.reg_password = QLineEdit()
        self.reg_password.setPlaceholderText("请输入密码")
        self.reg_password.setEchoMode(QLineEdit.Password)
        register_form.addRow("密码:", self.reg_password)
        
        self.reg_real_name = QLineEdit()
        self.reg_real_name.setPlaceholderText("请输入真实姓名")
        register_form.addRow("姓名:", self.reg_real_name)
        
        self.reg_id_card = QLineEdit()
        self.reg_id_card.setPlaceholderText("请输入身份证号")
        register_form.addRow("身份证:", self.reg_id_card)
        
        register_layout.addWidget(register_group)
        
        face_reg_group = QGroupBox("人脸注册（可选）")
        face_reg_layout = QVBoxLayout(face_reg_group)
        
        self.face_reg_video = QLabel()
        self.face_reg_video.setFixedSize(300, 225)
        self.face_reg_video.setStyleSheet("background-color: #2a2a2a; border-radius: 8px;")
        self.face_reg_video.setAlignment(Qt.AlignCenter)
        self.face_reg_video.setText("摄像头加载中...")
        face_reg_layout.addWidget(self.face_reg_video, alignment=Qt.AlignCenter)
        
        self.capture_face_btn = QPushButton("📷 采集人脸")
        self.capture_face_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.capture_face_btn.clicked.connect(self.capture_face)
        face_reg_layout.addWidget(self.capture_face_btn)
        
        self.face_status_label = QLabel("状态: 等待采集人脸")
        self.face_status_label.setStyleSheet("color: #7f8c8d;")
        face_reg_layout.addWidget(self.face_status_label)
        
        register_layout.addWidget(face_reg_group)
        
        register_btn = QPushButton("注册")
        register_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 12px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #8e44ad; }
        """)
        register_btn.clicked.connect(self.handle_register)
        register_layout.addWidget(register_btn)
        
        register_layout.addStretch()
        
        self.tab_widget.addTab(register_tab, "注册")
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("请登录或注册")
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
        """)
    
    def init_camera(self):
        try:
            self.cap = init_camera(VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS)
            if self.cap:
                self.face_timer = QTimer()
                self.face_timer.timeout.connect(self.update_face_video)
                self.face_timer.start(100)
            else:
                self.face_login_video.setText("摄像头不可用")
                self.face_reg_video.setText("摄像头不可用")
        except Exception as e:
            self.face_login_video.setText(f"摄像头错误: {e}")
            self.face_reg_video.setText(f"摄像头错误: {e}")
    
    def update_face_video(self):
        if self.cap is None:
            return
        
        try:
            ret, frame = capture_frame(self.cap)
            if ret and frame is not None:
                small_frame = cv2.resize(frame, (300, 225))
                
                face_locations = detect_faces(small_frame)
                
                if len(face_locations) > 0:
                    for loc in face_locations:
                        draw_face_box(small_frame, loc, color=(0, 255, 0))
                
                rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_frame.shape
                qt_image = QImage(rgb_frame.data, w, h, ch * w, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qt_image)
                
                self.face_login_video.setPixmap(pixmap)
                self.face_reg_video.setPixmap(pixmap)
        except Exception as e:
            print(f"更新视频错误: {e}")
    
    def capture_face(self):
        if self.cap is None:
            QMessageBox.warning(self, "错误", "摄像头不可用")
            return
        
        try:
            ret, frame = capture_frame(self.cap)
            if ret and frame is not None:
                face_locations = detect_faces(frame)
                if len(face_locations) == 0:
                    self.face_status_label.setText("状态: 未检测到人脸")
                    self.face_status_label.setStyleSheet("color: #e74c3c;")
                    return
                
                if len(face_locations) > 1:
                    self.face_status_label.setText("状态: 检测到多张人脸，请只保留一张")
                    self.face_status_label.setStyleSheet("color: #e74c3c;")
                    return
                
                face_encoding = get_face_encoding(frame, face_locations[0])
                if face_encoding:
                    self.face_encoding = face_encoding
                    self.face_status_label.setText("状态: 人脸采集成功 ✓")
                    self.face_status_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                else:
                    self.face_status_label.setText("状态: 人脸特征提取失败")
                    self.face_status_label.setStyleSheet("color: #e74c3c;")
        except Exception as e:
            self.face_status_label.setText(f"状态: 错误 - {e}")
            self.face_status_label.setStyleSheet("color: #e74c3c;")
    
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "提示", "请输入用户名和密码")
            return
        
        success, result = login_with_server(SERVER_HOST, SERVER_PORT, username, password)
        if success:
            self.current_user = result
            self.open_main_window()
        else:
            QMessageBox.warning(self, "登录失败", str(result))
    
    def handle_face_login(self):
        if self.cap is None:
            QMessageBox.warning(self, "错误", "摄像头不可用")
            return
        
        if not is_face_recognition_available():
            QMessageBox.warning(self, "提示", "人脸识别功能需要安装 face_recognition 库\n请运行: pip install face_recognition")
            return
        
        try:
            ret, frame = capture_frame(self.cap)
            if ret and frame is not None:
                face_locations = detect_faces(frame)
                if len(face_locations) == 0:
                    QMessageBox.warning(self, "提示", "未检测到人脸")
                    return
                
                face_encoding = get_face_encoding(frame, face_locations[0])
                if face_encoding:
                    success, result = recognize_face_with_server(SERVER_HOST, SERVER_PORT, face_encoding)
                    if success:
                        self.current_user = result
                        self.open_main_window()
                    else:
                        QMessageBox.warning(self, "人脸登录失败", str(result))
                else:
                    QMessageBox.warning(self, "提示", "无法提取人脸特征")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"人脸登录失败: {e}")
    
    def handle_register(self):
        username = self.reg_username.text().strip()
        password = self.reg_password.text().strip()
        real_name = self.reg_real_name.text().strip()
        id_card = self.reg_id_card.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "提示", "用户名和密码不能为空")
            return
        
        success, result = register_user_with_server(SERVER_HOST, SERVER_PORT, username, password, real_name, id_card)
        if success:
            user_id = result
            if self.face_encoding:
                face_success, face_msg = register_face_with_server(SERVER_HOST, SERVER_PORT, user_id, self.face_encoding)
                if face_success:
                    QMessageBox.information(self, "成功", "注册成功，人脸已绑定！")
                else:
                    QMessageBox.information(self, "成功", f"注册成功，但人脸绑定失败: {face_msg}")
            else:
                QMessageBox.information(self, "成功", "注册成功！")
            
            self.tab_widget.setCurrentIndex(0)
            self.username_input.setText(username)
            self.password_input.setFocus()
        else:
            QMessageBox.warning(self, "注册失败", str(result))
    
    def open_main_window(self):
        if self.face_timer:
            self.face_timer.stop()
        if self.cap:
            release_camera(self.cap)
        
        self.main_window = VideoCallClient(self.current_user)
        self.main_window.show()
        self.close()
    
    def closeEvent(self, event):
        if self.face_timer:
            self.face_timer.stop()
        if self.cap:
            release_camera(self.cap)
        event.accept()


class VideoCallClient(QMainWindow):
    def __init__(self, user_info):
        super().__init__()
        self.user_info = user_info
        self.setWindowTitle(f"远程医疗系统 - {user_info.get('real_name', user_info.get('username', '用户'))}")
        self.resize(1400, 900)
        
        self.sio = socketio.Client()
        self.setup_socket_events()
        
        self.cap = None
        self.has_camera = False
        
        self.audio = None
        self.stream = None
        self.audio_enabled = False
        self.audio_output = None
        self.output_stream = None
        
        self.comm = Communicate()
        self.comm.new_local_frame.connect(self.update_local_video)
        self.comm.new_remote_frame.connect(self.update_remote_video)
        self.comm.new_message.connect(self.receive_message)
        self.comm.connection_status.connect(self.update_status)
        
        self.init_ui()
        self.init_camera()
        self.init_audio_output()
        self.init_audio_input()
        self.connect_to_server()
        
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.send_video_frame)
        self.video_timer.start(66)
        
        self.audio_thread_running = False
        self.start_audio_thread()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        video_widget = QWidget()
        video_layout = QVBoxLayout(video_widget)
        video_layout.setSpacing(10)
        
        remote_frame = QFrame()
        remote_frame.setFrameStyle(QFrame.StyledPanel)
        remote_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        remote_layout = QVBoxLayout(remote_frame)
        
        remote_label = QLabel("医生画面")
        remote_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        remote_label.setAlignment(Qt.AlignCenter)
        remote_layout.addWidget(remote_label)
        
        self.remote_video_label = QLabel()
        self.remote_video_label.setMinimumSize(640, 480)
        self.remote_video_label.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 4px;
            color: #888888;
            font-size: 16px;
        """)
        self.remote_video_label.setAlignment(Qt.AlignCenter)
        self.remote_video_label.setText("等待医生连接...")
        remote_layout.addWidget(self.remote_video_label)
        
        video_layout.addWidget(remote_frame)
        
        local_frame = QFrame()
        local_frame.setFrameStyle(QFrame.StyledPanel)
        local_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        local_layout = QVBoxLayout(local_frame)
        local_layout.setContentsMargins(5, 5, 5, 5)
        
        local_header = QHBoxLayout()
        local_label = QLabel("我的画面")
        local_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        local_header.addWidget(local_label)
        
        user_info_label = QLabel(f"👤 {self.user_info.get('real_name', self.user_info.get('username', '用户'))}")
        user_info_label.setStyleSheet("color: #3498db; font-size: 12px;")
        local_header.addWidget(user_info_label)
        local_header.addStretch()
        
        self.audio_btn = QPushButton("🎤 开启音频")
        self.audio_btn.setCheckable(True)
        self.audio_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:checked { background-color: #f44336; }
            QPushButton:checked:hover { background-color: #da190b; }
        """)
        self.audio_btn.clicked.connect(self.toggle_audio)
        local_header.addWidget(self.audio_btn)
        
        local_layout.addLayout(local_header)
        
        self.local_video_label = QLabel()
        self.local_video_label.setFixedSize(320, 240)
        self.local_video_label.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 4px;
            color: #888888;
            font-size: 12px;
        """)
        self.local_video_label.setAlignment(Qt.AlignCenter)
        self.local_video_label.setText("摄像头初始化中...")
        local_layout.addWidget(self.local_video_label)
        
        video_layout.addWidget(local_frame, alignment=Qt.AlignLeft)
        
        splitter.addWidget(video_widget)
        
        chat_widget = QWidget()
        chat_widget.setMaximumWidth(400)
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setSpacing(10)
        
        chat_title = QLabel("💬 医患交流")
        chat_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #333;
            padding: 10px;
            background-color: #f0f0f0;
            border-radius: 8px;
        """)
        chat_title.setAlignment(Qt.AlignCenter)
        chat_layout.addWidget(chat_title)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        chat_layout.addWidget(self.chat_display)
        
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 8px;")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setSpacing(8)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus { border: 2px solid #4CAF50; }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.message_input)
        
        send_btn = QPushButton("发送消息")
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        chat_layout.addWidget(input_frame)
        
        logout_btn = QPushButton("退出登录")
        logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        logout_btn.clicked.connect(self.logout)
        chat_layout.addWidget(logout_btn)
        
        splitter.addWidget(chat_widget)
        
        splitter.setSizes([800, 400])
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("正在连接服务器...")
        
        self.setStyleSheet("""
            QMainWindow { background-color: #e8e8e8; }
            QWidget { font-family: "Microsoft YaHei", "SimHei", sans-serif; }
        """)
    
    def setup_socket_events(self):
        @self.sio.on('connect')
        def on_connect():
            self.comm.connection_status.emit("已连接到服务器")
            print('Connected to server')
        
        @self.sio.on('disconnect')
        def on_disconnect():
            self.comm.connection_status.emit("与服务器断开连接")
            print('Disconnected from server')
        
        @self.sio.on('video_frame')
        def on_video_frame(data):
            frame = base64_to_frame(data)
            if frame is not None:
                self.comm.new_remote_frame.emit(frame)
        
        @self.sio.on('audio_frame')
        def on_audio_frame(data):
            if self.audio_enabled and self.output_stream:
                try:
                    audio_data = base64_to_audio(data)
                    self.output_stream.write(audio_data)
                except Exception as e:
                    print(f"播放音频错误: {e}")
        
        @self.sio.on('chat_message')
        def on_chat_message(data):
            self.comm.new_message.emit(data)
    
    def connect_to_server(self):
        try:
            self.sio.connect(f'http://{SERVER_HOST}:{SERVER_PORT}')
        except Exception as e:
            self.update_status(f'连接服务器失败: {e}')
            print(f'Error connecting to server: {e}')
    
    def init_camera(self):
        try:
            self.cap = init_camera(VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS)
            if self.cap is not None:
                self.has_camera = True
                self.update_status("摄像头初始化成功")
                print("摄像头初始化成功")
            else:
                self.update_status("摄像头初始化失败")
                print("摄像头初始化失败")
        except Exception as e:
            self.update_status(f"摄像头错误: {e}")
            print(f"摄像头初始化错误: {e}")
    
    def init_audio_output(self):
        try:
            self.audio_output = pyaudio.PyAudio()
            self.output_stream = self.audio_output.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=44100,
                output=True,
                frames_per_buffer=1024
            )
            print("音频输出初始化成功")
        except Exception as e:
            print(f"音频输出初始化错误: {e}")
    
    def init_audio_input(self):
        try:
            self.audio, self.stream = init_audio_stream()
            self.audio_enabled = True
            self.audio_btn.setText("🔇 关闭音频")
            self.update_status("音频已开启")
            print("音频输入初始化成功")
        except Exception as e:
            self.update_status(f"音频开启失败: {e}")
            print(f"音频输入初始化错误: {e}")
    
    def send_video_frame(self):
        if self.has_camera and self.cap is not None:
            try:
                ret, frame = capture_frame(self.cap)
                if ret and frame is not None:
                    self.comm.new_local_frame.emit(frame)
                    jpg_as_text = frame_to_base64(frame)
                    if jpg_as_text and self.sio.connected:
                        self.sio.emit('video_frame', jpg_as_text)
            except Exception as e:
                print(f"发送视频错误: {e}")
    
    def start_audio_thread(self):
        self.audio_thread_running = True
        self.audio_thread = threading.Thread(target=self.send_audio_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()
    
    def send_audio_loop(self):
        while self.audio_thread_running:
            if self.audio_enabled and self.stream is not None:
                try:
                    data = read_audio(self.stream)
                    audio_data = audio_to_base64(data)
                    if self.sio.connected:
                        self.sio.emit('audio_frame', audio_data)
                except Exception as e:
                    print(f"发送音频错误: {e}")
            import time
            time.sleep(0.01)
    
    def toggle_audio(self):
        if self.audio_enabled:
            try:
                if self.stream:
                    close_audio_stream(self.audio, self.stream)
                self.audio, self.stream = None, None
                self.audio_enabled = False
                self.audio_btn.setText("🎤 开启音频")
                self.update_status("音频已关闭")
                print("音频已关闭")
            except Exception as e:
                print(f"关闭音频错误: {e}")
        else:
            try:
                self.audio, self.stream = init_audio_stream()
                self.audio_enabled = True
                self.audio_btn.setText("🔇 关闭音频")
                self.update_status("音频已开启")
                print("音频已开启")
            except Exception as e:
                self.update_status(f"音频开启失败: {e}")
                print(f"音频初始化错误: {e}")
    
    def update_local_video(self, frame):
        if frame is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame = cv2.resize(rgb_frame, (320, 240))
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.local_video_label.setPixmap(pixmap)
    
    def update_remote_video(self, frame):
        if frame is not None:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb_frame = cv2.resize(rgb_frame, (640, 480))
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.remote_video_label.setPixmap(pixmap)
    
    def send_message(self):
        message = self.message_input.text().strip()
        if message and self.sio.connected:
            data = {"message": message, "sender": "patient"}
            self.sio.emit('chat_message', data)
            self.display_message("我", message, "right")
            self.message_input.clear()
    
    def receive_message(self, data):
        sender = data.get("sender", "未知")
        message = data.get("message", "")
        if sender == "doctor":
            self.display_message("医生", message, "left")
    
    def display_message(self, sender, message, align):
        if align == "right":
            html = f'''
            <div style="text-align: right; margin: 5px 0;">
                <span style="background-color: #DCF8C6; padding: 8px 12px; border-radius: 12px; display: inline-block; max-width: 80%; word-wrap: break-word;">
                    <b>{sender}</b><br/>{message}
                </span>
            </div>
            '''
        else:
            html = f'''
            <div style="text-align: left; margin: 5px 0;">
                <span style="background-color: #FFFFFF; padding: 8px 12px; border-radius: 12px; display: inline-block; max-width: 80%; word-wrap: break-word; border: 1px solid #ddd;">
                    <b>{sender}</b><br/>{message}
                </span>
            </div>
            '''
        self.chat_display.append(html)
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, message):
        self.status_bar.showMessage(message)
    
    def logout(self):
        reply = QMessageBox.question(self, '确认退出', '确定要退出登录吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()
            self.login_window = LoginWindow()
            self.login_window.show()
    
    def closeEvent(self, event):
        self.audio_thread_running = False
        
        if hasattr(self, 'video_timer'):
            self.video_timer.stop()
        
        if self.sio.connected:
            self.sio.disconnect()
        
        if self.has_camera and self.cap is not None:
            release_camera(self.cap)
        
        if self.audio_enabled:
            try:
                close_audio_stream(self.audio, self.stream)
            except:
                pass
        
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        if self.audio_output:
            self.audio_output.terminate()
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    login_window = LoginWindow()
    login_window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
