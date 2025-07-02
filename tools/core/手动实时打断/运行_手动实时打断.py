#!/usr/bin/env python3
"""
FractFlow 手动实时打断语音控制 - 快速启动脚本
"""

import asyncio
import sys
import os

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from 手动实时打断_agent import SimpleManualVoiceController

def print_banner():
    """打印启动横幅"""
    print("🎤 FractFlow 手动实时打断语音控制")
    print("=" * 60)
    print("⚡ 特色：立即打断AI回答，毫秒级响应")
    print("🧠 功能：智能对话上下文记忆")
    print("📊 监控：完整内存和系统健康监控")
    print("🎨 体验：实时彩色字幕显示")
    print("=" * 60)
    print()

async def main():
    """主函数"""
    print_banner()
    
    try:
        # 创建控制器
        controller = SimpleManualVoiceController()
        
        # 运行交互模式
        result = await controller.run_interactive_mode()
        
        if result["success"]:
            print(f"\n✅ 程序已正常结束：{result.get('message', '')}")
        else:
            print(f"\n❌ 程序异常结束：{result['error']}")
            
    except KeyboardInterrupt:
        print("\n👋 用户主动退出，再见！")
    except Exception as e:
        print(f"\n💥 程序异常：{str(e)}")
        print("请检查环境配置和API密钥设置")

if __name__ == "__main__":
    asyncio.run(main()) 