#!/usr/bin/env python3
"""
Realtime Voice Interactive MCP Server
FractFlow架构 - MCP工具服务器

功能：为FractFlow提供实时语音交互工具
支持：通用语音模式，适用于快速对话场景
特色：
- 实时语音识别+响应
- 低延迟交互体验
- 动态音量检测打断
- 分形架构Agent嵌套调用
"""

import asyncio
import os
import sys
import json
import logging
import threading
from typing import Any, Dict, List, Optional

# 添加项目根目录到Python路径（支持直接运行和模块导入）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))  # 向上三级到项目根目录
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置日志（静默模式以避免MCP通信干扰）
logging.basicConfig(level=logging.WARNING)

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("❌ 错误：无法导入FastMCP，请确保已安装mcp包")
    sys.exit(1)

# 根据运行环境选择不同的导入方式
try:
    # 当作为模块导入时使用相对导入
    from .realtime_voice_interactive import RealtimeVoiceInteractiveAgent
    from .voice_config import setup_api_keys
except ImportError:
    # 当直接运行时使用绝对导入
    from tools.core.realtime_voice_interactive.realtime_voice_interactive import RealtimeVoiceInteractiveAgent
    from tools.core.realtime_voice_interactive.voice_config import setup_api_keys

# Global state
voice_task = None
stop_event = threading.Event()

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
    try:
        from .realtime_voice_interactive import run_realtime_voice_interactive
    except ImportError:
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
    # MCP服务器启动，使用标准IO传输方式
    mcp.run() 