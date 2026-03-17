# 客户端配置文件

# 服务器地址和端口
SERVER_HOST = '192.168.185.61'  # 服务器IP地址，根据实际情况修改
SERVER_PORT = 5000

# 视频流配置 - 进一步降低分辨率以减少内存使用
VIDEO_WIDTH = 320   # 从480降低到320
VIDEO_HEIGHT = 240  # 从360降低到240
VIDEO_FPS = 10      # 从15降低到10

# 音频流配置
AUDIO_RATE = 22050  # 从44100降低到22050，减少带宽
AUDIO_CHANNELS = 1
AUDIO_CHUNK = 1024