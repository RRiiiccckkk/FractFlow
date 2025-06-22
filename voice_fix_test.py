#!/usr/bin/env python3
"""
语音检测修复测试脚本
解决OPPO耳机兼容性问题，尝试多种音频设备和参数
"""

import asyncio
import os
import sys
import json

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient
try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

def select_best_audio_device():
    """选择最适合的音频设备"""
    if not HAS_PYAUDIO:
        print("❌ PyAudio不可用")
        return None, None
    
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()
    
    print("🎵 可用音频设备:")
    input_devices = []
    
    for i in range(device_count):
        info = p.get_device_info_by_index(i)
        if info['maxInputChannels'] > 0:
            print(f"  {i}: {info['name']} (采样率: {info['defaultSampleRate']})")
            input_devices.append((i, info))
    
    # 优先选择MacBook内置麦克风
    for device_id, info in input_devices:
        if "MacBook" in info['name'] and "Microphone" in info['name']:
            print(f"✅ 选择内置麦克风: {info['name']}")
            p.terminate()
            return device_id, info
    
    # 如果没有内置麦克风，选择第一个可用设备
    if input_devices:
        device_id, info = input_devices[0]
        print(f"✅ 选择设备: {info['name']}")
        p.terminate()
        return device_id, info
    
    p.terminate()
    return None, None

class FixedQwenRealtimeVoiceClient(QwenRealtimeVoiceClient):
    """修复版的千问语音客户端"""
    
    def __init__(self, device_id=None, api_key=None):
        super().__init__(api_key)
        self.preferred_device_id = device_id
        
    async def _configure_session(self):
        """配置会话参数 - 更敏感的VAD设置"""
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
                    "threshold": 0.1,  # 更低阈值
                    "prefix_padding_ms": 100,  # 更短前缀
                    "silence_duration_ms": 300  # 更短静音时间
                },
                "temperature": 0.7,
                "max_response_output_tokens": 2048
            }
        }
        
        await self.websocket.send(json.dumps(config))
        print("⚙️ 会话配置完成（使用超敏感VAD设置）")
    
    def init_audio(self):
        """初始化音频系统 - 指定设备"""
        if not HAS_PYAUDIO:
            return {"success": False, "error": "PyAudio not available"}
        
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            
            # 获取设备信息
            if self.preferred_device_id is not None:
                device_info = self.pyaudio_instance.get_device_info_by_index(self.preferred_device_id)
                print(f"🎤 使用指定设备: {device_info['name']}")
            else:
                device_info = self.pyaudio_instance.get_default_input_device_info()
                print(f"🎤 使用默认设备: {device_info['name']}")
            
            return {"success": True, "message": "音频系统初始化成功"}
            
        except Exception as e:
            return {"success": False, "error": f"音频初始化失败: {e}"}
    
    def start_recording(self):
        """开始录音 - 使用指定设备"""
        if not HAS_PYAUDIO or not self.pyaudio_instance:
            audio_result = self.init_audio()
            if not audio_result["success"]:
                return audio_result
        
        try:
            # 创建输入流，指定设备
            self.input_stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self.preferred_device_id,
                frames_per_buffer=1024
            )
            
            self.is_recording = True
            self.stop_event.clear()
            self.stop_playback_event.clear()
            
            # 启动线程
            import threading
            self.recording_thread = threading.Thread(target=self._recording_worker)
            self.recording_thread.start()
            
            self.processing_thread = threading.Thread(target=self._processing_worker)
            self.processing_thread.start()
            
            self.audio_playback_thread = threading.Thread(target=self._audio_playback_worker)
            self.audio_playback_thread.start()
            
            print("🎤 录音已开始（使用修复版设置）")
            return {"success": True, "message": "录音开始"}
            
        except Exception as e:
            print(f"❌ 录音启动失败: {e}")
            return {"success": False, "error": f"录音启动失败: {e}"}

async def test_fixed_voice_interaction():
    """测试修复版语音交互"""
    print("🔧 语音检测修复测试")
    print("=" * 50)
    
    # 选择最佳音频设备
    device_id, device_info = select_best_audio_device()
    if device_id is None:
        print("❌ 没有找到合适的音频设备")
        return
    
    # 创建修复版客户端
    client = FixedQwenRealtimeVoiceClient(device_id=device_id)
    
    try:
        # 连接API
        print("🔗 正在连接千问Omni API...")
        connect_result = await client.connect()
        if not connect_result["success"]:
            print(f"❌ 连接失败: {connect_result['error']}")
            return
        
        print(f"✅ 连接成功！会话ID: {connect_result['session_id']}")
        
        # 初始化音频
        print("🎵 正在初始化音频系统...")
        audio_result = client.init_audio()
        if not audio_result["success"]:
            print(f"❌ 音频初始化失败: {audio_result['error']}")
            return
        
        print("✅ 音频系统初始化成功")
        
        # 开始录音
        print("🎤 正在启动录音...")
        record_result = client.start_recording()
        if not record_result["success"]:
            print(f"❌ 录音启动失败: {record_result['error']}")
            return
        
        print("✅ 录音已启动")
        
        print("\n" + "=" * 60)
        print("✅ 修复版语音交互已启动！")
        print("\n💡 修复内容:")
        print(f"   🎤 音频设备: {device_info['name']}")
        print("   ⚡ VAD阈值: 0.1 (超敏感)")
        print("   ⏱️ 延迟优化: 100ms前缀, 300ms静音")
        print("   🔧 设备兼容性修复")
        print("\n🎙️ 现在请对着麦克风说话测试:")
        print("   • '你好' - 简单测试")
        print("   • '请介绍一下自己' - 长对话测试")
        print("   • 在AI回答时打断测试")
        print("=" * 60)
        
        # 等待用户测试
        while True:
            try:
                command = input("\n输入 'status' 查看状态，'quit' 退出: ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    break
                elif command == 'status':
                    print(f"📊 连接状态: {'已连接' if client.is_connected else '未连接'}")
                    print(f"🎤 录音状态: {'录音中' if client.is_recording else '已停止'}")
                    print(f"🤖 AI说话: {'说话中' if getattr(client, 'is_ai_speaking', False) else '未说话'}")
                    print(f"⚡ 打断检测: {'已检测到' if getattr(client, 'interrupt_detected', False) else '正常'}")
                else:
                    print("❓ 未知命令，请输入 'status' 或 'quit'")
                    
            except KeyboardInterrupt:
                print("\n🛑 收到中断信号")
                break
            except EOFError:
                print("\n🛑 输入结束")
                break
    
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    finally:
        # 清理资源
        print("\n🧹 正在清理资源...")
        try:
            client.stop_recording()
            await client.disconnect()
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️ 清理资源时出现问题: {e}")
        
        print("\n🎉 修复测试完成！")

if __name__ == "__main__":
    asyncio.run(test_fixed_voice_interaction()) 