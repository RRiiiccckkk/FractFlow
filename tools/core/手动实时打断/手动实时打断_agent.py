#!/usr/bin/env python3
"""
FractFlow 手动语音控制工具 - 简化版
基于千问Omni实时语音API + 终端回车控制（无需管理员权限）
"""

import asyncio
import json
import os
import sys
import threading
import time
import base64
import select
from typing import Dict, Any, Optional
import psutil  # 添加系统监控库
import tracemalloc  # 添加内存跟踪
import queue
import gc
import signal
import tempfile
from threading import Lock, Event

# 添加项目路径支持
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入对话缓存管理器
try:
    from tools.core.manual_voice_control.conversation_cache_manager import ConversationCacheManager
    HAS_CACHE_MANAGER = True
except ImportError:
    HAS_CACHE_MANAGER = False
    print("⚠️ 对话缓存管理器不可用")

# 导入核心依赖
try:
    import websockets
    import pyaudio
    import numpy as np
    from dotenv import load_dotenv
    HAS_DEPENDENCIES = True
except ImportError as e:
    HAS_DEPENDENCIES = False
    missing_deps = str(e)

load_dotenv()

class MemoryMonitor:
    """内存使用监控器"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss
        self.peak_memory = self.initial_memory
        self.memory_growth_rate = []
        self.check_count = 0
        
        # 阈值设置 (字节)
        self.warning_threshold = 500 * 1024 * 1024  # 500MB
        self.critical_threshold = 1024 * 1024 * 1024  # 1GB
        
    def check_memory_status(self):
        """检查当前内存状态"""
        self.check_count += 1
        
        try:
            memory_info = self.process.memory_info()
            current_rss = memory_info.rss
            
            # 更新峰值内存
            if current_rss > self.peak_memory:
                self.peak_memory = current_rss
            
            # 计算内存增长率
            growth = current_rss - self.initial_memory
            if len(self.memory_growth_rate) >= 10:
                self.memory_growth_rate.pop(0)
            self.memory_growth_rate.append(growth)
            
            # 计算平均增长率
            avg_growth = sum(self.memory_growth_rate) / len(self.memory_growth_rate)
            
            # 判断状态
            status = {
                'current_mb': current_rss / (1024 * 1024),
                'peak_mb': self.peak_memory / (1024 * 1024),
                'growth_mb': growth / (1024 * 1024),
                'avg_growth_mb': avg_growth / (1024 * 1024),
                'warning': False,
                'critical': False,
                'message': ''
            }
            
            if current_rss > self.critical_threshold:
                status['critical'] = True
                status['message'] = f"内存使用达到临界值: {status['current_mb']:.1f}MB"
            elif current_rss > self.warning_threshold:
                status['warning'] = True
                status['message'] = f"内存使用超过警告值: {status['current_mb']:.1f}MB"
            elif avg_growth > 50 * 1024 * 1024:  # 平均增长超过50MB
                status['warning'] = True
                status['message'] = f"内存增长率过快: {status['avg_growth_mb']:.1f}MB"
            
            # 每50次检查打印一次状态
            if self.check_count % 50 == 0:
                print(f"📊 内存状态: 当前{status['current_mb']:.1f}MB, 峰值{status['peak_mb']:.1f}MB, 增长{status['growth_mb']:.1f}MB")
            
            return status
            
        except Exception as e:
            print(f"内存监控错误: {e}")
            return {'warning': False, 'critical': False, 'message': ''}

class SystemHealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        self.check_count = 0
        self.thread_count_history = []
        self.fd_count_history = []
        
    def check_system_health(self):
        """检查系统整体健康状态"""
        self.check_count += 1
        
        try:
            process = psutil.Process()
            
            # 检查线程数量
            thread_count = process.num_threads()
            if len(self.thread_count_history) >= 20:
                self.thread_count_history.pop(0)
            self.thread_count_history.append(thread_count)
            
            # 检查文件描述符数量（仅在支持的系统上）
            fd_count = 0
            try:
                fd_count = process.num_fds()
                if len(self.fd_count_history) >= 20:
                    self.fd_count_history.pop(0)
                self.fd_count_history.append(fd_count)
            except AttributeError:
                # Windows不支持num_fds
                pass
            
            # 检查CPU使用率
            cpu_percent = process.cpu_percent()
            
            # 分析健康状态
            status = {
                'healthy': True,
                'warning': '',
                'critical': False,
                'thread_count': thread_count,
                'fd_count': fd_count,
                'cpu_percent': cpu_percent
            }
            
            # 线程数量异常检查
            if thread_count > 50:
                status['healthy'] = False
                status['critical'] = True
                status['warning'] = f"线程数量异常: {thread_count}"
            elif thread_count > 20:
                status['healthy'] = False
                status['warning'] = f"线程数量偏高: {thread_count}"
            
            # 文件描述符检查
            if fd_count > 100:
                status['healthy'] = False
                status['critical'] = True
                status['warning'] = f"文件描述符过多: {fd_count}"
            elif fd_count > 50:
                status['healthy'] = False
                status['warning'] = f"文件描述符偏多: {fd_count}"
            
            # CPU使用率检查
            if cpu_percent > 80:
                status['healthy'] = False
                status['warning'] = f"CPU使用率过高: {cpu_percent:.1f}%"
            
            # 检查线程数量增长趋势
            if len(self.thread_count_history) >= 10:
                recent_avg = sum(self.thread_count_history[-5:]) / 5
                older_avg = sum(self.thread_count_history[-10:-5]) / 5
                if recent_avg > older_avg * 1.5:
                    status['healthy'] = False
                    status['warning'] = f"线程数量快速增长: {older_avg:.1f} -> {recent_avg:.1f}"
            
            # 每100次检查打印一次状态
            if self.check_count % 100 == 0:
                print(f"🔍 系统健康: 线程{thread_count}, FD{fd_count}, CPU{cpu_percent:.1f}%")
            
            return status
            
        except Exception as e:
            print(f"系统健康检查错误: {e}")
            return {'healthy': True, 'warning': '', 'critical': False}



class ThreadSafeAudioManager:
    """线程安全的音频管理器"""
    
    def __init__(self):
        # 独立的PyAudio实例
        self.input_pyaudio = None
        self.output_pyaudio = None
        
        # 音频流
        self.input_stream = None
        self.output_stream = None
        
        # 线程控制
        self.recording_thread = None
        self.playback_thread = None
        
        # 线程同步
        self.recording_event = Event()
        self.playback_event = Event()
        self.stop_recording_event = Event()
        self.stop_playback_event = Event()
        
        # 数据队列（线程安全）
        self.audio_input_queue = queue.Queue()
        self.audio_output_queue = queue.Queue()
        
        # 线程锁
        self.input_lock = Lock()
        self.output_lock = Lock()
        
        # 状态标志
        self.is_recording = False
        self.is_playing = False
        
        print("🔧 线程安全音频管理器已初始化")
    
    def initialize_audio(self):
        """初始化音频系统"""
        try:
            # 创建独立的PyAudio实例
            self.input_pyaudio = pyaudio.PyAudio()
            self.output_pyaudio = pyaudio.PyAudio()
            
            print("✅ 独立音频实例创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 音频初始化失败: {e}")
            return False
    
    def start_recording(self):
        """启动录音线程"""
        if self.is_recording:
            return False
            
        try:
            self.is_recording = True
            self.stop_recording_event.clear()
            self.recording_event.set()
            
            # 清空输入队列
            while not self.audio_input_queue.empty():
                try:
                    self.audio_input_queue.get_nowait()
                except queue.Empty:
                    break
            
            # 启动录音线程
            self.recording_thread = threading.Thread(
                target=self._recording_worker,
                name="AudioRecordingThread",
                daemon=True
            )
            self.recording_thread.start()
            
            print("🎙️ 录音线程已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动录音失败: {e}")
            self.is_recording = False
            return False
    
    def stop_recording(self):
        """停止录音线程"""
        if not self.is_recording:
            return []
            
        try:
            self.is_recording = False
            self.stop_recording_event.set()
            self.recording_event.clear()
            
            # 等待录音线程结束
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2.0)
                if self.recording_thread.is_alive():
                    print("⚠️ 录音线程未能及时结束")
            
            # 收集录音数据
            audio_data = []
            while not self.audio_input_queue.empty():
                try:
                    data = self.audio_input_queue.get_nowait()
                    audio_data.append(data)
                except queue.Empty:
                    break
            
            print(f"🛑 录音已停止，收集到 {len(audio_data)} 块数据")
            return audio_data
            
        except Exception as e:
            print(f"❌ 停止录音失败: {e}")
            return []
    
    def start_playback(self):
        """启动播放线程"""
        if self.is_playing:
            return False
            
        try:
            self.is_playing = True
            self.stop_playback_event.clear()
            self.playback_event.set()
            
            # 启动播放线程
            self.playback_thread = threading.Thread(
                target=self._playback_worker,
                name="AudioPlaybackThread",
                daemon=True
            )
            self.playback_thread.start()
            
            print("🔊 播放线程已启动")
            return True
            
        except Exception as e:
            print(f"❌ 启动播放失败: {e}")
            self.is_playing = False
            return False
    
    def stop_playback(self):
        """立即强制停止播放线程（毫秒级响应）"""
        if not self.is_playing:
            return
            
        try:
            print("🚨 立即强制停止播放...")
            
            # 第一步：立即设置停止标志
            self.is_playing = False
            self.stop_playback_event.set()
            self.playback_event.clear()
            
            # 第二步：立即强制关闭输出流，阻止新的音频输出
            with self.output_lock:
                if self.output_stream:
                    try:
                        if self.output_stream.is_active():
                            self.output_stream.stop_stream()
                        self.output_stream.close()
                        self.output_stream = None
                        print("🔇 播放流已立即关闭")
                    except Exception as e:
                        print(f"⚠️ 关闭播放流时出错: {e}")
                        self.output_stream = None
            
            # 第三步：快速清空播放队列，丢弃未播放的音频
            cleared_count = 0
            while not self.audio_output_queue.empty():
                try:
                    self.audio_output_queue.get_nowait()
                    cleared_count += 1
                    if cleared_count > 100:  # 防止无限循环
                        break
                except queue.Empty:
                    break
            
            if cleared_count > 0:
                print(f"🗑️ 已丢弃 {cleared_count} 个未播放音频块")
            
            # 第四步：快速等待播放线程结束
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=0.5)  # 更短超时
                if self.playback_thread.is_alive():
                    print("⚠️ 播放线程未能在0.5秒内结束")
                else:
                    print("✅ 播放线程已正常结束")
            
            print("🔇 播放已立即完全停止")
            
        except Exception as e:
            print(f"❌ 停止播放失败: {e}")
    
    def add_audio_for_playback(self, audio_base64: str):
        """添加音频到播放队列"""
        if not self.is_playing:
            return False
            
        try:
            audio_data = base64.b64decode(audio_base64)
            if audio_data:
                self.audio_output_queue.put(audio_data, timeout=0.1)
                return True
        except Exception as e:
            print(f"⚠️ 添加播放音频失败: {e}")
        
        return False
    
    def _recording_worker(self):
        """录音工作线程（完全独立）"""
        try:
            with self.input_lock:
                # 创建录音流
                self.input_stream = self.input_pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    frames_per_buffer=512
                )
                print("✅ 录音流创建成功")
            
            chunk_count = 0
            error_count = 0
            
            while self.recording_event.is_set() and not self.stop_recording_event.is_set():
                try:
                    if not self.input_stream or not self.input_stream.is_active():
                        break
                    
                    # 读取音频数据
                    audio_data = self.input_stream.read(512, exception_on_overflow=False)
                    if audio_data:
                        self.audio_input_queue.put(audio_data, timeout=0.1)
                        chunk_count += 1
                        error_count = 0
                    
                    time.sleep(0.005)
                    
                except queue.Full:
                    print("⚠️ 录音队列已满，丢弃数据")
                    continue
                except Exception as e:
                    error_count += 1
                    if error_count <= 3:
                        print(f"⚠️ 录音错误 {error_count}: {e}")
                    if error_count > 10:
                        break
                    time.sleep(0.01)
            
            print(f"🔧 录音线程结束，共录制 {chunk_count} 块")
            
        except Exception as e:
            print(f"❌ 录音线程严重错误: {e}")
        finally:
            # 清理录音流
            with self.input_lock:
                if self.input_stream:
                    try:
                        if self.input_stream.is_active():
                            self.input_stream.stop_stream()
                        self.input_stream.close()
                        self.input_stream = None
                    except Exception:
                        pass
    
    def _playback_worker(self):
        """播放工作线程（完全独立，优化立即打断响应）"""
        try:
            with self.output_lock:
                # 创建播放流
                self.output_stream = self.output_pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    output=True,
                    frames_per_buffer=512
                )
                print("✅ 播放流创建成功")
            
            play_count = 0
            
            while self.playback_event.is_set() and not self.stop_playback_event.is_set():
                try:
                    # 从队列获取音频数据
                    audio_data = self.audio_output_queue.get(timeout=0.1)
                    
                    # 立即检查是否需要停止
                    if not self.playback_event.is_set() or self.stop_playback_event.is_set():
                        print("🔇 收到停止信号，立即停止播放")
                        break
                    
                    # 极速分块播放，毫秒级响应停止信号
                    chunk_size = 64  # 极小块，毫秒级响应
                    chunk_count = 0
                    for i in range(0, len(audio_data), chunk_size):
                        # 每个chunk都检查停止信号，无延迟响应
                        if self.stop_playback_event.is_set():
                            print("🔇 播放中收到停止信号，立即停止")
                            break
                        
                        chunk = audio_data[i:i+chunk_size]
                        with self.output_lock:
                            if self.output_stream and self.output_stream.is_active():
                                try:
                                    self.output_stream.write(chunk, exception_on_underflow=False)
                                except Exception as write_err:
                                    # 如果写入失败，可能是被打断了，立即退出
                                    if self.stop_playback_event.is_set():
                                        print("🔇 写入失败，立即停止播放")
                                        break
                                    raise write_err
                            
                            # 写入完成后再次检查停止信号
                            if self.stop_playback_event.is_set():
                                print("🔇 写入完成后立即停止")
                                break
                        
                        chunk_count += 1
                    
                    play_count += 1
                    
                except queue.Empty:
                    # 队列空时也检查停止信号
                    if self.stop_playback_event.is_set():
                        print("🔇 队列空时收到停止信号")
                        break
                    continue
                except Exception as e:
                    if self.playback_event.is_set() and not self.stop_playback_event.is_set():
                        print(f"⚠️ 播放错误: {e}")
                    break
            
            print(f"🔧 播放线程结束，共播放 {play_count} 块")
            
        except Exception as e:
            print(f"❌ 播放线程严重错误: {e}")
        finally:
            # 清理播放流
            with self.output_lock:
                if self.output_stream:
                    try:
                        if self.output_stream.is_active():
                            self.output_stream.stop_stream()
                        self.output_stream.close()
                        self.output_stream = None
                        print("🔇 播放流已完全关闭")
                    except Exception:
                        pass
    
    def emergency_cleanup(self):
        """紧急清理所有音频资源"""
        print("🚨 执行音频紧急清理...")
        
        # 停止所有操作
        self.stop_recording()
        self.stop_playback()
        
        # 清理所有队列
        while not self.audio_input_queue.empty():
            try:
                self.audio_input_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.audio_output_queue.empty():
            try:
                self.audio_output_queue.get_nowait()
            except queue.Empty:
                break
        
        # 关闭PyAudio实例
        if self.input_pyaudio:
            try:
                self.input_pyaudio.terminate()
                self.input_pyaudio = None
            except Exception:
                pass
        
        if self.output_pyaudio:
            try:
                self.output_pyaudio.terminate()
                self.output_pyaudio = None
            except Exception:
                pass
        
        # 强制垃圾回收
        gc.collect()
        print("✅ 音频紧急清理完成")

class SimpleManualVoiceController:
    """简化版手动语音控制器 - 基于千问Omni实时API（终端控制）"""
    
    def __init__(self):
        # API配置
        self.api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
        self.api_url = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen-omni-turbo-realtime"
        
        # 连接状态
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.session_id: Optional[str] = None
        self.is_connected = False
        
        # 控制状态
        self.is_recording = False
        self.is_ai_speaking = False
        self.should_exit = False
        
        # 音频处理
        self.pyaudio_instance = None
        self.input_stream = None
        self.output_stream = None
        self.recorded_audio = []
        
        # 线程控制
        self.recording_thread = None
        self.response_task = None
        self.input_task = None
        
        # 状态追踪
        self.current_response = ""
        self.user_transcript = ""
        
        # 缓冲区管理
        self.max_buffer_size = 100  # 最大录音缓冲区块数
        self.audio_chunk_count = 0  # 当前音频块计数
        self.output_buffer_size = 0  # 输出缓冲区大小
        self.max_output_buffer = 50  # 最大输出缓冲区块数
        
        # 线程安全
        import threading
        self._audio_lock = threading.Lock()  # 音频操作锁
        self._buffer_lock = threading.Lock()  # 缓冲区操作锁
        
        # 添加监控相关变量
        self._memory_monitor = MemoryMonitor()
        self._health_checker = SystemHealthChecker()
        self._critical_threshold_reached = False
        
        # 启用内存跟踪
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        
        # 初始化对话缓存管理器
        if HAS_CACHE_MANAGER:
            self.conversation_cache = ConversationCacheManager()
        else:
            self.conversation_cache = None
            print("⚠️ 对话上下文功能不可用")
            
        print("手动语音控制系统已初始化，包含内存监控和对话缓存功能")
        
        # 初始化线程安全的音频管理器
        self.audio_manager = ThreadSafeAudioManager()
        
    async def connect(self) -> Dict[str, Any]:
        """连接到千问Omni实时API"""
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "未找到API密钥，请设置DASHSCOPE_API_KEY环境变量"
                }
            
            print("🔗 正在连接千问Omni实时API...")
            
            headers = [
                ("Authorization", f"Bearer {self.api_key}"),
                ("User-Agent", "FractFlow-SimpleManualVoiceControl/1.0")
            ]
            
            # 建立WebSocket连接
            self.websocket = await websockets.connect(
                self.api_url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=20
            )
            
            # 等待会话建立
            message = await asyncio.wait_for(self.websocket.recv(), timeout=10.0)
            session_data = json.loads(message)
            
            if session_data.get("type") == "session.created":
                self.session_id = session_data["session"]["id"]
                self.is_connected = True
                
                # 配置会话为非VAD模式（手动控制）
                await self._configure_session()
                
                print(f"✅ 连接成功！会话ID: {self.session_id}")
                return {
                    "success": True,
                    "session_id": self.session_id,
                    "message": "已连接到千问Omni实时API"
                }
            else:
                return {
                    "success": False,
                    "error": f"会话建立失败: {session_data}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"连接失败: {str(e)}"
            }
    
    async def _configure_session(self):
        """配置会话为手动控制模式"""
        session_config = {
            "type": "session.update",
            "session": {
                "turn_detection": None,  # 关闭服务器VAD，使用手动控制
                "voice": "Chelsie",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "temperature": 0.8,
                "max_response_output_tokens": "inf",
                "input_audio_transcription": {
                    "model": "gummy-realtime-v1"
                }
            }
        }
        await self.websocket.send(json.dumps(session_config))
        print("⚙️ 会话已配置为手动控制模式（非VAD）")
    
    def setup_audio(self) -> Dict[str, Any]:
        """初始化音频系统"""
        try:
            # 使用线程安全的音频管理器
            if not self.audio_manager.initialize_audio():
                return {"success": False, "error": "音频管理器初始化失败"}
            
            print("🔊 线程安全音频系统初始化完成")
            return {
                "success": True,
                "message": "线程安全音频系统已初始化"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"音频初始化失败: {str(e)}"
            }
    
    async def _wait_for_enter(self):
        """等待用户按回车键（异步方式）"""
        loop = asyncio.get_event_loop()
        
        def check_input():
            try:
                return sys.stdin.readline().strip()
            except:
                return ""
        
        # 使用线程池来处理阻塞的input
        return await loop.run_in_executor(None, check_input)
    
    def _handle_enter_action(self):
        """处理回车键动作"""
        try:
            if self.is_ai_speaking:
                # AI正在说话 → 打断并立即开始录音
                print("⚡ [打断AI并开始录音]")
                asyncio.create_task(self._interrupt_ai_and_start_recording())
                
            elif self.is_recording:
                # 正在录音 → 停止录音并发送
                print("🛑 [停止录音，正在发送...]")
                self._stop_recording()
                
            else:
                # 空闲状态 → 开始录音
                print("🎤 [开始录音，请说话...]")
                self._start_recording()
                
        except Exception as e:
            print(f"❌ 处理回车键失败: {e}")
    
    def _reset_audio_state(self):
        """重置音频状态"""
        try:
            if self.output_stream:
                if self.output_stream.is_active():
                    self.output_stream.stop_stream()
                self.output_stream.close()
                self.output_stream = None
                # 短暂等待确保资源释放
                time.sleep(0.05)
        except Exception as e:
            print(f"⚠️ 重置音频状态时出错: {e}")
            self.output_stream = None
    
    def _reset_response_flags(self):
        """重置响应标志"""
        if hasattr(self, '_response_started'):
            delattr(self, '_response_started')
        if hasattr(self, '_audio_started'):
            delattr(self, '_audio_started')
    
    def _check_and_clear_buffer(self):
        """检查并清理缓冲区，避免内存溢出，包含内存预警"""
        with self._buffer_lock:
            # 检查内存使用情况
            memory_warning = self._memory_monitor.check_memory_status()
            if memory_warning['critical']:
                print(f"⚠️ 内存使用临界警告: {memory_warning['message']}")
                self._emergency_cleanup()
                return
            
            # 检查录音缓冲区
            if len(self.recorded_audio) > self.max_buffer_size:
                print(f"⚠️ 录音缓冲区已满({len(self.recorded_audio)}块)，自动清理...")
                # 保留最后的50%数据，清除前面的
                keep_size = self.max_buffer_size // 2
                self.recorded_audio = self.recorded_audio[-keep_size:]
                print(f"✅ 缓冲区已清理，保留{len(self.recorded_audio)}块数据")
                
                # 强制垃圾回收
                import gc
                gc.collect()
    
    def _emergency_cleanup(self):
        """紧急清理所有缓存和资源"""
        print("🚨 执行紧急内存清理...")
        
        # 清空所有缓冲区
        with self._buffer_lock:
            if hasattr(self, 'recorded_audio'):
                self.recorded_audio.clear()
        
        # 删除临时录音文件
        if hasattr(self, 'temp_audio_file') and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
                print("✅ 临时录音文件已删除")
            except Exception as e:
                print(f"删除临时文件失败: {e}")
        
        # 重置音频流
        if hasattr(self, 'input_stream') and self.input_stream:
            try:
                if self.input_stream.is_active():
                    self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
                print("✅ 录音流已重置")
            except Exception as e:
                print(f"重置录音流失败: {e}")
        
        if hasattr(self, 'output_stream') and self.output_stream:
            try:
                if self.output_stream.is_active():
                    self.output_stream.stop_stream()  
                self.output_stream.close()
                self.output_stream = None
                print("✅ 输出流已重置")
            except Exception as e:
                print(f"重置输出流失败: {e}")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        # 设置临界状态标志
        self._critical_threshold_reached = True
        
        print("🚨 紧急清理完成，建议重启程序")
    
    async def _clear_api_buffer_if_needed(self):
        """检查并清空API缓冲区，包含系统健康检查"""
        try:
            # 检查系统健康状态
            health_status = self._health_checker.check_system_health()
            if not health_status['healthy']:
                print(f"⚠️ 系统健康警告: {health_status['warning']}")
                if health_status['critical']:
                    self._emergency_cleanup()
                    return
            
            # 当输出缓冲区过大时清空
            if self.output_buffer_size > self.max_output_buffer:
                print(f"⚠️ API输出缓冲区过大({self.output_buffer_size})，正在清空...")
                clear_msg = {"type": "input_audio_buffer.clear"}
                await self.websocket.send(json.dumps(clear_msg))
                self.output_buffer_size = 0
                print("✅ API缓冲区已清空")
        except Exception as e:
            print(f"⚠️ 清空API缓冲区时出错: {e}")
    
    def _clear_previous_recording_data(self):
        """清理上一次的录音数据，释放内存"""
        try:
            if self.recorded_audio:
                previous_size = len(self.recorded_audio)
                # 完全清空录音数据
                self.recorded_audio.clear()
                # 重置计数器
                self.audio_chunk_count = 0
                print(f"🧹 已清理{previous_size}块录音数据，释放内存")
                
                # 强制垃圾回收
                import gc
                gc.collect()
                print("♻️ 内存垃圾回收完成")
                
        except Exception as e:
            print(f"⚠️ 清理录音数据时出错: {e}")
    
    def _start_recording(self):
        """开始录音（使用线程安全音频管理器）"""
        if self.is_recording:
            return
        
        try:
            # 在录音前进行内存检查
            memory_status = self._memory_monitor.check_memory_status()
            if memory_status['critical']:
                print(f"🚨 录音前内存临界警告: {memory_status['message']}")
                self._emergency_cleanup()
                return
            elif memory_status['warning']:
                print(f"⚠️ 录音前内存警告: {memory_status['message']}")
            
            # 使用线程安全的音频管理器开始录音
            if self.audio_manager.start_recording():
                self.is_recording = True
                # 清空之前的录音数据
                if hasattr(self, 'recorded_audio'):
                    self.recorded_audio.clear()
                else:
                    self.recorded_audio = []
                
                print("📻 录音已开始... (按回车键停止)")
            else:
                print("❌ 录音启动失败")
                
        except Exception as e:
            print(f"❌ 录音启动失败: {e}")
            self.is_recording = False
    

    
    def _stop_recording(self):
        """停止录音并发送（使用线程安全音频管理器）"""
        if not self.is_recording:
            return
        
        try:
            # 使用线程安全的音频管理器停止录音
            audio_data = self.audio_manager.stop_recording()
            self.is_recording = False
            
            # 将音频数据存储到recorded_audio中
            if audio_data:
                self.recorded_audio = audio_data
                print(f"📼 录音完成，收集到 {len(audio_data)} 块数据")
            else:
                print("⚠️ 未收集到录音数据")
                return
            
            # 发送录音数据
            if self.recorded_audio and self.is_connected:
                asyncio.create_task(self._send_audio_data())
            
        except Exception as e:
            print(f"❌ 停止录音失败: {e}")
            self.is_recording = False
    
    async def _send_audio_data(self):
        """发送音频数据到API"""
        try:
            print("📤 正在发送音频数据...")
            
            # 检查并清空API缓冲区（如果需要）
            await self._clear_api_buffer_if_needed()
            
            # 如果有对话缓存，先发送上下文
            if self.conversation_cache and len(self.conversation_cache.conversation_history) > 0:
                context = self.conversation_cache.get_context_for_ai()
                if context:
                    # 发送上下文作为系统消息
                    context_msg = {
                        "type": "conversation.item.create",
                        "item": {
                            "type": "message",
                            "role": "system",
                            "content": [{"type": "text", "text": context}]
                        }
                    }
                    await self.websocket.send(json.dumps(context_msg))
                    print("🧠 已发送对话上下文")
            
            # 合并音频数据
            combined_audio = b''.join(self.recorded_audio)
            
            # 分块发送音频
            chunk_size = 1024
            chunk_count = 0
            for i in range(0, len(combined_audio), chunk_size):
                chunk = combined_audio[i:i+chunk_size]
                audio_base64 = base64.b64encode(chunk).decode('utf-8')
                
                event = {
                    "type": "input_audio_buffer.append",
                    "audio": audio_base64
                }
                
                await self.websocket.send(json.dumps(event))
                chunk_count += 1
                self.output_buffer_size += 1
                
                # 每发送20个块检查一次缓冲区
                if chunk_count % 20 == 0:
                    await self._clear_api_buffer_if_needed()
                
                await asyncio.sleep(0.01)
            
            # 提交音频缓冲区
            await self.websocket.send(json.dumps({"type": "input_audio_buffer.commit"}))
            
            # 请求AI响应
            await self.websocket.send(json.dumps({"type": "response.create"}))
            
            print("✅ 音频发送完成，等待AI回答...")
            
            # 重置状态并启动响应监听
            self.is_ai_speaking = True  # 标记AI即将开始说话
            self.current_response = ""  # 清空之前的响应
            self._reset_response_flags()  # 重置响应标志
            
            # 发送完成后，立即清理录音数据缓存
            print("🧹 音频已发送，正在清理发送缓存...")
            if hasattr(self, 'recorded_audio'):
                self.recorded_audio.clear()
            import gc
            gc.collect()
            
            if self.response_task:
                self.response_task.cancel()
            self.response_task = asyncio.create_task(self._listen_responses())
            
        except Exception as e:
            print(f"❌ 发送音频失败: {e}")
    
    async def _listen_responses(self):
        """监听AI响应"""
        self.current_response = ""
        
        try:
            while not self.should_exit and self.is_connected:
                try:
                    message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                    data = json.loads(message)
                    response_type = data.get("type", "")
                    
                    await self._handle_response_event(response_type, data)
                    
                    # 如果收到response.done或response.cancelled，退出监听循环
                    if response_type in ["response.done", "response.cancelled"]:
                        break
                    
                except asyncio.CancelledError:
                    # 被打断，正常退出
                    print(" [响应监听已取消]")
                    break
                except asyncio.TimeoutError:
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 WebSocket连接已关闭")
                    break
                except Exception as e:
                    print(f"❌ 响应处理错误: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ 监听响应失败: {e}")
    
    async def _handle_response_event(self, response_type: str, data: Dict[str, Any]):
        """处理响应事件"""
        if response_type == "conversation.item.input_audio_transcription.completed":
            # 用户语音识别完成 - 优化字幕显示
            transcript = data.get("transcript", "")
            if transcript.strip():
                self.user_transcript = transcript
                print(f"\n👤 您说: \033[94m{transcript}\033[0m")
        
        elif response_type == "response.audio_transcript.delta":
            # AI文本回答增量 - 优化字幕显示
            transcript = data.get("delta", "")
            if transcript.strip() and self.is_ai_speaking:  # 只有在AI仍在说话时才处理
                self.current_response += transcript
                if not hasattr(self, '_response_started'):
                    self._response_started = True
                    print("🤖 AI回答: ", end="", flush=True)
                # 实时字幕显示，带颜色和格式化
                print(f"\033[92m{transcript}\033[0m", end="", flush=True)
        
        elif response_type == "response.audio_transcript.done":
            # AI文本回答完成
            if self.current_response.strip():
                print()  # 换行
        
        elif response_type == "response.audio.delta":
            # AI音频回答增量 - 简化直接播放模式
            audio_base64 = data.get("delta", "")
            if audio_base64 and self.is_ai_speaking:  # 只有在AI仍在说话时才播放
                if not hasattr(self, '_audio_started'):
                    self._audio_started = True
                    print("🤖 AI正在回答...")
                # 直接播放音频，不使用复杂的线程队列
                self._play_audio_direct(audio_base64)
        
        elif response_type == "response.done":
            # AI回答完成
            self.is_ai_speaking = False
            self._reset_response_flags()
            
            # 保存这轮对话到缓存
            if self.conversation_cache and hasattr(self, 'user_transcript') and self.current_response.strip():
                try:
                    self.conversation_cache.add_conversation_turn(
                        user_text=self.user_transcript,
                        ai_text=self.current_response.strip()
                    )
                    print("💾 对话已保存到缓存")
                except Exception as e:
                    print(f"⚠️ 保存对话缓存失败: {e}")
            
            # 清理上一次的录音数据，释放内存
            self._clear_previous_recording_data()
            
            if self.current_response.strip():
                print("\n✅ [AI回答完成，录音数据已清理，按回车键开始新对话]")
            else:
                print("✅ [准备开始新对话，录音数据已清理]")
        
        elif response_type == "response.cancelled":
            # AI被打断
            self.is_ai_speaking = False
            self._reset_response_flags()
            
            # 清理录音数据
            self._clear_previous_recording_data()
            
            # 如果有内容被打断，不显示，直接清除
            if self.current_response.strip():
                print("\n⚡ [已成功打断并清除内容，录音数据已清理]")
            else:
                print("⚡ [已打断，录音数据已清理]")
            self.current_response = ""  # 确保清除被打断的内容
        
        elif response_type == "error":
            error_msg = data.get("error", {}).get("message", "未知错误")
            # 忽略因打断导致的常见错误
            if "none active response" in error_msg.lower():
                print(f"\n⚠️ [打断成功，已清除响应状态]")
            else:
                print(f"\n❌ API错误: {error_msg}")
    

    async def _interrupt_ai(self):
        """打断AI（简化版，不立即开始录音）"""
        if self.is_ai_speaking and self.is_connected:
            try:
                # 立即设置状态 - 这会让新的音频数据不再播放
                self.is_ai_speaking = False
                
                # 立即停止简单音频播放流
                self._stop_simple_audio()
                
                # 发送取消信号到API
                cancel_msg = {"type": "response.cancel"}
                await self.websocket.send(json.dumps(cancel_msg))
                
                # 清除当前响应缓存
                self.current_response = ""
                self._reset_response_flags()
                
                print("🔇 [AI已被打断]")
                
            except Exception as e:
                print(f"❌ 打断失败: {e}")
    
    def _play_audio_direct(self, audio_base64):
        """直接播放音频（简化版，立即响应打断）"""
        try:
            # 再次检查是否还在说话，实现立即打断
            if not self.is_ai_speaking:
                return
            
            audio_data = base64.b64decode(audio_base64)
            
            # 懒加载输出流
            if not hasattr(self, 'simple_output_stream') or not self.simple_output_stream:
                # 使用线程安全音频管理器的PyAudio实例，但直接控制流
                self.simple_output_stream = self.audio_manager.output_pyaudio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    output=True,
                    frames_per_buffer=512
                )
            
            # 再次检查状态，确保可以立即停止
            if audio_data and self.is_ai_speaking:
                self.simple_output_stream.write(audio_data, exception_on_underflow=False)
                
        except Exception as e:
            if self.is_ai_speaking:  # 只有在应该播放时才报错
                print(f"⚠️ 音频播放错误: {e}")
    
    def _stop_simple_audio(self):
        """停止简单音频播放"""
        try:
            if hasattr(self, 'simple_output_stream') and self.simple_output_stream:
                self.simple_output_stream.stop_stream()
                self.simple_output_stream.close()
                self.simple_output_stream = None
                print("🔇 简单音频播放已停止")
        except Exception as e:
            print(f"⚠️ 停止简单音频时出错: {e}")
    
    async def _interrupt_ai_and_start_recording(self):
        """打断AI并立即开始录音（回到简单有效的实现）"""
        if self.is_ai_speaking and self.is_connected:
            try:
                print("⚡ [立即打断AI]")
                
                # 第一步：立即设置状态 - 这会让新的音频数据不再播放
                self.is_ai_speaking = False
                
                # 第二步：立即停止简单音频播放流
                self._stop_simple_audio()
                
                # 第三步：发送取消信号到API
                cancel_msg = {"type": "response.cancel"}
                await self.websocket.send(json.dumps(cancel_msg))
                
                # 第四步：清除当前响应缓存
                self.current_response = ""
                self._reset_response_flags()
                
                print("🔇 [AI已立即停止，开始录音]")
                
                # 立即开始录音
                self._start_recording()
                
            except Exception as e:
                print(f"❌ 打断并录音失败: {e}")
        else:
            # 如果AI不在说话，直接开始录音
            print("🎤 [开始录音，请说话...]")
            self._start_recording()
    
    def _cleanup(self):
        """清理所有资源（线程安全版本）"""
        print("正在清理资源...")
        
        # 内存监控最终报告
        if hasattr(self, '_memory_monitor'):
            final_status = self._memory_monitor.check_memory_status()
            print(f"📊 最终内存状态: {final_status['current_mb']:.1f}MB (峰值: {final_status['peak_mb']:.1f}MB)")
        
        self.is_recording = False
        self.is_ai_speaking = False
        
        # 清理简单音频流
        self._stop_simple_audio()
        
        # 使用线程安全的音频管理器进行紧急清理
        if hasattr(self, 'audio_manager'):
            self.audio_manager.emergency_cleanup()
        
        # 清理录音数据
        if hasattr(self, 'recorded_audio') and self.recorded_audio:
            print(f"🧹 清理 {len(self.recorded_audio)} 块录音数据...")
            self.recorded_audio.clear()
        
        # 取消任务
        if hasattr(self, 'response_task') and self.response_task:
            self.response_task.cancel()
        if hasattr(self, 'input_task') and self.input_task:
            self.input_task.cancel()
        
        # 关闭对话缓存管理器
        if hasattr(self, 'conversation_cache') and self.conversation_cache:
            try:
                self.conversation_cache.close()
            except Exception as e:
                print(f"⚠️ 关闭对话缓存失败: {e}")
        
        # 强制垃圾回收
        import gc
        gc.collect()
        print("♻️ 线程安全资源清理和内存回收完成")
    
    async def disconnect(self):
        """断开连接"""
        self._cleanup()
        
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception:
                pass
        
        self.is_connected = False
        self.websocket = None
        self.session_id = None
        
        print("🔌 已断开连接")
    
    async def _input_handler(self):
        """处理用户输入的协程"""
        while not self.should_exit:
            try:
                # 等待用户按回车
                user_input = await self._wait_for_enter()
                
                if user_input.lower() in ['q', 'quit', 'exit']:
                    print("🚪 正在退出...")
                    self.should_exit = True
                    break
                else:
                    # 处理回车键动作
                    self._handle_enter_action()
                
            except Exception as e:
                print(f"❌ 输入处理错误: {e}")
                break
    
    async def run_interactive_mode(self) -> Dict[str, Any]:
        """运行交互模式"""
        try:
            # 初始化连接
            connect_result = await self.connect()
            if not connect_result["success"]:
                return connect_result
            
            # 初始化音频
            audio_result = self.setup_audio()
            if not audio_result["success"]:
                return audio_result
            
            print("\n🎮 简化版手动语音控制已启动！")
            print("💡 按回车键开始第一次录音...")
            print("📋 操作说明：")
            print("   1. 按回车键开始录音")
            print("   2. 说完话后再按回车键停止录音并发送")
            print("   3. AI回答时按回车键打断并0.3秒后开始录音 ⚡")
            print("   4. 输入 'q' 或 'quit' 退出")
            print("🌟 智能缓冲区管理：自动监控和清理，避免内存溢出！")
            print(f"🔧 缓冲区配置：录音最大{self.max_buffer_size}块，输出最大{self.max_output_buffer}块")
            print()
            
            # 启动输入处理
            self.input_task = asyncio.create_task(self._input_handler())
            
            # 主循环
            try:
                while not self.should_exit:
                    await asyncio.sleep(0.1)
                    
            except KeyboardInterrupt:
                print("\n🛑 用户按Ctrl+C退出")
            
            return {
                "success": True,
                "message": "交互模式已结束"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"运行失败: {str(e)}"
            }
        finally:
            await self.disconnect()

# MCP工具函数
async def start_simple_manual_voice_control() -> str:
    """
    启动简化版手动语音控制助手
    
    基于千问Omni实时语音API，使用终端回车键控制（无需管理员权限）。
    
    Returns:
        str: 执行结果描述
    """
    try:
        controller = SimpleManualVoiceController()
        result = await controller.run_interactive_mode()
        
        if result["success"]:
            return f"✅ 简化版手动语音控制助手已启动并运行完成。{result.get('message', '')}"
        else:
            return f"❌ 启动失败: {result['error']}"
            
    except Exception as e:
        return f"❌ 启动简化版手动语音控制助手失败: {str(e)}"

# 直接运行模式
async def main():
    """直接运行简化版手动语音控制助手"""
    print("🎤 FractFlow 简化版手动语音控制助手")
    print("=" * 60)
    print("🎯 基于千问Omni实时语音API + 终端回车控制")
    print("⚡ 特色：无需管理员权限，终端输入控制")
    print("=" * 60)
    
    result = await start_simple_manual_voice_control()
    print(f"\n📊 执行结果: {result}")

if __name__ == "__main__":
    asyncio.run(main()) 