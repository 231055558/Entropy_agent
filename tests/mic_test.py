#!/usr/bin/env python3
import sounddevice as sd
import numpy as np
import time

# 音频配置
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.5  # 每次处理0.5秒的音频
FRAMES_PER_CHUNK = int(SAMPLE_RATE * CHUNK_DURATION)

def audio_callback(indata, frames, time, status):
    """音频回调函数"""
    if status:
        print(f"音频状态错误: {status}")
        return
    
    # 计算音频的音量级别（RMS）
    audio_data = indata[:, 0] if indata.ndim > 1 else indata
    rms = np.sqrt(np.mean(audio_data ** 2))
    volume_level = int(rms * 100)
    
    # 简单的音量条显示
    bar_length = 30
    filled_length = min(volume_level, bar_length)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\r音量: [{bar}] {volume_level:3d}%", end='', flush=True)

def list_audio_devices():
    """列出所有可用的音频设备"""
    print("可用的音频输入设备:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            print(f"  {i}: {device['name']} (输入通道: {device['max_input_channels']})")

def test_microphone():
    """测试麦克风录制"""
    print("=== 麦克风测试程序 ===\n")
    
    # 显示可用设备
    list_audio_devices()
    print()
    
    # 显示当前默认设备
    try:
        default_device = sd.query_devices(kind='input')
        print(f"当前默认输入设备: {default_device['name']}")
        print(f"采样率: {SAMPLE_RATE} Hz")
        print(f"声道数: {CHANNELS}")
        print()
    except Exception as e:
        print(f"获取默认设备信息失败: {e}")
        return
    
    print("开始录制... 请对着麦克风说话")
    print("按 Ctrl+C 停止测试\n")
    
    try:
        # 开始录制
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            callback=audio_callback,
            blocksize=FRAMES_PER_CHUNK,
            dtype=np.float32
        ):
            # 保持程序运行
            while True:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n\n测试结束")
    except Exception as e:
        print(f"\n录制过程中出错: {e}")

if __name__ == "__main__":
    test_microphone()