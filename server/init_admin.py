# 初始化管理员和医生用户
from database import add_user, get_user_by_username

# 添加默认管理员用户
def init_admin():
    admin_username = "admin"
    admin_password = "admin123"
    admin_name = "系统管理员"
    
    # 检查管理员是否已存在
    existing_admin = get_user_by_username(admin_username)
    if not existing_admin:
        admin = add_user(admin_username, admin_password, admin_name, role="admin")
        print(f"成功创建管理员用户: {admin.username}")
    else:
        print(f"管理员用户 {admin_username} 已存在")

# 添加默认医生用户
def init_doctor():
    doctor_username = "doctor"
    doctor_password = "doctor123"
    doctor_name = "张医生"
    
    # 检查医生是否已存在
    existing_doctor = get_user_by_username(doctor_username)
    if not existing_doctor:
        doctor = add_user(doctor_username, doctor_password, doctor_name, role="doctor")
        print(f"成功创建医生用户: {doctor.username}")
    else:
        print(f"医生用户 {doctor_username} 已存在")

if __name__ == "__main__":
    print("正在初始化默认用户...")
    init_admin()
    init_doctor()
    print("默认用户初始化完成！")
    print("\n默认登录信息：")
    print("管理员：用户名 admin，密码 admin123")
    print("医生：用户名 doctor，密码 doctor123")