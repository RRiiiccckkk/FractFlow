"""
千问Omni实时语音MCP工具 v2.1
支持实时语音打断功能
"""

import asyncio
import json
import os
import uuid
import base64
import threading
import queue
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import websockets
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False
    print("Warning: pyaudio not installed. Install with: uv add pyaudio")

load_dotenv()
mcp = FastMCP("qwen_realtime_voice")

# 配置
API_KEY = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
API_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen-omni-turbo-realtime"

# 音频参数
SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16 if HAS_PYAUDIO else None

class QwenRealtimeVoiceClient:
    """千问Omni实时语音客户端 - 支持实时打断功能"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or API_KEY
        self.websocket = None
        self.session_id = None
        self.is_connected = False
        self.is_recording = False
        
        # 音频相关
        if HAS_PYAUDIO:
            self.pyaudio_instance = None
            self.input_stream = None
            self.output_stream = None
        
        # 队列和状态
        self.audio_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.conversation_history = []
        
        # 线程控制
        self.recording_thread = None
        self.processing_thread = None
        self.stop_event = threading.Event()
        
        # 实时打断功能相关状态
        self.is_ai_speaking = False
        self.interrupt_detected = False
        self.audio_playback_thread = None
        self.audio_buffer = queue.Queue()
        self.stop_playback_event = threading.Event()
        
    async def connect(self) -> Dict[str, Any]:
        """连接到千问Omni API"""
        try:
            print("🔗 正在连接千问Omni实时API...")
            
            headers = [
                ("Authorization", f"Bearer {self.api_key}"),
                ("User-Agent", "FractFlow-QwenOmni/2.1")
            ]
            
            # 建立WebSocket连接
            self.websocket = await websockets.connect(
                API_URL,
                additional_headers=headers,
                ping_interval=30,
                ping_timeout=10
            )
            
            # 等待会话建立
            message = await asyncio.wait_for(self.websocket.recv(), timeout=5.0)
            session_data = json.loads(message)
            
            if session_data.get("type") == "session.created":
                self.session_id = session_data["session"]["id"]
                self.is_connected = True
                
                # 配置会话
                await self._configure_session()
                
                print(f"✅ 连接成功！会话ID: {self.session_id}")
                return {"success": True, "session_id": self.session_id}
            else:
                return {"success": False, "error": "Unexpected session response"}
                
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _configure_session(self):
        """配置会话参数 - 优化打断功能"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": "你是一个友好的AI助手，请用中文自然地回答问题。保持回复简洁明了。支持被用户随时打断。",
                "voice": "Chelsie",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.2,  # 降低阈值，更敏感地检测打断
                    "prefix_padding_ms": 200,  # 减少前缀延迟
                    "silence_duration_ms": 600  # 减少静音判断时间
                },
                "temperature": 0.7,
                "max_response_output_tokens": 2048
            }
        }
        
        await self.websocket.send(json.dumps(config))
        print("⚙️ 会话配置完成（已启用实时打断功能）")
    
    def init_audio(self) -> Dict[str, Any]:
        """初始化音频系统"""
        if not HAS_PYAUDIO:
            return {"success": False, "error": "PyAudio not available"}
        
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # 检查音频设备
            device_count = self.pyaudio_instance.get_device_count()
            print(f"🎵 发现 {device_count} 个音频设备")
            
            # 查找默认输入设备
            default_input = self.pyaudio_instance.get_default_input_device_info()
            print(f"🎤 默认输入设备: {default_input['name']}")
            
            return {"success": True, "message": "音频系统初始化成功"}
            
        except Exception as e:
            return {"success": False, "error": f"音频初始化失败: {e}"}
    
    def start_recording(self) -> Dict[str, Any]:
        """开始录音"""
        if not HAS_PYAUDIO or not self.pyaudio_instance:
            audio_result = self.init_audio()
            if not audio_result["success"]:
                return audio_result
        
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
            self.stop_playback_event.clear()
            
            # 启动录音线程
            self.recording_thread = threading.Thread(target=self._recording_worker)
            self.recording_thread.start()
            
            # 启动处理线程
            self.processing_thread = threading.Thread(target=self._processing_worker)
            self.processing_thread.start()
            
            # 启动音频播放线程
            self.audio_playback_thread = threading.Thread(target=self._audio_playback_worker)
            self.audio_playback_thread.start()
            
            print("🎤 录音已开始（支持实时打断）")
            return {"success": True, "message": "录音开始"}
            
        except Exception as e:
            return {"success": False, "error": f"录音启动失败: {e}"}
    
    def _recording_worker(self):
        """录音工作线程"""
        print("🎵 录音线程启动")
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                # 读取音频数据
                audio_data = self.input_stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                # 放入队列
                if not self.audio_queue.full():
                    self.audio_queue.put(audio_data)
                
                time.sleep(0.01)  # 小延迟避免CPU占用过高
                
            except Exception as e:
                if self.is_recording:
                    print(f"❌ 录音错误: {e}")
                break
                
        print("🛑 录音线程结束")
    
    def _processing_worker(self):
        """音频处理工作线程"""
        print("🔄 处理线程启动")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_processing())
        except Exception as e:
            print(f"❌ 处理线程错误: {e}")
        finally:
            loop.close()
            print("🛑 处理线程结束")
    
    async def _async_processing(self):
        """异步音频处理"""
        audio_chunks_sent = 0
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                # 发送音频数据
                if not self.audio_queue.empty():
                    audio_data = self.audio_queue.get_nowait()
                    await self._send_audio_chunk(audio_data)
                    audio_chunks_sent += 1
                    
                    if audio_chunks_sent % 100 == 0:
                        print(f"📤 已发送 {audio_chunks_sent} 个音频块")
                
                # 处理服务器响应
                await self._handle_responses()
                
                # 小延迟
                await asyncio.sleep(0.05)
                
            except Exception as e:
                if "websocket" not in str(e).lower():
                    print(f"❌ 处理错误: {e}")
                await asyncio.sleep(0.1)
    
    async def _send_audio_chunk(self, audio_data: bytes):
        """发送音频块到服务器"""
        try:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            event = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            
            await self.websocket.send(json.dumps(event))
            
        except Exception as e:
            print(f"❌ 发送音频失败: {e}")
            if "1011" in str(e):
                print("🔄 检测到服务器错误，可能需要重连")
    
    async def _handle_responses(self):
        """处理服务器响应 - 增强打断检测"""
        try:
            # 非阻塞检查是否有新消息
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.01)
            response_data = json.loads(message)
            
            response_type = response_data.get("type", "")
            
            # 处理不同类型的响应
            if response_type == "input_audio_buffer.speech_started":
                print("🎤 [用户开始说话]")
                # 检测到用户开始说话，执行打断逻辑
                if self.is_ai_speaking:
                    await self._interrupt_ai_response()
                
            elif response_type == "input_audio_buffer.speech_stopped":
                print("🔇 [用户停止说话]")
                self.interrupt_detected = False
                
            elif response_type == "response.audio_transcript.delta":
                transcript = response_data.get("delta", "")
                if transcript.strip():
                    print(f"💬 AI: {transcript}", end="", flush=True)
                    
            elif response_type == "response.audio_transcript.done":
                print()  # 换行
                
            elif response_type == "response.audio.delta":
                # 将音频数据加入播放缓冲区
                audio_base64 = response_data.get("delta", "")
                if audio_base64 and not self.interrupt_detected:
                    self.audio_buffer.put(audio_base64)
                    self.is_ai_speaking = True
                    
            elif response_type == "response.done":
                print("✅ [AI响应完成]")
                self.is_ai_speaking = False
                
            elif response_type == "conversation.item.created":
                print("📝 [对话项创建]")
                
        except asyncio.TimeoutError:
            # 正常情况，没有新消息
            pass
        except Exception as e:
            if "websocket" not in str(e).lower():
                print(f"❌ 响应处理错误: {e}")
    
    async def _interrupt_ai_response(self):
        """执行AI响应打断"""
        print("⚡ [检测到打断，停止AI语音播放]")
        self.interrupt_detected = True
        self.is_ai_speaking = False
        
        # 清空音频播放缓冲区
        while not self.audio_buffer.empty():
            try:
                self.audio_buffer.get_nowait()
            except queue.Empty:
                break
        
        # 通知服务器取消当前响应
        try:
            cancel_event = {
                "type": "response.cancel"
            }
            await self.websocket.send(json.dumps(cancel_event))
            print("📤 [已发送取消信号给服务器]")
        except Exception as e:
            print(f"❌ 发送取消信号失败: {e}")
    
    def _audio_playback_worker(self):
        """音频播放工作线程"""
        print("🔊 音频播放线程启动")
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                if not self.audio_buffer.empty() and not self.interrupt_detected:
                    audio_base64 = self.audio_buffer.get(timeout=0.1)
                    self._play_audio_sync(audio_base64)
                else:
                    time.sleep(0.01)
                    
            except queue.Empty:
                time.sleep(0.01)
            except Exception as e:
                if self.is_recording:
                    print(f"❌ 音频播放错误: {e}")
                    
        print("🛑 音频播放线程结束")
    
    def _play_audio_sync(self, audio_base64: str):
        """同步播放音频（支持打断）"""
        try:
            if not HAS_PYAUDIO or self.interrupt_detected:
                return
                
            audio_data = base64.b64decode(audio_base64)
            
            # 创建输出流（如果还没有）
            if not self.output_stream:
                self.output_stream = self.pyaudio_instance.open(
                    format=FORMAT,
                    channels=CHANNELS,
                    rate=SAMPLE_RATE,
                    output=True
                )
            
            # 检查是否被打断
            if not self.interrupt_detected:
                self.output_stream.write(audio_data)
            
        except Exception as e:
            print(f"❌ 音频播放错误: {e}")
    
    def stop_recording(self) -> Dict[str, Any]:
        """停止录音"""
        try:
            print("🛑 正在停止录音...")
            
            self.is_recording = False
            self.stop_event.set()
            self.stop_playback_event.set()
            
            # 等待线程结束
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=2)
                
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=2)
                
            if self.audio_playback_thread and self.audio_playback_thread.is_alive():
                self.audio_playback_thread.join(timeout=2)
            
            # 关闭音频流
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
                
            if self.output_stream:
                self.output_stream.stop_stream()
                self.output_stream.close()
                self.output_stream = None
            
            return {"success": True, "message": "录音已停止"}
            
        except Exception as e:
            return {"success": False, "error": f"停止录音失败: {e}"}
    
    async def disconnect(self) -> Dict[str, Any]:
        """断开连接"""
        try:
            print("🔌 正在断开连接...")
            
            # 停止录音
            self.stop_recording()
            
            # 关闭WebSocket
            if self.websocket and self.is_connected:
                await self.websocket.close()
                
            self.is_connected = False
            
            # 清理音频资源
            if HAS_PYAUDIO and self.pyaudio_instance:
                self.pyaudio_instance.terminate()
                self.pyaudio_instance = None
            
            return {"success": True, "message": "连接已断开"}
            
        except Exception as e:
            return {"success": False, "error": f"断开连接失败: {e}"}

