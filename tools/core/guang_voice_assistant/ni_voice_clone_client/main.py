"""
Ni Voice Clone Client for HKUST-GZ
Author: FractFlow Team
Brief: Voice cloning client for Ni using GPT-SoVITS
"""

import requests
import pyaudio
import wave
import io

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

def play_ni_voice(text=None):
    """播放倪校声色克隆音频"""
    # 创建请求参数
    request_params = params.copy()
    if text:
        request_params["text"] = text
    
    # 打开音频播放流
    p = pyaudio.PyAudio()
    stream = None

    # 发起POST请求（修复：使用POST方法而不是GET）
    with requests.post(url, json=request_params, stream=True) as response:
        buffer = b""
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                buffer += chunk

                # 尝试解析一个有效的 WAV 头并开始播放
                if stream is None and len(buffer) > 44:
                    try:
                        wav_io = io.BytesIO(buffer)
                        wav = wave.open(wav_io, "rb")
                        stream = p.open(
                            format=p.get_format_from_width(wav.getsampwidth()),
                            channels=wav.getnchannels(),
                            rate=wav.getframerate(),
                            output=True,
                        )
                        # 播放当前已有的音频数据
                        wav_io.seek(44)  # 跳过头部
                        stream.write(wav_io.read())
                    except wave.Error:
                        pass  # 继续缓存直到完整的WAV头

                elif stream is not None:
                    stream.write(chunk)

    # 清理资源
    if stream:
        stream.stop_stream()
        stream.close()
    p.terminate()

if __name__ == "__main__":
    play_ni_voice()