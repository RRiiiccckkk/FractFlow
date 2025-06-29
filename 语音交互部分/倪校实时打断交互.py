#!/usr/bin/env python3
"""
倪校实时打断语音交互程序 v1.0
香港科技大学广州校长倪明选教授语音克隆版本
支持实时打断功能 + GPT-SoVITS TTS集成
"""

import asyncio
import os
import sys
import json
import threading
import queue
import time
import wave
import io
import base64
import requests
from typing import Optional
import websockets

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    print("⚠️  PyAudio未安装，将无法播放音频")

# 导入基础类
from simple_voice_assistant import SimpleVoiceAssistant
from voice_config import setup_api_keys

# GPT-SoVITS配置常量
GPT_SOVITS_URL = "http://10.120.17.57:9880/tts"
GPT_SOVITS_PARAMS = {
    "text_lang": "zh",
    "ref_audio_path": "ref_audio/ni_zh_01.wav",
    "prompt_lang": "zh", 
    "text_split_method": "cut5",
    "batch_size": 1,
    "media_type": "wav",
    "streaming_mode": "true"
}

# 倪校系统指令
NIXIAO_SYSTEM_INSTRUCTION = """你是香港科技大学广州校长倪明选教授。

作为香港科技大学广州的校长，你的特点：
1. 权威而亲和，既有学者的严谨，又有长者的温和
2. 对学校发展充满热情，关心学生成长
3. 表达清晰有条理，富有感染力
4. 经常用"我们香港科技大学广州"来表达对学校的自豪

你的回答风格：
• 语调温和而有力，体现校长的权威性
• 经常鼓励学生，表达对年轻人的期望
• 介绍学校时充满自豪感
• 回答问题时会适当联系到教育理念和人才培养

请用校长的身份和语调，自然地回答学生和访客的问题。回答要简洁明了，语调亲和友好。"""

