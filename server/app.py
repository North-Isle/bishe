# 服务器主程序
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import cv2
import numpy as np
import base64
import pickle

# 不使用face_recognition库，只使用自定义实现
face_recognition_available = False
print("使用自定义的人脸距离计算实现")
from database import (add_consultation, get_all_consultations, delete_consultation,
                      add_user, get_all_users, delete_user, get_user_by_username,
                      add_face_data, get_all_faces, delete_face_data, get_all_face_encodings,
                      get_user_by_id, get_stats, authenticate_user)
from config import HOST, PORT, VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

# 配置登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 设置登录页面路由
login_manager.login_message = '请先登录'

# 用户认证回调
@login_manager.user_loader
def load_user(user_id):
    user = get_user_by_id(int(user_id))
    if user:
        # 为用户对象添加必要的方法和属性
        user.is_authenticated = True
        user.is_active = True
        user.is_anonymous = False
        user.get_id = lambda: str(user.id)
    return user

clients = {}

@app.route('/')
def index():
    return render_template('index.html')

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        role = request.form.get('role')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 验证用户
        user = authenticate_user(username, password)
        if user and user.role == role:
            # 为用户对象添加必要的方法和属性
            user.is_authenticated = True
            user.is_active = True
            user.is_anonymous = False
            user.get_id = lambda: str(user.id)
            
            login_user(user)
            
            # 根据角色重定向到不同页面
            if role == 'doctor':
                return redirect(url_for('doctor'))
            elif role == 'admin':
                return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='用户名、密码或角色错误')
    
    return render_template('login.html')

# 注销路由
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

# 医生页面 - 需要登录且角色为医生
@app.route('/doctor')
@login_required
def doctor():
    if current_user.role != 'doctor':
        return redirect(url_for('index'))
    consultations = get_all_consultations()
    return render_template('doctor.html', consultations=consultations)

# 患者页面已移除，因为不需要患者登录功能

# 管理员页面 - 需要登录且角色为管理员
@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return render_template('admin.html')

# API路由
@app.route('/api/stats')
def api_stats():
    return jsonify(get_stats())

@app.route('/api/consultations')
@login_required
def api_consultations():
    # 允许医生和管理员访问
    if current_user.role not in ['doctor', 'admin']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
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
@login_required
def api_delete_consultation(id):
    # 只允许管理员删除
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    if delete_consultation(id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '记录不存在'})

@app.route('/api/users')
@login_required
def api_users():
    # 只允许管理员访问
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
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
@login_required
def api_delete_user(id):
    # 只允许管理员删除
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    if delete_user(id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '用户不存在'})

@app.route('/api/faces')
@login_required
def api_faces():
    # 只允许管理员访问
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
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
@login_required
def api_delete_face(id):
    # 只允许管理员删除
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    if delete_face_data(id):
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '人脸数据不存在'})

@app.route('/api/register', methods=['POST'])
@login_required
def api_register():
    # 只允许管理员注册新用户
    if current_user.role != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    data = request.json
    username = data.get('username')
    password = data.get('password')
    real_name = data.get('real_name')
    id_card = data.get('id_card')
    role = data.get('role')
    
    # 验证角色，只允许医生或管理员
    if role not in ['doctor', 'admin']:
        return jsonify({'success': False, 'message': '无效的角色，只能创建医生或管理员'})
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'})
    
    if get_user_by_username(username):
        return jsonify({'success': False, 'message': '用户名已存在'})
    
    user = add_user(username, password, real_name, id_card, role)
    return jsonify({'success': True, 'user_id': user.id})

# API登录功能已移除，统一使用Web登录界面

# 人脸注册和识别API
@app.route('/api/face/register', methods=['POST'])
@login_required
def api_face_register():
    # 只允许医生和管理员注册人脸
    if current_user.role not in ['doctor', 'admin']:
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    data = request.json
    user_id = data.get('user_id')
    face_encoding = data.get('face_encoding')
    
    if not user_id or not face_encoding:
        return jsonify({'success': False, 'message': '缺少必要参数'}), 400
    
    try:
        # 将人脸编码转换为二进制存储
        face_encoding_bytes = pickle.dumps(face_encoding)
        add_face_data(user_id, face_encoding_bytes)
        return jsonify({'success': True, 'message': '人脸注册成功'})
    except Exception as e:
        print(f"人脸注册错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '人脸注册失败'})

@app.route('/api/face/recognize', methods=['POST'])
def api_face_recognize():
    data = request.json
    face_encoding = data.get('face_encoding')
    
    if not face_encoding:
        return jsonify({'success': False, 'message': '缺少人脸编码参数'}), 400
    
    try:
        # 获取所有已注册的人脸数据
        all_faces = get_all_face_encodings()
        
        if not all_faces:
            return jsonify({'success': False, 'message': '没有注册的人脸数据'}), 404
        
        # 计算人脸距离
        face_to_compare = np.array(face_encoding)
        
        best_match = None
        best_distance = float('inf')
        
        for face_id, user_id, stored_encoding_bytes in all_faces:
            stored_encoding = pickle.loads(stored_encoding_bytes)
            distance = face_distance([np.array(stored_encoding)], face_to_compare)[0]
            
            if distance < best_distance:
                best_distance = distance
                best_match = user_id
        
        # 设置阈值，小于0.6认为匹配成功
        if best_match is not None and best_distance < 0.6:
            user = get_user_by_id(best_match)
            if user:
                return jsonify({
                    'success': True,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'real_name': user.real_name,
                        'role': user.role
                    }
                })
        
        return jsonify({'success': False, 'message': '未识别到匹配的人脸'}), 404
    except Exception as e:
        print(f"人脸识别错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': '人脸识别失败'})

# API登录功能
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
    
    # 验证用户
    user = authenticate_user(username, password)
    if user:
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'real_name': user.real_name,
                'role': user.role
            }
        })
    else:
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

def face_distance(face_encodings, face_to_compare):
    """计算人脸编码之间的距离"""
    if len(face_encodings) == 0:
        return np.empty((0))
    return np.linalg.norm(face_encodings - face_to_compare, axis=1)

# 视频帧处理优化 - 添加帧速率控制
import time
last_video_frame_time = 0
VIDEO_FRAME_INTERVAL = 0.1  # 控制在10fps左右，减少服务器负载

@socketio.on('video_frame')
def handle_video_frame(data):
    global last_video_frame_time
    try:
        current_time = time.time()
        # 控制帧率，避免服务器过载
        if current_time - last_video_frame_time >= VIDEO_FRAME_INTERVAL:
            last_video_frame_time = current_time
            emit('video_frame', data, broadcast=True, include_self=False)
    except Exception as e:
        print(f"处理视频帧错误: {e}")
        import traceback
        traceback.print_exc()

# 音频帧处理优化
@socketio.on('audio_frame')
def handle_audio_frame(data):
    try:
        emit('audio_frame', data, broadcast=True, include_self=False)
    except Exception as e:
        print(f"处理音频帧错误: {e}")
        import traceback
        traceback.print_exc()

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
