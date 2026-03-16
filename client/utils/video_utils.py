import cv2
import numpy as np
import base64

# 尝试导入picamera2库，用于树莓派5的摄像头
picamera2_available = False
try:
    from picamera2 import Picamera2
    from libcamera import controls
    picamera2_available = True
except ImportError:
    print("picamera2库未安装，将使用传统的cv2.VideoCapture")

def capture_frame(cap):
    if picamera2_available and hasattr(cap, 'capture_array'):
        # 使用picamera2捕获帧
        frame = cap.capture_array()
        # 转换颜色空间，从RGB到BGR（OpenCV使用BGR）
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return True, frame
    else:
        # 使用传统的cv2.VideoCapture
        ret, frame = cap.read()
        return ret, frame

def init_camera(width, height, fps):
    """初始化摄像头，优先使用picamera2（树莓派5）， fallback到cv2.VideoCapture"""
    if picamera2_available:
        try:
            # 初始化Picamera2
            cap = Picamera2()
            # 配置摄像头参数
            config = cap.create_preview_configuration(
                main={
                    "size": (width, height),
                    "format": "RGB888"
                },
                controls={
                    "FrameRate": fps
                }
            )
            cap.configure(config)
            cap.start()
            print("使用picamera2成功初始化摄像头")
            return cap
        except Exception as e:
            print(f"使用picamera2初始化摄像头失败: {e}")
            # 失败后尝试使用传统方法
            pass
    
    # 使用传统的cv2.VideoCapture
    try:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_FPS, fps)
        if cap.isOpened():
            print("使用cv2.VideoCapture成功初始化摄像头")
            return cap
        else:
            print("使用cv2.VideoCapture初始化摄像头失败")
            return None
    except Exception as e:
        print(f"初始化摄像头错误: {e}")
        return None

def release_camera(cap):
    """释放摄像头资源"""
    if cap is not None:
        if picamera2_available and hasattr(cap, 'stop'):
            # 停止picamera2
            cap.stop()
        else:
            # 释放cv2.VideoCapture
            cap.release()

def frame_to_base64(frame):
    try:
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
        data = base64.b64encode(buffer).decode('utf-8')
        return data
    except:
        return ""

def base64_to_frame(data):
    try:
        missing_padding = len(data) % 4
        if missing_padding:
            data += '=' * (4 - missing_padding)

        img_data = base64.b64decode(data)
        np_data = np.frombuffer(img_data, dtype=np.uint8)
        frame = cv2.imdecode(np_data, cv2.IMREAD_COLOR)
        return frame
    except:
        return None

def show_frame(window_name, frame):
    if frame is not None:
        cv2.imshow(window_name, frame)
        return cv2.waitKey(1) & 0xFF
    return -1