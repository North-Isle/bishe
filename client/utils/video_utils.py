import cv2
import numpy as np
import base64
import subprocess

# 尝试导入picamera2库，用于树莓派5的摄像头
picamera2_available = False
try:
    from picamera2 import Picamera2
    from libcamera import controls
    picamera2_available = True
except ImportError:
    print("picamera2库未安装，将使用传统的cv2.VideoCapture")

# 检查rpicam-vid命令是否可用
def is_rpicam_available():
    try:
        subprocess.run(["rpicam-vid", "--version"], capture_output=True, text=True, check=True)
        return True
    except:
        return False

# rpicam-vid命令是否可用
rpicam_available = is_rpicam_available()

def capture_frame(cap):
    # 只使用cv2.VideoCapture捕获帧
    try:
        ret, frame = cap.read()
        return ret, frame
    except Exception as e:
        print(f"捕获帧失败: {e}")
        return False, None

def init_camera(width, height, fps):
    """初始化摄像头，只使用cv2.VideoCapture以避免弹出预览窗口"""
    # 直接使用cv2.VideoCapture，避免rpicam-vid和picamera2可能弹出的窗口
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
        try:
            cap.release()
        except Exception as e:
            print(f"释放摄像头失败: {e}")

def frame_to_base64(frame):
    try:
        # 降低JPEG质量到30%，减少数据传输量，提高流畅度
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 30])
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
    """显示帧（仅返回默认值，不使用OpenCV GUI）"""
    # 移除cv2.imshow和cv2.waitKey调用以避免Qt冲突
    return -1