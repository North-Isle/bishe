# 服务器配置文件

# 服务器主机和端口
HOST = '0.0.0.0'
PORT = 5000

# 数据库配置
DATABASE_URI = 'sqlite:///clinic.db'

# 密钥 - 生产环境应使用随机生成的强密钥
import os
SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secure-random-secret-key-change-in-production'

# 视频流配置
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
VIDEO_FPS = 30