# 全局客户端实例
_client = None

def get_client() -> QwenRealtimeVoiceClient:
    """获取客户端实例"""
    global _client
    if _client is None:
        _client = QwenRealtimeVoiceClient()
    return _client

@mcp.tool()
async def connect_to_qwen_realtime() -> str:
    """连接到千问Omni实时语音API"""
    try:
        client = get_client()
        result = await client.connect()
        
        if result["success"]:
            return f"✅ 成功连接到千问Omni实时API\n会话ID: {result['session_id']}"
        else:
            return f"❌ 连接失败: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"❌ 连接错误: {str(e)}"

@mcp.tool()
async def start_voice_conversation_with_interrupt() -> str:
    """启动支持实时打断的语音对话功能"""
    try:
        client = get_client()
        
        # 连接API
        connect_result = await client.connect()
        if not connect_result["success"]:
            return f"❌ 连接失败: {connect_result.get('error')}"
        
        # 初始化音频
        audio_result = client.init_audio()
        if not audio_result["success"]:
            return f"❌ 音频初始化失败: {audio_result.get('error')}"
        
        # 开始录音
        record_result = client.start_recording()
        if not record_result["success"]:
            return f"❌ 录音启动失败: {record_result.get('error')}"
        
        return """✅ 支持实时打断的语音对话已启动！
        
🎙️ 现在你可以：
   • 直接对着麦克风说话
   • AI会自动识别并回复
   • ⚡ **随时打断AI的回复** - 只需开始说话即可
   • 使用 stop_voice_conversation() 停止对话
        
💡 新功能特性：
   - 🔄 实时语音活动检测
   - ⚡ 智能打断AI回复
   - 🎵 优化的音频缓冲机制
   - 📢 更敏感的语音检测
        
请开始说话，系统会自动检测你的语音输入！"""
        
    except Exception as e:
        return f"❌ 启动语音对话失败: {str(e)}"

