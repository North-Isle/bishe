# 数据库操作文件
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URI

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
    role = Column(String(20), default='patient')
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
session = Session()

# 问诊记录操作
def add_consultation(patient_name, patient_id_card, doctor_name, symptoms, diagnosis=None, prescription=None):
    consultation = Consultation(
        patient_name=patient_name,
        patient_id_card=patient_id_card,
        doctor_name=doctor_name,
        symptoms=symptoms,
        diagnosis=diagnosis,
        prescription=prescription
    )
    session.add(consultation)
    session.commit()
    return consultation

def get_all_consultations():
    return session.query(Consultation).order_by(Consultation.created_at.desc()).all()

def get_consultation_by_id(id):
    return session.query(Consultation).filter_by(id=id).first()

def delete_consultation(id):
    consultation = session.query(Consultation).filter_by(id=id).first()
    if consultation:
        session.delete(consultation)
        session.commit()
        return True
    return False

def get_today_consultations_count():
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return session.query(Consultation).filter(Consultation.created_at >= today).count()

# 用户操作
def add_user(username, password, real_name=None, id_card=None, role='patient'):
    user = User(
        username=username,
        password=password,
        real_name=real_name,
        id_card=id_card,
        role=role
    )
    session.add(user)
    session.commit()
    return user

def get_user_by_username(username):
    return session.query(User).filter_by(username=username).first()

def get_user_by_id(user_id):
    return session.query(User).filter_by(id=user_id).first()

def get_all_users():
    return session.query(User).order_by(User.created_at.desc()).all()

def delete_user(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    if user:
        session.delete(user)
        session.commit()
        return True
    return False

def authenticate_user(username, password):
    user = session.query(User).filter_by(username=username, password=password).first()
    return user

# 人脸数据操作
def add_face_data(user_id, face_encoding):
    face = FaceData(
        user_id=user_id,
        face_encoding=face_encoding
    )
    session.add(face)
    session.commit()
    return face

def get_face_by_user_id(user_id):
    return session.query(FaceData).filter_by(user_id=user_id).first()

def get_all_faces():
    return session.query(FaceData).order_by(FaceData.created_at.desc()).all()

def delete_face_data(face_id):
    face = session.query(FaceData).filter_by(id=face_id).first()
    if face:
        session.delete(face)
        session.commit()
        return True
    return False

def get_all_face_encodings():
    faces = session.query(FaceData).all()
    return [(f.id, f.user_id, f.face_encoding) for f in faces]

# 统计数据
def get_stats():
    return {
        'total_consultations': session.query(Consultation).count(),
        'today_consultations': get_today_consultations_count(),
        'total_users': session.query(User).count(),
        'total_faces': session.query(FaceData).count()
    }
