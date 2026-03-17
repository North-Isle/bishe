# 人脸识别工具函数
import cv2
import numpy as np
import base64
import requests
import json

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("face_recognition库未安装，将使用OpenCV进行人脸检测")

face_cascade = None

def init_face_detector():
    global face_cascade
    if face_cascade is None:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    return face_cascade

def detect_faces(frame):
    if FACE_RECOGNITION_AVAILABLE:
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        return face_locations
    else:
        cascade = init_face_detector()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        face_locations = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
        return face_locations

def get_face_encoding(frame, face_location=None):
    if not FACE_RECOGNITION_AVAILABLE:
        return None
    
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    if face_location:
        face_encodings = face_recognition.face_encodings(rgb_frame, [face_location])
    else:
        face_encodings = face_recognition.face_encodings(rgb_frame)
    
    if len(face_encodings) > 0:
        return face_encodings[0].tolist()
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
