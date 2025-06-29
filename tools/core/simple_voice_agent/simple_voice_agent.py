#!/usr/bin/env python3
"""
Simple Voice Agent for HKUST-GZ
Author: FractFlow Team
Brief: Simplified voice assistant without web search functionality
Supports both default voice and Ni voice modes
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

class SimpleVoiceAgent(QwenRealtimeVoiceClient):
    """极简版语音助手 - 支持双音色模式"""
    
    def __init__(self, api_key=None, voice_mode="default"):
        super().__init__(api_key)
        
        # 音色模式：default 或 ni
        self.voice_mode = voice_mode
        
        # 核心状态
        self.is_ai_speaking = False
        self.interrupt_detected = False
        self.user_speaking = False
        
        # 音频缓冲区
        self.audio_buffer = queue.Queue(maxsize=50)
        
        # 文本累积
        self.current_ai_response = ""
        self.last_user_input_shown = False
        
        # TTS渐进式播放（倪校模式）
        self.tts_queue = queue.Queue()  # TTS播放队列
        self.tts_thread = None  # TTS工作线程
        self.sentence_buffer = ""  # 句子缓冲区
        self.is_tts_playing = False  # TTS播放状态
        self.tts_stop_event = threading.Event()  # TTS停止信号
        self.tts_interrupt_event = threading.Event()  # TTS快速中断信号
        
        # 分句配置
        self.sentence_endings = ['。', '！', '？', '.', '!', '?']
        self.min_sentence_length = 8  # 最小句子长度
        self.max_sentence_length = 150  # 最大句子长度
        
        # 改进的音量检测
        self.volume_threshold = 25  # 提高基础阈值
        self.volume_samples = []  # 音量采样缓冲区
        self.volume_buffer_size = 3  # 连续性检测窗口
        self.background_noise_level = 0  # 背景噪音基线
        self.calibration_samples = 0  # 校准采样计数
        
        # 初始化完成（移除print以避免MCP通信干扰）
    
    async def _configure_session(self):
        """配置会话 - 根据voice_mode选择配置"""
        config = get_voice_session_config(self.voice_mode)
        await self.websocket.send(json.dumps({"type": "session.update", "session": config}))

    def _recording_worker(self):
        """录音工作线程 - 增强版音量检测"""
        # 录音线程启动（移除print避免MCP干扰）
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                audio_data = self.input_stream.read(1024, exception_on_overflow=False)
                
                # 改进的音量检测
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                if len(audio_array) > 0:
                    volume = np.sqrt(np.mean(audio_array.astype(np.float64)**2))
                    
                    # 动态背景噪音校准（前50个采样）
                    if self.calibration_samples < 50:
                        self.background_noise_level = (self.background_noise_level * self.calibration_samples + volume) / (self.calibration_samples + 1)
                        self.calibration_samples += 1
                    
                    # 动态阈值：背景噪音 + 固定增量
                    adaptive_threshold = max(self.volume_threshold, self.background_noise_level + 15)
                    
                    # 音量缓冲区用于连续性检测
                    self.volume_samples.append(volume > adaptive_threshold)
                    if len(self.volume_samples) > self.volume_buffer_size:
                        self.volume_samples.pop(0)
                    
                    # 连续性验证：至少2/3的采样超过阈值
                    speaking_confidence = sum(self.volume_samples) / len(self.volume_samples)
                    
                    # 检测用户说话
                    if speaking_confidence >= 0.6 and len(self.volume_samples) >= 2:
                        if not self.user_speaking:
                            self.user_speaking = True
                            if not self.last_user_input_shown:
                                print(f"\n🎤 [正在听取您的问题...]", flush=True)
                        
                        # 如果AI正在说话，则打断（多级打断）
                        if self.is_ai_speaking or self.is_tts_playing:
                            self._interrupt_ai_multilevel()
                    
                    # 发送音频到处理队列
                    if not self.audio_queue.full():
                        self.audio_queue.put(audio_data)
                
                time.sleep(0.005)  # 提高检测频率到5ms
                
            except Exception as e:
                if self.is_recording:
                    print(f"\n❌ 录音错误: {e}")
                break
        
        print(f"\n🛑 录音线程结束")
    
    def _interrupt_ai_multilevel(self):
        """多级打断AI - 快速响应机制"""
        if self.is_ai_speaking or self.is_tts_playing:
            # 第一级：立即设置中断信号
            self.interrupt_detected = True
            self.tts_interrupt_event.set()
            
            # 第二级：立即停止倪校TTS播放
            if self.voice_mode == "ni":
                try:
                    from tools.core.guang_voice_assistant.ni_voice_clone_client.main import set_interrupt
                    set_interrupt()  # 立即中断TTS播放
                except ImportError:
                    pass
            
            # 第三级：清空所有缓冲区和队列
            self.is_ai_speaking = False
            self.is_tts_playing = False
            
            # 清空音频缓冲区
            while not self.audio_buffer.empty():
                try:
                    self.audio_buffer.get_nowait()
                except:
                    break
            
            # 清空TTS队列
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                except:
                    break
            
            # 重置句子缓冲区
            self.sentence_buffer = ""
            
            # 显示打断信息
            if self.current_ai_response.strip():
                print(f"\n💬 AI: {self.current_ai_response.strip()} [被快速打断]")
            else:
                print(f"\n⚡ [AI被快速打断]")
            
            # 重置回答累积
            self.current_ai_response = ""

    def _interrupt_ai(self):
        """打断AI - 兼容旧接口，重定向到多级打断"""
        self._interrupt_ai_multilevel()
    
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
        """处理AI响应 - 支持倪校TTS模式"""
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.01)
            data = json.loads(message)
            response_type = data.get("type", "")
            
            if response_type == "response.audio.delta":
                # AI音频回答 - 默认模式播放，倪校模式跳过
                audio_base64 = data.get("delta", "")
                if audio_base64 and not self.interrupt_detected:
                    if self.voice_mode == "default":
                        # 默认模式：直接播放千问音频
                        self.audio_buffer.put(audio_base64)
                    # 倪校模式：跳过音频，等待文本完成后用TTS播放
                    if not self.is_ai_speaking:
                        self.is_ai_speaking = True
                        print("\n🤖 [AI正在回答...]")
            
            elif response_type == "response.audio_transcript.delta":
                # AI文本回答（累积显示+流式TTS）
                transcript = data.get("delta", "")
                if transcript.strip() and not self.interrupt_detected:
                    self.current_ai_response += transcript
                    
                    # 倪校模式：流式分句TTS
                    if self.voice_mode == "ni":
                        self.sentence_buffer += transcript
                        
                        # 检查是否有完整句子可以播放
                        sentences = self._extract_sentences(self.sentence_buffer)
                        if len(sentences) > 1:  # 至少有一个完整句子
                            # 播放除最后一个句子外的所有句子
                            for sentence in sentences[:-1]:
                                self._queue_sentence_tts(sentence)
                            # 保留最后一个未完成的句子
                            self.sentence_buffer = sentences[-1] if sentences else ""
            
            elif response_type == "response.audio_transcript.done":
                # AI文本回答完成，显示完整内容并播放剩余TTS
                if not self.interrupt_detected and self.current_ai_response.strip():
                    print(f"💬 AI: {self.current_ai_response.strip()}")
                    
                    # 倪校模式：播放剩余的句子缓冲区
                    if self.voice_mode == "ni" and self.sentence_buffer.strip():
                        self._queue_sentence_tts(self.sentence_buffer.strip())
                        self.sentence_buffer = ""
                    
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
        """播放音频 - 仅默认模式使用"""
        try:
            if not HAS_PYAUDIO or self.interrupt_detected or self.voice_mode == "ni":
                return  # 倪校模式不播放千问音频
            
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
    
    def _extract_sentences(self, text):
        """智能分句提取"""
        sentences = []
        current_sentence = ""
        
        for char in text:
            current_sentence += char
            
            # 检测句子结束
            if char in self.sentence_endings:
                # 检查句子长度是否合理
                if len(current_sentence.strip()) >= self.min_sentence_length:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
                # 如果太短，继续累积
            
            # 防止单句过长
            elif len(current_sentence) >= self.max_sentence_length:
                # 寻找最近的标点符号分割
                for i in range(len(current_sentence) - 1, -1, -1):
                    if current_sentence[i] in ['，', ',', '；', ';', '：', ':']:
                        sentences.append(current_sentence[:i+1].strip())
                        current_sentence = current_sentence[i+1:]
                        break
                else:
                    # 没找到标点，强制分割
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
        
        # 处理剩余文本
        if current_sentence.strip():
            sentences.append(current_sentence.strip())
        
        return sentences
    
    def _start_tts_worker(self):
        """启动TTS工作线程"""
        if self.voice_mode == "ni" and (self.tts_thread is None or not self.tts_thread.is_alive()):
            self.tts_stop_event.clear()
            self.tts_thread = threading.Thread(target=self._tts_worker, daemon=True)
            self.tts_thread.start()
    
    def _stop_tts_worker(self):
        """停止TTS工作线程"""
        if self.tts_thread and self.tts_thread.is_alive():
            self.tts_stop_event.set()
            self.tts_interrupt_event.set()  # 设置快速中断信号
            
            # 立即停止倪校TTS播放
            if self.voice_mode == "ni":
                try:
                    from tools.core.guang_voice_assistant.ni_voice_clone_client.main import set_interrupt
                    set_interrupt()
                except ImportError:
                    pass
            
            # 清空队列
            while not self.tts_queue.empty():
                try:
                    self.tts_queue.get_nowait()
                except:
                    break
    
    def _tts_worker(self):
        """TTS队列处理器 - 增强中断响应"""
        try:
            # 导入倪校TTS功能
            from tools.core.guang_voice_assistant.ni_voice_clone_client.main import play_ni_voice
            
            while not self.tts_stop_event.is_set():
                try:
                    # 检查快速中断信号
                    if self.tts_interrupt_event.is_set():
                        # 清空队列并重置信号
                        while not self.tts_queue.empty():
                            try:
                                self.tts_queue.get_nowait()
                                self.tts_queue.task_done()
                            except:
                                break
                        self.tts_interrupt_event.clear()
                        continue
                    
                    # 从队列获取句子
                    sentence = self.tts_queue.get(timeout=0.2)  # 减少超时时间提高响应性
                    
                    # 再次检查中断信号
                    if sentence and not self.interrupt_detected and not self.tts_interrupt_event.is_set():
                        self.is_tts_playing = True
                        play_ni_voice(sentence)
                        self.is_tts_playing = False
                    
                    # 标记任务完成
                    self.tts_queue.task_done()
                    
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"⚠️ TTS播放错误: {e}")
                    self.is_tts_playing = False
                    
        except ImportError:
            print("⚠️ 倪校TTS模块不可用")
    
    def _queue_sentence_tts(self, sentence):
        """将句子加入TTS队列"""
        if self.voice_mode == "ni" and sentence.strip():
            try:
                self.tts_queue.put_nowait(sentence.strip())
                if not self.is_ai_speaking:
                    self.is_ai_speaking = True
                    print("🎓 [倪校长开始回答...]")
            except queue.Full:
                print("⚠️ TTS队列已满，跳过句子")
    
    def _play_ni_tts(self, text):
        """播放倪校TTS音频（兼容旧接口）"""
        if not text.strip():
            return
            
        try:
            # 分句处理
            sentences = self._extract_sentences(text)
            for sentence in sentences:
                self._queue_sentence_tts(sentence)
                
        except Exception as e:
            print(f"⚠️ 分句处理失败: {e}，降级为文本显示")

async def run_simple_voice_agent(voice_mode="default"):
    """运行极简版语音助手"""
    mode_name = "默认音色版" if voice_mode == "default" else "倪校音色版（流式TTS）"
    print(f"🏫 香港科技大学广州智能语音助手 - {mode_name}")
    print("🎓 HKUST-GZ Intelligent Voice Assistant - Simple Edition")
    print("=" * 60)
    
    setup_api_keys()
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    
    if not api_key:
        print("❌ 未找到API密钥")
        return
    
    agent = SimpleVoiceAgent(api_key, voice_mode)
    
    try:
        # 正在连接千问Omni API（移除print避免MCP干扰）
        await agent.connect()
        
        result = agent.start_recording()
        if not result["success"]:
            print(f"❌ 启动失败: {result['error']}")
            return
        
        # 启动TTS工作线程（倪校模式）
        if voice_mode == "ni":
            agent._start_tts_worker()
            print("🎓 [倪校TTS引擎已启动]")
        
        print(f"\n✅ {mode_name}语音助手已启动！")
        print("\n🎤 核心功能:")
        print("   • 实时语音对话")
        print("   • ⚡ 智能快速打断（100-300ms响应）")
        print("   • 🔊 动态音量检测+背景噪音适应")
        print("   • 实时AI回答字幕")
        if voice_mode == "ni":
            print("   • 🚀 流式TTS播放（大幅提升响应速度）")
            print("   • 🛑 多级打断机制（立即停止音频）")
        print("   • 按 Ctrl+C 退出")
        print("\n💡 使用说明:")
        print("   • 直接说话提问")
        print("   • 🎯 开始说话时自动快速打断AI（极速响应）")
        if voice_mode == "ni":
            print("   • 倪校声音会在句子生成时立即播放")
        print("   • 等待AI回答完成后继续对话")
        print("=" * 60)
        print("\n🔧 正在校准背景噪音...")
        print("🎤 开始对话吧（前几秒系统会自动适应环境音量）...")
        
        # 主循环
        while True:
            await asyncio.sleep(1)
            
            # 检查系统状态
            if not agent.is_recording:
                print("\n⚠️ 检测到录音系统已停止")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 用户主动退出")
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
    finally:
        print("\n🧹 正在关闭语音助手...")
        
        # 停止TTS工作线程
        if voice_mode == "ni":
            agent._stop_tts_worker()
            print("🎓 [倪校TTS引擎已停止]")
        
        await agent.disconnect()
        print("✅ 语音助手已安全关闭")
        print("🎓 感谢使用HKUST-GZ智能语音助手！")

if __name__ == "__main__":
    import sys
    voice_mode = sys.argv[1] if len(sys.argv) > 1 else "default"
    asyncio.run(run_simple_voice_agent(voice_mode)) 