# 人脸识别工具函数
import cv2
import numpy as np
import base64
import requests
import json
import sys

# 尝试导入face_recognition库并检查版本兼容性
FACE_RECOGNITION_AVAILABLE = False
FACE_RECOGNITION_VERSION = None
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    FACE_RECOGNITION_VERSION = getattr(face_recognition, '__version__', 'unknown')
    print(f"成功加载face_recognition库，版本: {FACE_RECOGNITION_VERSION}")
except ImportError as e:
    FACE_RECOGNITION_AVAILABLE = False
    print(f"face_recognition库未安装: {e}")
except Exception as e:
    FACE_RECOGNITION_AVAILABLE = False
    print(f"加载face_recognition库时发生错误: {e}")
    import traceback
    traceback.print_exc()

face_cascade = None

def init_face_detector():
    global face_cascade
    if face_cascade is None:
        # 尝试多种方式加载Haar级联分类器
        cascade_paths = [
            # 方法1: 使用cv2.data（OpenCV 4.0+）
            getattr(cv2, 'data', None) and (cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'),
            # 方法2: 标准系统路径
            '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
            '/usr/local/share/opencv4/haarcascades/haarcascade_frontalface_default.xml',
            'C:/opencv/sources/data/haarcascades/haarcascade_frontalface_default.xml',
            # 方法3: 当前目录相对路径
            'haarcascade_frontalface_default.xml',
            './utils/haarcascade_frontalface_default.xml'
        ]
        
        for path in cascade_paths:
            if path:
                try:
                    face_cascade = cv2.CascadeClassifier(path)
                    if face_cascade.empty():
                        face_cascade = None
                    else:
                        print(f"成功加载Haar级联分类器: {path}")
                        break
                except Exception as e:
                    print(f"尝试加载{path}失败: {e}")
        
        if face_cascade is None:
            print("警告: 无法加载Haar级联分类器，人脸检测功能将不可用")
    return face_cascade

def detect_faces(frame):
    if FACE_RECOGNITION_AVAILABLE:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        return face_locations
    else:
        cascade = init_face_detector()
        if cascade is None:
            # 如果无法加载级联分类器，返回空列表
            return []
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        face_locations = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
        return face_locations

def get_face_encoding(frame, face_location=None):
    if not FACE_RECOGNITION_AVAILABLE:
        return None
    
    try:
        # 将BGR格式转换为RGB格式
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 获取人脸编码
        if face_location:
            # 确保face_location是正确的格式
            if isinstance(face_location, (list, tuple)) and len(face_location) == 4:
                face_encodings = face_recognition.face_encodings(rgb_frame, [face_location])
            else:
                print(f"无效的人脸位置格式: {face_location}")
                return None
        else:
            face_encodings = face_recognition.face_encodings(rgb_frame)
        
        # 检查结果
        if len(face_encodings) > 0:
            encoding = face_encodings[0]
            # 确保返回的是可序列化的列表
            if hasattr(encoding, 'tolist'):
                return encoding.tolist()
            elif isinstance(encoding, list):
                return encoding
            else:
                print(f"未知的人脸编码格式: {type(encoding)}")
                return None
        else:
            print("未检测到人脸编码")
            return None
    except Exception as e:
        print(f"获取人脸编码时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

def draw_face_box(frame, face_location, color=(0, 255, 0), label=None):
    top, right, bottom, left = face_location
    
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    
    if label:
        cv2.rectangle(frame, (left, bottom - 25), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)
    
    return frame

def register_face_with_server(server_host, server_port, user_id, face_encoding):
    try:
        url = f"http://{server_host}:{server_port}/api/face/register"
        data = {
            "user_id": user_id,
            "face_encoding": face_encoding
        }
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        return result.get('success', False), result.get('message', '')
    except Exception as e:
        return False, str(e)

def recognize_face_with_server(server_host, server_port, face_encoding):
    try:
        url = f"http://{server_host}:{server_port}/api/face/recognize"
        data = {
            "face_encoding": face_encoding
        }
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        if result.get('success'):
            return True, result.get('user')
        return False, result.get('message', '识别失败')
    except Exception as e:
        return False, str(e)

def register_user_with_server(server_host, server_port, username, password, real_name=None, id_card=None, role='patient'):
    try:
        url = f"http://{server_host}:{server_port}/api/register"
        data = {
            "username": username,
            "password": password,
            "real_name": real_name,
            "id_card": id_card,
            "role": role
        }
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        if result.get('success'):
            return True, result.get('user_id')
        return False, result.get('message', '注册失败')
    except Exception as e:
        return False, str(e)

def login_with_server(server_host, server_port, username, password):
    try:
        url = f"http://{server_host}:{server_port}/api/login"
        data = {
            "username": username,
            "password": password
        }
        response = requests.post(url, json=data, timeout=5)
        result = response.json()
        if result.get('success'):
            return True, result.get('user')
        return False, result.get('message', '登录失败')
    except Exception as e:
        return False, str(e)

def is_face_recognition_available():
    return FACE_RECOGNITION_AVAILABLE
