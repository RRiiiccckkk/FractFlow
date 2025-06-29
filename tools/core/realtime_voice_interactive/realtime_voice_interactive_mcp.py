#!/usr/bin/env python3
"""
realtime_voice_interactive_mcp.py
Author: FractFlow Team
Brief: MCP server for Realtime Voice Interactive Assistant - Default Voice Mode

TOOL_DESCRIPTION = '''
实时语音交互助手 - 默认音色版

这是一个基于千问Omni的实时语音对话系统，专为HKUST-GZ设计。

核心功能：
- 🎤 实时语音识别：支持中文语音输入，自动转换为文本
- 🔊 实时语音合成：使用系统Chelsie音色进行语音输出
- ⚡ 智能快速打断：100-300ms极速响应，支持用户随时打断AI回答
- 🔧 动态音量检测：自动适应环境噪音，智能连续性验证
- 🛑 多级打断机制：立即音频停止+队列清理+状态重置

使用方式：
start_realtime_voice_interactive() - 启动默认音色语音助手
stop_realtime_voice_interactive() - 停止语音助手
get_voice_interactive_status() - 查询运行状态

注意事项：
- 需要麦克风和扬声器设备
- 建议在安静环境中使用以获得最佳体验
- 系统会自动校准背景噪音（前几秒钟）
'''
"""

import asyncio
import threading
from mcp.server.fastmcp import FastMCP

# Global state
voice_task = None
stop_event = threading.Event()

from tools.core.realtime_voice_interactive.realtime_voice_interactive import RealtimeVoiceInteractiveAgent
from tools.core.realtime_voice_interactive.voice_config import setup_api_keys

mcp = FastMCP("realtime_voice_interactive")

@mcp.tool()
async def start_realtime_voice_interactive() -> str:
    """启动实时语音交互助手 - 默认音色版"""
    global voice_task, stop_event
    
    try:
        if voice_task and not voice_task.done():
            return "⚠️ 实时语音交互助手已经在运行中"
        
        # Reset stop event
        stop_event.clear()
        
        # Start voice interactive task
        voice_task = asyncio.create_task(_run_voice_interactive_task())
        
        return "✅ 实时语音交互助手已启动（默认音色版）！\n🎤 现在可以开始语音对话了"
        
    except Exception as e:
        return f"❌ 启动失败：{str(e)}"

@mcp.tool()
async def stop_realtime_voice_interactive() -> str:
    """停止实时语音交互助手"""
    global voice_task, stop_event
    
    try:
        if not voice_task or voice_task.done():
            return "⚠️ 实时语音交互助手未在运行"
        
        # Set stop event
        stop_event.set()
        
        # Cancel the task
        voice_task.cancel()
        
        try:
            await voice_task
        except asyncio.CancelledError:
            pass
        
        return "✅ 实时语音交互助手已停止"
        
    except Exception as e:
        return f"❌ 停止失败：{str(e)}"

@mcp.tool()
def get_voice_interactive_status() -> str:
    """获取实时语音交互助手状态"""
    global voice_task
    
    if not voice_task:
        return "🔴 实时语音交互助手未启动"
    elif voice_task.done():
        return "🟡 实时语音交互助手已停止"
    else:
        return "🟢 实时语音交互助手正在运行中（默认音色版）"

async def _run_voice_interactive_task():
    """运行语音交互任务"""
    from tools.core.realtime_voice_interactive.realtime_voice_interactive import run_realtime_voice_interactive
    
    try:
        await run_realtime_voice_interactive("default")
    except Exception as e:
        print(f"语音交互任务错误: {e}")

class RealtimeVoiceInteractiveServer:
    """实时语音交互MCP服务器"""
    
    def __init__(self):
        self.mcp = mcp

if __name__ == "__main__":
    import sys
    mcp.run(sys.argv) 