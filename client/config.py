# 客户端配置文件

# 服务器地址和端口
SERVER_HOST = '192.168.185.61'  # 服务器IP地址，根据实际情况修改
SERVER_PORT = 5000

# 视频流配置 - 降低分辨率和帧率以减少卡顿
VIDEO_WIDTH = 480   # 从640降低到480
VIDEO_HEIGHT = 360  # 从480降低到360
VIDEO_FPS = 15      # 从30降低到15，减少网络带宽占用

# 音频流配置
AUDIO_RATE = 22050  # 从44100降低到22050，减少带宽
AUDIO_CHANNELS = 1
AUDIO_CHUNK = 1024