# 客户端主程序（树莓派端）- 使用PyQt5桌面应用
# 推荐使用 run_client.py 启动图形界面
# 此文件保留作为备用命令行版本

import cv2
import socketio
import threading
import numpy as np
from config import SERVER_HOST, SERVER_PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.video_utils import capture_frame, frame_to_base64, base64_to_frame, show_frame, init_camera, release_camera
from utils.audio_utils import init_audio_stream, read_audio, audio_to_base64, close_audio_stream

# 初始化SocketIO客户端
sio = socketio.Client()

# 视频捕获对象
cap = None
has_camera = False

# 尝试初始化摄像头
try:
    cap = init_camera(VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS)
    if cap is not None:
        has_camera = True
        print("摄像头初始化成功")
    else:
        print("摄像头初始化失败，将使用默认帧")
        cap = None
except Exception as e:
    print(f"摄像头初始化错误: {e}，将使用默认帧")
    cap = None

# 创建默认帧（黑色背景）
def get_default_frame():
    return np.zeros((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)

# 音频流控制
audio, stream = None, None
audio_enabled = False

# 初始化音频流
def init_audio():
    global audio, stream, audio_enabled
    try:
        audio, stream = init_audio_stream()
        audio_enabled = True
        print("音频初始化成功")
    except Exception as e:
        print(f"音频初始化错误: {e}")
        audio, stream = None, None
        audio_enabled = False

# 切换音频状态
def toggle_audio():
    global audio, stream, audio_enabled
    if audio_enabled:
        try:
            close_audio_stream(audio, stream)
            audio, stream = None, None
            audio_enabled = False
            print("音频已关闭")
        except Exception as e:
            print(f"关闭音频错误: {e}")
    else:
        init_audio()

# 连接到服务器
def connect_to_server():
    try:
        sio.connect(f'http://{SERVER_HOST}:{SERVER_PORT}')
        print('Connected to server')
    except Exception as e:
        print(f'Error connecting to server: {e}')

# 发送视频流
def send_video():
    while True:
        if has_camera and cap is not None:
            try:
                ret, frame = capture_frame(cap)
                if ret and frame is not None:
                    # 将帧转换为base64编码
                    jpg_as_text = frame_to_base64(frame)
                    if jpg_as_text:
                        sio.emit('video_frame', jpg_as_text)
            except Exception as e:
                print(f"发送视频错误: {e}")
                # 使用默认帧
                frame = get_default_frame()
                jpg_as_text = frame_to_base64(frame)
                sio.emit('video_frame', jpg_as_text)
        else:
            # 使用默认帧
            frame = get_default_frame()
            jpg_as_text = frame_to_base64(frame)
            sio.emit('video_frame', jpg_as_text)

# 发送音频流
def send_audio():
    global audio, stream, audio_enabled
    while True:
        if audio_enabled and audio is not None and stream is not None:
            try:
                data = read_audio(stream)
                audio_data = audio_to_base64(data)
                sio.emit('audio_frame', audio_data)
            except Exception as e:
                print(f"发送音频错误: {e}")
                # 尝试重新初始化音频
                toggle_audio()
                toggle_audio()

# 接收视频流
@sio.on('video_frame')
def receive_video(data):
    # 将base64编码转换为帧 - 仅在控制台显示接收状态，不显示窗口
    frame = base64_to_frame(data)
    if frame is not None:
        # 不再使用OpenCV窗口显示，避免与GUI客户端冲突
        # 如果需要查看视频，请使用gui_client.py
        pass

# 接收音频流
@sio.on('audio_frame')
def receive_audio(data):
    # 这里可以添加音频播放逻辑
    pass

# 接收聊天消息
@sio.on('chat_message')
def receive_message(data):
    print(f'{data["sender"]}: {data["message"]}')

# 发送聊天消息
def send_message():
    while True:
        message = input('Enter message (或输入 "audio" 切换音频状态): ')
        if message == "audio":
            toggle_audio()
        else:
            sio.emit('chat_message', {"message": message, "sender": "patient"})

if __name__ == '__main__':
    print("=" * 50)
    print("远程医疗系统 - 患者端")
    print("推荐使用 run_client.py 启动图形界面")
    print("=" * 50)
    
    # 默认开启音频
    init_audio()
    
    # 连接到服务器
    connect_to_server()
    
    # 启动视频发送线程
    video_thread = threading.Thread(target=send_video)
    video_thread.daemon = True
    video_thread.start()
    
    # 启动音频发送线程
    audio_thread = threading.Thread(target=send_audio)
    audio_thread.daemon = True
    audio_thread.start()
    
    # 启动消息发送线程
    message_thread = threading.Thread(target=send_message)
    message_thread.daemon = True
    message_thread.start()
    
    # 保持主线程运行
    sio.wait()