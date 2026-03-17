# 音频处理工具函数
import pyaudio
import base64
from config import AUDIO_RATE, AUDIO_CHANNELS, AUDIO_CHUNK

# 音频格式
AUDIO_FORMAT = pyaudio.paInt16

# 初始化音频流
def init_audio_stream():
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=AUDIO_FORMAT,
        channels=AUDIO_CHANNELS,
        rate=AUDIO_RATE,
        input=True,
        frames_per_buffer=AUDIO_CHUNK
    )
    return audio, stream

# 读取音频数据
def read_audio(stream):
    data = stream.read(AUDIO_CHUNK)
    return data

# 将音频数据转换为base64编码
def audio_to_base64(data):
    audio_data = base64.b64encode(data).decode('utf-8')
    return audio_data

# 将base64编码转换为音频数据
def base64_to_audio(data):
    audio_data = base64.b64decode(data)
    return audio_data

# 关闭音频流
def close_audio_stream(audio, stream):
    stream.stop_stream()
    stream.close()
    audio.terminate()