# 数据库操作文件
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
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
    patient_id_card = Column(String(18), nullable=False)  # 身份证号
    doctor_name = Column(String(100), nullable=False)
    symptoms = Column(Text, nullable=False)
    diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# 初始化数据库
engine = create_engine(DATABASE_URI)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# 新增问诊记录
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

# 获取所有问诊记录
def get_all_consultations():
    return session.query(Consultation).all()

# 根据ID获取问诊记录
def get_consultation_by_id(id):
    return session.query(Consultation).filter_by(id=id).first()