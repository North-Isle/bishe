# 音频处理工具函数
import pyaudio
import base64
from config import AUDIO_RATE, AUDIO_CHANNELS, AUDIO_CHUNK
import logging

# 音频格式
AUDIO_FORMAT = pyaudio.paInt16

# 支持的采样率列表（树莓派常见支持的采样率）
SUPPORTED_SAMPLE_RATES = [44100, 22050, 16000, 8000]

# 初始化音频流
def init_audio_stream():
    audio = pyaudio.PyAudio()
    
    # 尝试使用配置的采样率，如果失败则尝试其他支持的采样率
    selected_rate = AUDIO_RATE
    
    for rate in [AUDIO_RATE] + SUPPORTED_SAMPLE_RATES:
        try:
            print(f"尝试使用采样率: {rate} Hz")
            stream = audio.open(
                format=AUDIO_FORMAT,
                channels=AUDIO_CHANNELS,
                rate=rate,
                input=True,
                frames_per_buffer=AUDIO_CHUNK,
                input_device_index=None  # 自动选择默认设备
            )
            print(f"成功使用采样率: {rate} Hz")
            return audio, stream
        except Exception as e:
            print(f"采样率 {rate} Hz 不可用: {e}")
            continue
    
    # 如果所有采样率都失败，抛出异常
    raise Exception("无法初始化音频流，所有采样率都不可用")

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