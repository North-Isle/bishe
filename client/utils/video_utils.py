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

# 用于存储Picamera2实例
picamera2_instance = None

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
    """捕获视频帧，支持cv2.VideoCapture和Picamera2实例"""
    try:
        # 检查是否是Picamera2实例
        if hasattr(cap, 'capture_array'):
            try:
                frame = cap.capture_array()
                if frame is not None and frame.size > 0:
                    return True, frame
                return False, None
            except Exception as e:
                print(f"Picamera2捕获帧失败: {e}")
                return False, None
        
        # 否则使用cv2.VideoCapture
        ret, frame = cap.read()
        return ret, frame
    except Exception as e:
        print(f"捕获帧失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def init_camera(width, height, fps):
    """初始化摄像头，优先使用Picamera2（树莓派5），其次使用cv2.VideoCapture"""
    global picamera2_instance
    try:
        # 优先尝试使用Picamera2（树莓派5推荐）
        if picamera2_available:
            try:
                picam2 = Picamera2()
                config = picam2.create_video_configuration(
                    main={"size": (width, height)}, 
                    controls={"FrameRate": fps}
                )
                picam2.configure(config)
                picam2.start()
                picamera2_instance = picam2
                print(f"使用Picamera2成功初始化摄像头 ({width}x{height} @ {fps}fps)")
                return picam2  # 返回Picamera2实例
            except Exception as e:
                print(f"Picamera2初始化失败: {e}")
        
        # 如果Picamera2不可用或失败，尝试使用cv2.VideoCapture
        print("尝试使用cv2.VideoCapture初始化摄像头...")
        # 对于树莓派，尝试使用不同的后端
        backends = [
            cv2.CAP_V4L2,
            cv2.CAP_GSTREAMER,
            cv2.CAP_FFMPEG,
            cv2.CAP_ANY
        ]
        
        for backend in backends:
            try:
                cap = cv2.VideoCapture(0, backend)
                if cap.isOpened():
                    # 设置参数
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    cap.set(cv2.CAP_PROP_FPS, fps)
                    print(f"使用cv2.VideoCapture({backend})成功初始化摄像头 ({width}x{height} @ {fps}fps)")
                    return cap
                cap.release()
            except Exception as e:
                print(f"cv2.VideoCapture({backend})失败: {e}")
        
        print("所有摄像头初始化方法都失败了")
        return None
    except Exception as e:
        print(f"初始化摄像头错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def release_camera(cap):
    """释放摄像头资源，支持cv2.VideoCapture和Picamera2实例"""
    global picamera2_instance
    if cap is not None:
        try:
            # 检查是否是Picamera2实例
            if hasattr(cap, 'stop'):
                cap.stop()
                cap.close()
                picamera2_instance = None
                print("Picamera2资源已释放")
            else:
                # 否则使用cv2.VideoCapture的release方法
                cap.release()
                print("cv2.VideoCapture资源已释放")
        except Exception as e:
            print(f"释放摄像头失败: {e}")
            import traceback
            traceback.print_exc()

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