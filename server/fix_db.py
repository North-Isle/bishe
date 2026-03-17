#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复数据库表结构脚本
直接添加缺失的patient_id_card列
"""

import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from config import DATABASE_URI


def main():
    print("正在修复数据库表结构...")
    print(f"数据库路径: {DATABASE_URI}")
    
    # 提取SQLite数据库文件路径
    if DATABASE_URI.startswith('sqlite:///'):
        db_file = DATABASE_URI.replace('sqlite:///', '')
    else:
        print("错误: 只支持SQLite数据库")
        return
    
    try:
        # 连接到SQLite数据库
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        print(f"成功连接到数据库: {db_file}")
        
        # 检查consultations表是否存在patient_id_card列
        cursor.execute("PRAGMA table_info(consultations)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'patient_id_card' in columns:
            print("✓ patient_id_card列已经存在")
        else:
            print("✗ patient_id_card列不存在，正在添加...")
            # 添加patient_id_card列
            cursor.execute("ALTER TABLE consultations ADD COLUMN patient_id_card TEXT NOT NULL DEFAULT ''")
            conn.commit()
            print("✓ 成功添加patient_id_card列")
        
        # 检查其他表的结构
        print("\n检查其他表结构...")
        
        # 检查users表
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [column[1] for column in cursor.fetchall()]
        required_user_columns = ['id', 'username', 'password', 'real_name', 'id_card', 'role', 'created_at']
        for col in required_user_columns:
            if col in user_columns:
                print(f"✓ users表存在列: {col}")
            else:
                print(f"✗ users表缺少列: {col}")
        
        # 检查face_data表
        cursor.execute("PRAGMA table_info(face_data)")
        face_columns = [column[1] for column in cursor.fetchall()]
        required_face_columns = ['id', 'user_id', 'face_encoding', 'created_at']
        for col in required_face_columns:
            if col in face_columns:
                print(f"✓ face_data表存在列: {col}")
            else:
                print(f"✗ face_data表缺少列: {col}")
        
        # 检查consultations表的所有列
        print("\nconsultations表的所有列:")
        cursor.execute("PRAGMA table_info(consultations)")
        for column in cursor.fetchall():
            print(f"  - {column[1]} (类型: {column[2]}, 主键: {column[5]})")
        
        print("\n数据库修复完成！")
        
    except Exception as e:
        print(f"修复数据库时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    main()