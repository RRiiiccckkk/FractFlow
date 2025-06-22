#!/usr/bin/env python3
"""
快速打断功能测试脚本
"""

import asyncio
import os
import sys
from pathlib import Path

# 设置环境变量 - 请在环境变量中设置您的API密钥
# os.environ['QWEN_API_KEY'] = 'your_qwen_api_key_here'
# os.environ['DASHSCOPE_API_KEY'] = 'your_dashscope_api_key_here'

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient

async def quick_test():
    """快速测试打断功能"""
    print("⚡ 千问Omni实时打断功能快速测试")
    print("=" * 50)
    
    client = QwenRealtimeVoiceClient()
    
    try:
        # 1. 连接API
        print("🔗 正在连接...")
        result = await client.connect()
        if not result["success"]:
            print(f"❌ 连接失败: {result.get('error')}")
            return
        print("✅ 连接成功")
        
        # 2. 初始化音频
        print("🎵 初始化音频...")
        audio_result = client.init_audio()
        if not audio_result["success"]:
            print(f"❌ 音频失败: {audio_result.get('error')}")
            return
        print("✅ 音频就绪")
        
        # 3. 开始录音
        print("🎤 启动录音...")
        record_result = client.start_recording()
        if not record_result["success"]:
            print(f"❌ 录音失败: {record_result.get('error')}")
            return
        print("✅ 录音启动")
        
        print("\n" + "=" * 50)
        print("🧪 开始测试 - 请按以下步骤操作：")
        print("")
        print("第1步：说出一个长问题")
        print("   建议：'请详细介绍一下人工智能的发展历史'")
        print("")
        print("第2步：等待AI开始回复")
        print("   观察：出现 '💬 AI: ...' 消息")
        print("")
        print("第3步：在AI说话中途开始说话")
        print("   期望：看到 '⚡ [检测到打断，停止AI语音播放]'")
        print("")
        print("第4步：继续新的问题")
        print("   验证：AI能正常响应新输入")
        print("=" * 50)
        
        # 保持运行30秒进行测试
        print("\n🚀 测试开始！（30秒自动结束）")
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        print("\n🛑 测试被中断")
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
    finally:
        print("\n🧹 清理资源...")
        client.stop_recording()
        await client.disconnect()
        print("✅ 测试结束")

if __name__ == "__main__":
    asyncio.run(quick_test()) 