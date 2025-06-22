#!/usr/bin/env python3
"""
千问Omni实时语音对话 - 简单启动脚本
"""

import asyncio
import os
import sys
import signal
from pathlib import Path

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量 - 请在环境变量中设置您的API密钥
# os.environ['QWEN_API_KEY'] = 'your_qwen_api_key_here'
# os.environ['DASHSCOPE_API_KEY'] = 'your_dashscope_api_key_here'

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import get_client

class SimpleVoiceChat:
    """简单的语音聊天会话"""
    
    def __init__(self):
        self.client = None
        self.is_running = False
        
    async def start(self):
        """启动语音聊天"""
        print("🎙️ 千问Omni实时语音对话 v2.1")
        print("✨ 新功能：支持实时语音打断")
        print("=" * 50)
        
        try:
            self.client = get_client()
            self.is_running = True
            
            # 连接API
            print("🔗 正在连接千问Omni API...")
            connect_result = await self.client.connect()
            if not connect_result["success"]:
                print(f"❌ 连接失败: {connect_result.get('error')}")
                return
            
            # 初始化音频
            print("🎵 正在初始化音频系统...")
            audio_result = self.client.init_audio()
            if not audio_result["success"]:
                print(f"❌ 音频初始化失败: {audio_result.get('error')}")
                return
            
            # 开始录音
            print("🎤 正在启动录音...")
            record_result = self.client.start_recording()
            if not record_result["success"]:
                print(f"❌ 录音启动失败: {record_result.get('error')}")
                return
            
            print("\n" + "=" * 50)
            print("✅ 语音对话已启动！")
            print("\n💡 使用指南:")
            print("   🎙️ 直接对着麦克风说话")
            print("   🤖 AI会自动识别并语音回复")
            print("   ⚡ 在AI说话时可以随时打断（直接开始说话）")
            print("   ⌨️ 按 Ctrl+C 结束对话")
            print("=" * 50)
            print("\n🎤 请开始说话...")
            
            # 保持运行状态
            while self.is_running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n👋 用户主动结束对话")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """清理资源"""
        print("\n🛑 正在停止语音对话...")
        self.is_running = False
        
        if self.client:
            # 停止录音
            self.client.stop_recording()
            
            # 断开连接
            await self.client.disconnect()
        
        print("✅ 语音对话已停止，资源已清理")
        print("👋 再见！")

def signal_handler(signum, frame):
    """信号处理器"""
    print("\n收到停止信号...")
    # 这里不能直接调用async函数，只能设置标志
    sys.exit(0)

async def main():
    """主函数"""
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动语音聊天
    chat = SimpleVoiceChat()
    await chat.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序被中断")
    except Exception as e:
        print(f"程序错误: {e}") 