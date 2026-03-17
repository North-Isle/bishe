# 服务器主程序
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import pickle
from database import (add_consultation, get_all_consultations, delete_consultation,
                      add_user, get_all_users, delete_user, get_user_by_username,
                      add_face_data, get_all_faces, delete_face_data, get_all_face_encodings,
                      get_user_by_id, get_stats)
from config import HOST, PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

clients = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/doctor')
def doctor():
    consultations = get_all_consultations()
    return render_template('doctor.html', consultations=consultations)

@app.route('/patient')
def patient():
    return render_template('patient.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

# API路由
@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/consultations')
def api_consultations():
    consultations = get_all_consultations()
    return jsonify([{
        'id': c.id,
        'patient_name': c.patient_name,
        'patient_id_card': c.patient_id_card,
        'doctor_name': c.doctor_name,
        'symptoms': c.symptoms,
        'diagnosis': c.diagnosis,
        'prescription': c.prescription,
        'created_at': c.created_at.isoformat() if c.created_at else None
    } for c in consultations])

@app.route('/api/consultations/<int:id>', methods=['DELETE'])
def api_delete_consultation(id):
    if delete_consultation(id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '记录不存在'})

@app.route('/api/users')
def api_users():
    users = get_all_users()
    return jsonify([{
        'id': u.id,
        'username': u.username,
        'real_name': u.real_name,
        'id_card': u.id_card,
        'role': u.role,
        'created_at': u.created_at.isoformat() if u.created_at else None
    } for u in users])

@app.route('/api/users/<int:id>', methods=['DELETE'])
def api_delete_user(id):
    if delete_user(id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '用户不存在'})

@app.route('/api/faces')
def api_faces():
    faces = get_all_faces()
    result = []
    for f in faces:
        user = get_user_by_id(f.user_id)
        result.append({
            'id': f.id,
            'user_id': f.user_id,
            'username': user.username if user else None,
            'created_at': f.created_at.isoformat() if f.created_at else None
        })
    return jsonify(result)

@app.route('/api/faces/<int:id>', methods=['DELETE'])
def api_delete_face(id):
    if delete_face_data(id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '人脸数据不存在'})

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    real_name = data.get('real_name')
    id_card = data.get('id_card')
    role = data.get('role', 'patient')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    if get_user_by_username(username):
        return jsonify({'success': False, 'message': '用户名已存在'})
    
    user = add_user(username, password, real_name, id_card, role)
    return jsonify({'success': True, 'user_id': user.id})

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    user = get_user_by_username(username)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'})
    
    if user.password != password:
        return jsonify({'success': False, 'message': '密码错误'})
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'real_name': user.real_name,
            'role': user.role
        }
    })

@app.route('/api/face/register', methods=['POST'])
def api_face_register():
    data = request.json
    user_id = data.get('user_id')
    face_encoding = data.get('face_encoding')
    
    if not user_id or not face_encoding:
        return jsonify({'success': False, 'message': '参数不完整'})
    
    face_encoding_bytes = pickle.dumps(face_encoding)
    add_face_data(user_id, face_encoding_bytes)
    return jsonify({'success': True})

@app.route('/api/face/recognize', methods=['POST'])
def api_face_recognize():
    data = request.json
    face_encoding = data.get('face_encoding')
    
    if not face_encoding:
        return jsonify({'success': False, 'message': '未提供人脸数据'})
    
    all_faces = get_all_face_encodings()
    if not all_faces:
        return jsonify({'success': False, 'message': '未找到已注册的人脸'})
    
    input_encoding = np.array(face_encoding)
    
    for face_id, user_id, stored_encoding in all_faces:
        stored_encoding = pickle.loads(stored_encoding)
        match = face_distance(stored_encoding, input_encoding) < 0.6
        if match:
            user = get_user_by_id(user_id)
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'real_name': user.real_name,
                    'role': user.role
                } if user else None
            })
    
    return jsonify({'success': False, 'message': '人脸识别失败'})

def face_distance(face_encodings, face_to_compare):
    if len(face_encodings) == 0:
        return np.empty((0))
    return np.linalg.norm(face_encodings - face_to_compare, axis=1)

@socketio.on('video_frame')
def handle_video_frame(data):
    try:
        emit('video_frame', data, broadcast=True, include_self=False)
    except Exception as e:
        print(f"处理视频帧错误: {e}")

@socketio.on('audio_frame')
def handle_audio_frame(data):
    try:
        emit('audio_frame', data, broadcast=True, include_self=False)
    except Exception as e:
        print(f"处理音频帧错误: {e}")

@socketio.on('chat_message')
def handle_chat_message(data):
    try:
        emit('chat_message', data, broadcast=True)
    except Exception as e:
        print(f"处理聊天消息错误: {e}")

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

@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    clients[client_id] = True
    print(f'Client {client_id} connected')

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    if client_id in clients:
        del clients[client_id]
    print(f'Client {client_id} disconnected')

if __name__ == '__main__':
    socketio.run(app, host=HOST, port=PORT, debug=True)
