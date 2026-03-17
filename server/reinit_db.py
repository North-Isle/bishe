#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新初始化数据库脚本
用于修复数据库表结构与模型定义不一致的问题
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URI

# 创建Base类
Base = declarative_base()

# 定义所有模型类
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

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    real_name = Column(String(100), nullable=True)
    id_card = Column(String(18), nullable=True)
    role = Column(String(20), default='patient')
    created_at = Column(DateTime, default=datetime.utcnow)

class FaceData(Base):
    __tablename__ = 'face_data'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    face_encoding = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def main():
    print("正在重新初始化数据库...")
    print(f"数据库路径: {DATABASE_URI}")
    
    # 询问用户是否确定要重新初始化
    confirm = input("警告: 这将删除所有现有数据！是否继续？(y/n): ").strip().lower()
    if confirm != 'y':
        print("操作已取消")
        return
    
    try:
        # 删除现有数据库文件（如果是SQLite）
        if DATABASE_URI.startswith('sqlite:///'):
            db_file = DATABASE_URI.replace('sqlite:///', '')
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"已删除现有数据库文件: {db_file}")
        
        # 创建数据库引擎
        engine = create_engine(DATABASE_URI)
        
        # 创建所有表
        Base.metadata.create_all(engine)
        print("成功创建所有数据库表")
        
        # 插入测试数据（可选）
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # 创建管理员用户
        admin_user = User(
            username='admin',
            password='admin123',
            real_name='管理员',
            role='admin'
        )
        session.add(admin_user)
        
        # 创建测试医生
        doctor_user = User(
            username='doctor',
            password='doctor123',
            real_name='张医生',
            role='doctor'
        )
        session.add(doctor_user)
        
        # 创建测试患者
        patient_user = User(
            username='patient',
            password='patient123',
            real_name='李患者',
            id_card='110101199001011234',
            role='patient'
        )
        session.add(patient_user)
        
        session.commit()
        print("已添加测试用户数据")
        print("\n数据库初始化完成！")
        print("\n测试账号:")
        print("管理员: admin / admin123")
        print("医生: doctor / doctor123")
        print("患者: patient / patient123")
        
    except Exception as e:
        print(f"初始化数据库时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()