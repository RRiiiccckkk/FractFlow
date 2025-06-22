#!/usr/bin/env python3
"""
完美版语音交互程序
修复了所有发现的问题，提供最佳的语音交互体验
"""

import asyncio
import os
import sys
import json
import threading
import queue
import time
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient

class PerfectVoiceClient(QwenRealtimeVoiceClient):
    """完美版语音客户端"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.debug_mode = True
        
    async def _configure_session(self):
        """优化的会话配置"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "你是一个友好的AI助手，请用中文自然地回答问题。保持回复简洁明了。支持被用户随时打断。",
                "voice": "Chelsie",  # 修复：使用正确的语音名称
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.15,  # 优化：平衡敏感度
                    "prefix_padding_ms": 150,  # 优化：适中的前缀
                    "silence_duration_ms": 400  # 优化：适中的静音时间
                },
                "temperature": 0.7,
                "max_response_output_tokens": 2048
            }
        }
        
        await self.websocket.send(json.dumps(config))
        print("⚙️ 会话配置完成（使用完美优化设置）")
    
    def select_best_microphone(self):
        """选择最佳麦克风设备"""
        if not HAS_PYAUDIO:
            return None
        
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        
        # 优先选择MacBook内置麦克风
        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                if "MacBook" in info['name'] and "Microphone" in info['name']:
                    print(f"🎤 自动选择最佳设备: {info['name']}")
                    p.terminate()
                    return i
        
        # 如果没有内置麦克风，选择第一个可用设备
        for i in range(device_count):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0 and "OPPO" not in info['name']:  # 避免OPPO兼容性问题
                print(f"🎤 选择备用设备: {info['name']}")
                p.terminate()
                return i
        
        p.terminate()
        return None
    
    def start_recording(self):
        """增强的录音启动"""
        if not HAS_PYAUDIO:
            return {"success": False, "error": "PyAudio不可用"}
        
        try:
            # 初始化PyAudio
            if not self.pyaudio_instance:
                self.pyaudio_instance = pyaudio.PyAudio()
            
            # 选择最佳麦克风
            device_id = self.select_best_microphone()
            if device_id is None:
                return {"success": False, "error": "未找到合适的麦克风设备"}
            
            # 创建输入流
            self.input_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,  # 标准采样率
                input=True,
                input_device_index=device_id,
                frames_per_buffer=1024
            )
            
            # 创建输出流（用于播放AI语音）
            self.output_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                output=True
            )
            
            self.is_recording = True
            self.stop_event.clear()
            self.stop_playback_event.clear()
            
            # 启动线程
            self.recording_thread = threading.Thread(target=self._enhanced_recording_worker)
            self.recording_thread.start()
            
            self.processing_thread = threading.Thread(target=self._processing_worker)
            self.processing_thread.start()
            
            self.audio_playback_thread = threading.Thread(target=self._audio_playback_worker)
            self.audio_playback_thread.start()
            
            print("🎤 完美录音系统已启动")
            return {"success": True, "message": "录音开始"}
            
        except Exception as e:
            return {"success": False, "error": f"录音启动失败: {e}"}
    
    def _enhanced_recording_worker(self):
        """增强的录音工作线程"""
        print("🎵 完美录音线程启动")
        
        chunk_count = 0
        silent_chunks = 0
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                # 读取音频数据
                audio_data = self.input_stream.read(1024, exception_on_overflow=False)
                
                # 简单的音频级别检测
                if self.debug_mode and chunk_count % 50 == 0:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                    if len(audio_array) > 0:
                        volume = np.sqrt(np.mean(audio_array.astype(np.float64)**2))
                        if not np.isnan(volume):
                            if volume > 200:
                                print(f"\r🎤 检测到语音输入 (音量: {volume:.0f})  ", end="", flush=True)
                                silent_chunks = 0
                            else:
                                silent_chunks += 1
                                if silent_chunks > 100:  # 5秒静音后显示等待状态
                                    print(f"\r🎤 等待语音输入...                    ", end="", flush=True)
                                    silent_chunks = 0
                
                # 放入队列
                if not self.audio_queue.full():
                    self.audio_queue.put(audio_data)
                
                chunk_count += 1
                time.sleep(0.01)
                
            except Exception as e:
                if self.is_recording:
                    print(f"\n❌ 录音错误: {e}")
                break
                
        print(f"\n🛑 录音线程结束")
    
    async def _handle_responses(self):
        """增强的响应处理"""
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.01)
            response_data = json.loads(message)
            
            response_type = response_data.get("type", "")
            
            if response_type == "input_audio_buffer.speech_started":
                print(f"\n🎤 [检测到语音] 开始识别...")
                if self.is_ai_speaking:
                    await self._interrupt_ai_response()
                    
            elif response_type == "input_audio_buffer.speech_stopped":
                print(f"🔇 [语音结束] 正在处理...")
                self.interrupt_detected = False
                
            elif response_type == "conversation.item.input_audio_transcription.completed":
                # 获取转录文本
                item = response_data.get("item", {})
                content = item.get("content", [])
                if content and len(content) > 0:
                    transcript = content[0].get("transcript", "")
                    if transcript:
                        print(f"👤 您说: {transcript}")
                
            elif response_type == "response.created":
                print(f"🤖 AI正在思考...")
                
            elif response_type == "response.audio_transcript.delta":
                transcript = response_data.get("delta", "")
                if transcript.strip():
                    print(f"🤖 AI: {transcript}", end="", flush=True)
                    
            elif response_type == "response.audio_transcript.done":
                print()  # 换行
                
            elif response_type == "response.audio.delta":
                audio_base64 = response_data.get("delta", "")
                if audio_base64 and not self.interrupt_detected:
                    self.audio_buffer.put(audio_base64)
                    self.is_ai_speaking = True
                    
            elif response_type == "response.done":
                print("✅ [对话完成] 请继续说话...")
                self.is_ai_speaking = False
                
            elif response_type == "error":
                error_info = response_data.get("error", {})
                print(f"\n❌ 错误: {error_info.get('message', '未知错误')}")
                
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            if "websocket" not in str(e).lower():
                print(f"\n❌ 响应处理错误: {e}")

