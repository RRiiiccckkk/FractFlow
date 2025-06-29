"""
Ni Voice Clone Client for HKUST-GZ
Author: FractFlow Team
Brief: Voice cloning client for Ni using GPT-SoVITS with interrupt support
"""

import requests
import pyaudio
import wave
import io
import threading
import time

# 全局中断控制
_interrupt_event = threading.Event()
_current_stream = None
_current_pyaudio = None

# API地址
url = "http://10.120.17.57:9880/tts"
params = {
    "text": "大家好呀，我是香港科技大学广州校长倪哥。欢迎大家来到香港科技大学广州校园，祝大家生活快乐，学业有成。", # 改这行，其他参数不要动
    "text_lang": "zh",
    "ref_audio_path": "ref_audio/ni_zh_01.wav",
    "prompt_lang": "zh",
    "text_split_method": "cut5",
    "batch_size": "1",
    "media_type": "wav",
    "streaming_mode": "true",
}

def set_interrupt():
    """设置中断信号"""
    global _current_stream, _current_pyaudio
    _interrupt_event.set()
    
    # 立即停止当前音频流
    if _current_stream:
        try:
            _current_stream.stop_stream()
        except:
            pass

def clear_interrupt():
    """清除中断信号"""
    _interrupt_event.clear()

def is_interrupted():
    """检查是否被中断"""
    return _interrupt_event.is_set()

def play_ni_voice(text=None):
    """播放倪校声色克隆音频 - 支持中断"""
    global _current_stream, _current_pyaudio
    
    # 清除之前的中断信号
    clear_interrupt()
    
    # 创建请求参数
    request_params = params.copy()
    if text:
        request_params["text"] = text
    
    # 初始化音频
    _current_pyaudio = pyaudio.PyAudio()
    _current_stream = None
    
    try:
        # 发起POST请求
        with requests.post(url, json=request_params, stream=True, timeout=10) as response:
            if response.status_code != 200:
                print(f"⚠️ TTS请求失败: {response.status_code}")
                return
                
            buffer = b""
            wav_initialized = False
            wav_params = None
            
            for chunk in response.iter_content(chunk_size=512):  # 减小块大小提高响应性
                # 检查中断信号
                if is_interrupted():
                    break
                    
                if chunk:
                    buffer += chunk
                    
                    # 初始化音频流
                    if not wav_initialized and len(buffer) > 44:
                        try:
                            wav_io = io.BytesIO(buffer)
                            wav = wave.open(wav_io, "rb")
                            wav_params = {
                                'format': _current_pyaudio.get_format_from_width(wav.getsampwidth()),
                                'channels': wav.getnchannels(),
                                'rate': wav.getframerate()
                            }
                            
                            _current_stream = _current_pyaudio.open(
                                format=wav_params['format'],
                                channels=wav_params['channels'],
                                rate=wav_params['rate'],
                                output=True,
                                frames_per_buffer=512
                            )
                            
                            wav_initialized = True
                            
                            # 播放当前缓冲的音频（跳过WAV头）
                            audio_data = buffer[44:]
                            if audio_data and not is_interrupted():
                                _play_audio_chunk(audio_data)
                                
                        except wave.Error:
                            pass  # 继续等待完整的WAV头
                    
                    # 播放新的音频块
                    elif wav_initialized and not is_interrupted():
                        _play_audio_chunk(chunk)
                        
    except requests.exceptions.RequestException as e:
        print(f"⚠️ TTS网络错误: {e}")
    except Exception as e:
        print(f"⚠️ TTS播放错误: {e}")
    finally:
        # 清理资源
        _cleanup_audio()

def _play_audio_chunk(audio_data):
    """分块播放音频数据，支持中断检查"""
    global _current_stream
    
    if not _current_stream or not audio_data:
        return
        
    # 将音频数据分成更小的块
    chunk_size = 256
    for i in range(0, len(audio_data), chunk_size):
        if is_interrupted():
            break
            
        chunk = audio_data[i:i + chunk_size]
        try:
            if _current_stream:
                _current_stream.write(chunk, exception_on_underflow=False)
            # 短暂暂停，提高中断响应性
            time.sleep(0.001)
        except Exception:
            break

def _cleanup_audio():
    """清理音频资源"""
    global _current_stream, _current_pyaudio
    
    try:
        if _current_stream:
            _current_stream.stop_stream()
            _current_stream.close()
            _current_stream = None
    except:
        pass
        
    try:
        if _current_pyaudio:
            _current_pyaudio.terminate()
            _current_pyaudio = None
    except:
        pass

if __name__ == "__main__":
    play_ni_voice()