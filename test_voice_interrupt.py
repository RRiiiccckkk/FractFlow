#!/usr/bin/env python3
"""
千问Omni实时语音打断功能测试脚本
测试语音对话中的实时打断能力
"""

import asyncio
import os
import sys

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient

async def test_interrupt_feature():
    """测试实时打断功能"""
    print("🧪 千问Omni实时语音打断功能测试")
    print("=" * 50)
    
    # 创建客户端
    client = QwenRealtimeVoiceClient()
    
    try:
        # 连接API
        print("1️⃣ 正在连接千问Omni API...")
        connect_result = await client.connect()
        if not connect_result["success"]:
            print(f"❌ 连接失败: {connect_result['error']}")
            return
        
        print(f"✅ 连接成功！会话ID: {connect_result['session_id']}")
        
        # 初始化音频
        print("\n2️⃣ 正在初始化音频系统...")
        audio_result = client.init_audio()
        if not audio_result["success"]:
            print(f"❌ 音频初始化失败: {audio_result['error']}")
            return
        
        print("✅ 音频系统初始化成功")
        
        # 开始录音
        print("\n3️⃣ 启动语音对话...")
        record_result = client.start_recording()
        if not record_result["success"]:
            print(f"❌ 录音启动失败: {record_result['error']}")
            return
        
        print("✅ 语音对话已启动")
        
        print("\n" + "=" * 50)
        print("🎤 实时打断功能测试说明：")
        print("📢 1. 先让AI开始说话（问一个需要较长回答的问题）")
        print("⚡ 2. 在AI说话过程中，直接开始说话进行打断")
        print("🔍 3. 观察系统是否能检测到打断并停止AI语音")
        print("💡 4. 系统会显示 '⚡ [检测到打断，停止AI语音播放]' 消息")
        print("🛑 5. 输入 'quit' 或 'exit' 退出测试")
        print("=" * 50)
        
        print("\n🎯 测试场景建议：")
        print("   • 问：'请详细介绍一下人工智能的发展历史'")
        print("   • 问：'能否解释一下量子计算的原理？'")
        print("   • 问：'请讲一个长故事'")
        print("   • 然后在AI回答过程中开始说话，测试打断效果")
        
        print("\n🚀 开始测试！请开始说话...")
        
        # 等待用户输入退出命令
        while True:
            try:
                command = input("\n输入 'status' 查看状态，'test' 手动测试打断，'quit' 退出: ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    break
                elif command == 'status':
                    print(f"📊 连接状态: {'已连接' if client.is_connected else '未连接'}")
                    print(f"🎤 录音状态: {'录音中' if client.is_recording else '已停止'}")
                    print(f"🤖 AI说话: {'说话中' if getattr(client, 'is_ai_speaking', False) else '未说话'}")
                    print(f"⚡ 打断检测: {'已检测到' if getattr(client, 'interrupt_detected', False) else '正常'}")
                elif command == 'test':
                    if hasattr(client, '_interrupt_ai_response'):
                        await client._interrupt_ai_response()
                        print("✅ 手动触发打断测试完成")
                    else:
                        print("❌ 打断功能不可用")
                else:
                    print("❓ 未知命令，请输入 'status'、'test' 或 'quit'")
                    
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
        
        print("\n🎉 测试完成！")

def print_interrupt_features():
    """打印实时打断功能特性说明"""
    print("\n🔥 实时打断功能特性：")
    print("=" * 40)
    print("⚡ 智能语音活动检测")
    print("   - 实时监听用户语音输入")
    print("   - 降低VAD阈值提高敏感度")
    print("   - 减少延迟时间")
    
    print("\n🛑 AI响应打断机制")
    print("   - 检测到用户说话立即停止AI播放")
    print("   - 清空音频播放缓冲区")
    print("   - 发送取消信号给服务器")
    
    print("\n🎵 优化的音频处理")
    print("   - 独立的音频播放线程")
    print("   - 支持打断的同步播放")
    print("   - 智能缓冲区管理")
    
    print("\n🔄 状态管理")
    print("   - 实时跟踪AI说话状态")
    print("   - 打断检测状态监控")
    print("   - 多线程状态同步")

if __name__ == "__main__":
    print_interrupt_features()
    asyncio.run(test_interrupt_feature()) 