async def run_perfect_voice_chat():
    """运行完美版语音聊天"""
    print("🎙️ 千问Omni完美语音交互系统")
    print("="*60)
    
    client = PerfectVoiceClient()
    
    try:
        # 连接API
        print("🔗 正在连接千问Omni API...")
        connect_result = await client.connect()
        if not connect_result["success"]:
            print(f"❌ 连接失败: {connect_result['error']}")
            return
        
        print(f"✅ 连接成功！会话ID: {connect_result['session_id']}")
        
        # 启动录音
        print("🎤 正在启动完美录音系统...")
        record_result = client.start_recording()
        if not record_result["success"]:
            print(f"❌ 录音启动失败: {record_result['error']}")
            return
        
        print("\n" + "🎉" * 20)
        print("✅ 完美语音交互系统已启动！")
        print("\n💡 系统特性:")
        print("   🎤 自动选择最佳麦克风")
        print("   🔊 高质量语音播放")
        print("   ⚡ 优化的语音检测")
        print("   🤖 实时对话交互")
        print("   📝 语音转录显示")
        print("\n🗣️ 使用指南:")
        print("   • 直接对着麦克风说话")
        print("   • 等待AI语音回复")
        print("   • 可以随时打断AI说话")
        print("   • 按 Ctrl+C 退出")
        print("🎉" * 20)
        print("\n🎤 系统就绪，请开始对话...")
        
        # 保持运行
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n👋 用户结束对话")
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
    finally:
        # 清理资源
        print("\n🧹 正在清理资源...")
        client.stop_recording()
        await client.disconnect()
        print("✅ 完美语音交互系统已关闭")
        print("👋 再见！")

if __name__ == "__main__":
    asyncio.run(run_perfect_voice_chat()) 