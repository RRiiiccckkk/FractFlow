#!/usr/bin/env python3
"""
香港科技大学广州智能语音助手 - 极简版
HKUST-GZ Intelligent Voice Assistant - Simple Edition
只包含核心功能：实时语音交互 + 基本打断 + 网络搜索
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
import re

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

# 添加websearch模块导入
sys.path.insert(0, os.path.join(parent_dir, 'tools', 'core', 'websearch', 'src'))
try:
    from core_logic import web_search_and_browse
    HAS_WEBSEARCH = True
    print("✅ 网络搜索功能已加载")
except ImportError as e:
    HAS_WEBSEARCH = False
    print(f"⚠️  网络搜索功能未加载: {e}")

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient
from voice_config import setup_api_keys, get_voice_session_config

class SimpleVoiceAssistant(QwenRealtimeVoiceClient):
    """极简版语音助手 - 专注核心功能 + 网络搜索"""
    
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
        
        # 网络搜索相关
        self.last_user_question = ""  # 记录最后用户问题
        self.search_in_progress = False  # 搜索进行中标志
        
        # 搜索触发词
        self.search_triggers = [
            "我做不到", "我不知道", "我无法", "抱歉，我不能", 
            "我没有相关信息", "我无法提供", "我不确定", "我没有这方面的信息",
            "我需要搜索", "让我搜索一下", "我去查一查", "我需要查找"
        ]
        
        print("🎤 极简版语音助手初始化完成（含网络搜索）")
    
    async def _configure_session(self):
        """配置会话"""
        config = get_voice_session_config()
        config["instructions"] = (
            "你是香港科技大学广州的智能语音助手，具备网络搜索能力。"
            "请用自然、连贯的语气回答用户问题。回答要简洁明了，语调亲和友好。"
            "\n重要功能说明："
            "1. 当遇到你无法直接回答的问题（如最新信息、实时数据、专业知识等）时，"
            "请明确告诉用户：'让我为您搜索最新信息'，然后说'我需要搜索'。"
            "2. 当你说出'我需要搜索'时，系统会自动启动网络搜索功能。"
            "3. 搜索完成后，你会收到搜索结果，请基于这些信息重新回答用户问题。"
            "\n示例回答模式："
            "- 对于实时信息：'让我为您搜索最新信息。我需要搜索。'"
            "- 对于专业问题：'这个问题比较专业，让我搜索详细资料。我需要搜索。'"
            "- 对于不确定信息：'我不太确定这个信息，让我搜索确认一下。我需要搜索。'"
        )
        await self.websocket.send(json.dumps({"type": "session.update", "session": config}))
        
    def detect_search_trigger(self, text):
        """检测是否需要触发搜索"""
        if not HAS_WEBSEARCH or not text:
            return False
            
        text_lower = text.lower()
        for trigger in self.search_triggers:
            if trigger in text_lower:
                return True
        return False
    
    async def perform_web_search(self, question):
        """执行网络搜索"""
        if not HAS_WEBSEARCH or not question.strip():
            return "搜索功能不可用或问题为空"
            
        try:
            print(f"\n🔍 正在搜索: {question}")
            
            # 使用网络搜索功能
            search_result = await web_search_and_browse(
                query=question,
                search_engine="duckduckgo", 
                num_results=3,
                max_browse=1,  # 浏览第一个结果
                max_length=3000  # 限制内容长度
            )
            
            print(f"✅ 搜索完成，结果长度: {len(search_result)}字符")
            return search_result
            
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return f"搜索过程中出现错误: {str(e)}"
    
    def synthesize_search_response(self, search_result):
        """合成搜索结果回答"""
        if not search_result or "搜索过程中出现错误" in search_result:
            return "抱歉，搜索时遇到了问题，请稍后再试。"
        
        # 简化搜索结果，提取关键信息
        lines = search_result.split('\n')
        useful_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('🔍') and not line.startswith('📌') and not line.startswith('🔗'):
                useful_lines.append(line)
                if len(useful_lines) >= 8:  # 限制行数
                    break
        
        summary = ' '.join(useful_lines[:5])  # 取前5行作为摘要
        if len(summary) > 800:  # 限制长度
            summary = summary[:800] + "..."
            
        return f"根据搜索结果，{summary}"
    
    async def _handle_search_trigger(self):
        """处理搜索触发"""
        try:
            if not self.last_user_question.strip():
                print("⚠️ 没有记录到用户问题，无法执行搜索")
                self.search_in_progress = False
                return
            
            print(f"\n🔍 AI触发搜索功能")
            
            # 执行搜索
            search_result = await self.perform_web_search(self.last_user_question)
            
            if search_result and "搜索过程中出现错误" not in search_result:
                # 合成搜索结果回答
                enhanced_response = self.synthesize_search_response(search_result)
                
                # 通过websocket发送新的回答
                await self._send_search_response(enhanced_response)
            else:
                print("❌ 搜索失败，无法提供增强回答")
                
        except Exception as e:
            print(f"❌ 搜索处理错误: {e}")
        finally:
            self.search_in_progress = False
    
    async def _send_search_response(self, response_text):
        """发送搜索结果回答"""
        try:
            print(f"\n🔍 基于搜索结果的回答:")
            print(f"💬 AI: {response_text}")
            
            # 发送会话项目以包含搜索结果
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "assistant",
                    "content": [
                        {
                            "type": "text",
                            "text": response_text
                        }
                    ]
                }
            }
            await self.websocket.send(json.dumps(message))
            
            # 请求响应
            response_request = {"type": "response.create"}
            await self.websocket.send(json.dumps(response_request))
            
        except Exception as e:
            print(f"❌ 发送搜索回答失败: {e}")

    def _recording_worker(self):
        """录音工作线程 - 极简版"""
        print("🎤 录音线程启动")
        
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
        print("🔄 处理线程启动")
        
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
                    
                    # 检测是否需要触发搜索
                    if self.detect_search_trigger(self.current_ai_response) and not self.search_in_progress:
                        self.search_in_progress = True
                        asyncio.create_task(self._handle_search_trigger())
                    
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
                    self.last_user_question = transcript  # 记录用户问题用于搜索
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
        print("🔊 音频播放线程启动")
        
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
        print("🔗 正在连接千问Omni API...")
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