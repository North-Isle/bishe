# 数据库操作文件
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URI
import bcrypt

Base = declarative_base()

# 问诊记录模型
class Consultation(Base):
    __tablename__ = 'consultations'
    
    id = Column(Integer, primary_key=True)
    patient_name = Column(String(100), nullable=False)
    patient_id_card = Column(String(18), nullable=False)
    doctor_name = Column(String(100), nullable=False)
    symptoms = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 用户模型
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    real_name = Column(String(100), nullable=True)
    id_card = Column(String(18), nullable=True)
    role = Column(String(20), nullable=False)  # 移除默认值，必须指定角色
    created_at = Column(DateTime, default=datetime.utcnow)

# 人脸数据模型
class FaceData(Base):
    __tablename__ = 'face_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    face_encoding = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 初始化数据库
engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# 使用上下文管理器管理数据库会话
def get_session():
    """获取数据库会话的上下文管理器"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# 问诊记录操作
def add_consultation(patient_name, patient_id_card, doctor_name, symptoms, diagnosis=None, prescription=None):
    with next(get_session()) as db_session:
        consultation = Consultation(
            patient_name=patient_name,
            patient_id_card=patient_id_card,
            doctor_name=doctor_name,
            symptoms=symptoms,
            diagnosis=diagnosis,
            prescription=prescription
        )
        db_session.add(consultation)
        db_session.commit()
        return consultation

def get_all_consultations():
    with next(get_session()) as db_session:
        return db_session.query(Consultation).order_by(Consultation.created_at.desc()).all()

def get_consultation_by_id(id):
    with next(get_session()) as db_session:
        return db_session.query(Consultation).filter_by(id=id).first()

def delete_consultation(id):
    with next(get_session()) as db_session:
        consultation = db_session.query(Consultation).filter_by(id=id).first()
        if consultation:
            db_session.delete(consultation)
            db_session.commit()
            return True
        return False

def get_today_consultations_count():
    with next(get_session()) as db_session:
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return db_session.query(Consultation).filter(Consultation.created_at >= today).count()

# 用户操作
def add_user(username, password, real_name=None, id_card=None, role=None):
    # 验证角色必须提供且只能是医生或管理员
    if not role or role not in ['doctor', 'admin']:
        raise ValueError("角色必须提供，且只能是'doctor'或'admin'")
    
    # 对密码进行哈希处理
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    with next(get_session()) as db_session:
        user = User(
            username=username,
            password=hashed_password.decode('utf-8'),  # 存储哈希后的密码字符串
            real_name=real_name,
            id_card=id_card,
            role=role
        )
        db_session.add(user)
        db_session.commit()
        return user

def get_user_by_username(username):
    with next(get_session()) as db_session:
        return db_session.query(User).filter_by(username=username).first()

def get_user_by_id(user_id):
    with next(get_session()) as db_session:
        return db_session.query(User).filter_by(id=user_id).first()

def get_all_users():
    with next(get_session()) as db_session:
        return db_session.query(User).order_by(User.created_at.desc()).all()

def delete_user(user_id):
    with next(get_session()) as db_session:
        user = db_session.query(User).filter_by(id=user_id).first()
        if user:
            db_session.delete(user)
            db_session.commit()
            return True
        return False

def authenticate_user(username, password):
    try:
        with next(get_session()) as db_session:
            user = db_session.query(User).filter_by(username=username).first()
            if user:
                # 检查密码是否已经是哈希格式（bcrypt哈希通常以$2b$或$2a$开头）
                if user.password.startswith('$2b$') or user.password.startswith('$2a$'):
                    # 使用bcrypt验证哈希密码
                    if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                        return user
                else:
                    # 旧的明文密码，直接比较
                    if user.password == password:
                        return user
        return None
    except Exception as e:
        print(f"认证用户时出错: {e}")
        import traceback
        traceback.print_exc()
        return None

# 人脸数据操作
def add_face_data(user_id, face_encoding):
    with next(get_session()) as db_session:
        face = FaceData(
            user_id=user_id,
            face_encoding=face_encoding
        )
        db_session.add(face)
        db_session.commit()
        return face

def get_face_by_user_id(user_id):
    with next(get_session()) as db_session:
        return db_session.query(FaceData).filter_by(user_id=user_id).first()

def get_all_faces():
    with next(get_session()) as db_session:
        return db_session.query(FaceData).order_by(FaceData.created_at.desc()).all()

def delete_face_data(face_id):
    with next(get_session()) as db_session:
        face = db_session.query(FaceData).filter_by(id=face_id).first()
        if face:
            db_session.delete(face)
            db_session.commit()
            return True
        return False

def get_all_face_encodings():
    with next(get_session()) as db_session:
        faces = db_session.query(FaceData).all()
        return [(f.id, f.user_id, f.face_encoding) for f in faces]

# 统计数据
def get_stats():
    with next(get_session()) as db_session:
        return {
            'total_consultations': db_session.query(Consultation).count(),
            'today_consultations': get_today_consultations_count(),
            'total_users': db_session.query(User).count(),
            'total_faces': db_session.query(FaceData).count()
        }
