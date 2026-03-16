import cv2
import numpy as np
import base64

def capture_frame(cap):
    ret, frame = cap.read()
    return ret, frame

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