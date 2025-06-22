#!/usr/bin/env python3
"""
深度语音调试工具
检查音频输入级别、服务器响应和VAD检测问题
"""

import asyncio
import json
import os
import sys
import numpy as np
import base64
import threading
import queue
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient

class DeepDebugVoiceClient(QwenRealtimeVoiceClient):
    """深度调试版语音客户端"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        self.audio_levels = []
        self.server_responses = []
        self.vad_events = []
        self.debug_mode = True
        
    def _recording_worker(self):
        """增强的录音工作线程 - 包含音频级别监控"""
        print("🎵 调试录音线程启动")
        
        chunk_count = 0
        total_volume = 0
        max_volume = 0
        
        while self.is_recording and not self.stop_event.is_set():
            try:
                # 读取音频数据
                audio_data = self.input_stream.read(1024, exception_on_overflow=False)
                
                # 分析音频级别
                audio_array = np.frombuffer(audio_data, dtype=np.int16)
                if len(audio_array) > 0:
                    volume = np.sqrt(np.mean(audio_array.astype(np.float64)**2))
                    if not np.isnan(volume):
                        total_volume += volume
                        max_volume = max(max_volume, volume)
                        self.audio_levels.append(volume)
                        
                        # 实时显示音频级别
                        if chunk_count % 20 == 0:  # 每20个块显示一次
                            bar_length = int(min(volume / 100, 50))
                            bar = "█" * bar_length + "░" * (50 - bar_length)
                            avg_volume = total_volume / (chunk_count + 1) if chunk_count > 0 else 0
                            print(f"\r🎤 音量: [{bar}] 当前:{volume:.0f} 平均:{avg_volume:.0f} 最高:{max_volume:.0f}", end="", flush=True)
                
                # 放入队列
                if not self.audio_queue.full():
                    self.audio_queue.put(audio_data)
                
                chunk_count += 1
                time.sleep(0.01)
                
            except Exception as e:
                if self.is_recording:
                    print(f"\n❌ 录音错误: {e}")
                break
                
        print(f"\n🛑 调试录音线程结束 - 处理了 {chunk_count} 个音频块")
        print(f"📊 音频统计: 平均音量 {total_volume/max(chunk_count,1):.0f}, 最高音量 {max_volume:.0f}")
    
    async def _handle_responses(self):
        """增强的响应处理 - 详细记录所有服务器事件"""
        try:
            message = await asyncio.wait_for(self.websocket.recv(), timeout=0.01)
            response_data = json.loads(message)
            
            response_type = response_data.get("type", "")
            timestamp = time.strftime("%H:%M:%S")
            
            # 记录所有服务器响应
            self.server_responses.append({
                "timestamp": timestamp,
                "type": response_type,
                "data": response_data
            })
            
            # 详细打印重要事件
            if response_type == "input_audio_buffer.speech_started":
                print(f"\n🎤 [{timestamp}] 检测到语音开始!")
                self.vad_events.append({"timestamp": timestamp, "event": "speech_started"})
                if self.is_ai_speaking:
                    await self._interrupt_ai_response()
                    
            elif response_type == "input_audio_buffer.speech_stopped":
                print(f"\n🔇 [{timestamp}] 检测到语音结束")
                self.vad_events.append({"timestamp": timestamp, "event": "speech_stopped"})
                self.interrupt_detected = False
                
            elif response_type == "input_audio_buffer.committed":
                print(f"\n📝 [{timestamp}] 音频缓冲区已提交")
                
            elif response_type == "conversation.item.created":
                item = response_data.get("item", {})
                if item.get("type") == "message":
                    role = item.get("role", "unknown")
                    print(f"\n💬 [{timestamp}] 创建{role}消息")
                    
            elif response_type == "response.created":
                print(f"\n🤖 [{timestamp}] AI开始响应")
                
            elif response_type == "response.audio_transcript.delta":
                transcript = response_data.get("delta", "")
                if transcript.strip():
                    print(f"💬 AI: {transcript}", end="", flush=True)
                    
            elif response_type == "response.audio_transcript.done":
                print()  # 换行
                
            elif response_type == "response.audio.delta":
                audio_base64 = response_data.get("delta", "")
                if audio_base64 and not self.interrupt_detected:
                    self.audio_buffer.put(audio_base64)
                    self.is_ai_speaking = True
                    
            elif response_type == "response.done":
                print(f"\n✅ [{timestamp}] AI响应完成")
                self.is_ai_speaking = False
                
            elif response_type == "error":
                error_info = response_data.get("error", {})
                print(f"\n❌ [{timestamp}] 服务器错误: {error_info}")
                
            else:
                # 记录其他事件但不打印详细信息
                print(f"\n📡 [{timestamp}] {response_type}")
                
        except asyncio.TimeoutError:
            pass
        except Exception as e:
            if "websocket" not in str(e).lower():
                print(f"\n❌ 响应处理错误: {e}")
    
    def get_debug_report(self):
        """生成调试报告"""
        print("\n" + "="*60)
        print("📊 调试报告")
        print("="*60)
        
        # 音频统计
        if self.audio_levels:
            avg_level = np.mean(self.audio_levels)
            max_level = np.max(self.audio_levels)
            active_chunks = len([l for l in self.audio_levels if l > 100])
            
            print(f"🎤 音频统计:")
            print(f"   平均音量: {avg_level:.0f}")
            print(f"   最高音量: {max_level:.0f}")
            print(f"   活跃音频块: {active_chunks}/{len(self.audio_levels)} ({active_chunks/len(self.audio_levels)*100:.1f}%)")
            
            if max_level < 50:
                print("   ⚠️ 音量过低 - 可能麦克风有问题")
            elif active_chunks < len(self.audio_levels) * 0.1:
                print("   ⚠️ 语音活动很少 - 尝试更大声说话")
            else:
                print("   ✅ 音频输入正常")
        
        # VAD事件统计
        print(f"\n🔍 VAD事件: {len(self.vad_events)} 个")
        for event in self.vad_events[-5:]:  # 显示最近5个事件
            print(f"   {event['timestamp']}: {event['event']}")
        
        # 服务器响应统计
        response_types = {}
        for resp in self.server_responses:
            resp_type = resp["type"]
            response_types[resp_type] = response_types.get(resp_type, 0) + 1
        
        print(f"\n📡 服务器响应统计:")
        for resp_type, count in response_types.items():
            print(f"   {resp_type}: {count} 次")
        
        # 问题诊断
        print(f"\n🔧 问题诊断:")
        if len(self.vad_events) == 0:
            print("   ❌ 服务器未检测到任何语音活动")
            print("   💡 可能原因:")
            print("      • VAD阈值设置过高")
            print("      • 音频格式不匹配")
            print("      • 麦克风权限问题")
            print("      • 网络传输问题")
        else:
            print("   ✅ 服务器检测到语音活动")

async def run_deep_debug_test():
    """运行深度调试测试"""
    print("🔍 深度语音调试测试")
    print("="*50)
    
    client = DeepDebugVoiceClient()
    
    try:
        # 连接
        print("🔗 连接API...")
        connect_result = await client.connect()
        if not connect_result["success"]:
            print(f"❌ 连接失败: {connect_result['error']}")
            return
        
        print(f"✅ 连接成功: {connect_result['session_id']}")
        
        # 初始化音频 - 强制使用内置麦克风
        client.pyaudio_instance = pyaudio.PyAudio()
        
        # 找到MacBook内置麦克风
        device_id = None
        for i in range(client.pyaudio_instance.get_device_count()):
            info = client.pyaudio_instance.get_device_info_by_index(i)
            if "MacBook" in info['name'] and "Microphone" in info['name']:
                device_id = i
                break
        
        if device_id is None:
            print("❌ 未找到MacBook内置麦克风")
            return
        
        print(f"🎤 使用设备: {client.pyaudio_instance.get_device_info_by_index(device_id)['name']}")
        
        # 创建输入流
        client.input_stream = client.pyaudio_instance.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=16000,  # 强制使用16kHz
            input=True,
            input_device_index=device_id,
            frames_per_buffer=1024
        )
        
        client.is_recording = True
        client.stop_event.clear()
        
        # 启动线程
        client.recording_thread = threading.Thread(target=client._recording_worker)
        client.recording_thread.start()
        
        client.processing_thread = threading.Thread(target=client._processing_worker)
        client.processing_thread.start()
        
        print("\n" + "="*60)
        print("🎤 深度调试模式已启动")
        print("📊 实时显示音频级别和服务器响应")
        print("🗣️ 请大声清晰地说话:")
        print("   • '你好千问' - 测试基础识别")
        print("   • '现在几点了' - 测试问答")
        print("   • 观察音量条和服务器响应")
        print("="*60)
        
        # 运行30秒测试
        for i in range(30):
            await asyncio.sleep(1)
            print(f"\r⏱️ 测试时间: {30-i}秒  ", end="", flush=True)
        
        print("\n\n🛑 测试结束")
        
    except Exception as e:
        print(f"❌ 测试错误: {e}")
    
    finally:
        # 生成调试报告
        client.get_debug_report()
        
        # 清理
        client.is_recording = False
        client.stop_event.set()
        
        if client.recording_thread:
            client.recording_thread.join(timeout=2)
        if client.processing_thread:
            client.processing_thread.join(timeout=2)
        
        if client.input_stream:
            client.input_stream.close()
        if client.pyaudio_instance:
            client.pyaudio_instance.terminate()
        
        await client.disconnect()
        print("\n✅ 调试测试完成")

if __name__ == "__main__":
    asyncio.run(run_deep_debug_test()) 