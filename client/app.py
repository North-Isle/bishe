# 客户端主程序（树莓派端）
import cv2
import socketio
import threading
from config import SERVER_HOST, SERVER_PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS
from utils.video_utils import capture_frame, frame_to_base64, base64_to_frame, show_frame
from utils.audio_utils import init_audio_stream, read_audio, audio_to_base64, close_audio_stream

# 初始化SocketIO客户端
sio = socketio.Client()

# 视频捕获对象
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, VIDEO_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, VIDEO_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, VIDEO_FPS)

# 初始化音频流
audio, stream = init_audio_stream()

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
        ret, frame = capture_frame(cap)
        if ret:
            # 将帧转换为base64编码
            jpg_as_text = frame_to_base64(frame)
            sio.emit('video_frame', jpg_as_text)

# 发送音频流
def send_audio():
    while True:
        data = read_audio(stream)
        audio_data = audio_to_base64(data)
        sio.emit('audio_frame', audio_data)

# 接收视频流
@sio.on('video_frame')
def receive_video(data):
    # 将base64编码转换为帧
    frame = base64_to_frame(data)
    if frame is not None:
        key = show_frame('Doctor Video', frame)
        if key == ord('q'):
            sio.disconnect()
            cap.release()
            close_audio_stream(audio, stream)
            cv2.destroyAllWindows()
            exit()

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
        message = input('Enter message: ')
        sio.emit('chat_message', {"message": message, "sender": "patient"})

if __name__ == '__main__':
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