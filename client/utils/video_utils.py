# 视频处理工具函数
import cv2
import numpy as np
import base64

# 捕获视频帧
def capture_frame(cap):
    ret, frame = cap.read()
    return ret, frame

# 将帧转换为base64编码
def frame_to_base64(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return jpg_as_text

# 将base64编码转换为帧
def base64_to_frame(data):
    img_data = base64.b64decode(data)
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame

# 显示视频帧
def show_frame(window_name, frame):
    cv2.imshow(window_name, frame)
    return cv2.waitKey(1) & 0xFF