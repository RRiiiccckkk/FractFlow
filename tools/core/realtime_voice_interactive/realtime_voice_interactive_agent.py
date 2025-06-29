#!/usr/bin/env python3
"""
realtime_voice_interactive_agent.py
Author: FractFlow Team
Brief: FractFlow Agent for Realtime Voice Interactive Assistant - Default Voice Mode

FractFlow Agent Entry Point for Default Voice Mode
"""

import asyncio
import argparse
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from FractFlow.agent import Agent

class RealtimeVoiceInteractiveAgent(Agent):
    """实时语音交互助手 Agent - 默认音色版"""
    
    def __init__(self):
        super().__init__()
        self.current_task = None
        
    async def initialize(self):
        """初始化 Agent"""
        print("🎤 实时语音交互助手 Agent 初始化中...")
        await super().initialize()
        
    async def start_voice_interactive(self):
        """启动语音交互功能"""
        try:
            from tools.core.realtime_voice_interactive.realtime_voice_interactive import run_realtime_voice_interactive
            print("🎤 启动实时语音交互助手（默认音色版）...")
            await run_realtime_voice_interactive("default")
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            
    async def run_interactive_mode(self):
        """运行交互模式"""
        print("🎤 进入实时语音交互模式...")
        await self.start_voice_interactive()

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Realtime Voice Interactive Agent")
    parser.add_argument("--voice-interactive", action="store_true", 
                       help="Start voice interactive mode")
    parser.add_argument("--interactive", action="store_true",
                       help="Start interactive mode")
    args = parser.parse_args()
    
    agent = RealtimeVoiceInteractiveAgent()
    await agent.initialize()
    
    if args.voice_interactive:
        await agent.start_voice_interactive()
    elif args.interactive:
        await agent.run_interactive_mode()
    else:
        # Default: Register with orchestrator
        agent.register_tools([
            ("tools/core/realtime_voice_interactive/realtime_voice_interactive_mcp.py", "realtime_voice_interactive")
        ])
        
        # Start the agent
        await agent.start()

if __name__ == "__main__":
    asyncio.run(main()) 