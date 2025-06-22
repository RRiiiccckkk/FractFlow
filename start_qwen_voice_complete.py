#!/usr/bin/env python3
"""
千问Omni实时语音对话 - 完整启动脚本
一键启动所有功能，支持多种启动模式
"""

import asyncio
import os
import sys
import argparse
import signal
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional

# 设置项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 设置环境变量 - 请在环境变量中设置您的API密钥
# os.environ['QWEN_API_KEY'] = 'your_qwen_api_key_here'
# os.environ['DASHSCOPE_API_KEY'] = 'your_dashscope_api_key_here'

class QwenVoiceStarter:
    """千问语音启动器"""
    
    def __init__(self):
        self.processes = []
        self.current_mode = None
        
    def print_banner(self):
        """打印启动横幅"""
        print("\n" + "=" * 70)
        print("🎤 千问Omni实时语音对话系统 v2.1")
        print("✨ 支持实时语音打断功能")
        print("🚀 完整启动脚本")
        print("=" * 70)
        
    def print_menu(self):
        """打印功能菜单"""
        print("\n📋 可用功能模式：")
        print("  1️⃣  简单语音对话 (推荐)")
        print("  2️⃣  Agent交互模式")
        print("  3️⃣  打断功能测试")
        print("  4️⃣  Web可视化界面")
        print("  5️⃣  快速打断测试")
        print("  6️⃣  显示状态信息")
        print("  0️⃣  退出程序")
        print("-" * 50)
        
    async def start_simple_voice(self):
        """启动简单语音对话"""
        print("\n🎙️ 启动简单语音对话模式...")
        self.current_mode = "simple_voice"
        
        try:
            from tools.core.qwen_realtime_voice.qwen_realtime_voice_mcp import QwenRealtimeVoiceClient
            
            client = QwenRealtimeVoiceClient()
            
            # 连接API
            print("🔗 正在连接千问Omni API...")
            connect_result = await client.connect()
            if not connect_result["success"]:
                print(f"❌ 连接失败: {connect_result.get('error')}")
                return
            
            print(f"✅ 连接成功！会话ID: {connect_result['session_id']}")
            
            # 初始化音频
            print("🎵 初始化音频系统...")
            audio_result = client.init_audio()
            if not audio_result["success"]:
                print(f"❌ 音频初始化失败: {audio_result.get('error')}")
                return
            
            print("✅ 音频系统就绪")
            
            # 开始录音
            print("🎤 启动语音录制...")
            record_result = client.start_recording()
            if not record_result["success"]:
                print(f"❌ 录音启动失败: {record_result.get('error')}")
                return
            
            print("\n" + "🎉" * 20)
            print("✅ 千问Omni实时语音对话已启动！")
            print("\n💡 使用指南：")
            print("   🎙️ 直接对着麦克风说话")
            print("   🤖 AI会自动识别并语音回复")
            print("   ⚡ 在AI说话时可以随时打断（直接开始说话）")
            print("   ⌨️ 按 Ctrl+C 结束对话")
            print("🎉" * 20)
            
            print("\n🎤 请开始说话...")
            
            # 保持运行状态
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\n\n🛑 正在停止语音对话...")
                client.stop_recording()
                await client.disconnect()
                print("✅ 语音对话已停止")
                
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            
    def start_agent_mode(self):
        """启动Agent交互模式"""
        print("\n🤖 启动Agent交互模式...")
        self.current_mode = "agent"
        
        try:
            cmd = [sys.executable, "tools/core/qwen_realtime_voice/qwen_realtime_voice_agent.py", "--interactive"]
            subprocess.run(cmd, cwd=project_root)
        except KeyboardInterrupt:
            print("\n🛑 Agent模式已退出")
        except Exception as e:
            print(f"❌ Agent启动失败: {e}")
            
    def start_interrupt_test(self):
        """启动打断功能测试"""
        print("\n🧪 启动打断功能测试...")
        self.current_mode = "interrupt_test"
        
        try:
            cmd = [sys.executable, "test_voice_interrupt.py"]
            subprocess.run(cmd, cwd=project_root)
        except KeyboardInterrupt:
            print("\n🛑 测试已中断")
        except Exception as e:
            print(f"❌ 测试启动失败: {e}")
            
    def start_web_interface(self):
        """启动Web可视化界面"""
        print("\n🌐 启动Web可视化界面...")
        self.current_mode = "web"
        
        try:
            # 检查是否存在Web界面文件
            web_file = project_root / "qwen_voice_web.py"
            if not web_file.exists():
                print("📝 正在创建Web界面...")
                self.create_web_interface()
            
            print("🚀 启动Web服务器...")
            cmd = [sys.executable, "qwen_voice_web.py"]
            process = subprocess.Popen(cmd, cwd=project_root)
            self.processes.append(process)
            
            # 等待服务器启动
            import time
            time.sleep(2)
            
            # 打开浏览器
            webbrowser.open("http://localhost:8000")
            print("🌐 Web界面已在浏览器中打开：http://localhost:8000")
            print("⌨️ 按 Ctrl+C 停止Web服务器")
            
            # 等待进程结束
            process.wait()
            
        except KeyboardInterrupt:
            print("\n🛑 正在停止Web服务器...")
            self.cleanup_processes()
        except Exception as e:
            print(f"❌ Web界面启动失败: {e}")
            
    def start_quick_test(self):
        """启动快速打断测试"""
        print("\n⚡ 启动快速打断测试...")
        self.current_mode = "quick_test"
        
        try:
            cmd = [sys.executable, "quick_interrupt_test.py"]
            subprocess.run(cmd, cwd=project_root)
        except KeyboardInterrupt:
            print("\n🛑 快速测试已中断")
        except Exception as e:
            print(f"❌ 快速测试启动失败: {e}")
            
    def show_status(self):
        """显示系统状态"""
        print("\n📊 系统状态信息：")
        print("-" * 40)
        
        # 检查Python环境
        print(f"🐍 Python版本: {sys.version.split()[0]}")
        print(f"📁 项目路径: {project_root}")
        
        # 检查依赖
        try:
            import pyaudio
            print("🎵 PyAudio: ✅ 已安装")
        except ImportError:
            print("🎵 PyAudio: ❌ 未安装")
            
        try:
            import websockets
            print("🌐 WebSockets: ✅ 已安装")
        except ImportError:
            print("🌐 WebSockets: ❌ 未安装")
            
        # 检查环境变量
        api_key = os.getenv('QWEN_API_KEY')
        if api_key:
            print(f"🔑 API密钥: ✅ 已配置 (...{api_key[-6:]})")
        else:
            print("🔑 API密钥: ❌ 未配置")
            
        # 检查文件
        files_to_check = [
            "tools/core/qwen_realtime_voice/qwen_realtime_voice_mcp.py",
            "tools/core/qwen_realtime_voice/qwen_realtime_voice_agent.py",
            "qwen_voice_chat.py",
            "test_voice_interrupt.py"
        ]
        
        print("\n📄 核心文件检查：")
        for file in files_to_check:
            file_path = project_root / file
            if file_path.exists():
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file}")
                
        print("-" * 40)
        
    def create_web_interface(self):
        """创建Web可视化界面"""
        # 这个方法会在后面创建Web界面文件
        pass
        
    def cleanup_processes(self):
        """清理后台进程"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                try:
                    process.kill()
                except:
                    pass
        self.processes.clear()
        
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print("\n🛑 收到退出信号...")
        self.cleanup_processes()
        sys.exit(0)
        
    async def interactive_menu(self):
        """交互式菜单"""
        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.print_banner()
        
        while True:
            self.print_menu()
            
            try:
                choice = input("请选择功能模式 (0-6): ").strip()
                
                if choice == "0":
                    print("\n👋 再见！")
                    break
                elif choice == "1":
                    await self.start_simple_voice()
                elif choice == "2":
                    self.start_agent_mode()
                elif choice == "3":
                    self.start_interrupt_test()
                elif choice == "4":
                    self.start_web_interface()
                elif choice == "5":
                    self.start_quick_test()
                elif choice == "6":
                    self.show_status()
                else:
                    print("❓ 无效选择，请输入 0-6")
                    
                if choice != "0":
                    print("\n🔄 返回主菜单...")
                    input("按 Enter 继续...")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 程序被中断")
                break
            except EOFError:
                print("\n\n🛑 输入结束")
                break
                
        self.cleanup_processes()

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="千问Omni实时语音对话完整启动脚本")
    parser.add_argument("--mode", choices=["simple", "agent", "test", "web", "quick"], 
                       help="直接启动指定模式")
    parser.add_argument("--status", action="store_true", help="显示系统状态")
    
    args = parser.parse_args()
    
    starter = QwenVoiceStarter()
    
    if args.status:
        starter.show_status()
        return
        
    if args.mode:
        if args.mode == "simple":
            asyncio.run(starter.start_simple_voice())
        elif args.mode == "agent":
            starter.start_agent_mode()
        elif args.mode == "test":
            starter.start_interrupt_test()
        elif args.mode == "web":
            starter.start_web_interface()
        elif args.mode == "quick":
            starter.start_quick_test()
    else:
        # 默认启动交互式菜单
        asyncio.run(starter.interactive_menu())

if __name__ == "__main__":
    main() 