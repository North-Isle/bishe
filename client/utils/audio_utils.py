# 音频处理工具函数
import pyaudio
import base64
import subprocess
import json
from config import AUDIO_RATE, AUDIO_CHANNELS, AUDIO_CHUNK

# 音频格式
AUDIO_FORMAT = pyaudio.paInt16

# 支持的采样率列表（树莓派常见支持的采样率）
SUPPORTED_SAMPLE_RATES = [44100, 22050, 16000, 8000]

# 检测音频设备支持的采样率
def get_supported_sample_rates(device_index):
    """获取指定音频设备支持的采样率"""
    audio = pyaudio.PyAudio()
    supported_rates = []
    
    # 尝试获取设备信息
    try:
        device_info = audio.get_device_info_by_index(device_index)
        print(f"设备信息: {device_info}")
    except Exception as e:
        print(f"获取设备信息失败: {e}")
        return supported_rates
    
    # 尝试使用ALSA命令行工具获取设备支持的采样率
    try:
        # 使用arecord命令获取设备信息
        result = subprocess.run(
            ["arecord", "-D", f"hw:{device_info['index']}", "--dump-hw-params", "-c1", "-traw", "-fS16_LE", "/dev/null"],
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        print("ALSA设备参数:")
        print(result.stderr)
        
        # 解析支持的采样率
        import re
        rate_match = re.search(r'Supported sample rates: (.+)', result.stderr)
        if rate_match:
            rates_str = rate_match.group(1)
            # 提取数字部分
            rates = re.findall(r'\d+', rates_str)
            supported_rates = [int(rate) for rate in rates]
            print(f"ALSA检测到的采样率: {supported_rates}")
    except Exception as e:
        print(f"使用arecord检测采样率失败: {e}")
        
    audio.terminate()
    return supported_rates

# 列出所有音频输入设备
def list_audio_devices():
    """列出所有可用的音频输入设备"""
    audio = pyaudio.PyAudio()
    devices = []
    
    print("\n可用的音频输入设备:")
    for i in range(audio.get_device_count()):
        device_info = audio.get_device_info_by_index(i)
        if device_info.get('maxInputChannels', 0) > 0:
            devices.append({
                'index': i,
                'name': device_info.get('name', 'Unknown'),
                'channels': device_info.get('maxInputChannels', 0),
                'defaultSampleRate': device_info.get('defaultSampleRate', 0)
            })
            print(f"  设备 {i}: {device_info.get('name', 'Unknown')}")
            print(f"     最大输入通道: {device_info.get('maxInputChannels', 0)}")
            print(f"     默认采样率: {device_info.get('defaultSampleRate', 0)} Hz")
    
    audio.terminate()
    return devices

# 初始化音频流
def init_audio_stream():
    """初始化音频流，增加设备检测和容错处理"""
    audio = pyaudio.PyAudio()
    
    # 列出所有可用设备
    devices = list_audio_devices()
    
    # 如果没有可用设备，返回None
    if not devices:
        print("没有检测到音频输入设备")
        return None, None
    
    # 获取默认设备或第一个可用设备
    default_device = devices[0]
    print(f"\n使用设备: {default_device['name']}")
    
    # 检测该设备支持的采样率
    supported_rates = get_supported_sample_rates(default_device['index'])
    
    # 如果没有检测到支持的采样率，使用默认列表
    if not supported_rates:
        print(f"未检测到支持的采样率，使用默认列表: {SUPPORTED_SAMPLE_RATES}")
        supported_rates = SUPPORTED_SAMPLE_RATES
    
    # 尝试所有支持的采样率
    for rate in supported_rates:
        try:
            print(f"尝试使用采样率: {rate} Hz")
            stream = audio.open(
                format=AUDIO_FORMAT,
                channels=AUDIO_CHANNELS,
                rate=rate,
                input=True,
                frames_per_buffer=AUDIO_CHUNK,
                input_device_index=default_device['index']
            )
            print(f"成功使用采样率: {rate} Hz")
            return audio, stream
        except Exception as e:
            print(f"采样率 {rate} Hz 不可用: {e}")
            continue
    
    # 尝试使用设备的默认采样率
    default_rate = default_device['defaultSampleRate']
    if default_rate > 0:
        try:
            print(f"尝试使用设备默认采样率: {default_rate} Hz")
            stream = audio.open(
                format=AUDIO_FORMAT,
                channels=AUDIO_CHANNELS,
                rate=int(default_rate),
                input=True,
                frames_per_buffer=AUDIO_CHUNK,
                input_device_index=default_device['index']
            )
            print(f"成功使用设备默认采样率: {default_rate} Hz")
            return audio, stream
        except Exception as e:
            print(f"设备默认采样率 {default_rate} Hz 不可用: {e}")
    
    # 所有采样率都失败，尝试不指定采样率（让PyAudio自动选择）
    try:
        print("尝试不指定采样率，让系统自动选择")
        stream = audio.open(
            format=AUDIO_FORMAT,
            channels=AUDIO_CHANNELS,
            rate=None,  # 不指定采样率
            input=True,
            frames_per_buffer=AUDIO_CHUNK,
            input_device_index=default_device['index']
        )
        actual_rate = stream.getframerate()
        print(f"系统自动选择采样率: {actual_rate} Hz")
        return audio, stream
    except Exception as e:
        print(f"自动选择采样率失败: {e}")
    
    # 所有尝试都失败
    print("无法初始化音频流")
    audio.terminate()
    return None, None

# 读取音频数据
def read_audio(stream):
    try:
        # 使用exception_on_overflow=False参数防止输入溢出错误
        data = stream.read(AUDIO_CHUNK, exception_on_overflow=False)
        return data
    except Exception as e:
        print(f"读取音频数据错误: {e}")
        # 返回空数据，避免程序崩溃
        return b''

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