@mcp.tool()
async def start_voice_conversation() -> str:
    """启动完整的语音对话功能（向后兼容版本）"""
    return await start_voice_conversation_with_interrupt()

@mcp.tool()
async def stop_voice_conversation() -> str:
    """停止语音对话"""
    try:
        client = get_client()
        
        # 停止录音
        stop_result = client.stop_recording()
        if not stop_result["success"]:
            return f"⚠️ 停止录音时出现问题: {stop_result.get('error')}"
        
        # 断开连接
        disconnect_result = await client.disconnect()
        if not disconnect_result["success"]:
            return f"⚠️ 断开连接时出现问题: {disconnect_result.get('error')}"
        
        return """✅ 语音对话已停止
        
🔇 已完成：
   • 停止音频录制
   • 停止AI语音播放
   • 关闭WebSocket连接
   • 清理音频资源"""
        
    except Exception as e:
        return f"❌ 停止语音对话失败: {str(e)}"

@mcp.tool()
def get_voice_status() -> str:
    """获取语音对话状态"""
    try:
        client = get_client()
        
        status = {
            "连接状态": "已连接" if client.is_connected else "未连接",
            "录音状态": "录音中" if client.is_recording else "已停止",
            "AI说话状态": "说话中" if getattr(client, 'is_ai_speaking', False) else "未说话",
            "打断检测": "已检测到" if getattr(client, 'interrupt_detected', False) else "正常",
            "会话ID": client.session_id or "无"
        }
        
        status_text = "📊 当前语音对话状态：\n"
        for key, value in status.items():
            status_text += f"   • {key}: {value}\n"
        
        return status_text
        
    except Exception as e:
        return f"❌ 获取状态失败: {str(e)}"

@mcp.tool()
async def test_interrupt_feature() -> str:
    """测试实时打断功能"""
    try:
        client = get_client()
        
        if not client.is_connected:
            return "❌ 请先连接语音服务"
        
        if not client.is_recording:
            return "❌ 请先启动语音对话"
        
        # 模拟打断
        if hasattr(client, '_interrupt_ai_response'):
            await client._interrupt_ai_response()
            return """✅ 打断功能测试完成
            
🧪 测试结果：
   • 已触发打断逻辑
   • 清空了音频播放缓冲区
   • 发送了取消信号给服务器
   
💡 在实际使用中，只需开始说话即可自动触发打断功能"""
        else:
            return "❌ 打断功能不可用，请检查客户端版本"
            
    except Exception as e:
        return f"❌ 测试打断功能失败: {str(e)}"

if __name__ == "__main__":
    # 启动MCP服务器
    mcp.run() 