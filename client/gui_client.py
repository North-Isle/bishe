# 树莓派客户端桌面应用程序（PyQt5）
import sys
import cv2
import socketio
import threading
import numpy as np
import base64
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTextEdit, 
                             QLineEdit, QSplitter, QFrame, QStatusBar)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QFont
from config import SERVER_HOST, SERVER_PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.video_utils import capture_frame, frame_to_base64, base64_to_frame, init_camera, release_camera
from utils.audio_utils import init_audio_stream, read_audio, audio_to_base64, close_audio_stream, base64_to_audio
import pyaudio


# 信号类，用于线程间通信
class Communicate(QObject):
    new_local_frame = pyqtSignal(np.ndarray)
    new_remote_frame = pyqtSignal(np.ndarray)
    new_message = pyqtSignal(dict)
    connection_status = pyqtSignal(str)


class VideoCallClient(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("远程医疗系统 - 患者端")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化SocketIO客户端
        self.sio = socketio.Client()
        self.setup_socket_events()
        
        # 视频捕获对象
        self.cap = None
        self.has_camera = False
        
        # 音频相关
        self.audio = None
        self.stream = None
        self.audio_enabled = False
        self.audio_output = None
        self.output_stream = None
        
        # 通信信号
        self.comm = Communicate()
        self.comm.new_local_frame.connect(self.update_local_video)
        self.comm.new_remote_frame.connect(self.update_remote_video)
        self.comm.new_message.connect(self.receive_message)
        self.comm.connection_status.connect(self.update_status)
        
        # 初始化UI
        self.init_ui()
        
        # 初始化摄像头
        self.init_camera()
        
        # 初始化音频播放
        self.init_audio_output()
        
        # 连接服务器
        self.connect_to_server()
        
        # 启动视频发送定时器
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.send_video_frame)
        self.video_timer.start(33)  # 约30fps
        
        # 启动音频发送线程
        self.audio_thread_running = False
        self.start_audio_thread()
    
    def init_ui(self):
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # ===== 左侧：视频区域 =====
        video_widget = QWidget()
        video_layout = QVBoxLayout(video_widget)
        video_layout.setSpacing(10)
        
        # 远程视频（医生画面）
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
        self.remote_video_label.setStyleSheet("background-color: #2a2a2a; border-radius: 4px;")
        self.remote_video_label.setAlignment(Qt.AlignCenter)
        self.remote_video_label.setText("等待医生连接...")
        self.remote_video_label.setStyleSheet("""
            background-color: #2a2a2a; 
            border-radius: 4px;
            color: #888888;
            font-size: 16px;
        """)
        remote_layout.addWidget(self.remote_video_label)
        
        video_layout.addWidget(remote_frame)
        
        # 本地视频（患者画面）
        local_frame = QFrame()
        local_frame.setFrameStyle(QFrame.StyledPanel)
        local_frame.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        local_layout = QVBoxLayout(local_frame)
        local_layout.setContentsMargins(5, 5, 5, 5)
        
        local_header = QHBoxLayout()
        local_label = QLabel("我的画面")
        local_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        local_header.addWidget(local_label)
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
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:checked {
                background-color: #f44336;
            }
            QPushButton:checked:hover {
                background-color: #da190b;
            }
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
        
        # ===== 右侧：聊天区域 =====
        chat_widget = QWidget()
        chat_widget.setMaximumWidth(400)
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setSpacing(10)
        
        # 聊天标题
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
        
        # 聊天记录显示区
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
        
        # 消息输入区
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
            QLineEdit:focus {
                border: 2px solid #4CAF50;
            }
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
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)
        
        chat_layout.addWidget(input_frame)
        
        splitter.addWidget(chat_widget)
        
        # 设置分割器比例
        splitter.setSizes([800, 400])
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("正在连接服务器...")
        
        # 设置整体样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #e8e8e8;
            }
            QWidget {
                font-family: "Microsoft YaHei", "SimHei", sans-serif;
            }
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
        """初始化音频输出（播放医生端的声音）"""
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
    
    def send_video_frame(self):
        """发送视频帧到服务器"""
        if self.has_camera and self.cap is not None:
            try:
                ret, frame = capture_frame(self.cap)
                if ret and frame is not None:
                    # 更新本地显示
                    self.comm.new_local_frame.emit(frame)
                    # 发送到服务器
                    jpg_as_text = frame_to_base64(frame)
                    if jpg_as_text and self.sio.connected:
                        self.sio.emit('video_frame', jpg_as_text)
            except Exception as e:
                print(f"发送视频错误: {e}")
    
    def start_audio_thread(self):
        """启动音频发送线程"""
        self.audio_thread_running = True
        self.audio_thread = threading.Thread(target=self.send_audio_loop)
        self.audio_thread.daemon = True
        self.audio_thread.start()
    
    def send_audio_loop(self):
        """音频发送循环"""
        while self.audio_thread_running:
            if self.audio_enabled and self.stream is not None:
                try:
                    data = read_audio(self.stream)
                    audio_data = audio_to_base64(data)
                    if self.sio.connected:
                        self.sio.emit('audio_frame', audio_data)
                except Exception as e:
                    print(f"发送音频错误: {e}")
            # 小延迟避免CPU占用过高
            import time
            time.sleep(0.01)
    
    def toggle_audio(self):
        """切换音频状态"""
        if self.audio_enabled:
            # 关闭音频
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
            # 开启音频
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
        """更新本地视频显示"""
        if frame is not None:
            # 转换颜色空间从BGR到RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 调整大小以适应显示区域
            rgb_frame = cv2.resize(rgb_frame, (320, 240))
            # 转换为QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.local_video_label.setPixmap(pixmap)
    
    def update_remote_video(self, frame):
        """更新远程视频显示（医生画面）"""
        if frame is not None:
            # 转换颜色空间从BGR到RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # 调整大小以适应显示区域
            rgb_frame = cv2.resize(rgb_frame, (640, 480))
            # 转换为QImage
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            self.remote_video_label.setPixmap(pixmap)
    
    def send_message(self):
        """发送聊天消息"""
        message = self.message_input.text().strip()
        if message and self.sio.connected:
            data = {"message": message, "sender": "patient"}
            self.sio.emit('chat_message', data)
            self.display_message("我", message, "right")
            self.message_input.clear()
    
    def receive_message(self, data):
        """接收聊天消息"""
        sender = data.get("sender", "未知")
        message = data.get("message", "")
        if sender == "doctor":
            self.display_message("医生", message, "left")
    
    def display_message(self, sender, message, align):
        """在聊天区显示消息"""
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
        # 滚动到底部
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_status(self, message):
        """更新状态栏消息"""
        self.status_bar.showMessage(message)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        self.audio_thread_running = False
        
        # 停止视频定时器
        if hasattr(self, 'video_timer'):
            self.video_timer.stop()
        
        # 断开Socket连接
        if self.sio.connected:
            self.sio.disconnect()
        
        # 释放摄像头
        if self.has_camera and self.cap is not None:
            release_camera(self.cap)
        
        # 关闭音频
        if self.audio_enabled:
            try:
                close_audio_stream(self.audio, self.stream)
            except:
                pass
        
        # 关闭音频输出
        if self.output_stream:
            self.output_stream.stop_stream()
            self.output_stream.close()
        if self.audio_output:
            self.audio_output.terminate()
        
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    client = VideoCallClient()
    client.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
