#!/usr/bin/env python3
"""
千问Omni实时语音智能体 v2.1
支持实时语音打断功能
"""

import asyncio
import sys
import os
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from FractFlow.agent import Agent
from FractFlow.infra.config import ConfigManager

class QwenRealtimeVoiceAgent(Agent):
    """千问Omni实时语音智能体"""
    
    def __init__(self, config=None):
        # 创建配置管理器
        if config is None:
            config = ConfigManager()
            # 设置默认配置
            config.set('agent.provider', 'qwen')
        
        # 初始化基类
        super().__init__(config=config, name="qwenrealtimevoiceagent_agent")
        
        # 添加语音工具
        tool_path = str(Path(__file__).parent / "qwen_realtime_voice_mcp.py")
        self.add_tool(tool_path, "qwen_realtime_voice")
    
    async def process_voice_command(self, command: str) -> str:
        """处理语音命令"""
        # 确保Agent已初始化
        await self.initialize()
        
        if command.lower() in ["开始语音对话", "start voice", "语音对话"]:
            return await self._tool_executor.execute_tool(
                "qwen_realtime_voice", 
                "start_voice_conversation_with_interrupt", 
                {}
            )
        elif command.lower() in ["停止语音对话", "stop voice", "结束对话"]:
            return await self._tool_executor.execute_tool(
                "qwen_realtime_voice", 
                "stop_voice_conversation", 
                {}
            )
        elif command.lower() in ["语音状态", "voice status", "状态"]:
            return await self._tool_executor.execute_tool(
                "qwen_realtime_voice", 
                "get_voice_status", 
                {}
            )
        elif command.lower() in ["测试打断", "test interrupt", "打断测试"]:
            return await self._tool_executor.execute_tool(
                "qwen_realtime_voice", 
                "test_interrupt_feature", 
                {}
            )
        else:
            return await self.process_query(command)

def main():
    parser = argparse.ArgumentParser(description="千问Omni实时语音智能体 v2.1")
    parser.add_argument("--interactive", action="store_true", help="启动交互模式")
    parser.add_argument("--voice", action="store_true", help="直接启动语音对话")
    args = parser.parse_args()
    
    # 设置环境变量 - 请在环境变量中设置您的API密钥
    # os.environ['QWEN_API_KEY'] = 'your_qwen_api_key_here'
    # os.environ['DASHSCOPE_API_KEY'] = 'your_dashscope_api_key_here'
    
    agent = QwenRealtimeVoiceAgent()
    
    if args.voice:
        # 直接启动语音对话模式
        asyncio.run(start_voice_mode(agent))
    elif args.interactive:
        # 启动交互模式
        asyncio.run(start_interactive_mode(agent))
    else:
        print("请使用 --interactive 或 --voice 参数")
        print("  --interactive: 启动文本交互模式")
        print("  --voice: 直接启动语音对话模式")

async def start_voice_mode(agent):
    """启动语音对话模式"""
    print("🎙️ 千问Omni实时语音对话模式 v2.1")
    print("✨ 支持实时语音打断功能")
    print("=" * 50)
    
    try:
        # 启动语音对话
        result = await agent.process_voice_command("开始语音对话")
        print(result)
        
        if "✅" in result:
            print("\n💡 语音对话已启动，请开始说话...")
            print("⚡ 在AI说话时可以随时打断")
            print("⌨️ 按 Ctrl+C 结束对话")
            
            # 保持运行状态
            while True:
                await asyncio.sleep(1)
                
    except KeyboardInterrupt:
        print("\n🛑 正在停止语音对话...")
        result = await agent.process_voice_command("停止语音对话")
        print(result)
        print("👋 再见！")

async def start_interactive_mode(agent):
    """启动交互模式"""
    print("🤖 千问Omni实时语音智能体 v2.1 - 交互模式")
    print("✨ 支持实时语音打断功能")
    print("=" * 60)
    print("可用命令:")
    print("  🎙️ '开始语音对话' - 启动支持打断的语音对话")
    print("  🛑 '停止语音对话' - 停止语音对话")
    print("  📊 '语音状态' - 查看当前状态")
    print("  🧪 '测试打断' - 测试打断功能")
    print("  ❓ 其他文本 - 普通对话")
    print("  🚪 'exit' - 退出程序")
    print("=" * 60)
    
    try:
        while True:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye', '退出']:
                # 确保停止语音对话
                try:
                    await agent.process_voice_command("停止语音对话")
                except:
                    pass
                break
            
            if not user_input:
                continue
                
            try:
                response = await agent.process_voice_command(user_input)
                print(f"\n助手: {response}")
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                
    except KeyboardInterrupt:
        print("\n\n🛑 正在退出...")
        try:
            await agent.process_voice_command("停止语音对话")
        except:
            pass
    
    print("👋 再见！")

if __name__ == "__main__":
    main() 