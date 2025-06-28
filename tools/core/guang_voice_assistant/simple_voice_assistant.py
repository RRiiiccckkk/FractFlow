#!/usr/bin/env python3
"""
Simple Voice Assistant for HKUST-GZ
Author: FractFlow Team
Brief: Simplified voice assistant without web search functionality
"""

import asyncio
import os
import sys
import json
import threading
import queue
import time
import numpy as np
import base64

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    pass  # PyAudio未安装警告（移除print避免MCP干扰）

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient
from .voice_config import setup_api_keys, get_voice_session_config

class SimpleVoiceAssistant(QwenRealtimeVoiceClient):
    """极简版语音助手 - 专注核心功能"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        
        # 核心状态
        self.is_ai_speaking = False
        self.interrupt_detected = False
        self.user_speaking = False
        
        # 音频缓冲区
        self.audio_buffer = queue.Queue(maxsize=50)
        
        # 文本累积
        self.current_ai_response = ""
        self.last_user_input_shown = False
        
        # 初始化完成（移除print以避免MCP通信干扰）
    
    async def _configure_session(self):
        """配置会话"""
        config = get_voice_session_config()
        # 移除网络搜索相关的指令
        config["instructions"] = (
            "你是香港科技大学广州的智能语音助手。"
            "请用自然、连贯的语气回答用户问题。回答要简洁明了，语调亲和友好。"
        )
        await self.websocket.send(json.dumps({"type": "session.update", "session": config}))

    def _recording_worker(self):
        """录音工作线程 - 极简版"""
        # 录音线程启动（移除print避免MCP干扰）
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                audio_data = self.input_stream.read(1024, exception_on_overflow=False)
                
                # 简单的音量检测
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                if len(audio_array) > 0:
                    volume = np.sqrt(np.mean(audio_array.astype(np.float64)**2))
                    
                    # 检测用户说话
                    if volume > 20:  # 简单阈值
                        if not self.user_speaking:
                            self.user_speaking = True
                            if not self.last_user_input_shown:
                                print(f"\n🎤 [正在听取您的问题...]", flush=True)
                        
                        # 如果AI正在说话，则打断
                        if self.is_ai_speaking:
                            self._interrupt_ai()
                    
                    # 发送音频到处理队列
                    if not self.audio_queue.full():
                        self.audio_queue.put(audio_data)
                
                time.sleep(0.01)
                
            except Exception as e:
                if self.is_recording:
                    print(f"\n❌ 录音错误: {e}")
                break
        
        print(f"\n🛑 录音线程结束")
    
    def _interrupt_ai(self):
        """打断AI"""
        if self.is_ai_speaking:
            self.interrupt_detected = True
            self.is_ai_speaking = False
            
            # 清空音频缓冲区
            while not self.audio_buffer.empty():
                try:
                    self.audio_buffer.get_nowait()
                except:
                    break
            
            # 显示不完整回答
            if self.current_ai_response.strip():
                print(f"\n💬 AI: {self.current_ai_response.strip()} [被打断]")
            else:
                print(f"\n⚡ [AI被打断]")
            
            # 重置回答累积
            self.current_ai_response = ""
    
    def _processing_worker(self):
        """处理工作线程"""
        # 处理线程启动（移除print避免MCP干扰）
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_processing())
        finally:
            loop.close()
    
    async def _async_processing(self):
        """异步处理"""
        while self.is_recording and not self.stop_event.is_set():
            try:
                # 发送取消信号（如果需要）
                if self.interrupt_detected:
                    await self._send_cancel()
                    self.interrupt_detected = False
                
                # 发送音频
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get_nowait()
                    await self._send_audio_chunk(audio_data)
                
                # 处理响应
                await self._handle_responses()
                await asyncio.sleep(0.02)
                
            except Exception as e:
                if "websocket" not in str(e).lower():
                    print(f"\n❌ 处理错误: {e}")
                await asyncio.sleep(0.1)
    
    async def _send_cancel(self):
        """发送取消信号"""
        try:
            cancel_msg = {"type": "response.cancel"}
            await self.websocket.send(json.dumps(cancel_msg))
            print("\r🚫 [取消信号已发送]", end="", flush=True)
        except:
            pass
    
    async def _handle_responses(self):
        """处理AI响应"""
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.01)
            data = json.loads(message)
            response_type = data.get("type", "")
            
            if response_type == "response.audio.delta":
                # AI音频回答
                audio_base64 = data.get("delta", "")
                if audio_base64 and not self.interrupt_detected:
                    self.audio_buffer.put(audio_base64)
                    if not self.is_ai_speaking:
                        self.is_ai_speaking = True
                        print("\n🤖 [AI正在回答...]")
            
            elif response_type == "response.audio_transcript.delta":
                # AI文本回答（累积显示）
                transcript = data.get("delta", "")
                if transcript.strip() and not self.interrupt_detected:
                    self.current_ai_response += transcript
            
            elif response_type == "response.audio_transcript.done":
                # AI文本回答完成，显示完整内容
                if not self.interrupt_detected and self.current_ai_response.strip():
                    print(f"💬 AI: {self.current_ai_response.strip()}")
                    self.current_ai_response = ""
            
            elif response_type == "response.done":
                # AI回答完成
                self.is_ai_speaking = False
                self.last_user_input_shown = False  # 重置状态，准备下次用户输入
                if not self.interrupt_detected:
                    print("✅ [AI回答完成]\n")
            
            elif response_type == "response.cancelled":
                # AI回答被取消
                self.is_ai_speaking = False
                if self.current_ai_response.strip():
                    print(f"💬 AI: {self.current_ai_response.strip()} [已取消]")
                else:
                    print("🚫 [AI回答已取消]")
                self.current_ai_response = ""
            
            elif response_type == "conversation.item.input_audio_transcription.completed":
                # 用户语音识别完成
                transcript = data.get("transcript", "")
                if transcript.strip():
                    self.user_speaking = False
                    self.last_user_input_shown = True
                    print(f"👤 您说: {transcript}")
            
            elif response_type == "error":
                error_msg = data.get("error", {}).get("message", "未知错误")
                print(f"❌ 错误: {error_msg}")
        
        except asyncio.TimeoutError:
            # 正常情况，没有新消息
            pass
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析错误: {e}")
        except Exception as e:
            if "websocket" not in str(e).lower():
                print(f"❌ 响应处理错误: {e}")
    
    def _audio_playback_worker(self):
        """音频播放线程"""
        # 音频播放线程启动（移除print避免MCP干扰）
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                if not self.audio_buffer.empty():
                    audio_base64 = self.audio_buffer.get(timeout=0.1)
                    if not self.interrupt_detected:
                        self._play_audio(audio_base64)
                else:
                    time.sleep(0.01)
            except queue.Empty:
                time.sleep(0.01)
            except Exception as e:
                print(f"❌ 播放错误: {e}")
    
    def _play_audio(self, audio_base64):
        """播放音频"""
        try:
            if not HAS_PYAUDIO or self.interrupt_detected:
                return
            
            audio_data = base64.b64decode(audio_base64)
            
            if not self.output_stream:
                self.output_stream = self.pyaudio_instance.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    output=True,
                    frames_per_buffer=1024
                )
            
            # 播放音频
            if audio_data:
                self.output_stream.write(audio_data, exception_on_underflow=False)
        
        except Exception as e:
            if not self.interrupt_detected:
                print(f"❌ 音频播放错误: {e}")

async def run_simple_voice_assistant():
    """运行极简版语音助手"""
    print("🏫 香港科技大学广州智能语音助手 - 极简版")
    print("🎓 HKUST-GZ Intelligent Voice Assistant - Simple Edition")
    print("=" * 60)
    
    setup_api_keys()
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    
    if not api_key:
        print("❌ 未找到API密钥")
        return
    
    assistant = SimpleVoiceAssistant(api_key)
    
    try:
        # 正在连接千问Omni API（移除print避免MCP干扰）
        await assistant.connect()
        
        result = assistant.start_recording()
        if not result["success"]:
            print(f"❌ 启动失败: {result['error']}")
            return
        
        print("\n✅ 极简版语音助手已启动！")
        print("\n🎤 核心功能:")
        print("   • 实时语音对话")
        print("   • 自动音量检测打断")
        print("   • 实时AI回答字幕")
        print("   • 按 Ctrl+C 退出")
        print("\n💡 使用说明:")
        print("   • 直接说话提问")
        print("   • 开始说话时会自动打断AI")
        print("   • 等待AI回答完成后继续对话")
        print("=" * 60)
        print("\n🎤 开始对话吧...")
        
        # 主循环
        while True:
            await asyncio.sleep(1)
            
            # 检查系统状态
            if not assistant.is_recording:
                print("\n⚠️ 检测到录音系统已停止")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 用户主动退出")
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
    finally:
        print("\n🧹 正在关闭语音助手...")
        await assistant.disconnect()
        print("✅ 语音助手已安全关闭")
        print("🎓 感谢使用HKUST-GZ智能语音助手！")

if __name__ == "__main__":
    asyncio.run(run_simple_voice_assistant()) 