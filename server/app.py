# 服务器主程序
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
from database import add_consultation, get_all_consultations
from config import HOST, PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# 存储客户端连接
clients = {}

# 主页面
@app.route('/')
def index():
    return render_template('index.html')

# 医生页面
@app.route('/doctor')
def doctor():
    consultations = get_all_consultations()
    return render_template('doctor.html', consultations=consultations)

# 患者页面
@app.route('/patient')
def patient():
    return render_template('patient.html')

# 接收视频流
@socketio.on('video_frame')
def handle_video_frame(data):
    # 广播视频帧给所有连接的客户端
    emit('video_frame', data, broadcast=True, include_self=False)

# 接收音频流
@socketio.on('audio_frame')
def handle_audio_frame(data):
    # 广播音频帧给所有连接的客户端
    emit('audio_frame', data, broadcast=True, include_self=False)

# 接收聊天消息
@socketio.on('chat_message')
def handle_chat_message(data):
    # 广播聊天消息给所有连接的客户端
    emit('chat_message', data, broadcast=True)

# 保存问诊记录
@socketio.on('save_consultation')
def handle_save_consultation(data):
    patient_name = data.get('patient_name')
    patient_id_card = data.get('patient_id_card')
    doctor_name = data.get('doctor_name')
    symptoms = data.get('symptoms')
    diagnosis = data.get('diagnosis')
    prescription = data.get('prescription')
    
    if patient_name and patient_id_card and doctor_name and symptoms:
        add_consultation(patient_name, patient_id_card, doctor_name, symptoms, diagnosis, prescription)
        emit('consultation_saved', {'status': 'success'})
    else:
        emit('consultation_saved', {'status': 'error', 'message': 'Missing required fields'})

# 客户端连接
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    clients[client_id] = True
    print(f'Client {client_id} connected')

# 客户端断开连接
@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in clients:
        del clients[client_id]
    print(f'Client {client_id} disconnected')

if __name__ == '__main__':
    socketio.run(app, host=HOST, port=PORT, debug=True)