class NiXiaoInterruptVoiceAssistant(SimpleVoiceAssistant):
    """倪校实时打断语音助手 - 支持GPT-SoVITS声音克隆"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        
        # GPT-SoVITS相关状态
        self.gptsovits_available = False
        self.wav_audio_buffer = queue.Queue(maxsize=50)
        self.current_tts_request = None
        self.tts_generating = False
        
        # 移除原有音频缓冲，使用WAV缓冲
        self.audio_buffer = self.wav_audio_buffer
        
        self.websocket_lock = asyncio.Lock()  # 新增WebSocket异步锁
        
        print("🎓 倪校实时打断语音助手初始化完成")
        
    async def _configure_session(self):
        """配置会话 - 禁用千问音频输出，仅使用文本"""
        config = {
            "type": "session.update", 
            "session": {
                "modalities": ["text"],  # 仅使用文本模式
                "instructions": NIXIAO_SYSTEM_INSTRUCTION,
                "input_audio_format": "pcm16",
                # 移除output_audio_format，禁用千问TTS
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.1,  # 更敏感的检测阈值
                    "prefix_padding_ms": 200,  # 减少前缀延迟
                    "silence_duration_ms": 500  # 更快的静音判断
                },
                "temperature": 0.7,
                "max_response_output_tokens": 2048
            }
        }
        
        async with self.websocket_lock:
            await self.websocket.send(json.dumps(config))
        print("⚙️ 倪校会话配置完成（已禁用千问TTS，启用GPT-SoVITS）")
        
        # 检查GPT-SoVITS服务可用性
        await self._check_gptsovits_availability()
    
    async def _check_gptsovits_availability(self):
        """检查GPT-SoVITS服务可用性"""
        try:
            test_params = GPT_SOVITS_PARAMS.copy()
            test_params["text"] = "测试"
            
            response = requests.get(GPT_SOVITS_URL, params=test_params, timeout=5)
            self.gptsovits_available = response.status_code == 200
            
            if self.gptsovits_available:
                print("✅ GPT-SoVITS服务可用")
            else:
                print(f"⚠️ GPT-SoVITS服务异常，状态码: {response.status_code}")
                
        except Exception as e:
            self.gptsovits_available = False
            print(f"❌ GPT-SoVITS服务不可用: {e}")
    
    async def _call_gptsovits_tts(self, text: str) -> Optional[bytes]:
        """调用GPT-SoVITS TTS服务"""
        if not self.gptsovits_available or not text.strip():
            return None
            
        try:
            params = GPT_SOVITS_PARAMS.copy()
            params["text"] = text
            
            print(f"🔊 正在生成倪校语音: {text[:30]}...")
            
            response = requests.get(GPT_SOVITS_URL, params=params, stream=True, timeout=10)
            
            if response.status_code == 200:
                audio_data = b""
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk and not self.interrupt_detected:
                        audio_data += chunk
                    elif self.interrupt_detected:
                        print("🚫 TTS生成被打断")
                        break
                        
                return audio_data if not self.interrupt_detected else None
            else:
                print(f"❌ GPT-SoVITS请求失败，状态码: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ GPT-SoVITS调用错误: {e}")
            return None
    
    async def _robust_gptsovits_call(self, text: str, max_retries: int = 3) -> Optional[bytes]:
        """带重试机制的GPT-SoVITS调用"""
        for attempt in range(max_retries):
            if self.interrupt_detected:
                return None
                
            audio_data = await self._call_gptsovits_tts(text)
            if audio_data:
                return audio_data
                
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 指数退避
                print(f"🔄 第{attempt + 1}次重试失败，{wait_time}秒后重试...")
                await asyncio.sleep(wait_time)
        
        print("❌ GPT-SoVITS调用失败，已达到最大重试次数")
        return None
    
    def _play_wav_audio(self, wav_data: bytes):
        """播放WAV音频数据"""
        try:
            if not HAS_PYAUDIO or self.interrupt_detected or not wav_data:
                return
                
            # 解析WAV数据
            wav_io = io.BytesIO(wav_data)
            wav = wave.open(wav_io, "rb")
            
            # 配置音频流
            if not self.output_stream or self.output_stream._rate != wav.getframerate():
                if self.output_stream:
                    self.output_stream.stop_stream()
                    self.output_stream.close()
                    
                self.output_stream = self.pyaudio_instance.open(
                    format=self.pyaudio_instance.get_format_from_width(wav.getsampwidth()),
                    channels=wav.getnchannels(),
                    rate=wav.getframerate(),
                    output=True,
                    frames_per_buffer=1024
                )
            
            # 播放音频
            wav_io.seek(44)  # 跳过WAV头部
            while True:
                if self.interrupt_detected:
                    break
                    
                audio_chunk = wav_io.read(1024)
                if not audio_chunk:
                    break
                    
                self.output_stream.write(audio_chunk, exception_on_underflow=False)
                
            wav.close()
            
        except Exception as e:
            if not self.interrupt_detected:
                print(f"❌ WAV音频播放错误: {e}")
    
    def _safe_create_task(self, coro):
        """安全地创建异步任务，处理事件循环问题"""
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return loop.create_task(coro)
            else:
                # 如果循环未运行，尝试使用默认循环
                return asyncio.create_task(coro)
        except RuntimeError as e:
            if "attached to a different loop" in str(e) or "no running event loop" in str(e):
                # 事件循环问题，使用线程安全方式
                try:
                    loop = asyncio.get_running_loop()
                    return loop.create_task(coro)
                except RuntimeError:
                    # 降级到后台线程执行
                    import threading
                    def run_coro():
                        try:
                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            new_loop.run_until_complete(coro)
                        except Exception as e:
                            print(f"❌ 后台任务执行失败: {e}")
                        finally:
                            new_loop.close()
                    
                    thread = threading.Thread(target=run_coro)
                    thread.daemon = True
                    thread.start()
                    return None
            else:
                raise e

    async def _handle_responses(self):
        """处理AI响应 - 重写以集成GPT-SoVITS"""
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
            data = json.loads(message)
            response_type = data.get("type", "")
            
            # 移除对千问音频的处理，只处理文本
            if response_type == "response.audio_transcript.delta":
                # AI文本回答（累积显示）
                transcript = data.get("delta", "")
                if transcript.strip() and not self.interrupt_detected:
                    self.current_ai_response += transcript
            
            elif response_type == "response.audio_transcript.done":
                # AI文本回答完成，调用GPT-SoVITS生成音频
                if not self.interrupt_detected and self.current_ai_response.strip():
                    print(f"💬 倪校: {self.current_ai_response.strip()}")
                    
                    # 安全调用GPT-SoVITS生成音频
                    if self.gptsovits_available:
                        try:
                            self._safe_create_task(self._generate_and_play_nixiao_voice(self.current_ai_response.strip()))
                        except Exception as e:
                            print(f"⚠️ 创建音频生成任务失败: {e}")
                    
                    # 检测搜索触发
                    if self.detect_search_trigger(self.current_ai_response) and not self.search_in_progress:
                        self.search_in_progress = True
                        try:
                            self._safe_create_task(self._handle_search_trigger())
                        except Exception as e:
                            print(f"⚠️ 创建搜索任务失败: {e}")
                            self.search_in_progress = False
                    
                    self.current_ai_response = ""
            
            elif response_type == "response.done":
                # AI回答完成
                self.last_user_input_shown = False
                if not self.interrupt_detected:
                    print("✅ [倪校回答完成]\n")
            
            elif response_type == "response.cancelled":
                # AI回答被取消
                if self.current_ai_response.strip():
                    print(f"💬 倪校: {self.current_ai_response.strip()} [已取消]")
                else:
                    print("🚫 [倪校回答已取消]")
                self.current_ai_response = ""
            
            elif response_type == "conversation.item.input_audio_transcription.completed":
                # 用户语音识别完成
                transcript = data.get("transcript", "")
                if transcript.strip():
                    self.user_speaking = False
                    self.last_user_input_shown = True
                    self.last_user_question = transcript
                    print(f"👤 您说: {transcript}")
            
            elif response_type == "error":
                error_msg = data.get("error", {}).get("message", "未知错误")
                print(f"❌ 错误: {error_msg}")
        
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            if "websocket" not in str(e).lower():
                print(f"❌ 响应处理错误: {e}")
    
    async def _generate_and_play_nixiao_voice(self, text: str):
        """生成并播放倪校语音"""
        try:
            self.tts_generating = True
            self.is_ai_speaking = True
            
            # 调用GPT-SoVITS生成音频
            audio_data = await self._robust_gptsovits_call(text)
            
            if audio_data and not self.interrupt_detected:
                # 将音频数据放入播放队列
                self.wav_audio_buffer.put(audio_data)
            elif self.interrupt_detected:
                print("🚫 倪校语音生成被打断")
            
        except Exception as e:
            print(f"❌ 倪校语音生成错误: {e}")
        finally:
            self.tts_generating = False
    
    def _audio_playback_worker(self):
        """音频播放线程 - 支持WAV格式"""
        print("🔊 倪校音频播放线程启动")
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                if not self.wav_audio_buffer.empty():
                    wav_data = self.wav_audio_buffer.get(timeout=0.1)
                    if not self.interrupt_detected:
                        self._play_wav_audio(wav_data)
                        self.is_ai_speaking = False
                else:
                    time.sleep(0.01)
            except queue.Empty:
                time.sleep(0.01)
            except Exception as e:
                print(f"❌ 倪校音频播放错误: {e}")
        
        print("🛑 倪校音频播放线程结束")
    
    def _interrupt_ai(self):
        """打断AI - 增强版，同时停止GPT-SoVITS"""
        if self.is_ai_speaking or self.tts_generating:
            self.interrupt_detected = True
            self.is_ai_speaking = False
            self.tts_generating = False
            
            # 清空WAV音频缓冲区
            while not self.wav_audio_buffer.empty():
                try:
                    self.wav_audio_buffer.get_nowait()
                except:
                    break
            
            # 显示打断信息
            if self.current_ai_response.strip():
                print(f"\n💬 倪校: {self.current_ai_response.strip()} [被打断]")
            else:
                print(f"\n⚡ [倪校被打断]")
            
            self.current_ai_response = ""

    async def _send_audio_chunk(self, audio_data: bytes):
        try:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            event = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            async with self.websocket_lock:
                await self.websocket.send(json.dumps(event))
        except Exception as e:
            print(f"❌ 发送音频失败: {e}")
            if "1011" in str(e):
                print("🔄 检测到服务器错误，可能需要重连")

    async def _send_cancel(self):
        try:
            cancel_event = {"type": "response.cancel"}
            async with self.websocket_lock:
                await self.websocket.send(json.dumps(cancel_event))
            print("🚫 [取消信号已发送]", end="", flush=True)
        except Exception as e:
            print(f"❌ 发送取消信号失败: {e}")

    async def _send_search_response(self, response_text):
        try:
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {"type": "text", "text": response_text}
                    ]
                }
            }
            async with self.websocket_lock:
                await self.websocket.send(json.dumps(message))
            response_request = {"type": "response.create"}
            async with self.websocket_lock:
                await self.websocket.send(json.dumps(response_request))
        except Exception as e:
            print(f"❌ 发送搜索回答失败: {e}")

    async def _reconnect(self):
        print("🔄 检测到WebSocket断开，正在尝试重连...")
        retry = 0
        while True:
            try:
                if self.websocket:
                    try:
                        await self.websocket.close()
                    except Exception:
                        pass
                await asyncio.sleep(min(2 ** retry, 30))
                result = await self.connect()
                if result and result.get("success"):
                    print("✅ 重连成功！")
                    return
                else:
                    print(f"⚠️ 重连失败: {result.get('error') if result else '未知错误'}")
            except Exception as e:
                print(f"❌ 重连异常: {e}")
            retry += 1

    async def _async_processing(self):
        audio_chunks_sent = 0
        while self.is_recording and not self.stop_event.is_set():
            try:
                if self.interrupt_detected:
                    await self._send_cancel()
                    self.interrupt_detected = False
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get_nowait()
                    await self._send_audio_chunk(audio_data)
                    audio_chunks_sent += 1
                await self._handle_responses()
                await asyncio.sleep(0.01)
            except websockets.exceptions.ConnectionClosed:
                print("⚠️ WebSocket连接已断开，尝试自动重连...")
                await self._reconnect()
            except Exception as e:
                if "websocket" not in str(e).lower():
                    print(f"❌ 处理错误: {e}")
                await asyncio.sleep(0.1)

    async def disconnect(self):
        try:
            print("🔌 正在断开连接...")
            self.stop_recording()
            if self.websocket and self.is_connected:
                try:
                    await self.websocket.close()
                except Exception:
                    pass
            self.is_connected = False
            if HAS_PYAUDIO and self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
            return {"success": True, "message": "连接已断开"}
        except Exception as e:
            return {"success": False, "error": f"断开连接失败: {e}"}

async def run_nixiao_interrupt_assistant():
    """运行倪校实时打断语音助手"""
    print("🎓 香港科技大学广州 - 倪校实时打断语音助手")
    print("🔊 President Ni Mingxuan Voice Assistant - Interrupt Edition")
    print("=" * 60)
    
    setup_api_keys()
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    
    if not api_key:
        print("❌ 未找到API密钥")
        return
    
    assistant = NiXiaoInterruptVoiceAssistant(api_key)
    
    try:
        print("🔗 正在连接千问Omni API...")
        await assistant.connect()
        
        result = assistant.start_recording()
        if not result["success"]:
            print(f"❌ 启动失败: {result['error']}")
            return
        
        print("\n✅ 倪校实时打断语音助手已启动！")
        print("\n🎓 特色功能:")
        print("   • 倪校声音克隆 (GPT-SoVITS)")
        print("   • 实时语音打断")
        print("   • 智能对话理解")
        print("   • 按 Ctrl+C 退出")
        print("\n💡 使用说明:")
        print("   • 直接说话与倪校对话")
        print("   • 开始说话时会自动打断倪校")
        print("   • 等待倪校回答完成后继续对话")
        print("=" * 60)
        print("\n🎤 您好！我是香港科技大学广州校长倪明选，请开始对话...")
        
        # 主循环
        while True:
            await asyncio.sleep(1)
            
            if not assistant.is_recording:
                print("\n⚠️ 检测到录音系统已停止")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 用户主动退出")
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
    finally:
        print("\n🧹 正在关闭倪校语音助手...")
        await assistant.disconnect()
        print("✅ 倪校语音助手已安全关闭")
        print("🎓 感谢使用HKUST-GZ倪校语音助手！")

if __name__ == "__main__":
    asyncio.run(run_nixiao_interrupt_assistant()) 