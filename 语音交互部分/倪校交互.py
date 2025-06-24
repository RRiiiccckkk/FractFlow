#!/usr/bin/env python3
"""
倪校简化版语音交互程序 v1.0
香港科技大学广州校长倪明选教授语音克隆版本
简化版 - 移除实时打断功能，采用传统对话模式
"""

import asyncio
import os
import sys
import json
import time
import wave
import io
import requests
from typing import Optional

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
from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient
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
    "streaming_mode": "false"  # 简化版使用非流式模式
}

# 倪校系统指令（简化版）
NIXIAO_SIMPLE_INSTRUCTION = """你是香港科技大学广州校长倪明选教授。

作为校长，请用温和而权威的语调回答问题：
• 回答要简洁明了，避免过长的回复
• 体现校长的权威性和亲和力
• 适当表达对学校的自豪感
• 关心学生成长和发展

请保持回答简洁，适合语音交流。"""

class NiXiaoSimpleVoiceAssistant(QwenRealtimeVoiceClient):
    """倪校简化版语音助手 - 无打断功能，传统对话模式"""
    
    def __init__(self, api_key=None):
        super().__init__(api_key)
        
        # 简化版状态管理
        self.gptsovits_available = False
        self.waiting_for_user = True
        self.conversation_active = False
        self.current_response_text = ""
        
        print("🎓 倪校简化版语音助手初始化完成")
    
    async def _configure_session(self):
        """配置会话 - 简化版配置"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text"],  # 仅文本模式
                "instructions": NIXIAO_SIMPLE_INSTRUCTION,
                "input_audio_format": "pcm16",
                "turn_detection": {
                    "type": "server_vad", 
                    "threshold": 0.3,  # 提高阈值，减少误触发
                    "prefix_padding_ms": 500,
                    "silence_duration_ms": 1000  # 增加静音时间
                },
                "temperature": 0.7,
                "max_response_output_tokens": 1024  # 限制回答长度
            }
        }
        
        await self.websocket.send(json.dumps(config))
        print("⚙️ 倪校简化版会话配置完成")
        
        # 检查GPT-SoVITS服务
        await self._check_gptsovits_service()
    
    async def _check_gptsovits_service(self):
        """检查GPT-SoVITS服务状态"""
        try:
            test_params = GPT_SOVITS_PARAMS.copy()
            test_params["text"] = "测试连接"
            
            response = requests.get(GPT_SOVITS_URL, params=test_params, timeout=3)
            self.gptsovits_available = response.status_code == 200
            
            if self.gptsovits_available:
                print("✅ GPT-SoVITS服务连接成功")
            else:
                print(f"⚠️ GPT-SoVITS服务异常: {response.status_code}")
                
        except Exception as e:
            self.gptsovits_available = False
            print(f"❌ GPT-SoVITS服务不可用: {e}")
    
    async def _call_gptsovits_simple(self, text: str) -> Optional[bytes]:
        """简化版GPT-SoVITS调用"""
        if not self.gptsovits_available or not text.strip():
            return None
            
        try:
            params = GPT_SOVITS_PARAMS.copy()
            params["text"] = text
            
            print(f"🔊 倪校正在回答: {text[:25]}...")
            
            # 同步请求，简化处理
            response = requests.get(GPT_SOVITS_URL, params=params, timeout=20)
            
            if response.status_code == 200:
                return response.content
            else:
                print(f"❌ TTS生成失败: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ TTS调用错误: {e}")
            return None
    
    def _play_wav_simple(self, wav_data: bytes) -> bool:
        """简化版WAV音频播放"""
        if not HAS_PYAUDIO or not wav_data:
            return False
            
        try:
            wav_io = io.BytesIO(wav_data)
            wav = wave.open(wav_io, "rb")
            
            # 创建音频流
            stream = self.pyaudio_instance.open(
                format=self.pyaudio_instance.get_format_from_width(wav.getsampwidth()),
                channels=wav.getnchannels(),
                rate=wav.getframerate(),
                output=True,
                frames_per_buffer=1024
            )
            
            # 播放音频
            wav_io.seek(44)  # 跳过WAV头
            while True:
                audio_chunk = wav_io.read(1024)
                if not audio_chunk:
                    break
                stream.write(audio_chunk)
            
            # 清理资源
            stream.stop_stream()
            stream.close()
            wav.close()
            
            return True
            
        except Exception as e:
            print(f"❌ 音频播放错误: {e}")
            return False
    
    async def _simple_conversation_loop(self):
        """简化版对话循环 - 传统模式"""
        print("\n🎤 请开始对话...")
        
        while self.conversation_active:
            try:
                # 等待用户输入
                self.waiting_for_user = True
                user_input = await self._wait_for_user_input()
                
                if user_input:
                    print(f"👤 您说: {user_input}")
                    
                    # 获取AI回答
                    self.waiting_for_user = False
                    ai_response = await self._get_ai_response(user_input)
                    
                    if ai_response:
                        print(f"💬 倪校: {ai_response}")
                        
                        # 生成并播放语音
                        if self.gptsovits_available:
                            await self._generate_and_play_voice(ai_response)
                        
                    print("\n" + "="*50)
                
                # 短暂等待后继续下一轮对话
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"❌ 对话循环错误: {e}")
                await asyncio.sleep(2)
    
    async def _wait_for_user_input(self) -> Optional[str]:
        """等待用户语音输入"""
        user_transcript = ""
        timeout_count = 0
        
        while self.waiting_for_user and self.conversation_active:
            try:
                # 检查WebSocket消息
                message = await asyncio.wait_for(self.websocket.recv(), timeout=0.1)
                data = json.loads(message)
                response_type = data.get("type", "")
                
                if response_type == "conversation.item.input_audio_transcription.completed":
                    transcript = data.get("transcript", "").strip()
                    if transcript:
                        return transcript
                
                elif response_type == "error":
                    error_msg = data.get("error", {}).get("message", "未知错误")
                    print(f"❌ 语音识别错误: {error_msg}")
                
            except asyncio.TimeoutError:
                timeout_count += 1
                # 30秒无输入提醒
                if timeout_count > 300:  # 30秒
                    print("💭 [等待您的问题...]")
                    timeout_count = 0
                continue
            except Exception as e:
                print(f"❌ 输入处理错误: {e}")
                await asyncio.sleep(1)
        
        return None
    
    async def _get_ai_response(self, user_input: str) -> Optional[str]:
        """获取AI文本回答"""
        try:
            # 发送用户消息
            await self._send_user_message(user_input)
            
            # 请求AI回答
            response_request = {"type": "response.create"}
            await self.websocket.send(json.dumps(response_request))
            
            # 等待AI回答
            ai_response = ""
            while True:
                message = await asyncio.wait_for(self.websocket.recv(), timeout=10)
                data = json.loads(message)
                response_type = data.get("type", "")
                
                if response_type == "response.audio_transcript.delta":
                    transcript = data.get("delta", "")
                    ai_response += transcript
                
                elif response_type == "response.audio_transcript.done":
                    return ai_response.strip() if ai_response.strip() else None
                
                elif response_type == "response.done":
                    return ai_response.strip() if ai_response.strip() else None
                
                elif response_type == "error":
                    error_msg = data.get("error", {}).get("message", "AI回答错误")
                    print(f"❌ {error_msg}")
                    return None
            
        except asyncio.TimeoutError:
            print("⏰ AI回答超时")
            return None
        except Exception as e:
            print(f"❌ 获取AI回答错误: {e}")
            return None
    
    async def _send_user_message(self, text: str):
        """发送用户消息到对话"""
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message", 
                "role": "user",
                "content": [{"type": "text", "text": text}]
            }
        }
        await self.websocket.send(json.dumps(message))
    
    async def _generate_and_play_voice(self, text: str):
        """生成并播放倪校语音 - 简化版"""
        try:
            print("🎵 正在生成倪校语音...")
            
            # 调用GPT-SoVITS
            audio_data = await self._call_gptsovits_simple(text)
            
            if audio_data:
                print("▶️ 正在播放倪校语音...")
                success = self._play_wav_simple(audio_data)
                if success:
                    print("✅ 语音播放完成")
                else:
                    print("❌ 语音播放失败")
            else:
                print("❌ 语音生成失败")
                
        except Exception as e:
            print(f"❌ 语音处理错误: {e}")
    
    async def start_simple_conversation(self):
        """启动简化版对话"""
        try:
            # 初始化音频
            if HAS_PYAUDIO:
                self.init_audio()
            
            # 开始录音
            result = self.start_recording()
            if not result["success"]:
                print(f"❌ 录音启动失败: {result['error']}")
                return False
            
            self.conversation_active = True
            
            # 启动对话循环
            await self._simple_conversation_loop()
            
        except Exception as e:
            print(f"❌ 对话启动错误: {e}")
            return False
        
        return True
    
    async def stop_simple_conversation(self):
        """停止简化版对话"""
        self.conversation_active = False
        self.waiting_for_user = False
        
        # 停止录音
        self.stop_recording()
        
        # 断开连接
        await self.disconnect()

async def run_nixiao_simple_assistant():
    """运行倪校简化版语音助手"""
    print("🎓 香港科技大学广州 - 倪校简化版语音助手")
    print("🔊 President Ni Mingxuan Voice Assistant - Simple Edition")
    print("=" * 60)
    
    setup_api_keys()
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    
    if not api_key:
        print("❌ 未找到API密钥")
        return
    
    assistant = NiXiaoSimpleVoiceAssistant(api_key)
    
    try:
        print("🔗 正在连接千问Omni API...")
        await assistant.connect()
        
        print("\n✅ 倪校简化版语音助手已启动！")
        print("\n🎓 功能特点:")
        print("   • 倪校声音克隆 (GPT-SoVITS)")
        print("   • 传统对话模式") 
        print("   • 简化操作流程")
        print("   • 按 Ctrl+C 退出")
        print("\n💡 使用说明:")
        print("   • 等待提示后开始说话")
        print("   • 等待倪校回答完成")
        print("   • 继续下一轮对话")
        print("=" * 60)
        print("\n🎤 您好！我是香港科技大学广州校长倪明选。")
        
        # 启动对话
        await assistant.start_simple_conversation()
        
    except KeyboardInterrupt:
        print("\n🛑 用户主动退出")
    except Exception as e:
        print(f"\n❌ 系统错误: {e}")
    finally:
        print("\n🧹 正在关闭倪校语音助手...")
        await assistant.stop_simple_conversation()
        print("✅ 倪校语音助手已安全关闭")
        print("🎓 感谢使用HKUST-GZ倪校语音助手！")

if __name__ == "__main__":
    asyncio.run(run_nixiao_simple_assistant()) 