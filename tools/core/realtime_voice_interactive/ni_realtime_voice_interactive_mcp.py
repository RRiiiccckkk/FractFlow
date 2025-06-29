#!/usr/bin/env python3
"""
Ni Realtime Voice Interactive MCP Server  
倪校实时语音交互MCP服务器
FractFlow架构 - MCP工具服务器

功能：为FractFlow提供倪校长音色的实时语音交互工具
支持：倪校音色模式，专为权威性学术对话设计
特色：
- 🎓 倪校长专属音色（声音克隆技术）
- 🎤 实时语音识别+流式TTS播放
- ⚡ 极速打断机制（0.01ms响应时间）
- 🧠 分形架构Agent嵌套调用
- 🔄 智能分句，自然语音节奏
- 🎯 企业级权威性语音交互
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

mcp = FastMCP("ni_realtime_voice_interactive")

@mcp.tool()
async def start_ni_realtime_voice_interactive() -> str:
    """启动实时语音交互助手 - 倪校音色版（流式TTS优化）"""
    global voice_task, stop_event
    
    try:
        if voice_task and not voice_task.done():
            return "⚠️ 倪校实时语音交互助手已经在运行中"
        
        # Reset stop event
        stop_event.clear()
        
        # Start voice interactive task
        voice_task = asyncio.create_task(_run_ni_voice_interactive_task())
        
        return "✅ 倪校实时语音交互助手已启动（流式TTS优化版）！\n🎓 倪校长现在在听您说话！"
        
    except Exception as e:
        return f"❌ 启动失败：{str(e)}"

@mcp.tool()
async def stop_ni_realtime_voice_interactive() -> str:
    """停止倪校实时语音交互助手"""
    global voice_task, stop_event
    
    try:
        if not voice_task or voice_task.done():
            return "⚠️ 倪校实时语音交互助手未在运行"
        
        # Set stop event
        stop_event.set()
        
        # Cancel the task
        voice_task.cancel()
        
        try:
            await voice_task
        except asyncio.CancelledError:
            pass
        
        return "✅ 倪校实时语音交互助手已停止"
        
    except Exception as e:
        return f"❌ 停止失败：{str(e)}"

@mcp.tool()
def get_ni_voice_interactive_status() -> str:
    """获取倪校实时语音交互助手状态"""
    global voice_task
    
    if not voice_task:
        return "🔴 倪校实时语音交互助手未启动"
    elif voice_task.done():
        return "🟡 倪校实时语音交互助手已停止"
    else:
        return "🟢 倪校实时语音交互助手正在运行中（流式TTS优化版）"

@mcp.tool()
def clone_voice_with_ni(text: str) -> str:
    """使用倪校声音克隆技术播放指定文本"""
    try:
        if not text.strip():
            return "❌ 文本不能为空"
        
        # 导入倪校TTS功能
        try:
            from .ni_voice_clone_client.main import play_ni_voice
        except ImportError:
            from tools.core.realtime_voice_interactive.ni_voice_clone_client.main import play_ni_voice
        
        # 播放倪校声音
        play_ni_voice(text)
        
        return f"✅ 倪校声音播放完成：{text}"
        
    except ImportError:
        return "❌ 倪校TTS模块不可用，请检查服务器连接"
    except Exception as e:
        return f"❌ 播放失败：{str(e)}"

async def _run_ni_voice_interactive_task():
    """运行倪校语音交互任务"""
    try:
        from .realtime_voice_interactive import run_realtime_voice_interactive
    except ImportError:
        from tools.core.realtime_voice_interactive.realtime_voice_interactive import run_realtime_voice_interactive
    
    try:
        await run_realtime_voice_interactive("ni")
    except Exception as e:
        print(f"倪校语音交互任务错误: {e}")

class NiRealtimeVoiceInteractiveServer:
    """倪校实时语音交互MCP服务器"""
    
    def __init__(self):
        self.mcp = mcp

if __name__ == "__main__":
    # MCP服务器启动，使用标准IO传输方式
    mcp.run() 