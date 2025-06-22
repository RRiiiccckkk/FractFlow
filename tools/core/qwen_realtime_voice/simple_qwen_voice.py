#!/usr/bin/env python3
"""
基于官方文档的千问Omni实时语音实现
遵循官方WebSocket协议规范
"""

import asyncio
import json
import os
import base64
import threading
import queue
import time
from typing import Dict, Any, Optional
import websocket

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    print("Warning: pyaudio not installed. Install with: uv add pyaudio")

# 配置
API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
API_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen-omni-turbo-realtime"

# 音频参数 - 严格按照官方文档
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16 if HAS_PYAUDIO else None

class QwenOmniVoiceChat:
    """千问Omni语音聊天 - 官方协议版"""
    
    def __init__(self):
        self.ws = None
        self.session_id = None
        self.is_connected = False
        self.is_recording = False
        
        # 音频相关
        if HAS_PYAUDIO:
            self.pyaudio_instance = None
            self.input_stream = None
            self.output_stream = None
            
        # 队列
        self.audio_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.recording_thread = None
        
    def connect(self):
        """连接到千问Omni API - 使用官方协议"""
        print("🔗 正在连接千问Omni实时API...")
        
        headers = [f"Authorization: Bearer {API_KEY}"]
        
        self.ws = websocket.WebSocketApp(
            API_URL,
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # 启动WebSocket连接
        self.ws.run_forever()
    
    def on_open(self, ws):
        """连接建立回调"""
        print(f"✅ 已连接到服务器: {API_URL}")
        self.is_connected = True
        
        # 发送会话配置 - 使用server_vad模式
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "你是一个友好的AI助手，请用中文自然地回答问题。保持回复简洁明了。",
                "voice": "Chelsie",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.3,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 800,
                    "create_response": True
                },
                "temperature": 0.7,
                "max_response_output_tokens": 2048
            }
        }
        
        ws.send(json.dumps(session_config))
        print("⚙️ 会话配置已发送")
        
        # 初始化并开始录音
        self.init_audio()
        self.start_recording()
    
    def on_message(self, ws, message):
        """消息接收回调"""
        try:
            data = json.loads(message)
            event_type = data.get("type", "")
            
            # 处理不同类型的事件
            if event_type == "session.created":
                self.session_id = data["session"]["id"]
                print(f"📝 会话已创建: {self.session_id}")
                
            elif event_type == "session.updated":
                print("⚙️ 会话配置已更新")
                
            elif event_type == "input_audio_buffer.speech_started":
                print("🎤 [检测到语音开始]")
                
            elif event_type == "input_audio_buffer.speech_stopped":
                print("🔇 [检测到语音结束]")
                
            elif event_type == "response.audio_transcript.delta":
                transcript = data.get("delta", "")
                if transcript.strip():
                    print(f"💬 AI: {transcript}", end="", flush=True)
                    
            elif event_type == "response.audio_transcript.done":
                print()  # 换行
                
            elif event_type == "response.audio.delta":
                # 播放音频响应
                audio_base64 = data.get("delta", "")
                if audio_base64:
                    self.play_audio(audio_base64)
                    
            elif event_type == "response.done":
                print("✅ [响应完成]")
                
            elif event_type == "conversation.item.created":
                print("📝 [对话项已创建]")
                
            else:
                print(f"📥 收到事件: {event_type}")
                
        except json.JSONDecodeError:
            print(f"❌ JSON解析错误: {message}")
        except Exception as e:
            print(f"❌ 消息处理错误: {e}")
    
    def on_error(self, ws, error):
        """错误回调"""
        print(f"❌ WebSocket错误: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """连接关闭回调"""
        print("🔌 WebSocket连接已关闭")
        self.is_connected = False
        self.cleanup()
    
    def init_audio(self):
        """初始化音频系统"""
        if not HAS_PYAUDIO:
            print("❌ PyAudio未安装，无法使用音频功能")
            return False
            
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # 检查音频设备
            device_count = self.pyaudio_instance.get_device_count()
            print(f"🎵 发现 {device_count} 个音频设备")
            
            # 查找默认输入设备
            default_input = self.pyaudio_instance.get_default_input_device_info()
            print(f"🎤 默认输入设备: {default_input['name']}")
            
            return True
            
        except Exception as e:
            print(f"❌ 音频初始化失败: {e}")
            return False
    
    def start_recording(self):
        """开始录音"""
        if not HAS_PYAUDIO or not self.pyaudio_instance:
            return
            
        try:
            # 创建输入流
            self.input_stream = self.pyaudio_instance.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            
            self.is_recording = True
            self.stop_event.clear()
            
            # 启动录音线程
            self.recording_thread = threading.Thread(target=self.recording_worker, daemon=True)
            self.recording_thread.start()
            
            print("🎤 录音已开始")
            
        except Exception as e:
            print(f"❌ 录音启动失败: {e}")
    
    def recording_worker(self):
        """录音工作线程"""
        print("🎵 录音线程启动")
        
        chunk_count = 0
        last_send_time = 0
        send_interval = 0.05  # 50ms间隔
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                # 读取音频数据
                audio_data = self.input_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                # 控制发送频率
                current_time = time.time()
                if current_time - last_send_time >= send_interval:
                    # 发送音频到服务器
                    self.send_audio_chunk(audio_data)
                    last_send_time = current_time
                    chunk_count += 1
                    
                    # 定期显示进度
                    if chunk_count % 100 == 0:
                        print(f"📤 已发送 {chunk_count} 个音频块")
                
                time.sleep(0.01)  # 防止CPU占用过高
                
            except Exception as e:
                if self.is_recording:
                    print(f"❌ 录音错误: {e}")
                break
        
        print("🛑 录音线程结束")
    
    def send_audio_chunk(self, audio_data):
        """发送音频块到服务器"""
        if not self.is_connected or not self.ws:
            return
            
        try:
            # 按照官方协议编码音频
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            # 构建input_audio_buffer.append事件
            event = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            
            self.ws.send(json.dumps(event))
            
        except Exception as e:
            print(f"❌ 发送音频失败: {e}")
    
    def play_audio(self, audio_base64):
        """播放音频响应"""
        if not HAS_PYAUDIO:
            return
            
        try:
            audio_data = base64.b64decode(audio_base64)
            
            # 创建输出流（如果还没有）
            if not self.output_stream:
                self.output_stream = self.pyaudio_instance.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True
                )
            
            # 播放音频
            self.output_stream.write(audio_data)
            
        except Exception as e:
            print(f"❌ 音频播放错误: {e}")
    
    def cleanup(self):
        """清理资源"""
        print("🛑 正在清理资源...")
        
        self.is_recording = False
        self.stop_event.set()
        
        # 等待录音线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2)
        
        # 关闭音频流
        if self.input_stream:
            try:
                self.input_stream.stop_stream()
                self.input_stream.close()
            except:
                pass
            self.input_stream = None
            
        if self.output_stream:
            try:
                self.output_stream.stop_stream()
                self.output_stream.close()
            except:
                pass
            self.output_stream = None
        
        # 清理音频资源
        if HAS_PYAUDIO and self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
            self.pyaudio_instance = None
        
        print("✅ 资源清理完成")

def main():
    """主函数"""
    print("🎙️ 千问Omni实时语音对话 - 官方协议版")
    print("=" * 50)
    
    # 检查音频支持
    if not HAS_PYAUDIO:
        print("❌ 警告: PyAudio未安装，将无法使用音频功能")
        print("请运行: uv add pyaudio")
        return
    
    chat = QwenOmniVoiceChat()
    
    try:
        print("\n💡 使用指南:")
        print("   🎙️ 直接对着麦克风说话")
        print("   🤖 AI会自动识别并语音回复")
        print("   ⌨️ 按 Ctrl+C 结束对话")
        print("=" * 50)
        print("\n🔗 正在建立连接...")
        
        # 开始连接（这会阻塞运行）
        chat.connect()
        
    except KeyboardInterrupt:
        print("\n👋 用户主动结束对话")
    except Exception as e:
        print(f"\n❌ 程序错误: {e}")
    finally:
        chat.cleanup()
        print("👋 再见！")

if __name__ == "__main__":
    main() 